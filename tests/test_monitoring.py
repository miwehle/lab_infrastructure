from __future__ import annotations

import subprocess
from datetime import UTC, datetime

import lab_infrastructure.clock as clock_module
from lab_infrastructure.clock import (
    get_clock,
    is_in_use,
    lap,
    reset_clocks,
    stop,
    total_lap_times,
    total_time,
)
from lab_infrastructure.compute_metrics import (
    detect_compute_hardware,
    estimate_compute_units,
    estimate_cost,
    get_gpu_util,
)


class TestClock:
    def setup_method(self):
        reset_clocks()

    def teardown_method(self):
        reset_clocks()

    def _set_time_source(self, monkeypatch, *values: float):
        times = iter(values)
        monkeypatch.setattr(clock_module, "_now", lambda: next(times))
        monkeypatch.setattr(clock_module, "_registry", clock_module._ClockRegistry(clock_module._now))

    def test_get_clock_reuses_running_clock(self, monkeypatch):
        self._set_time_source(monkeypatch, 1.0)

        clock = get_clock("train")
        same_clock = get_clock("train")

        assert same_clock is clock
        assert same_clock.reused is True
        assert is_in_use("train") is True

    def test_total_lap_times_aggregates_labeled_and_unlabeled_laps_of_running_clocks(self, monkeypatch):
        self._set_time_source(monkeypatch, 0.0, 0.5, 1.0, 1.5, 2.5, 4.0)

        clock = get_clock("train")
        lap(clock, "forward")
        lap(clock)
        stop(clock, "optimizer")
        second_clock = get_clock("train")
        lap(second_clock, "forward")

        assert total_lap_times("train") == {"forward": 2.0, None: 0.5, "optimizer": 0.5}

    def test_total_time_counts_only_stopped_clocks(self, monkeypatch):
        self._set_time_source(monkeypatch, 0.0, 2.0, 3.0, 4.5)

        first_clock = get_clock("train")
        stop(first_clock, "optimizer")
        second_clock = get_clock("train")
        lap(second_clock, "forward")

        assert total_time("train") == 2.0
        assert is_in_use("train") is True

    def test_stop_adds_last_open_lap_with_label(self, monkeypatch):
        self._set_time_source(monkeypatch, 0.0, 1.0, 3.5)

        clock = get_clock("train")
        lap(clock, "forward")
        stop(clock, "optimizer")

        assert total_lap_times("train") == {"forward": 1.0, "optimizer": 2.5}
        assert total_time("train") == 3.5


class TestMonitoringHelpers:
    def test_get_gpu_util_returns_none_when_nvidia_smi_is_missing(self, monkeypatch):
        def raise_missing(*args, **kwargs):
            raise FileNotFoundError

        monkeypatch.setattr(subprocess, "check_output", raise_missing)

        assert get_gpu_util() is None

    def test_get_gpu_util_parses_integer_output(self, monkeypatch):
        monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: "87\n")

        assert get_gpu_util() == 87

    def test_detect_compute_hardware_returns_cpu_when_nvidia_smi_is_missing(self, monkeypatch):
        def raise_missing(*args, **kwargs):
            raise FileNotFoundError

        monkeypatch.setattr(subprocess, "run", raise_missing)

        assert detect_compute_hardware() == "CPU"

    def test_detect_compute_hardware_normalizes_known_gpu_names(self, monkeypatch):
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout="NVIDIA H100 PCIe\n"),
        )

        assert detect_compute_hardware() == "H100"

    def test_detect_compute_hardware_returns_unknown_for_blank_gpu_name(self, monkeypatch):
        monkeypatch.setattr(
            subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout=" \n")
        )

        assert detect_compute_hardware() == "(unknown)"

    def test_estimate_compute_units_uses_known_rate(self):
        start_time = datetime(2026, 4, 11, 8, 0, tzinfo=UTC)
        end_time = datetime(2026, 4, 11, 10, 0, tzinfo=UTC)

        assert estimate_compute_units("A100", start_time, end_time) == 25.0

    def test_estimate_compute_units_returns_none_for_unknown_hardware(self):
        start_time = datetime(2026, 4, 11, 8, 0, tzinfo=UTC)
        end_time = datetime(2026, 4, 11, 10, 0, tzinfo=UTC)

        assert estimate_compute_units("MYSTERY_GPU", start_time, end_time) is None

    def test_estimate_compute_units_returns_none_for_negative_elapsed_time(self):
        start_time = datetime(2026, 4, 11, 10, 0, tzinfo=UTC)
        end_time = datetime(2026, 4, 11, 8, 0, tzinfo=UTC)

        assert estimate_compute_units("A100", start_time, end_time) is None

    def test_estimate_cost_uses_default_euro_per_cu(self):
        assert estimate_cost(12.5) == 1.25

    def test_estimate_cost_returns_none_for_missing_compute_units(self):
        assert estimate_cost(None) is None

    def test_estimate_cost_returns_none_for_negative_euro_per_cu(self):
        assert estimate_cost(12.5, -1.0) is None

