"""Tiny owned-child supervision tests; no solver or vehicle process is used."""

from __future__ import annotations

import errno
import os
import sys
import time

import pytest

from scripts.wo03_owned_process import (
    OwnedProcessError,
    darwin_process_callbacks,
    run_owned,
)


def _run_failure(argv, tmp_path, **kwargs):
    log_path = tmp_path / "child.log"
    status_path = tmp_path / "status.json"
    with pytest.raises(OwnedProcessError) as raised:
        run_owned(
            argv,
            log_path=log_path,
            status_path=status_path,
            wall_limit_s=kwargs.pop("wall_limit_s", 2.0),
            **kwargs,
        )
    assert log_path.exists()
    assert status_path.exists()
    return raised.value.result, log_path.read_text(), status_path


def test_rapid_exit_logs_stderr_and_ignores_only_disappeared_pid_race(tmp_path):
    calls = []

    def raced_rss(_pid: int) -> int:
        # Ensure the child exits between the supervisor's poll and RSS lookup.
        calls.append(_pid)
        time.sleep(0.05)
        raise PermissionError("stale process query returned access denied")

    result, log, status_path = _run_failure(
        [
            sys.executable,
            "-c",
            "import sys; print('rapid stderr sentinel', file=sys.stderr); sys.exit(7)",
        ],
        tmp_path,
        wall_limit_s=1.0,
        sample_period_s=0.005,
        rss_callback=raced_rss,
    )
    persisted = __import__("json").loads(status_path.read_text())
    assert calls
    assert "rapid stderr sentinel" in log
    assert result["returncode"] == 7
    assert result["error"]["kind"] == "child_exit"
    assert "permission" not in str(result["error"]).lower()
    assert persisted["status"] == "failed"
    assert persisted["cpu_accounting"]["children_rusage_sampled_after_reap"] is True


def test_live_rss_callback_failure_is_persisted_and_child_terminated(tmp_path):
    def broken_rss(_pid: int) -> int:
        raise ProcessLookupError(
            errno.ESRCH, os.strerror(errno.ESRCH), "deliberate live RSS reader ESRCH"
        )

    result, _log, status_path = _run_failure(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        tmp_path,
        sample_period_s=0.01,
        rss_callback=broken_rss,
        terminate_grace_s=0.3,
    )
    assert result["error"]["kind"] == "rss_reader"
    assert "deliberate live RSS reader ESRCH" in result["error"]["message"]
    assert result["returncode"] is not None and result["returncode"] < 0
    assert any(item["result"] == "popen_terminate" for item in result["cleanup_outcomes"])
    assert __import__("json").loads(status_path.read_text())["returncode"] == result["returncode"]


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS waitable-child RSS race control")
def test_rss_esrch_for_waitable_root_is_resolved_as_normal_exit(tmp_path):
    observed = []
    real_rss, _descendants = darwin_process_callbacks()

    def esrch_after_waitable_exit(pid: int) -> int:
        # The supervisor's preceding poll has returned None. While this callback
        # holds that loop turn, no Popen.poll/wait runs. Wait for the actual
        # libproc RSS query to observe root ESRCH, then return that exact race.
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            try:
                real_rss(pid)
            except ProcessLookupError:
                observed.append(pid)
                raise
            time.sleep(0.001)
        raise AssertionError("libproc did not observe root ESRCH during the race-control window")

    result = run_owned(
        [sys.executable, "-c", "import time; time.sleep(0.2); print('exit-after-rss-race')"],
        log_path=tmp_path / "race.log",
        status_path=tmp_path / "race.json",
        wall_limit_s=1.0,
        sample_period_s=0.005,
        rss_callback=esrch_after_waitable_exit,
        descendants_callback=lambda _pid: [],
    )
    assert observed == [result["pid"]]
    assert result["success"] is True
    assert result["returncode"] == 0
    assert result["error"] is None
    assert "exit-after-rss-race" in (tmp_path / "race.log").read_text()
    assert __import__("json").loads((tmp_path / "race.json").read_text())["success"] is True


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS libproc process-ownership probe")
def test_wall_timeout_signals_owned_child_and_grandchild_by_pid(tmp_path):
    rss, descendants = darwin_process_callbacks()
    pid_file = tmp_path / "grandchild.pid"
    child_code = (
        "import subprocess,sys,time,pathlib; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
        f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid)); "
        "time.sleep(30)"
    )
    result, _log, _status_path = _run_failure(
        [sys.executable, "-c", child_code],
        tmp_path,
        wall_limit_s=0.8,
        sample_period_s=0.01,
        rss_callback=rss,
        descendants_callback=descendants,
        rss_limit_bytes=2 * 1024 * 1024 * 1024,
        terminate_grace_s=0.5,
    )
    assert result["timed_out"] is True
    assert result["guard_failure"] == "wall_limit"
    assert result["returncode"] is not None and result["returncode"] < 0
    assert pid_file.exists()
    grandchild_pid = int(pid_file.read_text())
    known = set(result["known_descendant_pids"])
    assert grandchild_pid in known
    assert result["pid"] not in known

    # proc_pidinfo is scoped to the explicitly recorded child PIDs, not a
    # machine-wide listing. Allow the OS a brief interval to finish reaping.
    monitored_pids = known | {int(result["pid"])}
    deadline = time.monotonic() + 2.0
    live = set(monitored_pids)
    while time.monotonic() < deadline and live:
        live = set()
        for pid in monitored_pids:
            try:
                rss(pid)
                live.add(pid)
            except ProcessLookupError:
                pass
        if live:
            time.sleep(0.02)
    assert not live, f"owned PIDs remained after cleanup: {sorted(live)}"
    assert not any("killpg" in str(item).lower() for item in result["cleanup_outcomes"])


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS libproc process-ownership probe")
def test_parent_that_reaps_its_short_child_completes_successfully(tmp_path):
    rss, descendants = darwin_process_callbacks()
    child_code = (
        "import subprocess,sys; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(0.15)']); "
        "p.wait()"
    )
    result = run_owned(
        [sys.executable, "-c", child_code],
        log_path=tmp_path / "reaped-child.log",
        status_path=tmp_path / "reaped-child.json",
        wall_limit_s=2.0,
        sample_period_s=0.005,
        rss_callback=rss,
        descendants_callback=descendants,
        rss_limit_bytes=2 * 1024 * 1024 * 1024,
    )
    assert result["success"] is True
    assert result["returncode"] == 0
    assert result["known_descendant_pids"]
    assert result["historical_descendant_checks"]
    assert all(item["state"] == "gone" for item in result["historical_descendant_checks"])


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS libproc process-ownership probe")
def test_unreaped_short_orphan_fails_closed_without_signaling_history(tmp_path):
    rss, descendants = darwin_process_callbacks()
    pid_file = tmp_path / "orphan.pid"
    child_code = (
        "import pathlib,subprocess,sys,time; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(0.6)']); "
        f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid)); time.sleep(0.1)"
    )
    with pytest.raises(OwnedProcessError) as raised:
        run_owned(
            [sys.executable, "-c", child_code],
            log_path=tmp_path / "orphan.log",
            status_path=tmp_path / "orphan.json",
            wall_limit_s=2.0,
            sample_period_s=0.005,
            rss_callback=rss,
            descendants_callback=descendants,
            rss_limit_bytes=2 * 1024 * 1024 * 1024,
        )
    result = raised.value.result
    assert pid_file.exists()
    orphan_pid = int(pid_file.read_text())
    assert result["error"]["kind"] == "unexpected_descendants"
    checks = {item["pid"]: item for item in result["historical_descendant_checks"]}
    assert checks[orphan_pid]["state"] == "present"
    assert not any(item.get("pid") == orphan_pid for item in result["cleanup_outcomes"])

    # The test orphan has a short natural lifetime; do not signal an unverified
    # historical PID after its parent has exited.
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        try:
            rss(orphan_pid)
        except ProcessLookupError:
            break
        time.sleep(0.02)
    else:
        raise AssertionError(f"short orphan {orphan_pid} did not exit naturally")
