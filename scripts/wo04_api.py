"""Serve inspection and explicitly requested bounded experiment/replay endpoints."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/platform.yaml",
        help="Reserved platform identity; catalog is explicitly allowlisted",
    )
    parser.add_argument("--preset", choices=("tiny", "sim", "rl", "real"), default="tiny")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Development only: reload the API when project src Python files change",
    )
    args = parser.parse_args()
    import uvicorn

    if args.reload:
        uvicorn.run(
            "src.api.workbench_app:create_app",
            factory=True,
            host=args.host,
            port=args.port,
            reload=True,
            reload_dirs=[str(Path(__file__).resolve().parents[1] / "src")],
        )
    else:
        from src.api.workbench_app import create_app

        uvicorn.run(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
