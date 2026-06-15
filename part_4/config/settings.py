import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

SETTINGS_DIR = Path(__file__).resolve().parent.parent / "settings"
TASKS_FILE = Path(__file__).resolve().parent / "tasks.yaml"


class Config(BaseSettings):
    """Secrets and environment knobs read from the active .env file."""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr = Field(validation_alias="OPEN_ROUTER_API_KEY")
    database_url: SecretStr = Field(validation_alias="DATABASE_URL")
    embedding_model: str = Field(
        validation_alias="EMBEDDING_MODEL",
    )
    sql_max_limit: int = Field(
        default=100,
        validation_alias="SQL_MAX_LIMIT",
    )
    search_limit: int = Field(
        default=5,
        validation_alias="SEARCH_LIMIT",
    )
    llm_max_retries: int = Field(
        default=2,
        validation_alias="LLM_MAX_RETRIES",
    )
    log_level: str = "DEBUG"


class TaskConfig(BaseModel):
    """Model pool and sampling for a single task."""

    temperature: float
    models: list[str] = Field(min_length=1)


class TasksConfig(BaseModel):
    """All task definitions loaded from tasks.yaml."""

    max_output_tokens: int
    tasks: dict[str, TaskConfig]

    def task(self, name: str) -> TaskConfig:
        if name not in self.tasks:
            raise KeyError(f"Unknown task '{name}'. Known tasks: {sorted(self.tasks)}")
        return self.tasks[name]


@lru_cache
def get_config() -> Config:
    # APP_ENV picks the file (.env.dev / .env.prod); defaults to dev.
    app_env = os.getenv("APP_ENV", "dev").lower()
    return Config(_env_file=SETTINGS_DIR / f".env.{app_env}")


@lru_cache
def get_tasks() -> TasksConfig:
    data = yaml.safe_load(TASKS_FILE.read_text(encoding="utf-8"))
    return TasksConfig.model_validate(data)
