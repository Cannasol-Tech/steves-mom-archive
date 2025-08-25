import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

try:
    # xai_sdk 1.x exposes `Client`. Alias to XAI for backward-compat usage below.
    from xai_sdk import Client as XAI
    from xai_sdk.chat import assistant, system, user
except Exception:  # pragma: no cover
    XAI = None
from .connection_manager import manager
from .routes import tasks
from .schemas import ChatMessage, ChatRequest, ChatResponse

app = FastAPI(title="Steve's Mom API", version="0.1.0")

app.include_router(tasks.router, prefix="/api", tags=["tasks"])

# Allow local dev origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
Load environment variables from the repository root .env for local development.
This ensures GROK_API_KEY and other secrets are available when running Uvicorn.
"""
try:
    # backend/api/app.py -> repo root is two levels up
    REPO_ROOT = Path(__file__).resolve().parents[2]
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except Exception:
    # Non-fatal if dotenv loading fails; explicit env vars can still be used
    pass

# --- UI Animation directive parsing & broadcast ---
import json as _json
import re as _re

_ANIM_JSON_RE = _re.compile(r"\{\s*\"type\"\s*:\s*\"smom\"[^}]*\}", _re.IGNORECASE)
_ANIM_COMMENT_RE = _re.compile(r"smom:\s*\{[^}]*\}", _re.IGNORECASE)
_DSL_RE = _re.compile(r"\[smom\s+([^\]]+)\]", _re.IGNORECASE)


def _parse_animation_cmd(text: str):
    """Extract a minimal animation command dict from assistant text, if present."""
    if not text:
        return None
    # JSON block
    m = _ANIM_JSON_RE.search(text)
    if m:
        try:
            return _json.loads(m.group(0))
        except Exception:
            pass
    # HTML comment envelope
    m = _ANIM_COMMENT_RE.search(text)
    if m:
        try:
            js = m.group(0)
            js = js[js.find("{") :]
            cmd = _json.loads(js)
            cmd.setdefault("type", "smom")
            return cmd
        except Exception:
            pass
    # DSL fallback: [smom action=dance side=right intensity=high]
    m = _DSL_RE.search(text)
    if m:
        try:
            params = {}
            for part in m.group(1).split():
                if "=" in part:
                    k, v = part.split("=", 1)
                    params[k.strip()] = v.strip()
            if params:
                params.setdefault("type", "smom")
                return params
        except Exception:
            pass
    return None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    api_key = os.environ.get("GROK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROK_API_KEY not set")

    if XAI is None:
        raise HTTPException(
            status_code=500, detail="xai_sdk is not installed on the server"
        )

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

    # Robust extraction across xAI SDK variants
    assistant_content = ""
    reasoning_content = None

    # Direct attributes (newer SDKs)
    if hasattr(resp, "content") and resp.content:
        assistant_content = resp.content
    if hasattr(resp, "reasoning_content") and getattr(resp, "reasoning_content"):
        reasoning_content = getattr(resp, "reasoning_content")

    # Fallback to choices[0].message (older style)
    if not assistant_content and getattr(resp, "choices", None):
        choice = resp.choices[0]
        message = getattr(choice, "message", None)
        if message is not None:
            if reasoning_content is None:
                reasoning_content = getattr(message, "reasoning_content", None)
            assistant_content = getattr(message, "content", "") or str(message)

    # Final fallback
    if not assistant_content:
        assistant_content = str(resp) if resp is not None else ""

    if not assistant_content:
        raise HTTPException(status_code=502, detail="No completion returned")

    usage = getattr(resp, "usage", None)

    # Broadcast any inline animation directive via WebSocket
    try:
        cmd = _parse_animation_cmd(assistant_content)
        if cmd:
            await manager.broadcast(_json.dumps(cmd))
    except Exception:
        pass

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
