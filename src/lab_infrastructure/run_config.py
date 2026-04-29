from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path

import yaml
from pydantic import TypeAdapter, ValidationError


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


def read_run_config_as[T](path: str | Path, config_type: type[T]) -> T:
    config_path = Path(path)
    payload = read_run_config(config_path)
    try:
        return TypeAdapter(config_type).validate_python(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid config in {config_path}: {exc}") from exc


def run[T, R](runner: Callable[[T], R], config_path: str | Path, config_type: type[T] | None = None) -> R:
    """Call a runner function with YAML config validation.

    The YAML payload is validated against the config type with Pydantic's
    TypeAdapter, so config fields are type-checked before the runner is called.

    If `config_type` is omitted, infer it by convention:
    runner function name -> PascalCase + RunConfig.

    Example:
    filter -> FilterRunConfig
    """

    def runner_config_name() -> str:
        return "".join(part.capitalize() for part in runner.__name__.split("_")) + "RunConfig"

    def infer_run_config_type() -> type[T]:
        package_name = runner.__module__.split(".", maxsplit=1)[0]
        config_name = runner_config_name()
        package = import_module(package_name)
        try:
            return getattr(package, config_name)
        except AttributeError as exc:
            message = f"Could not infer config type {config_name} from package {package_name}"
            raise ValueError(message) from exc

    return runner(read_run_config_as(config_path, config_type or infer_run_config_type()))


def run_cli[T, R](runner: Callable[[T], R], config_type: type[T] | None = None) -> R:
    """Call a runner function with the YAML path given by a command-line parameter."""
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <config-path>")
        raise SystemExit(1)
    try:
        return run(runner, Path(sys.argv[1]), config_type)
    except Exception as exc:
        print(f"{Path(sys.argv[0]).stem.replace('_', ' ').capitalize()} failed: {exc}")
        raise SystemExit(1) from exc


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
