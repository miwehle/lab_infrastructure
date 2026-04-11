from __future__ import annotations

import nmt_lab_shared.monitoring as clock_module
from nmt_lab_shared.monitoring import (
    get_clock,
    is_in_use,
    lap,
    reset_clocks,
    stop,
    total_lap_times,
    total_time,
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
