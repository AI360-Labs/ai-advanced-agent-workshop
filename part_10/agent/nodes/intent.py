from agent.state import AgentState, IntentResult, StateUpdate
from prompts import load_prompt
from utils.llm_client import LLMClient
from utils.logger import get_logger

logger = get_logger(__name__)

INTENT_PROMPT = load_prompt("intent_recognition")
client = LLMClient(task="intent")


async def recognize_intent(state: AgentState) -> StateUpdate:
    """Returns a partial state update; LangGraph merges it into the graph state."""
    result = await client.astructured(
        INTENT_PROMPT, {"question": state["question"]}, IntentResult
    )
    logger.info(f"Intent='{result.intent}' reason='{result.reason}'")
    return {
        "intent": result,
        "approved": False,
        "user_feedback": None,
        # New turn: the prior turn ended approved=True, so reset. Revision
        # loop-back: approved is False, so preserve the in-progress count —
        # otherwise HUMAN_REVIEW_MAX_RETRIES could never trigger.
        "retry_count": 0 if state.get("approved") else state.get("retry_count", 0),
        "thinking": None,  # reset the per-turn log (see thinking_reducer)
    }
