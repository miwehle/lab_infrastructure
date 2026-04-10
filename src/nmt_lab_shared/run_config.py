from __future__ import annotations

import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import yaml


def _current_time() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _current_git_commit(repo_root: str | Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=str(Path(repo_root)),
        )
    except Exception:
        return None
    commit = out.strip()
    return commit if commit else None


def _current_git_status(repo_root: str | Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=str(Path(repo_root)),
        )
    except Exception:
        return "local changes exist"
    return "no local changes" if out.strip() == "" else "local changes exist"


def read_run_config(path: str | Path) -> dict[str, object]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _build_run_config_payload(
    payload: Mapping[str, object],
    *,
    repo_root: str | Path,
    git_key_prefix: str,
    schema_version: str = "1",
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "created_at_utc": _current_time(),
        f"{git_key_prefix}_git_commit": _current_git_commit(repo_root),
        f"{git_key_prefix}_git_status": _current_git_status(repo_root),
        **payload,
    }


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
    full_payload = _build_run_config_payload(
        payload,
        repo_root=repo_root,
        git_key_prefix=git_key_prefix,
        schema_version=schema_version,
    )
    with target_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(full_payload, handle, sort_keys=False, allow_unicode=True)
    return target_path
