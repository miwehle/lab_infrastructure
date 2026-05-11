from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from pathlib import Path


def insert_row(
    register_path: Path, fieldnames: Sequence[str], row: Mapping[str, str], *, artifact_key: str
) -> None:
    """Insert a CSV register row after the last row with the same artifact lineage."""

    def lineage(artifact_ref: str) -> str:
        return artifact_ref.partition("/")[0] if "/" in artifact_ref else ""

    def read_rows() -> list[dict[str, str]]:
        if not register_path.exists():
            return []
        with register_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=";")
            return [{field: row.get(field, "") for field in fieldnames} for row in reader]

    register_path.parent.mkdir(parents=True, exist_ok=True)
    rows = read_rows()
    row_lineage = lineage(row[artifact_key])
    insert_at = len(rows)
    for index in range(len(rows) - 1, -1, -1):
        if lineage(rows[index][artifact_key]) == row_lineage:
            insert_at = index + 1
            break
    rows.insert(insert_at, dict(row))
    with register_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
