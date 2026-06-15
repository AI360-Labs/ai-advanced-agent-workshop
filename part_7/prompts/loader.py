from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent


@lru_cache
def load_prompt(name: str) -> str:
    """Read a prompt template from ``prompts/<name>.md``.

    Keeping prompts in their own files (not inline strings) makes them easy to
    review, diff, and edit without touching node code.
    """
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"No prompt named '{name}' in {PROMPTS_DIR}")
    return path.read_text(encoding="utf-8")
