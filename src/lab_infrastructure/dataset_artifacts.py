from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from lab_infrastructure.run_config import git_head_commit

_DATASET_DIR_RE = re.compile(r"^d(?P<n>\d+)(?:_|$)")
_DATASET_REF_RE = re.compile(r"^(?P<family>[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)/(?P<dataset>d\d+)$")
_RUN_DIR_RE = re.compile(r"^r(?P<n>\d+)$")


@dataclass(frozen=True)
class DatasetArtifact:
    family: str
    dataset_id: str
    path: Path


def dataset_id_from_path(path: Path) -> str:
    """Return the stable dataset id for a concrete dataset folder.

    Example: ``datasets/europarl/d2_split_train`` -> ``europarl/d2``.
    """
    family = path.parent.name
    match = _DATASET_DIR_RE.match(path.name)
    if match is None:
        raise ValueError(f"Dataset directory must start with dN, got: {path}")
    return f"{family}/d{int(match.group('n'))}"


def next_dataset_artifact(datasets_root: Path, family: str, operation: str) -> DatasetArtifact:
    """Return the next dataset id and folder path for a family.

    Example: if ``datasets/europarl/d1_preprocess`` exists, then
    ``next_dataset_artifact(datasets, "europarl", "curate")`` returns
    ``dataset_id="europarl/d2"`` and ``path=datasets/europarl/d2_curate``.
    """
    if _DATASET_REF_RE.fullmatch(f"{family}/d1") is None:
        raise ValueError(f"dataset_family must be a lowercase slug, got: {family}")
    family_dir = datasets_root / family
    existing = [
        int(match.group("n"))
        for child in (family_dir.iterdir() if family_dir.exists() else ())
        if child.is_dir() and (match := _DATASET_DIR_RE.match(child.name))
    ]
    n = max(existing, default=0) + 1
    path = family_dir / f"d{n}_{operation}"
    return DatasetArtifact(family=family, dataset_id=f"{family}/d{n}", path=path)


def resolve_dataset(datasets_root: Path, dataset_id: str) -> Path:
    """Resolve a stable dataset id to its concrete folder.

    Example: if ``datasets/europarl/d2_split_train`` exists, then
    ``resolve_dataset(datasets, "europarl/d2")`` returns that folder.
    """
    def match_dataset_ref(dataset_id: str) -> re.Match[str]:
        match = _DATASET_REF_RE.fullmatch(dataset_id)
        if match is None:
            raise ValueError(f"dataset must use family/dN format, got: {dataset_id}")
        return match

    # Keep stable refs like "europarl/d2" independent from readable folder suffixes.
    # This is shared by curation and should also be used by translator training configs.
    match = match_dataset_ref(dataset_id)
    family_dir = datasets_root / match.group("family")
    dataset = match.group("dataset")
    candidates = [
        child for child in family_dir.iterdir()
        if child.is_dir() and (child.name == dataset or child.name.startswith(f"{dataset}_"))
    ] if family_dir.is_dir() else []
    if len(candidates) != 1:
        raise FileNotFoundError(f"Dataset id {dataset_id} matched {len(candidates)} directories.")
    return candidates[0]


def next_numbered_path(root: Path, prefix: str = "r") -> Path:
    """Return the next numbered child path without creating it.

    Example: if ``loss_buckets/r1`` exists, then
    ``next_numbered_path(loss_buckets)`` returns ``loss_buckets/r2``.
    """
    existing = [
        int(match.group("n")) for child in root.iterdir()
        if root.exists() and child.is_dir() and (match := _RUN_DIR_RE.fullmatch(child.name))
    ] if root.exists() else []
    return root / f"{prefix}{max(existing, default=0) + 1}"


def append_dataset_register(
    datasets_root: Path,
    *,
    parent: str,
    operation: str,
    dataset_id: str,
    repo_root: Path,
) -> None:
    register_path = datasets_root / "datasets.csv"
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
                "dataset": dataset_id,
                "operation": operation,
                "parent": parent,
                "git_commit": commit[:20],
            }
        )
