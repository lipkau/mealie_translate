"""Logging configuration for the Mealie Recipe Translator."""

import logging
import sys


def setup_logging(
    log_level: str = "INFO", log_file: str | None = None
) -> logging.Logger:
    """Setup logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path

    Returns:
        Configured logger
    """
    level = getattr(logging, log_level.upper())

    # Configure the root logger so every logger in the process inherits
    # the handler and level — including module-level loggers that use
    # get_logger(__name__) with names like 'mealie_translate.main'.
    root = logging.getLogger()
    root.setLevel(level)

    # Add console handler only once — check specifically for a StreamHandler
    # targeting stdout. pytest adds its own handlers to root, so `if not
    # root.handlers` would be False in tests even when ours isn't there yet.
    has_stdout_handler = any(type(h) is logging.StreamHandler for h in root.handlers)
    if not has_stdout_handler:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        root.addHandler(console_handler)

    if log_file:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(console_formatter)
        root.addHandler(file_handler)

    # Also keep the named logger for backwards compatibility.
    logger = logging.getLogger("mealie_translator")
    logger.setLevel(level)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (defaults to mealie_translator)

    Returns:
        Logger instance
    """
    return logging.getLogger(name or "mealie_translator")
