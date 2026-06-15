import asyncio

from langgraph.types import Command

from agent.graph import build_graph
from db.sqlite import init_db
from utils.logger import get_logger

logger = get_logger(__name__)


async def main() -> None:
    await init_db()
    graph = build_graph()
    thread_config = {"configurable": {"thread_id": "demo-session-1"}}

    question = "How many orders did customer ALFKI place?"
    logger.info(f"Run for: {question}")
    result = await graph.ainvoke({"question": question}, config=thread_config)
    if result.get("answer"):
        logger.info(f"Answer: {result['answer'].strip()[:300]}")

    snapshot = graph.get_state(thread_config)
    if snapshot.next:
        logger.info("Graph paused for human review — resuming with approval.")
        final = await graph.ainvoke(
            Command(resume={"approved": True}), config=thread_config
        )
        logger.info(f"Final answer: {final.get('answer', '')[:300]}")


if __name__ == "__main__":
    asyncio.run(main())
