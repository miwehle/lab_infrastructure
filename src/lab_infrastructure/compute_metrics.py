from __future__ import annotations

import subprocess
from datetime import datetime

_COMPUTE_UNIT_RATES = {"T4": 1.8, "V100": 5.0, "A100": 7.5, "H100": 22.5, "RTXPRO6000": 22.5, "CPU": 0.5}


def get_gpu_util() -> int | None:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"], text=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    try:
        return int(out.strip())
    except ValueError:
        return None


def detect_compute_hardware() -> str:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "CPU"

    gpu_name = result.stdout.strip()
    if not gpu_name:
        return "(unknown)"
    if "H100" in gpu_name:
        return "H100"
    if "A100" in gpu_name:
        return "A100"
    if "V100" in gpu_name:
        return "V100"
    if "T4" in gpu_name:
        return "T4"
    if "RTX PRO 6000" in gpu_name:
        return "RTXPRO6000"
    return gpu_name


def estimate_compute_units(
    hardware: str, start_time: datetime, end_time: datetime | None = None
) -> float | None:
    rate = _COMPUTE_UNIT_RATES.get(hardware)
    if rate is None:
        return None
    end = end_time or (datetime.now(tz=start_time.tzinfo) if start_time.tzinfo is not None else datetime.now())
    elapsed_seconds = (end - start_time).total_seconds()
    if elapsed_seconds < 0:
        return None
    return elapsed_seconds / 3600.0 * rate


def estimate_cost(compute_units: float | None, euro_per_cu: float = 0.10) -> float | None:
    if compute_units is None or euro_per_cu < 0:
        return None
    return compute_units * euro_per_cu
