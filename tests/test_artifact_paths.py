from __future__ import annotations

from pathlib import Path

from lab_infrastructure.artifact_paths import artifact_ref, next_named_path, next_numbered_path


def test_next_named_path_uses_first_free_suffix(tmp_path: Path) -> None:
    root = tmp_path / "datasets" / "europarl"

    assert next_named_path(root, "curated") == root / "curated"
    (root / "curated").mkdir(parents=True)
    (root / "curated-3").mkdir()
    assert next_named_path(root, "curated") == root / "curated-2"


def test_next_numbered_path_uses_first_free_suffix(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    (root / "r1").mkdir(parents=True)
    (root / "r3").mkdir()

    assert next_numbered_path(root, "r") == root / "r2"


def test_artifact_ref_uses_posix_relative_path(tmp_path: Path) -> None:
    root = tmp_path / "datasets"
    artifact = root / "europarl" / "preprocessed" / "splits" / "train"

    assert artifact_ref(root, artifact) == "europarl/preprocessed/splits/train"
