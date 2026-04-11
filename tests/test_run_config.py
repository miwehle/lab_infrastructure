from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from lab_infrastructure.run_config import git_head_commit, git_status, read_run_config, write_run_config


@dataclass(frozen=True, kw_only=True)
class ExampleConfig:
    dataset: str
    batch_size: int = 32


def test_read_run_config_reads_yaml_file(tmp_path: Path):
    config = ExampleConfig(dataset="demo")
    config_path = tmp_path / "input_config.yaml"
    config_path.write_text(
        yaml.safe_dump({"split_config": asdict(config)}, sort_keys=False), encoding="utf-8"
    )

    assert read_run_config(config_path) == {"split_config": {"dataset": "demo", "batch_size": 32}}


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

