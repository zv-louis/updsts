# encoding: utf-8-sig

import logging
import pytest
from unittest.mock import patch

from updsts import logutil


@pytest.fixture
def fresh_logger(tmp_path, monkeypatch):
    """Reset the module-level logger state and keep the log file under tmp_path."""
    logger = logging.getLogger(logutil.DEFAULT_LOGGER_NAME)
    saved_handlers = logger.handlers[:]
    saved_level = logger.level
    logger.handlers.clear()
    monkeypatch.setattr(logutil, "is_initialized", False)
    monkeypatch.setattr(logutil, "logger_obj", None)
    monkeypatch.setattr(logutil, "file_handler_obj", None)
    monkeypatch.setattr(logutil, "console_handler_obj", None)
    monkeypatch.setattr("os.path.expanduser", lambda p: str(tmp_path) if p == "~" else p)
    yield logger
    for h in logger.handlers:
        h.close()
    logger.handlers[:] = saved_handlers
    logger.setLevel(saved_level)


@pytest.mark.unit
class TestVerboseLevel:
    """-v must be applied to the handlers, not only to the logger."""

    @pytest.mark.parametrize("verbose, expected", [
        (0, logging.WARNING),
        (1, logging.INFO),
        (2, logging.DEBUG),
    ])
    def test_handler_levels_follow_verbose(self, fresh_logger, verbose, expected):
        logger = logutil.get_logger(verbose_level=verbose)
        assert logger.level == expected
        assert len(logger.handlers) == 2
        assert all(h.level == expected for h in logger.handlers)

    def test_debug_is_emitted_to_stderr_with_verbose_2(self, fresh_logger, capsys):
        logger = logutil.get_logger(verbose_level=2)
        logger.debug("debug-message")
        assert "debug-message" in capsys.readouterr().err

    def test_verbose_applies_after_initialization(self, fresh_logger, capsys):
        """A verbose level given after the logger was initialized with defaults must still take effect."""
        logutil.get_logger()  # initialized with the default WARNING level
        logger = logutil.get_logger(verbose_level=2)
        logger.debug("late-debug-message")
        assert "late-debug-message" in capsys.readouterr().err

    def test_verbose_can_be_lowered_again(self, fresh_logger, capsys):
        logutil.get_logger(verbose_level=2)
        logger = logutil.get_logger(verbose_level=0)
        logger.info("info-message")
        assert "info-message" not in capsys.readouterr().err

    def test_handlers_are_not_duplicated(self, fresh_logger):
        for verbose in (None, 0, 1, 2, None):
            logger = logutil.get_logger(verbose_level=verbose)
        assert len(logger.handlers) == 2

    def test_log_file_is_written(self, fresh_logger, tmp_path):
        logger = logutil.get_logger(verbose_level=1)
        logger.info("file-message")
        logutil.file_handler_obj.flush()
        assert "file-message" in (tmp_path / ".awscm" / "log" / "awscm.log").read_text(encoding="utf-8")


@pytest.mark.unit
class TestLogDirectoryFailure:
    """Failing to create the log directory must not crash; logging falls back to stderr only."""

    def test_makedirs_failure_falls_back_to_console(self, fresh_logger, capsys):
        with patch("updsts.logutil.os.makedirs", side_effect=PermissionError("read-only")):
            logger = logutil.get_logger(verbose_level=1)
        assert logutil.file_handler_obj is None
        assert len(logger.handlers) == 1
        logger.info("console-only-message")
        assert "console-only-message" in capsys.readouterr().err

    def test_makedirs_runs_only_on_initialization(self, fresh_logger):
        logutil.get_logger()
        with patch("updsts.logutil.os.makedirs") as makedirs:
            logutil.get_logger()
            logutil.get_logger(verbose_level=2)
        makedirs.assert_not_called()
