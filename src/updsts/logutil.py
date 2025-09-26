# encoding: utf-8-sig

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# globals
logger_obj: Optional[logging.Logger] = None
is_initialized: bool = False

DEFAULT_LOGGER_NAME = "awssts"
DEFALT_LOG_LEVEL = logging.WARNING
DEFAULT_FILE_LEVEL = logging.WARNING
DEFAULT_CONSOLE_LEVEL = logging.WARNING

# ----------------------------------------------------------------------------
def get_with_init(
    log_file: str | None = None,
    *,
    level: int = DEFALT_LOG_LEVEL,
    file_level: int = DEFAULT_FILE_LEVEL,
    console_level: int = DEFAULT_CONSOLE_LEVEL,
    force: bool = False
) -> logging.Logger:
    """
    Initialize the logger with the specified configuration.
    If the logger is already initialized, it will return the existing logger

    Args:
        log_file (str | None, optional): Defaults to None.
        level (int, optional): Defaults to DEFAULT_LEVEL.
        file_level (int, optional):  Defaults to DEFAULT_FILE_LEVEL.
        console_level (int, optional):  Defaults to DEFAULT_CONSOLE_LEVEL.
        force (bool, optional):  Defaults to False.

    Returns:
        logging.Logger: Logger instance for the mktotp module.
    """

    if log_file is None:
        user_home = os.path.expanduser("~")
        log_dir = Path(user_home) / ".awscm" / "log"
        os.makedirs(log_dir, exist_ok=True)
        log_file = log_dir / "awscm.log"
    else:
        # make the directory for the specified path if it does not exist
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
        except OSError:
            # If the directory cannot be created, we just ignore it
            pass

    global logger_obj, is_initialized
    if not is_initialized:
        logger_obj = logging.getLogger(DEFAULT_LOGGER_NAME)
        logger_obj.setLevel(level=level)
        formatter = logging.Formatter(
            '%(asctime)s [%(name)s] [%(levelname)s] %(message)s'
        )

        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(file_level)
            logger_obj.addHandler(file_handler)
        except (OSError, PermissionError):
            # If file handler creation fails, we just skip it and only use console handler
            pass

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(console_level)
        logger_obj.addHandler(console_handler)

        is_initialized = True
    return logger_obj

# ----------------------------------------------------------------------------
def get_logger(verbose_level: int | None = None) -> logging.Logger:
    """
    Module-level shortcut to get the logger.

    Returns:
        logging.Logger: Logger instance for the mktotp module.
    """
    global logger_obj, is_initialized

    # If logger is already initialized and no verbose_level is specified,
    # return the existing logger instance
    if is_initialized and verbose_level is None:
        return logger_obj

    logObj = None
    if verbose_level is not None:
        if verbose_level == 0:
            logObj = get_with_init(level=logging.WARNING)
        elif verbose_level == 1:
            logObj = get_with_init(level=logging.INFO)
        elif verbose_level == 2:
            logObj = get_with_init(level=logging.DEBUG)
    else:
        # If no verbose level is specified, use the default level
        logObj = get_with_init()
    return logObj


__all__ = ["get_logger"]
