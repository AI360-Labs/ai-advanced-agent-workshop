import csv
from pathlib import Path

from pydantic import BaseModel

from agent.state import Intent

CSV_PATH = Path(__file__).resolve().parent / "intent_dataset.csv"


class IntentExample(BaseModel):
    """One labelled example for evaluating the intent classifier."""

    text: str
    expected: Intent


def load_examples() -> list[IntentExample]:
    """Read the CSV once and return a validated list of ``IntentExample``s."""
    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return [
            IntentExample(text=row["text"], expected=row["expected"]) for row in reader
        ]


# A small, hand-labelled set.  The security_breach group is deliberately varied:
# prompt injection, destructive SQL, and credential/secret exfiltration.
INTENT_EXAMPLES: list[IntentExample] = load_examples()
