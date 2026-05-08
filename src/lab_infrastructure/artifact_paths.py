from __future__ import annotations

from pathlib import Path


def next_named_path(root: Path, name: str) -> Path:
    path = root / name
    if not path.exists():
        return path
    return next_numbered_path(root, f"{name}-", n=2)


def next_numbered_path(root: Path, prefix: str, n: int = 1) -> Path:
    while (root / f"{prefix}{n}").exists():
        n += 1
    return root / f"{prefix}{n}"


def artifact_ref(root: Path, artifact_path: Path) -> str:
    return artifact_path.relative_to(root).as_posix()
