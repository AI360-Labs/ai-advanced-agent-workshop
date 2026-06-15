import logging

# Raise litellm's logger level before importing it, so its import-time
# botocore (Bedrock/SageMaker) pre-load warnings are suppressed.
logging.getLogger("LiteLLM").setLevel(logging.ERROR)

from json_repair import repair_json  # noqa: E402
from langchain_core.messages import BaseMessage  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_litellm import ChatLiteLLMRouter  # noqa: E402
from litellm import Router  # noqa: E402
from pydantic import BaseModel, ValidationError  # noqa: E402
from tenacity import (  # noqa: E402
    retry,
    retry_if_exception_type,
    stop_after_attempt,
)

from config import get_config, get_tasks  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def to_openrouter(model: str) -> str:
    """Prefix a bare model name so litellm routes it to OpenRouter."""
    return model if model.startswith("openrouter/") else f"openrouter/{model}"


def parse_or_repair(result: dict, schema: type[BaseModel]) -> BaseModel:
    """Return the parsed Pydantic object, repairing the raw JSON if needed."""
    if result["parsing_error"] is None:
        return result["parsed"]

    # Structured parsing failed; try to repair the raw JSON before retrying.
    raw_text = str(result["raw"].content)
    try:
        return schema.model_validate_json(repair_json(raw_text))
    except (ValidationError, ValueError) as exc:
        logger.warning(f"json_repair could not recover valid output: {exc}")
        raise ValueError(f"Failed to produce valid '{schema.__name__}' output") from exc


class LLMClient:
    """A task-scoped LLM client backed by a litellm Router.

    The task name (e.g. ``"precise"`` or ``"creative"``) selects its model pool
    and temperature from ``tasks.yaml``. All models in the pool share one pool
    name, so the router falls back between them when one fails.
    """

    def __init__(self, task: str) -> None:
        cfg = get_config()
        task_cfg = get_tasks().task(task)
        self.task = task
        self.max_retries = cfg.llm_max_retries
        pool_name = f"{task}-pool"

        model_list = [
            {
                "model_name": pool_name,
                "litellm_params": {
                    "model": to_openrouter(model),
                    "api_key": cfg.api_key.get_secret_value(),
                },
            }
            for model in task_cfg.models
        ]
        router = Router(model_list=model_list)
        self.engine = ChatLiteLLMRouter(
            router=router,
            model_name=pool_name,
            temperature=task_cfg.temperature,
            max_tokens=get_tasks().max_output_tokens,
        )
        logger.info(
            f"Created LLM client for task '{task}' "
            f"(temperature={task_cfg.temperature}, models={task_cfg.models})"
        )

    def complete(self, prompt_template: str, variables: dict) -> BaseMessage:
        chain = ChatPromptTemplate.from_template(prompt_template) | self.engine
        return chain.invoke(variables)

    def structured(
        self, prompt_template: str, variables: dict, schema: type[BaseModel]
    ) -> BaseModel:
        @retry(
            retry=retry_if_exception_type(ValueError),
            stop=stop_after_attempt(self.max_retries),
            reraise=True,
        )
        def _attempt() -> BaseModel:
            structured_engine = self.engine.with_structured_output(
                schema, include_raw=True
            )
            chain = (
                ChatPromptTemplate.from_template(prompt_template) | structured_engine
            )
            result = chain.invoke(variables)
            return parse_or_repair(result, schema)

        return _attempt()
