import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
try:
    from xai_sdk import XAI
    from xai_sdk.chat import system, user, assistant
except Exception:  # pragma: no cover
    XAI = None
from .schemas import ChatRequest, ChatResponse, ChatMessage

app = FastAPI(title="Steve's Mom API", version="0.1.0")

# Allow local dev origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    api_key = os.environ.get("GROK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROK_API_KEY not set")

    if XAI is None:
        raise HTTPException(status_code=500, detail="xai_sdk is not installed on the server")

    client = XAI(api_key=api_key)

    # Default model if not provided
    model = req.model or "grok-3-mini"

    start = time.time()
    try:
        # Create chat session and append messages
        chat = client.chat.create(model=model)

        # If there's an initial system prompt in messages, honor order
        for m in req.messages:
            if m.role == "system":
                chat.append(system(m.content))
            elif m.role == "user":
                chat.append(user(m.content))
            elif m.role == "assistant":
                chat.append(assistant(m.content))

        # Generate completion (sample() is synchronous in current SDK)
        resp = chat.sample()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"xAI error: {e}")

    dur_ms = int((time.time() - start) * 1000)

    choice = resp.choices[0] if getattr(resp, "choices", None) else None
    if not choice or not getattr(choice, "message", None):
        raise HTTPException(status_code=502, detail="No completion returned")

    assistant_content = (
        getattr(choice.message, "reasoning_content", None)
        or getattr(choice.message, "content", "")
        or str(choice.message)
    )
    reasoning_content = getattr(choice.message, "reasoning_content", None)

    usage = getattr(resp, "usage", None)

    return ChatResponse(
        message=ChatMessage(role="assistant", content=assistant_content),
        provider="grok",
        model=getattr(resp, "model", model),
        response_time_ms=dur_ms,
        reasoning_content=reasoning_content,
        prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
        completion_tokens=getattr(usage, "completion_tokens", None) if usage else None,
        total_tokens=getattr(usage, "total_tokens", None) if usage else None,
    )
