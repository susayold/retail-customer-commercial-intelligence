"""Validate that the public web snapshot is source-backed and guarded."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ASSIGNMENT_RE = re.compile(r"window\.RETAIL_DASHBOARD_DATA\s*=\s*(\{.*\});\s*$", re.DOTALL)


def load_snapshot(path: Path) -> dict[str, object]:
    match = ASSIGNMENT_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError("web snapshot assignment not found")
    value = json.loads(match.group(1))
    if not isinstance(value, dict):
        raise ValueError("web snapshot must be a JSON object")
    return value


def verify(path: Path) -> dict[str, object]:
    snapshot = load_snapshot(path)
    meta = snapshot.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("snapshot metadata is missing")
    required = {"run_id", "quality_gate", "source_folder_id", "source_files", "observation_index"}
    missing = sorted(required - set(meta))
    if missing:
        raise ValueError(f"snapshot metadata missing: {', '.join(missing)}")
    if meta.get("quality_gate") != "READY":
        raise ValueError("snapshot quality gate is not READY")
    if not meta.get("source_files"):
        raise ValueError("snapshot has no source-file provenance")
    serialized = path.read_text(encoding="utf-8").lower()
    forbidden = ("gross margin", "gross_margin")
    found = [token for token in forbidden if token in serialized]
    if found:
        raise ValueError(f"unsupported web claim marker(s): {', '.join(found)}")
    return {"status": "PASS", "run_id": meta["run_id"], "source_files": len(meta["source_files"])}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=Path("web-dashboard/data.js"))
    args = parser.parse_args()
    print(json.dumps(verify(args.snapshot), ensure_ascii=False))


if __name__ == "__main__":
    main()
