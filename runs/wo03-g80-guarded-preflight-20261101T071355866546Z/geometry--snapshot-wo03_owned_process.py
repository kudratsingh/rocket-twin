"""Small subprocess supervisor for explicitly owned WO-03 worker processes."""

from __future__ import annotations

import ctypes
import errno
import json
import os
import resource
import signal
import subprocess
import time
from collections import deque
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RssCallback = Callable[[int], int]
DescendantsCallback = Callable[[int], Sequence[int]]
CpuCallback = Callable[[int], Any]


class OwnedProcessError(RuntimeError):
    """Raised after failure status and cleanup outcomes have been persisted."""

    def __init__(self, result: dict[str, Any]):
        self.result = result
        reason = result.get("error") or result.get("guard_failure") or "owned process failed"
        super().__init__(str(reason))


def darwin_process_callbacks() -> tuple[RssCallback, DescendantsCallback]:
    """Return RSS and live-descendant readers backed by macOS libproc.

    Descendant enumeration walks only the launched process's child tree via
    ``proc_listchildpids``; it never scans the machine process table.
    """

    class ProcTaskInfo(ctypes.Structure):
        _fields_ = [
            (name, ctypes.c_uint64)
            for name in (
                "virtual",
                "resident",
                "total_user",
                "total_system",
                "threads_user",
                "threads_system",
            )
        ] + [(f"i{i}", ctypes.c_int32) for i in range(12)]

    lib = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    lib.proc_pidinfo.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint64,
        ctypes.c_void_p,
        ctypes.c_int,
    ]
    lib.proc_pidinfo.restype = ctypes.c_int
    lib.proc_listchildpids.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
    lib.proc_listchildpids.restype = ctypes.c_int

    def rss(pid: int) -> int:
        info = ProcTaskInfo()
        ctypes.set_errno(0)
        size = lib.proc_pidinfo(pid, 4, 0, ctypes.byref(info), ctypes.sizeof(info))
        if size == ctypes.sizeof(info):
            return int(info.resident)
        code = ctypes.get_errno()
        if code == errno.ESRCH or size == 0:
            raise ProcessLookupError(code or errno.ESRCH, os.strerror(code or errno.ESRCH), pid)
        if code == errno.EPERM or code == errno.EACCES:
            raise PermissionError(code, os.strerror(code), pid)
        raise OSError(code or errno.EIO, f"proc_pidinfo returned {size}", pid)

    def children(pid: int) -> list[int]:
        capacity = 256
        buffer = (ctypes.c_int * capacity)()
        ctypes.set_errno(0)
        count = lib.proc_listchildpids(pid, buffer, ctypes.sizeof(buffer))
        if count < 0:
            code = ctypes.get_errno()
            if code == errno.ESRCH:
                raise ProcessLookupError(code, os.strerror(code), pid)
            if code in (errno.EPERM, errno.EACCES):
                raise PermissionError(code, os.strerror(code), pid)
            raise OSError(code or errno.EIO, "proc_listchildpids failed", pid)
        if count >= capacity:
            raise RuntimeError("Owned process tree exceeds 255 direct children")
        return [int(child) for child in buffer[:count] if int(child) > 0]

    def descendants(root_pid: int) -> list[int]:
        pending = deque([(root_pid, 0)])
        result: list[int] = []
        seen = {root_pid}
        while pending:
            parent, _depth = pending.popleft()
            try:
                direct = children(parent)
            except ProcessLookupError:
                # A non-root process can exit between adjacent tree queries.
                continue
            for child in direct:
                if child in seen:
                    continue
                seen.add(child)
                result.append(child)
                pending.append((child, 0))
        return result

    return rss, descendants


def _fresh_descendants(
    process: subprocess.Popen[bytes], callback: DescendantsCallback | None
) -> list[int]:
    if callback is None or process.poll() is not None:
        return []
    try:
        pids = [int(pid) for pid in callback(process.pid)]
    except ProcessLookupError:
        if process.poll() is not None:
            return []
        raise
    if process.poll() is not None:
        return []
    if process.pid in pids or any(pid <= 0 for pid in pids):
        raise ValueError("Descendants callback returned the root or an invalid PID")
    return list(dict.fromkeys(pids))


def _signal_fresh_descendants(
    process: subprocess.Popen[bytes],
    callback: DescendantsCallback | None,
    signum: int,
    outcomes: list[dict[str, Any]],
    errors: list[str],
) -> list[int]:
    pids = _fresh_descendants(process, callback)
    # The callback returns breadth-first order; reverse to signal leaf processes first.
    for pid in reversed(pids):
        try:
            os.kill(pid, signum)
            outcomes.append({"pid": pid, "signal": signum, "result": "sent_direct_pid"})
        except ProcessLookupError:
            try:
                still_owned = pid in _fresh_descendants(process, callback)
            except Exception as exc:  # noqa: BLE001 - persist callback failures during cleanup
                errors.append(
                    f"descendant recheck after ESRCH for {pid}: {type(exc).__name__}: {exc}"
                )
                continue
            if not still_owned:
                outcomes.append({"pid": pid, "signal": signum, "result": "already_exited"})
            else:
                errors.append(f"pid {pid} remained in fresh tree after ProcessLookupError")
        except OSError as exc:
            errors.append(
                f"direct signal {signum} to descendant {pid}: {type(exc).__name__}: {exc}"
            )
    return pids


def _cleanup(
    process: subprocess.Popen[bytes],
    descendants_callback: DescendantsCallback | None,
    terminate_grace_s: float,
    outcomes: list[dict[str, Any]],
    errors: list[str],
) -> None:
    if process.poll() is not None:
        return
    deadline = time.monotonic() + max(0.0, terminate_grace_s / 2)
    while process.poll() is None and time.monotonic() < deadline:
        try:
            descendants = _signal_fresh_descendants(
                process, descendants_callback, signal.SIGTERM, outcomes, errors
            )
        except Exception as exc:  # noqa: BLE001 - cleanup must record any callback failure
            errors.append(f"fresh descendant enumeration: {type(exc).__name__}: {exc}")
            descendants = []
        if not descendants:
            break
        time.sleep(0.02)
    if process.poll() is None:
        try:
            process.terminate()
            outcomes.append(
                {"pid": process.pid, "signal": signal.SIGTERM, "result": "popen_terminate"}
            )
        except ProcessLookupError:
            if process.poll() is None:
                errors.append("Popen.terminate raised ProcessLookupError while child remained live")
            else:
                outcomes.append(
                    {"pid": process.pid, "signal": signal.SIGTERM, "result": "already_exited"}
                )
        except OSError as exc:
            errors.append(f"Popen.terminate: {type(exc).__name__}: {exc}")
    try:
        process.wait(timeout=max(0.01, terminate_grace_s / 2))
        outcomes.append({"pid": process.pid, "result": "root_reaped"})
        return
    except subprocess.TimeoutExpired:
        pass
    except ChildProcessError as exc:
        errors.append(f"wait after terminate: {type(exc).__name__}: {exc}")
        return
    try:
        _signal_fresh_descendants(process, descendants_callback, signal.SIGKILL, outcomes, errors)
    except Exception as exc:  # noqa: BLE001 - persist cleanup failures
        errors.append(
            f"fresh descendant enumeration before escalation: {type(exc).__name__}: {exc}"
        )
    try:
        process.kill()
        outcomes.append({"pid": process.pid, "signal": signal.SIGKILL, "result": "popen_kill"})
    except ProcessLookupError:
        if process.poll() is None:
            errors.append("Popen.kill raised ProcessLookupError while child remained live")
        else:
            outcomes.append(
                {"pid": process.pid, "signal": signal.SIGKILL, "result": "already_exited"}
            )
    except OSError as exc:
        errors.append(f"Popen.kill: {type(exc).__name__}: {exc}")
    try:
        process.wait(timeout=max(0.05, terminate_grace_s))
        outcomes.append({"pid": process.pid, "result": "root_reaped_after_kill"})
    except Exception as exc:  # noqa: BLE001 - persist all wait failures
        errors.append(f"wait after kill: {type(exc).__name__}: {exc}")


def _write_status(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    if path.exists():
        temporary.unlink(missing_ok=True)
        raise FileExistsError(f"Refusing to overwrite owned-process status: {path}")
    os.replace(temporary, path)


def run_owned(
    argv: Sequence[str],
    *,
    log_path: Path,
    status_path: Path,
    wall_limit_s: float,
    sample_period_s: float = 0.05,
    rss_callback: RssCallback | None = None,
    descendants_callback: DescendantsCallback | None = None,
    cpu_callback: CpuCallback | None = None,
    rss_limit_bytes: int | None = None,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    terminate_grace_s: float = 1.0,
) -> dict[str, Any]:
    """Run one owned child, logging directly and persisting all terminal outcomes.

    Child stdout/stderr share a file opened before launch. Descendant callbacks
    must freshly return live descendants of the root PID; every descendant signal
    is sent by its direct PID only. The launched root is signaled through Popen.
    Failures are raised as ``OwnedProcessError`` only after status persistence.
    """
    if not argv or not all(isinstance(arg, str) for arg in argv):
        raise ValueError("argv must be a nonempty sequence of strings")
    if min(wall_limit_s, sample_period_s) <= 0 or terminate_grace_s < 0:
        raise ValueError("Wall, sampling periods must be positive and grace nonnegative")
    if rss_limit_bytes is not None and (rss_limit_bytes <= 0 or rss_callback is None):
        raise ValueError("A positive RSS limit requires an RSS callback")
    log_path, status_path = Path(log_path), Path(status_path)
    if log_path.resolve() == status_path.resolve():
        raise ValueError("log_path and status_path must differ")
    started_utc = datetime.now(UTC).isoformat()
    started = time.monotonic()
    self_usage_start = resource.getrusage(resource.RUSAGE_SELF)
    child_usage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
    result: dict[str, Any] = {
        "status": "starting",
        "success": False,
        "argv": list(argv),
        "pid": None,
        "started_utc": started_utc,
        "log_path": str(log_path),
        "status_path": str(status_path),
        "wall_limit_s": wall_limit_s,
        "rss_limit_bytes": rss_limit_bytes,
        "returncode": None,
        "timed_out": False,
        "guard_failure": None,
        "error": None,
        "wall_samples": [],
        "cpu_samples": [],
        "rss_samples_bytes": [],
        "descendant_pid_samples": [],
        "known_descendant_pids": [],
        "cleanup_outcomes": [],
        "cleanup_errors": [],
        "status_write_error": None,
    }
    failure: Exception | None = None
    process: subprocess.Popen[bytes] | None = None
    log_stream = None
    last_sample = -float("inf")

    def fail(kind: str, message: str, exc: Exception | None = None) -> None:
        nonlocal failure
        result["status"] = "failed"
        result["error"] = {"kind": kind, "message": message}
        if exc is not None:
            failure = exc

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_stream = log_path.open("xb")
        process = subprocess.Popen(
            list(argv),
            cwd=str(cwd) if cwd is not None else None,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log_stream,
            stderr=subprocess.STDOUT,
            close_fds=True,
        )
        result["pid"] = process.pid
        result["status"] = "running"
        result["launch_wall_s"] = time.monotonic() - started
        while True:
            returncode = process.poll()
            now = time.monotonic()
            elapsed = now - started
            if returncode is not None:
                result["returncode"] = returncode
                if result["known_descendant_pids"]:
                    fail(
                        "unexpected_descendants",
                        "owned child exited after live descendants were observed; they were not signaled without fresh parent verification",
                    )
                elif returncode != 0:
                    fail("child_exit", f"owned child exited with return code {returncode}")
                else:
                    result["status"] = "completed"
                    result["success"] = True
                break
            if elapsed >= wall_limit_s:
                result["timed_out"] = True
                result["guard_failure"] = "wall_limit"
                fail("wall_limit", f"owned child exceeded wall limit {wall_limit_s:.6g}s")
                break
            if now - last_sample >= sample_period_s:
                last_sample = now
                supervisor_usage = resource.getrusage(resource.RUSAGE_SELF)
                cpu_sample: dict[str, Any] = {
                    "elapsed_wall_s": elapsed,
                    "supervisor_cpu_user_s": supervisor_usage.ru_utime - self_usage_start.ru_utime,
                    "supervisor_cpu_system_s": supervisor_usage.ru_stime
                    - self_usage_start.ru_stime,
                }
                try:
                    descendants = _fresh_descendants(process, descendants_callback)
                    result["descendant_pid_samples"].append(
                        {"elapsed_wall_s": elapsed, "pids": descendants}
                    )
                    result["known_descendant_pids"] = sorted(
                        set(result["known_descendant_pids"]) | set(descendants)
                    )
                except ProcessLookupError as exc:
                    if process.poll() is None:
                        fail("descendant_reader", f"descendant enumeration failed: {exc}", exc)
                        break
                    descendants = []
                except Exception as exc:  # noqa: BLE001 - report live reader failures
                    if process.poll() is None:
                        fail(
                            "descendant_reader",
                            f"descendant enumeration failed: {type(exc).__name__}: {exc}",
                            exc,
                        )
                        break
                    descendants = []
                result["wall_samples"].append(elapsed)
                if cpu_callback is not None:
                    try:
                        cpu_sample["owned_cpu"] = cpu_callback(process.pid)
                    except ProcessLookupError as exc:
                        if process.poll() is None:
                            fail("cpu_reader", f"CPU reader failed: {exc}", exc)
                            break
                    except PermissionError as exc:
                        if process.poll() is None:
                            fail(
                                "cpu_reader_permission",
                                f"CPU access denied for live child: {exc}",
                                exc,
                            )
                            break
                    except Exception as exc:  # noqa: BLE001 - report callback failures
                        fail("cpu_reader", f"CPU reader failed: {type(exc).__name__}: {exc}", exc)
                        break
                result["cpu_samples"].append(cpu_sample)
                if rss_callback is not None:
                    try:
                        rss_bytes = int(rss_callback(process.pid))
                    except ProcessLookupError as exc:
                        if process.poll() is not None:
                            continue
                        fail(
                            "rss_reader",
                            f"RSS reader failed while process remained live: {exc}",
                            exc,
                        )
                        break
                    except PermissionError as exc:
                        if process.poll() is not None:
                            # A stale-PID query is not a live access-denied failure.
                            continue
                        fail(
                            "rss_reader_permission",
                            f"RSS access denied for live child: {exc}",
                            exc,
                        )
                        break
                    except Exception as exc:  # noqa: BLE001 - report callback failures
                        fail("rss_reader", f"RSS reader failed: {type(exc).__name__}: {exc}", exc)
                        break
                    if rss_bytes < 0:
                        fail("rss_reader", f"RSS callback returned negative byte count {rss_bytes}")
                        break
                    result["rss_samples_bytes"].append(
                        {"elapsed_wall_s": elapsed, "bytes": rss_bytes}
                    )
                    if rss_limit_bytes is not None and rss_bytes > rss_limit_bytes:
                        result["guard_failure"] = "rss_limit"
                        fail(
                            "rss_limit",
                            f"owned child RSS {rss_bytes} exceeds {rss_limit_bytes} bytes",
                        )
                        break
            time.sleep(min(sample_period_s, max(0.0, wall_limit_s - elapsed)))
    except Exception as exc:  # noqa: BLE001 - persist runner failures
        if result["error"] is None:
            fail("runner", f"{type(exc).__name__}: {exc}", exc)
    finally:
        if process is not None:
            if process.poll() is None:
                try:
                    _cleanup(
                        process,
                        descendants_callback,
                        terminate_grace_s,
                        result["cleanup_outcomes"],
                        result["cleanup_errors"],
                    )
                except Exception as exc:  # noqa: BLE001 - preserve cleanup outcome
                    result["cleanup_errors"].append(
                        f"cleanup supervisor: {type(exc).__name__}: {exc}"
                    )
                    if result["error"] is None:
                        fail("cleanup", "owned-child cleanup raised", exc)
            try:
                result["returncode"] = process.wait(timeout=max(0.05, terminate_grace_s))
            except Exception as exc:  # noqa: BLE001 - preserve wait outcome
                result["cleanup_errors"].append(f"final child wait: {type(exc).__name__}: {exc}")
                if result["error"] is None:
                    fail("cleanup", "could not reap launched child", exc)
        if log_stream is not None:
            try:
                log_stream.flush()
                log_stream.close()
            except Exception as exc:  # noqa: BLE001 - preserve logging outcome
                result["cleanup_errors"].append(f"close log: {type(exc).__name__}: {exc}")
                if result["error"] is None:
                    fail("cleanup", "could not close child log", exc)
        if result["cleanup_errors"] and result["error"] is None:
            fail("cleanup", "; ".join(result["cleanup_errors"]))
        child_usage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
        self_usage_end = resource.getrusage(resource.RUSAGE_SELF)
        result["cpu_accounting"] = {
            "child_user_s_delta": child_usage_end.ru_utime - child_usage_start.ru_utime,
            "child_system_s_delta": child_usage_end.ru_stime - child_usage_start.ru_stime,
            "supervisor_user_s_delta": self_usage_end.ru_utime - self_usage_start.ru_utime,
            "supervisor_system_s_delta": self_usage_end.ru_stime - self_usage_start.ru_stime,
            "children_rusage_sampled_after_reap": True,
        }
        result["total_wall_s"] = time.monotonic() - started
        result["finished_utc"] = datetime.now(UTC).isoformat()
        if result["status"] not in ("completed", "failed"):
            result["status"] = "failed"
            if result["error"] is None:
                result["error"] = {
                    "kind": "runner",
                    "message": "run ended without a terminal state",
                }
        result["success"] = result["status"] == "completed" and result["returncode"] == 0
        try:
            _write_status(status_path, result)
        except Exception as exc:  # noqa: BLE001 - record status persistence failure
            result["status_write_error"] = f"{type(exc).__name__}: {exc}"
            failure = failure or exc
    if not result["success"]:
        raise OwnedProcessError(result) from failure
    return result


__all__ = ["OwnedProcessError", "darwin_process_callbacks", "run_owned"]
