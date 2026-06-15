from agent.state import AgentState, StateUpdate
from db.persistence import save_agent_turn
from db.sqlite import get_sqlite_session_factory, init_db


async def persist_turn(state: AgentState) -> StateUpdate:
    """Write the completed Q&A turn to the local SQLite database."""
    session_id = state.get("session_id", "default")
    question = state["question"]
    answer = state.get("answer", "")
    steps = {
        "thinking": state.get("thinking", []),
        "intent": state["intent"].model_dump() if state.get("intent") else None,
        "sql": state["sql_result"].model_dump() if state.get("sql_result") else None,
    }

    await init_db()
    async with get_sqlite_session_factory()() as session:
        await save_agent_turn(session, session_id, question, answer, steps)

    return {}
