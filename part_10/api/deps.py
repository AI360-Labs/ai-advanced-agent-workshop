from langgraph.graph.state import CompiledStateGraph

from agent.graph import build_graph

graph: CompiledStateGraph | None = None


def get_graph() -> CompiledStateGraph:
    global graph
    if graph is None:
        graph = build_graph()
    return graph
