from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from lab_infrastructure.run_config import git_head_commit


def next_numbered_path(root: Path, prefix: str) -> Path:
    n = 1
    while (root / f"{prefix}{n}").exists():
        n += 1
    return root / f"{prefix}{n}"


def append_dataset_register(
    datasets_root: Path, *, parent: str, operation: str, dataset: str, repo_root: Path
) -> None:
    register_path = datasets_root / "dataset_register.csv"
    register_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not register_path.exists()
    with register_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["timestamp", "dataset", "operation", "parent", "git_commit"],
            delimiter=";",
        )
        if write_header:
            writer.writeheader()
        commit = git_head_commit(repo_root) or ""
        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "dataset": dataset,
                "operation": operation,
                "parent": parent,
                "git_commit": commit[:20],
            }
        )
