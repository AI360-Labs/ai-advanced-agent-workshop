from pydantic import BaseModel

from utils.llm_client import LLMClient
from utils.logger import get_logger

logger = get_logger(__name__)


class ServerSummary(BaseModel):
    topic: str
    keywords: list[str]


def main() -> None:
    creative = LLMClient(task="creative")
    precise = LLMClient(task="precise")

    poem = creative.complete(
        "Write a poem about: {text}",
        {"text": "a robust cloud server network"},
    )
    print(f"Poem: {poem.content}\n")

    summary = precise.structured(
        "Summarise the topic and list keywords as JSON for: {text}",
        {"text": "a robust cloud server network"},
        ServerSummary,
    )
    logger.info(f"Summary: {summary}")


if __name__ == "__main__":
    main()
