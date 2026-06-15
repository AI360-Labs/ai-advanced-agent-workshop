from typing import Any

from agent.graph import build_graph

graph: Any | None = None


def get_graph() -> Any:
    global graph
    if graph is None:
        graph = build_graph()
    return graph
