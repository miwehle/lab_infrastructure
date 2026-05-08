from __future__ import annotations

from pathlib import Path

from lab_infrastructure.dataset_schema import dataset_ref, next_named_path, next_numbered_path


def test_next_named_path_uses_plain_name_then_suffix(tmp_path: Path) -> None:
    root = tmp_path / "datasets" / "europarl"

    assert next_named_path(root, "curated") == root / "curated"
    (root / "curated").mkdir(parents=True)
    assert next_named_path(root, "curated") == root / "curated-2"
    (root / "curated-2").mkdir()
    assert next_named_path(root, "curated") == root / "curated-3"


def test_next_numbered_path_uses_prefix(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    (root / "r1").mkdir(parents=True)

    assert next_numbered_path(root, "r") == root / "r2"


def test_dataset_ref_uses_posix_relative_path(tmp_path: Path) -> None:
    datasets_root = tmp_path / "datasets"
    dataset = datasets_root / "europarl" / "preprocessed" / "splits" / "train"

    assert dataset_ref(datasets_root, dataset) == "europarl/preprocessed/splits/train"
