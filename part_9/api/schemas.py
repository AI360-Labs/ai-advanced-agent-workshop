from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    """Stable id for the conversation thread"""
    question: str = Field(min_length=1, description="User question")


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    intent: str
    reason: str
    paused_for_review: bool = False


class ResumeRequest(BaseModel):
    session_id: str
    approved: bool = False
    """Default to not-approved: a review gate must require an explicit approval,
    so an empty body is treated as a refusal rather than silently approving."""
    feedback: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
