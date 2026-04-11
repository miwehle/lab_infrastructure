from __future__ import annotations

from pathlib import Path

import lab_infrastructure.clock as clock_module
from lab_infrastructure.clock import get_clock, reset_clocks, total_time
from lab_infrastructure.logging import close_logger, get_logger, log_calls


class TestLogging:
    def teardown_method(self):
        close_logger("test.logger")
        close_logger("test.decorator")
        reset_clocks()

    def test_get_logger_configures_file_handler(self, tmp_path: Path):
        log_path = tmp_path / "logs" / "shared.log"

        logger = get_logger("test.logger", log_path=log_path)
        logger.info("configured file logger")

        assert log_path.read_text(encoding="utf-8").strip().endswith("configured file logger")

    def test_get_logger_replaces_existing_handlers(self, tmp_path: Path):
        first_path = tmp_path / "logs" / "first.log"
        second_path = tmp_path / "logs" / "second.log"

        first_logger = get_logger("test.logger", log_path=first_path)
        first_logger.info("first")
        second_logger = get_logger("test.logger", log_path=second_path)
        second_logger.info("second")

        assert first_logger is second_logger
        assert first_path.read_text(encoding="utf-8").strip().endswith("first")
        assert "second" not in first_path.read_text(encoding="utf-8")
        assert second_path.read_text(encoding="utf-8").strip().endswith("second")

    def test_get_logger_supports_stream_logging(self, capsys):
        logger = get_logger("test.logger", stream=True)
        logger.warning("stream message")

        captured = capsys.readouterr()
        assert "stream message" in captured.out

    def test_close_logger_removes_handlers(self, tmp_path: Path):
        logger = get_logger("test.logger", log_path=tmp_path / "logs" / "shared.log", stream=True)

        close_logger(logger)

        assert logger.handlers == []

    def _set_time_source(self, monkeypatch, *values: float):
        times = iter(values)
        monkeypatch.setattr(clock_module, "_now", lambda: next(times))
        monkeypatch.setattr(clock_module, "_registry", clock_module._ClockRegistry(clock_module._now))

    def test_log_calls_logs_start_and_finish(self, tmp_path: Path, monkeypatch):
        self._set_time_source(monkeypatch, 0.0, 0.25)
        log_path = tmp_path / "logs" / "decorator.log"
        logger = get_logger("test.decorator", log_path=log_path)

        @log_calls(logger)
        def preprocess() -> str:
            return "done"

        assert preprocess() == "done"

        messages = log_path.read_text(encoding="utf-8").splitlines()[-2:]
        assert messages[0].endswith("INFO [test.decorator] Start preprocess")
        assert messages[1].endswith("INFO [test.decorator] Finished preprocess in 0.250s")

    def test_log_calls_accumulates_time_in_default_clock(self, monkeypatch):
        self._set_time_source(monkeypatch, 10.0, 12.5)
        logger = get_logger("test.decorator")

        @log_calls(logger)
        def forward_pass() -> None:
            return None

        forward_pass()

        assert total_time("forward_pass") == 2.5

    def test_log_calls_uses_passed_clock(self, monkeypatch):
        self._set_time_source(monkeypatch, 5.0, 8.0)
        logger = get_logger("test.decorator")
        clock = get_clock("custom")

        @log_calls(logger, clock=clock)
        def train() -> None:
            return None

        train()

        assert total_time("custom") == 3.0

