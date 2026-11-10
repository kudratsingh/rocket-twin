"""Validate launcher selection without binding a socket or starting a process."""

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest
import uvicorn

ROOT = Path(__file__).resolve().parents[1]


def launcher() -> Any:
    spec = importlib.util.spec_from_file_location(
        "preview_api_launcher_test", ROOT / "scripts/wo04_api.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_api_reload_uses_factory_and_watches_only_source(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    monkeypatch.setattr(uvicorn, "run", lambda *a, **kw: calls.append((a, kw)))
    monkeypatch.setattr(sys, "argv", ["wo04_api.py", "--reload"])
    launcher().main()
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args == ("src.api.workbench_app:create_app",)
    assert kwargs == {
        "factory": True,
        "host": "127.0.0.1",
        "port": 8000,
        "reload": True,
        "reload_dirs": [str(ROOT / "src")],
    }
    assert all("output" not in p and "runs" not in p for p in kwargs["reload_dirs"])


def test_normal_launcher_preserves_nonreload_app_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.api import workbench_app

    marker = object()
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    monkeypatch.setattr(workbench_app, "create_app", lambda: marker)
    monkeypatch.setattr(uvicorn, "run", lambda *a, **kw: calls.append((a, kw)))
    monkeypatch.setattr(sys, "argv", ["wo04_api.py", "--host", "127.0.0.1", "--port", "8000"])
    launcher().main()
    assert calls == [((marker,), {"host": "127.0.0.1", "port": 8000})]
