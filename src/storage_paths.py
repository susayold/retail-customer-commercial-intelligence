"""Guard data and artifact paths so standalone stages remain Drive-only."""

from __future__ import annotations

from pathlib import Path


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def require_drive_path(
    path: Path,
    drive_root: Path | None,
    label: str,
) -> Path:
    """Resolve a path and reject missing, local, or repository-backed roots."""
    if drive_root is None:
        raise SystemExit(f"{label} requires an explicit --drive-root")
    drive = drive_root.expanduser().resolve()
    if not drive.is_dir():
        raise SystemExit(f"Drive root does not exist or is not a directory: {drive}")
    resolved = path.expanduser().resolve()
    if not _inside(resolved, drive):
        raise SystemExit(
            f"{label} must be underneath the declared Drive root: {resolved}"
        )
    repository_root = Path(__file__).resolve().parents[1]
    if _inside(resolved, repository_root):
        raise SystemExit(f"{label} must not be inside the GitHub checkout: {resolved}")
    return resolved
