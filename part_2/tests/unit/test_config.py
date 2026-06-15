from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

import config.settings as settings_module
from config.settings import TasksConfig, get_config

DEV_ENV = """\
OPEN_ROUTER_API_KEY="test-key"
LOG_LEVEL=DEBUG
"""

PROD_ENV = """\
OPEN_ROUTER_API_KEY="test-key"
LOG_LEVEL=INFO
"""

TASKS_YAML = {
    "max_output_tokens": 256,
    "tasks": {
        "precise": {"temperature": 0.0, "models": ["model-a", "model-b"]},
        "creative": {"temperature": 1.0, "models": ["model-a"]},
    },
}


@pytest.fixture
def settings_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / ".env.dev").write_text(DEV_ENV, encoding="utf-8")
    (tmp_path / ".env.prod").write_text(PROD_ENV, encoding="utf-8")
    monkeypatch.setattr(settings_module, "SETTINGS_DIR", tmp_path)
    for key in ("APP_ENV", "OPEN_ROUTER_API_KEY", "LOG_LEVEL"):
        monkeypatch.delenv(key, raising=False)
    get_config.cache_clear()
    return tmp_path


def test_defaults_to_dev_when_app_env_unset(settings_dir: Path) -> None:
    config = get_config()

    assert config.log_level == "DEBUG"
    assert isinstance(config.api_key, SecretStr)
    assert config.api_key.get_secret_value() == "test-key"


def test_loads_prod_when_app_env_prod(
    settings_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_ENV", "PROD")
    get_config.cache_clear()

    assert get_config().log_level == "INFO"


def test_missing_api_key_raises(
    settings_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (settings_dir / ".env.dev").write_text("LOG_LEVEL=DEBUG\n", encoding="utf-8")
    get_config.cache_clear()

    with pytest.raises(ValidationError):
        get_config()


def test_get_config_is_cached(settings_dir: Path) -> None:
    get_config.cache_clear()

    assert get_config() is get_config()


def test_tasks_config_parses_and_looks_up_task() -> None:
    tasks = TasksConfig.model_validate(TASKS_YAML)

    assert tasks.max_output_tokens == 256
    assert tasks.task("precise").temperature == 0.0
    assert tasks.task("precise").models == ["model-a", "model-b"]


def test_unknown_task_raises_key_error() -> None:
    tasks = TasksConfig.model_validate(TASKS_YAML)

    with pytest.raises(KeyError):
        tasks.task("missing")


def test_task_requires_at_least_one_model() -> None:
    invalid = {
        "max_output_tokens": 256,
        "tasks": {"precise": {"temperature": 0.0, "models": []}},
    }

    with pytest.raises(ValidationError):
        TasksConfig.model_validate(invalid)
