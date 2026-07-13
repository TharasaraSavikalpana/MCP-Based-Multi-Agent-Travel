import asyncio
import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agents.config import get_settings
from agents.entity import TravelState
from agents.graph import travel_graph


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, Any]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str
    route: Optional[str] = None
    events: List[Dict[str, object]] = []
    errors: List[str] = []


app = FastAPI(
    title="TripWeaver API",
    description="MCP-based multi-agent travel planner backend.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "service": "tripweaver-api"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    state = await _run_graph(request)
    return ChatResponse(
        response=state.get("response", ""),
        route=state.get("route"),
        events=state.get("events", []),
        errors=state.get("errors", []),
    )


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    async def event_generator():
        try:
            state = await _run_graph(request)
            for event in state.get("events", []):
                yield _sse("activity", event)
                await asyncio.sleep(0.05)

            response = state.get("response", "")
            buffer = ""
            for character in response:
                buffer += character
                if len(buffer) >= 12 or character in "\n.!?":
                    yield _sse("token", {"text": buffer})
                    buffer = ""
                    await asyncio.sleep(0.01)
            if buffer:
                yield _sse("token", {"text": buffer})

            yield _sse(
                "done",
                {
                    "route": state.get("route"),
                    "errors": state.get("errors", []),
                    "events": state.get("events", []),
                },
            )
        except Exception as exc:
            yield _sse(
                "error",
                {
                    "message": "TripWeaver hit an unexpected backend error. Please try again.",
                    "detail": str(exc),
                },
            )

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def _run_graph(request: ChatRequest) -> TravelState:
    initial_state: TravelState = {
        "user_query": request.message.strip(),
        "history": _normalise_history(request.history),
        "events": [],
        "errors": [],
        "hotel_results": [],
        "flight_results": [],
        "tool_status": "IDLE",
    }
    return await travel_graph.ainvoke(initial_state)


def _normalise_history(history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    clean_history: List[Dict[str, str]] = []
    for item in history[-12:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip() or "user"
        content = item.get("content", "")
        if isinstance(content, dict):
            content = content.get("text", "")
        content = str(content or "").strip()
        if role in {"user", "assistant", "system"} and content:
            clean_history.append({"role": role, "content": content})
    return clean_history


def _sse(event: str, payload: Dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("main:app", host=settings.backend_host, port=settings.backend_port, reload=True)
