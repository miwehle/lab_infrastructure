from __future__ import annotations

import subprocess
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from time import perf_counter

type LapLabel = str | None

_COMPUTE_UNIT_RATES = {"T4": 1.8, "V100": 5.0, "A100": 12.5, "H100": 22.5, "RTXPRO6000": 22.5, "CPU": 0.5}

"""Lightweight timing utilities for bottleneck analysis.

Example 1:
    # measure
    clock = get_clock("train")
    lap(clock, "forward")
    lap(clock, "backward")
    stop(clock, "optimizer")

    # evaluate
    total_lap_times("train") -> {"forward": 471.1, "backward": 753.76, "optimizer": 94.22}
    total_time("train") -> 1319.08

Example 2:
    # measure
    clock = get_clock("train")
    stop(clock)

    # evaluate
    total_lap_times("train") -> {None: 1319.08}
    total_time("train") -> 1319.08

All durations are measured in seconds.
Unlabeled laps are aggregated under None.
"""


def _now() -> float:
    return perf_counter()


class Clock:
    def __init__(self, name: str, *, now: float):
        self.name = name
        self._started_at = now
        self._last_lap_at = now
        self._stopped_at: float | None = None
        self._lap_times: dict[LapLabel, float] = defaultdict(float)
        self.reused = False

    @property
    def stopped(self) -> bool:
        return self._stopped_at is not None

    @property
    def total_time(self) -> float | None:
        if self._stopped_at is None:
            return None
        return self._stopped_at - self._started_at

    @property
    def lap_times(self) -> dict[LapLabel, float]:
        return dict(self._lap_times)


class _ClockRegistry:
    def __init__(self, time_source: Callable[[], float]):
        self._time_source = time_source
        self._clocks_by_name: dict[str, list[Clock]] = defaultdict(list)
        self._running_clocks: dict[str, Clock] = {}

    def get_clock(self, name: str) -> Clock:
        running_clock = self._running_clocks.get(name)
        if running_clock is not None:
            running_clock.reused = True
            return running_clock
        clock = Clock(name, now=self._time_source())
        self._clocks_by_name[name].append(clock)
        self._running_clocks[name] = clock
        return clock

    def lap(self, clock: Clock, label: LapLabel = None) -> float:
        if clock.stopped:
            return 0.0
        now = self._time_source()
        duration = now - clock._last_lap_at
        clock._lap_times[label] += duration
        clock._last_lap_at = now
        return duration

    def stop(self, clock: Clock, label: LapLabel = None) -> float | None:
        if clock.stopped:
            return clock.total_time
        now = self._time_source()
        duration = now - clock._last_lap_at
        clock._lap_times[label] += duration
        clock._last_lap_at = now
        clock._stopped_at = now
        self._running_clocks.pop(clock.name, None)
        return clock.total_time

    def total_lap_times(self, name: str) -> dict[LapLabel, float]:
        totals: dict[LapLabel, float] = defaultdict(float)
        for clock in self._clocks_by_name.get(name, []):
            for label, duration in clock._lap_times.items():
                totals[label] += duration
        return dict(totals)

    def total_time(self, name: str) -> float:
        return sum(clock.total_time or 0.0 for clock in self._clocks_by_name.get(name, []))

    def reset(self) -> None:
        self._clocks_by_name.clear()
        self._running_clocks.clear()

    def is_in_use(self, name: str) -> bool:
        return name in self._running_clocks


_registry = _ClockRegistry(_now)


def get_clock(name: str) -> Clock:
    return _registry.get_clock(name)


def lap(clock: Clock, label: LapLabel = None) -> float:
    return _registry.lap(clock, label)


def stop(clock: Clock, label: LapLabel = None) -> float | None:
    return _registry.stop(clock, label)


def total_lap_times(name: str) -> dict[LapLabel, float]:
    return _registry.total_lap_times(name)


def total_time(name: str) -> float:
    return _registry.total_time(name)


def reset_clocks() -> None:
    _registry.reset()


def is_in_use(name: str) -> bool:
    """Return whether a clock with this name is currently running."""
    return _registry.is_in_use(name)


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
    rate = _get_compute_unit_rate(hardware)
    if rate is None:
        return None
    end = end_time or _current_datetime(start_time)
    elapsed_seconds = (end - start_time).total_seconds()
    if elapsed_seconds < 0:
        return None
    return elapsed_seconds / 3600.0 * rate


def estimate_cost(compute_units: float | None, euro_per_cu: float = 0.10) -> float | None:
    if compute_units is None or euro_per_cu < 0:
        return None
    return compute_units * euro_per_cu


def _get_compute_unit_rate(hardware: str) -> float | None:
    return _COMPUTE_UNIT_RATES.get(hardware)


def _current_datetime(start_time: datetime) -> datetime:
    return datetime.now(tz=start_time.tzinfo) if start_time.tzinfo is not None else datetime.now()
