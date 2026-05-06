from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
import yaml
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from lab_infrastructure.run_config import (
    git_head_commit,
    git_status,
    run,
    run_cli,
    write_run_config,
)


@dataclass(frozen=True, kw_only=True, config=ConfigDict(extra="forbid"))
class ExampleRunConfig:
    dataset: str
    batch_size: int = 32


def _install_example_package(monkeypatch) -> None:
    package = types.ModuleType("example_package")
    package.ExampleRunConfig = ExampleRunConfig
    monkeypatch.setitem(sys.modules, "example_package", package)


def example(config: ExampleRunConfig) -> tuple[str, int]:
    return config.dataset, config.batch_size


example.__module__ = "example_package.api"


def test_run_validates_and_runs(tmp_path: Path, monkeypatch):
    _install_example_package(monkeypatch)
    config_path = tmp_path / "input_config.yaml"
    config_path.write_text(yaml.safe_dump({"dataset": "demo", "batch_size": 64}), encoding="utf-8")

    assert run(example, config_path) == ("demo", 64)


def test_run_applies_config_overrides(tmp_path: Path, monkeypatch):
    _install_example_package(monkeypatch)
    config_path = tmp_path / "input_config.yaml"
    config_path.write_text(yaml.safe_dump({"dataset": "demo", "batch_size": 64}), encoding="utf-8")

    result = run(example, config_path, config_overrides={"dataset": "cli-demo", "batch_size": "16"})

    assert result == ("cli-demo", 16)


def test_run_cli_maps_cli_overrides(monkeypatch, tmp_path: Path):
    _install_example_package(monkeypatch)
    config_path = tmp_path / "input_config.yaml"
    config_path.write_text(yaml.safe_dump({"dataset": "demo", "batch_size": 64}), encoding="utf-8")
    monkeypatch.setattr(
        sys, "argv", ["train.py", str(config_path), "--dataset", "cli-demo", "--batch-size", "16"]
    )

    result = run_cli(
        example,
        cli_override_map={"dataset": "dataset", "batch-size": "batch_size"},
    )

    assert result == ("cli-demo", 16)


def test_run_cli_raises_with_usage_when_argument_is_missing(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["train.py"])

    with pytest.raises(SystemExit, match="1"):
        run_cli(example)

    assert capsys.readouterr().out == "Usage: python train.py <config-path>\n"


def test_run_cli_raises_with_script_name_in_error(monkeypatch, capsys, tmp_path: Path):
    _install_example_package(monkeypatch)
    config_path = tmp_path / "input_config.yaml"
    config_path.write_text(yaml.safe_dump({"dataset": "demo"}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["comet_score.py", str(config_path)])

    def fail(_config: ExampleRunConfig) -> None:
        raise ValueError("boom")

    fail.__name__ = "example"
    fail.__module__ = "example_package.api"

    with pytest.raises(SystemExit, match="1"):
        run_cli(fail)

    assert capsys.readouterr().out == "Comet score failed: boom\n"


def test_write_run_config_writes_yaml_file(tmp_path: Path):
    config_path = write_run_config(
        tmp_path / "split_config.yaml",
        {"filter_config": {"dataset": "demo", "bucket_files": [1, 2]}},
        repo_root=Path(__file__).resolve().parents[1],
        git_key_prefix="lab_infrastructure",
    )

    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    assert payload["filter_config"] == {"dataset": "demo", "bucket_files": [1, 2]}
    assert payload["schema_version"] == "1"
    assert payload["created_at_utc"].endswith("Z")
    assert "lab_infrastructure_git_commit" in payload
    assert payload["lab_infrastructure_git_status"] in {"no local changes", "local changes exist"}


def test_git_head_commit_returns_commit_hash_or_none():
    commit = git_head_commit(Path(__file__).resolve().parents[1])
    assert commit is None or len(commit) == 40


def test_git_status_returns_known_state():
    assert git_status(Path(__file__).resolve().parents[1]) in {"no local changes", "local changes exist"}
