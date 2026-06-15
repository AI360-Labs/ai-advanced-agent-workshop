import logging
import sys
from types import SimpleNamespace

import pytest

import utils.logger as logger_module
from utils.logger import get_logger


# Run this setup before every test below, automatically.
@pytest.fixture(autouse=True)
# `monkeypatch` is an object pytest gives us. It can overwrite a function/attribute,
# and after the test ends it restores the original automatically.
def fake_config(monkeypatch: pytest.MonkeyPatch) -> None:
    # Overwrite `get_config` on logger_module so that, during the test, calling it
    # returns our fake config (log_level = "DEBUG") instead of reading real settings.
    monkeypatch.setattr(
        logger_module, "get_config", lambda: SimpleNamespace(log_level="DEBUG")
    )


def test_returns_logger_with_given_name() -> None:
    logger = get_logger("test.named")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.named"


def test_level_comes_from_config() -> None:
    logger = get_logger("test.level")

    assert logger.level == logging.DEBUG


def test_does_not_add_duplicate_handlers() -> None:

    first = get_logger("test.idempotent")

    # Second call with the same name: should reuse the existing logger, not reconfigure it.
    second = get_logger("test.idempotent")

    # Same name always returns the very same logger object (Python caches loggers by name).
    assert first is second
    # Handler count is unchanged, proving the second call didn't add another handler.
    assert len(second.handlers) == 1


def test_handler_writes_to_stdout() -> None:
    logger = get_logger("test.stdout")

    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream is sys.stdout
    assert handler.formatter is not None
