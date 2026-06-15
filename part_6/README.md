# Part 6 — Human-in-the-loop

Builds on Part 5. We add a **human review** step that pauses the graph with
LangGraph's `interrupt()` so a reviewer can approve the draft answer or send
feedback for a rewrite (up to `HUMAN_REVIEW_MAX_RETRIES` cycles, default 3). To survive the pause we compile the
graph with a `MemorySaver` checkpointer.

## Roadmap

1. Create the human-in-the-loop validation node in `agent/nodes/human_review.py`, and reset per-turn flags in `agent/nodes/intent.py`
2. Register the review node, retry loop, and `MemorySaver` in `agent/graph.py`
3. Update `main.py` to resume after the interrupt
4. Add unit tests for review routing in `tests/unit/test_human_review.py`

## Layout (added to Part 5)

```text
part_6/
├── agent/
│   ├── graph.py               # human_review node, retry loop & MemorySaver
│   └── nodes/
│       ├── human_review.py    # Pauses the graph for review/feedback
│       └── intent.py          # Resets per-turn flags at the start of each turn
├── main.py                    # Runs the graph and resumes on pause
└── tests/unit/
    └── test_human_review.py   # Review router tests
```

## Human review node — `agent/nodes/human_review.py`

```python
APOLOGY = "Sorry, I cannot help you with this request after several attempts."


def human_review(state: AgentState) -> StateUpdate:
    """Pause for human approval or revision (up to HUMAN_REVIEW_MAX_RETRIES retries)."""
    if state.get("approved"):
        return {}
    max_retries = get_config().human_review_max_retries
    ...
    decision = interrupt({...})
```

If the reviewer approves, the node sets `approved=True`; any other resume value is a
refusal, so it rewrites `question` to append the feedback and increments `retry_count`
— if the refusal carries no feedback text, it falls back to a generic revision
instruction rather than treating the blank as an approval. When retries are exhausted
the node returns the `APOLOGY` and forces `approved=True` so the router can rely on a
single flag.

These per-turn flags (`approved`, `user_feedback`, `retry_count`) live in the
checkpointed state, which `MemorySaver` keeps **per `thread_id`**. `recognize_intent`
clears `approved`/`user_feedback` every time it runs, so a stale approval can't leak
into a later turn (which would make `human_review` short-circuit and skip review).
`retry_count` is handled differently because `recognize_intent` is also re-entered on
the revision loop: a genuinely new turn arrives with `approved=True` from the previous
(completed) turn and resets the counter, while a revision loop-back arrives with
`approved=False` and **preserves** the in-progress count — otherwise
`HUMAN_REVIEW_MAX_RETRIES` could never be reached.

## Routing & checkpointer — `agent/graph.py`

```python
def route_after_review(state: AgentState) -> str:
    if state.get("approved"):
        return END
    return "recognize_intent"
```

`build_graph()` now wires `compose_answer -> human_review -> [END |
recognize_intent]` and compiles with a `MemorySaver` checkpointer so the interrupted
thread can be resumed. Routing back to `recognize_intent` (rather than
`compose_answer`) lets the rewritten question go through full intent classification
on the next pass.

## Running & resuming — `main.py`

`main.py` runs the graph on a thread (`thread_id`) with `await graph.ainvoke(...)`.
When the graph hits `interrupt()` it pauses; we detect the pending step via
`graph.get_state(config).next` and resume the thread with
`await graph.ainvoke(Command(resume=...))`.
