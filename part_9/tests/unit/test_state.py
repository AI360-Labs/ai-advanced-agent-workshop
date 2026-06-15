from agent.state import thinking_reducer


def test_thinking_reducer_appends_within_a_turn() -> None:
    # Steps from successive nodes accumulate, like operator.add did.
    assert thinking_reducer(["step1"], ["step2"]) == ["step1", "step2"]


def test_thinking_reducer_resets_on_none() -> None:
    # ``None`` is the per-turn reset signal sent by recognize_intent; without it
    # the log (and the checkpoint) would grow unbounded across turns.
    assert thinking_reducer(["old turn"], None) == []
