# encoding: utf-8-sig

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# globals
logger_obj: Optional[logging.Logger] = None
is_initialized: bool = False
# keep references to our own handlers: FileHandler is a subclass of StreamHandler,
# so they cannot be told apart reliably by type when walking logger.handlers
file_handler_obj: Optional[logging.Handler] = None
console_handler_obj: Optional[logging.Handler] = None

DEFAULT_LOGGER_NAME = "awssts"
DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_FILE_LEVEL = logging.WARNING
DEFAULT_CONSOLE_LEVEL = logging.WARNING

# -v/--verbose value -> logging level
VERBOSE_TO_LEVEL = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}

# ----------------------------------------------------------------------------
def get_with_init(
    log_file: str | os.PathLike | None = None,
    *,
    level: int = DEFAULT_LOG_LEVEL,
    file_level: int = DEFAULT_FILE_LEVEL,
    console_level: int = DEFAULT_CONSOLE_LEVEL,
) -> logging.Logger:
    """
    Initialize the updsts logger on the first call and return it.
    The handlers are created only once; later calls return the existing logger
    and ignore the arguments. Use set_level() to change the levels afterwards.

    Args:
        log_file (str | os.PathLike | None, optional): Log file path.
            Defaults to None (~/.awscm/log/awscm.log).
        level (int, optional): Logger level. Defaults to DEFAULT_LOG_LEVEL.
        file_level (int, optional): File handler level. Defaults to DEFAULT_FILE_LEVEL.
        console_level (int, optional): Console (stderr) handler level. Defaults to DEFAULT_CONSOLE_LEVEL.

    Returns:
        logging.Logger: Logger instance for the updsts package.
    """
    global logger_obj, is_initialized, file_handler_obj, console_handler_obj
    if is_initialized:
        return logger_obj

    if log_file is None:
        log_file = Path(os.path.expanduser("~")) / ".awscm" / "log" / "awscm.log"

    logger_obj = logging.getLogger(DEFAULT_LOGGER_NAME)
    logger_obj.setLevel(level=level)
    formatter = logging.Formatter(
        '%(asctime)s [%(name)s] [%(levelname)s] %(message)s'
    )

    try:
        # make the directory for the log file if it does not exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler_obj = logging.FileHandler(log_file, encoding="utf-8")
        file_handler_obj.setFormatter(formatter)
        file_handler_obj.setLevel(file_level)
        logger_obj.addHandler(file_handler_obj)
    except OSError:
        # If the log directory or file cannot be created (e.g. read-only home),
        # skip the file handler and only use the console handler
        file_handler_obj = None

    # console output goes to stderr; stdout is used for MCP stdio communication
    console_handler_obj = logging.StreamHandler(sys.stderr)
    console_handler_obj.setFormatter(formatter)
    console_handler_obj.setLevel(console_level)
    logger_obj.addHandler(console_handler_obj)

    is_initialized = True
    return logger_obj

# ----------------------------------------------------------------------------
def set_level(level: int) -> None:
    """
    Apply the level to the updsts logger and its handlers.
    Can be called at any time after initialization.

    Args:
        level (int): logging level (e.g. logging.DEBUG)
    """
    logger = get_with_init()
    logger.setLevel(level)
    for handler in (file_handler_obj, console_handler_obj):
        if handler is not None:
            handler.setLevel(level)

# ----------------------------------------------------------------------------
def get_logger(verbose_level: int | None = None) -> logging.Logger:
    """
    Module-level shortcut to get the logger.
    Initializes the logger on the first call. If verbose_level is given,
    the level is applied to the logger and its handlers even if it was already initialized.

    Args:
        verbose_level (int | None, optional): -v/--verbose value (0: warning, 1: info, 2: debug).
            Defaults to None (keep the current level).

    Returns:
        logging.Logger: Logger instance for the updsts package.
    """
    logger = get_with_init()
    if verbose_level is not None:
        set_level(VERBOSE_TO_LEVEL.get(verbose_level, logging.DEBUG))
    return logger


__all__ = ["get_logger", "set_level"]
