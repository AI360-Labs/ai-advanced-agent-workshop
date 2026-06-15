from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command

from api.deps import get_graph
from api.schemas import ChatRequest, ChatResponse, HealthResponse, ResumeRequest

app = FastAPI(
    title="Northwind Agent API",
    description="LangGraph agent over Northwind SQL and report documents.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the current health status of the API.",
)
async def health() -> HealthResponse:
    return HealthResponse()


@app.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a chat message",
    description="Process a single question and return the agent's response. This endpoint creates or resumes a conversation thread using the `session_id`.",
)
async def chat(body: ChatRequest) -> ChatResponse:
    graph = get_graph()
    config = {"configurable": {"thread_id": body.session_id}}
    final = await graph.ainvoke(
        {
            "question": body.question,
            "session_id": body.session_id,
        },
        config=config,
    )
    snapshot = graph.get_state(config)
    intent = final["intent"]
    return ChatResponse(
        session_id=body.session_id,
        answer=final.get("answer", ""),
        intent=intent.intent,
        reason=intent.reason,
        paused_for_review=bool(snapshot.next),
    )


@app.post(
    "/chat/resume",
    response_model=ChatResponse,
    summary="Resume a paused chat",
    description="Continue a paused chat thread after human review. Provide approval or textual feedback.",
)
async def resume_chat(body: ResumeRequest) -> ChatResponse:
    graph = get_graph()
    config = {"configurable": {"thread_id": body.session_id}}
    payload = {"approved": True} if body.approved else {"feedback": body.feedback or ""}
    final = await graph.ainvoke(Command(resume=payload), config=config)
    snapshot = graph.get_state(config)
    intent = final["intent"]
    return ChatResponse(
        session_id=body.session_id,
        answer=final.get("answer", ""),
        intent=intent.intent,
        reason=intent.reason,
        paused_for_review=bool(snapshot.next),
    )
