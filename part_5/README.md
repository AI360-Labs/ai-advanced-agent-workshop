# Part 5 — Graph assembly

Builds on Part 4. We assemble the retrieval nodes from Part 4 into a complete
**LangGraph** with conditional routing: intent recognition fans out to a refusal
path, a SQL query path, or a document search path, and the retrieval paths merge
into an **answer composition** node. We also align the document search path with
the real `rag.documents` table and switch the entry point to the async graph API.

## Roadmap

1. Add `user_feedback` and `approved` fields to `AgentState` in `agent/state.py`
2. Implement the safety/refusal node in `agent/nodes/refuse.py`
3. Add the `sql_answer.md` answer prompt and add a `{feedback}` placeholder to `document_answer.md` (carried over from Part 4) so revisions reach both paths
4. Implement the answer composition node in `agent/nodes/compose_answer.py`
5. Assemble the graph and conditional routing in `agent/graph.py`
6. Configure the PostgreSQL `search_path` in `db/session.py` and `db/schema_snippet.py`
7. Route the `aembed` embedding call through OpenRouter in `utils/llm_client.py`
8. Wire document search to `rag.documents` in `agent/nodes/document_search.py`, `db/schemas.py`, `db/models.py`
9. Switch `main.py` to the async graph API
10. Verify routing with unit tests in `tests/unit/test_graph_routing.py`

## Layout (added to Part 4)

```text
part_5/
├── agent/
│   ├── graph.py               # LangGraph assembly & routing logic
│   ├── state.py               # Updated with user_feedback and approved keys
│   └── nodes/
│       ├── compose_answer.py  # Composes natural-language answers
│       ├── document_search.py # Queries the real rag.documents table
│       └── refuse.py          # Handles out-of-scope / safety refusals
├── db/
│   ├── session.py             # search_path connect_args
│   ├── schema_snippet.py      # Header mentions the rag schema
│   ├── schemas.py             # ReportMatch uses the source column
│   └── models.py              # Report model -> rag.documents
├── prompts/
│   └── sql_answer.md          # Prompt template for database answers
├── utils/
│   └── llm_client.py          # aembed routes the model via OpenRouter
├── main.py                    # Runs the assembled graph asynchronously
└── tests/unit/
    └── test_graph_routing.py  # Unit tests for the routing function
```

## Routing & assembly — `agent/graph.py`

```python
def route_after_intent(state: AgentState) -> str:
    match state["intent"].intent:
        case "security_breach" | "out_of_scope":
            return "refuse"
        case "document_search":
            return "search_documents"
        case "northwind_query" | "reporting":
            return "select_query"
        case other:
            raise ValueError(f"Unhandled intent: {other}")
```

`build_graph()` wires `START -> recognize_intent -> [refuse | select_query |
search_documents]`. From `select_query` a second router dispatches to either
`run_catalog_query` (named ORM query) or `run_sql_query` (LLM SQL fallback); both
merge into `compose_answer -> END`. The refusal path goes straight to `END`.

## Answer prompt — `prompts/sql_answer.md`

```markdown
You answer questions using SQL query results from the Northwind database.

SQL executed:
{sql}

Rationale: {rationale}

Rows (JSON):
{rows}

User question:
{question}

{feedback}

Write a clear, concise answer. Use only the data shown above.
```

## Database schemas

Tables live across two PostgreSQL schemas: Northwind tables live in
`northwind`, the vector document store lives in `rag`. `db/session.py` sets
`search_path: "northwind,public,rag"` on the connection so queries resolve table
names without schema prefixes. Document search targets `rag.documents` with a
`source` column (not `title`).

## Tests — `tests/unit/test_graph_routing.py`

```python
def test_routes_security_to_refuse() -> None:
    assert route_after_intent(state_with_intent("security_breach")) == "refuse"


def test_routes_document_search() -> None:
    assert route_after_intent(state_with_intent("document_search")) == "search_documents"


def test_routes_reporting_to_select() -> None:
    assert route_after_intent(state_with_intent("reporting")) == "select_query"
```

See [db/schema_reference.md](db/schema_reference.md).
