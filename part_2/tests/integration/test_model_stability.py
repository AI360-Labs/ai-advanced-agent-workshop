import asyncio
import os

import pytest

from agent.state import IntentResult
from prompts import load_prompt
from utils.llm_client import LLMClient

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_LLM_TESTS") != "1",
        reason="set RUN_LLM_TESTS=1 to run live LLM tests",
    ),
]

INTENT_PROMPT = load_prompt("intent_recognition")


def test_same_input_yields_same_intent() -> None:
    """At temperature 0, concurrent calls with identical input must agree.

    This is the model-stability check: we fan out the same request with
    asyncio.gather and assert every reply lands on one intent.
    """

    async def run() -> list[IntentResult]:
        client = LLMClient(task="intent")
        question = "How many orders did customer ALFKI place?"
        return await asyncio.gather(
            *(
                client.astructured(INTENT_PROMPT, {"question": question}, IntentResult)
                for _ in range(5)
            )
        )

    results = asyncio.run(run())
    intents = {r.intent for r in results}

    assert len(intents) == 1, f"non-deterministic intents: {intents}"
