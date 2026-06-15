from agent.node_messages import (
    ANSWER_OUT_OF_SCOPE,
    ANSWER_SECURITY_REFUSAL,
    thinking_refused,
)
from agent.state import AgentState, StateUpdate
from utils.logger import get_logger

logger = get_logger(__name__)


def refuse(state: AgentState) -> StateUpdate:
    """Politely decline out-of-scope or security-breach requests."""
    intent = state["intent"].intent

    if intent == "security_breach":
        answer = ANSWER_SECURITY_REFUSAL
    else:
        answer = ANSWER_OUT_OF_SCOPE

    logger.info(f"Refused question with intent={intent}")
    return {"answer": answer, "thinking": [thinking_refused(intent)]}
