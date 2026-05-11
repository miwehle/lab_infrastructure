from __future__ import annotations

from datetime import datetime
from pathlib import Path

from lab_infrastructure.csv_register import insert_row
from lab_infrastructure.run_config import git_head_commit


def register_dataset(
    datasets_root: Path, *, parent: str, operation: str, dataset: str, repo_root: Path
) -> None:
    commit = git_head_commit(repo_root) or ""
    insert_row(
        datasets_root / "dataset_register.csv",
        ["dataset", "operation", "parent", "timestamp", "git_commit"],
        {
            "dataset": dataset,
            "operation": operation,
            "parent": parent,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "git_commit": commit[:20],
        },
        artifact_key="dataset",
    )
