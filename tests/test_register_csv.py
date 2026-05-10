from __future__ import annotations

import csv
from pathlib import Path

from lab_infrastructure.register_csv import insert_row


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def _insert(register_path: Path, artifact: str, kind: str) -> None:
    insert_row(
        register_path, ["artifact", "kind"], {"artifact": artifact, "kind": kind}, artifact_key="artifact"
    )


def test_insert_row_inserts_after_same_lineage(tmp_path: Path) -> None:
    register_path = tmp_path / "register.csv"

    _insert(register_path, "a/r1", "first")
    _insert(register_path, "b/r1", "second")
    _insert(register_path, "a/r2", "third")

    rows = _read_rows(register_path)

    assert [row["artifact"] for row in rows] == ["a/r1", "a/r2", "b/r1"]
