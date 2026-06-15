import asyncio
import os

import pytest

from agent.nodes.intent import recognize_intent
from tests.fixtures import INTENT_EXAMPLES

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_LLM_TESTS") != "1",
        reason="set RUN_LLM_TESTS=1 to run live LLM tests",
    ),
]


async def _recognize(question: str) -> dict:
    return await recognize_intent({"question": question})


def test_intent_accuracy_on_dataset() -> None:
    correct = 0
    for example in INTENT_EXAMPLES:
        update = asyncio.run(_recognize(example.text))
        if update["intent"].intent == example.expected:
            correct += 1

    accuracy = correct / len(INTENT_EXAMPLES)
    assert accuracy >= 0.7, f"intent accuracy too low: {accuracy:.2f}"
