import utils
from utils import LLMClient, get_logger, to_openrouter


def test_get_logger_importable_from_package() -> None:
    assert callable(get_logger)


def test_llm_client_importable_from_package() -> None:
    assert LLMClient is not None


def test_to_openrouter_importable_from_package() -> None:
    # to_openrouter must be accessible at the package level, not just from the submodule.
    # This matters because callers that write `from utils import to_openrouter`
    # break silently if __init__.py omits the export.
    assert to_openrouter("foo") == "openrouter/foo"
    assert to_openrouter("openrouter/bar") == "openrouter/bar"


def test_public_api_is_complete() -> None:
    assert set(utils.__all__) == {"LLMClient", "get_logger", "to_openrouter"}
