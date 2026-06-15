from agent.state import AgentState, StateUpdate, IntentResult
from prompts import load_prompt
from utils.llm_client import LLMClient
from utils.logger import get_logger

logger = get_logger(__name__)

INTENT_PROMPT = load_prompt("intent_recognition")
client = LLMClient(task="intent")


def recognize_intent(state: AgentState) -> StateUpdate:
    """Returns a partial state update; LangGraph merges it into the graph state."""
    result = client.structured(
        INTENT_PROMPT, {"question": state["question"]}, IntentResult
    )
    logger.info(f"Intent='{result.intent}' reason='{result.reason}'")
    return {"intent": result}


async def arecognize_intent(state: AgentState) -> StateUpdate:
    """Async variant of recognize_intent."""
    result = await client.astructured(
        INTENT_PROMPT, {"question": state["question"]}, IntentResult
    )
    logger.info(f"Intent='{result.intent}' reason='{result.reason}'")
    return {"intent": result}
