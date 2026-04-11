from __future__ import annotations

import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import yaml


def git_head_commit(repo_root: str | Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True, cwd=str(Path(repo_root))
        )
    except Exception:
        return None
    commit = out.strip()
    return commit if commit else None


def git_status(repo_root: str | Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL, text=True, cwd=str(Path(repo_root))
        )
    except Exception:
        return "local changes exist"
    return "no local changes" if out.strip() == "" else "local changes exist"


def read_run_config(path: str | Path) -> dict[str, object]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_run_config(
    path: str | Path,
    payload: Mapping[str, object],
    *,
    repo_root: str | Path,
    git_key_prefix: str,
    schema_version: str = "1",
) -> Path:
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    full_payload = {
        "schema_version": schema_version,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        f"{git_key_prefix}_git_commit": git_head_commit(repo_root),
        f"{git_key_prefix}_git_status": git_status(repo_root),
        **payload,
    }
    with target_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(full_payload, handle, sort_keys=False, allow_unicode=True)
    return target_path
