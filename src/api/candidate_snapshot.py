"""Allowlisted archived candidate projection; never changes active CAD validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException

ALIAS = "experimental-g80-retention-72"
IDENTITY = "90b2a9ad780fc81d11171363432c46088531817ddb6570fe9f800429bde2bdfc"
CAD = "344f646f81e15d42ab54e7d996179581d638c6046bf1d006935b028709eca53f"
INDEX_SHA256 = "53ea17425115ec5ebefe7c1327f95b6cf1c99723bb48306185e382803f03fc26"
FOLDER = "build/wo04-g80-retention-snapshot"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    folder = (root / FOLDER).resolve()
    if not folder.is_relative_to(root.resolve()):
        raise HTTPException(503, "Candidate snapshot path escapes workspace")
    try:
        index_bytes = (folder / "index.json").read_bytes()
        if digest(index_bytes) != INDEX_SHA256:
            raise ValueError("Candidate snapshot index identity mismatch")
        index = json.loads(index_bytes)
        projection_bytes = (folder / "projection.json").read_bytes()
        if digest(projection_bytes) != index["projection_sha256"]:
            raise ValueError("Candidate snapshot projection identity mismatch")
        projection = json.loads(projection_bytes)
        data = projection["data"]
        if (
            index["candidate_identity"] != IDENTITY
            or index["cad_revision_sha256"] != CAD
            or data["identity"]["resolved_spec_sha256"] != IDENTITY
            or data["identity"]["cad_revision_sha256"] != CAD
            or data["id"] != ALIAS
        ):
            raise ValueError("Candidate snapshot configuration identity mismatch")
        ids = [p["id"] for p in data["parts"]]
        if len(ids) != 72 or len(set(ids)) != 72 or set(ids) != set(index["mesh_sha256"]):
            raise ValueError("Candidate snapshot part coverage mismatch")
        return index, projection
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise HTTPException(503, f"Experimental snapshot unavailable: {error}") from error


def mesh(root: Path, part_id: str) -> tuple[Path, str]:
    index, _ = load(root)
    if part_id not in index["mesh_sha256"]:
        raise HTTPException(404, "Unknown candidate part mesh")
    folder = (root / FOLDER).resolve()
    path = (folder / "parts" / f"{part_id}.glb").resolve()
    if not path.is_relative_to(folder / "parts"):
        raise HTTPException(404, "Invalid candidate mesh path")
    try:
        expected = index["mesh_sha256"][part_id]
        if digest(path.read_bytes()) != expected:
            raise ValueError("Candidate mesh hash mismatch")
        return path, expected
    except (OSError, ValueError) as error:
        raise HTTPException(503, f"Experimental snapshot mesh unavailable: {error}") from error
