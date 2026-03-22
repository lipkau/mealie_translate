"""Tests for logger module."""

import logging
import os
import tempfile

import pytest

from mealie_translate.logger import get_logger, setup_logging


@pytest.fixture(autouse=True)
def reset_logging():
    """Ensure a clean root-logger state for every logging test."""
    root = logging.getLogger()
    original_level = root.level
    # Remove ALL handlers before the test so each test starts clean.
    for h in root.handlers[:]:
        h.close()
        root.removeHandler(h)
    yield
    # Restore after the test.
    for h in root.handlers[:]:
        h.close()
        root.removeHandler(h)
    root.setLevel(original_level)


def test_get_logger():
    """Test that get_logger returns a logger instance."""
    logger = get_logger("test_module")

    assert logger is not None
    assert logger.name == "test_module"
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "warning")
    assert hasattr(logger, "debug")


def test_get_logger_default_name():
    """Test that get_logger with no name returns default logger."""
    logger = get_logger()

    assert logger is not None
    assert logger.name == "mealie_translator"


def test_get_logger_none_name():
    """Test that get_logger with None name returns default logger."""
    logger = get_logger(None)

    assert logger is not None
    assert logger.name == "mealie_translator"


def test_logger_is_singleton():
    """Test that get_logger returns the same logger for the same name."""
    logger1 = get_logger("test")
    logger2 = get_logger("test")

    assert logger1 is logger2


def test_logger_different_names():
    """Test that different names return different loggers."""
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")

    assert logger1 is not logger2
    assert logger1.name == "module1"
    assert logger2.name == "module2"


def test_logger_functionality(caplog):
    """Test that logger actually logs messages."""
    import logging

    # Ensure the logger level allows info messages
    caplog.set_level(logging.INFO)

    logger = get_logger("test_logger")

    test_message = "This is a test message"
    logger.info(test_message)

    assert test_message in caplog.text


def test_setup_logging_basic():
    """Test basic setup_logging functionality."""
    logger = setup_logging()

    assert logger is not None
    assert logger.name == "mealie_translator"
    assert logger.level == logging.INFO
    # Handlers are attached to the root logger
    assert len(logging.getLogger().handlers) >= 1


def test_setup_logging_with_debug_level():
    """Test setup_logging with DEBUG level."""
    logger = setup_logging(log_level="DEBUG")

    assert logger.level == logging.DEBUG


def test_setup_logging_with_warning_level():
    """Test setup_logging with WARNING level."""
    logger = setup_logging(log_level="WARNING")

    assert logger.level == logging.WARNING


def test_setup_logging_with_error_level():
    """Test setup_logging with ERROR level."""
    logger = setup_logging(log_level="ERROR")

    assert logger.level == logging.ERROR


def test_setup_logging_case_insensitive():
    """Test setup_logging with lowercase level."""
    logger = setup_logging(log_level="debug")

    assert logger.level == logging.DEBUG


def test_setup_logging_with_file():
    """Test setup_logging with file handler."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        logger = setup_logging(log_file=temp_path)

        # Handlers live on root logger — console + file
        assert len(logging.getLogger().handlers) >= 2

        # Test that logging to file works
        logger.info("Test file logging")

        # Force flush handlers
        for handler in logging.getLogger().handlers:
            handler.flush()

        # Check file exists and has content
        assert os.path.exists(temp_path)
        with open(temp_path) as f:
            content = f.read()
            assert "Test file logging" in content
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_setup_logging_console_handler_format():
    """Test console handler format in setup_logging."""
    setup_logging()

    # Find console handler on the root logger.
    # Use exact type check — FileHandler is a subclass of StreamHandler.
    console_handler = None
    for handler in logging.getLogger().handlers:
        if type(handler) is logging.StreamHandler:
            console_handler = handler
            break

    assert console_handler is not None
    assert console_handler.formatter is not None

    # Test format includes timestamp, name, level, and message
    test_record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    formatted = console_handler.formatter.format(test_record)
    assert "test" in formatted
    assert "INFO" in formatted
    assert "Test message" in formatted


def test_setup_logging_file_handler_format():
    """Test file handler format in setup_logging."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        setup_logging(log_file=temp_path)

        # Find file handler on the root logger
        file_handler = None
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break

        assert file_handler is not None
        assert file_handler.formatter is not None
        assert file_handler.level == logging.DEBUG
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_console_handler_level():
    """Test console handler has INFO level."""
    setup_logging()

    console_handler = None
    for handler in logging.getLogger().handlers:
        if type(handler) is logging.StreamHandler:
            console_handler = handler
            break

    assert console_handler is not None
    assert console_handler.level == logging.INFO


def test_logger_levels_functionality(caplog):
    """Test different log levels work correctly."""
    logger = setup_logging(log_level="DEBUG")

    with caplog.at_level(logging.DEBUG):
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

    assert "Debug message" in caplog.text
    assert "Info message" in caplog.text
    assert "Warning message" in caplog.text
    assert "Error message" in caplog.text
    assert "Critical message" in caplog.text
