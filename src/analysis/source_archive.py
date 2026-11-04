"""Verify explicitly archived historical inputs without freezing current code."""

import hashlib
from pathlib import Path

ARCHIVES = {
    (
        "src/vehicle/schema.py",
        "e11d777cce363e45fd07376b45db4bde640cea00fefda8377ced735250de5093",
    ): "data/source-archives/schema-e11d777cce363e45.py.txt"
}


def verified_source(root: Path, relative: str, expected_sha256: str) -> Path:
    """Return exact current or explicitly archived bytes; unknown drift is an error."""
    root = root.resolve()
    current = (root / relative).resolve()
    if not current.is_relative_to(root):
        raise ValueError("Historical input escapes repository")
    if current.is_file() and hashlib.sha256(current.read_bytes()).hexdigest() == expected_sha256:
        return current
    archived = ARCHIVES.get((relative, expected_sha256))
    if archived:
        path = (root / archived).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Historical archive escapes repository")
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha256:
            return path
    raise ValueError(f"Historical input missing or changed without an exact archive: {relative}")
