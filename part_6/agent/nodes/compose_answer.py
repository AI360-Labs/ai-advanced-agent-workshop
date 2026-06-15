from agent.node_messages import (
    THINKING_COMPOSE_ANSWER,
    ANSWER_NO_DATA,
)
import json

from agent.state import AgentState, StateUpdate
from config.settings import get_config
from prompts import load_prompt
from utils.llm_client import LLMClient
from utils.logger import get_logger

logger = get_logger(__name__)

DOC_PROMPT = load_prompt("document_answer")
SQL_PROMPT = load_prompt("sql_answer")
client = LLMClient(task="answer")


async def compose_answer(state: AgentState) -> StateUpdate:
    """Turn retrieval results into a natural-language answer."""
    question = state["question"]

    feedback = state.get("user_feedback")
    feedback_block = f"\nUser corrections to apply:\n{feedback}\n" if feedback else ""

    intent_str = state["intent"].intent if state.get("intent") else ""

    if intent_str == "document_search" and state.get("document_matches"):
        excerpts = "\n\n---\n\n".join(
            f"Source: {m.source}\n{m.content}" for m in state["document_matches"]
        )
        message = await client.acomplete(
            DOC_PROMPT,
            {"excerpts": excerpts, "question": question, "feedback": feedback_block},
        )
        answer = str(message.content).strip()
    elif intent_str in ("northwind_query", "reporting") and state.get("sql_result"):
        sql_result = state["sql_result"]
        message = await client.acomplete(
            SQL_PROMPT,
            {
                "sql": sql_result.sql,
                "rationale": sql_result.rationale,
                "rows": json.dumps(sql_result.rows, default=str)[
                    : get_config().sql_result_truncation
                ],
                "question": question,
                "feedback": feedback_block,
            },
        )
        answer = str(message.content).strip()
    else:
        answer = ANSWER_NO_DATA

    logger.info("Answer composed")
    return {
        "answer": answer,
        "thinking": [THINKING_COMPOSE_ANSWER],
        "user_feedback": None,
    }
