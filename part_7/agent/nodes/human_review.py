from agent.node_messages import (
    REVIEW_GENERIC_REVISION,
    REVIEW_INTERRUPT_PROMPT,
    THINKING_AWAITING_REVIEW,
    thinking_user_revision,
)
from config.settings import get_config
from langgraph.types import interrupt

from agent.state import AgentState, StateUpdate
from utils.logger import get_logger

logger = get_logger(__name__)

APOLOGY = "Sorry, I cannot help you with this request after several attempts."


def human_review(state: AgentState) -> StateUpdate:
    """Pause for human approval or revision (up to HUMAN_REVIEW_MAX_RETRIES retries)."""
    if state.get("approved"):
        return {}

    retry = state.get("retry_count", 0)
    max_retries = get_config().human_review_max_retries
    new_thinking = []

    if retry >= max_retries:
        new_thinking.append("Maximum revision attempts reached.")
        logger.info("Human review: retries exhausted")
        return {"answer": APOLOGY, "approved": True, "thinking": new_thinking}

    new_thinking.append(THINKING_AWAITING_REVIEW)
    decision = interrupt(
        {
            "answer": state.get("answer", ""),
            "retry_count": retry,
            "message": REVIEW_INTERRUPT_PROMPT,
        }
    )

    if isinstance(decision, dict) and decision.get("approved"):
        logger.info("Human review: approved")
        return {"approved": True, "thinking": new_thinking}

    # Anything that is not an explicit approval is a refusal, i.e. a request to
    # revise. Blank feedback must NOT be read as approval — that would let a
    # rejection silently pass the review gate — so fall back to a generic
    # revision instruction and route back to recognize_intent.
    feedback = ""
    if isinstance(decision, dict):
        feedback = str(decision.get("feedback") or decision.get("message") or "")
    else:
        feedback = str(decision)

    feedback = feedback.strip() or REVIEW_GENERIC_REVISION

    new_thinking.append(thinking_user_revision(feedback))
    logger.info(f"Human review: revision {retry + 1}/{max_retries}")
    return {
        "retry_count": retry + 1,
        "question": f"{state['question']}\nFeedback: {feedback}",
        "thinking": new_thinking,
    }
