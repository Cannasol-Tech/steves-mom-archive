from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

try:
    # xai_sdk 1.x exposes `Client`. Alias to XAI for backward-compat usage below.
    from xai_sdk import Client as XAI
except Exception:  # pragma: no cover
    XAI = None
from contextlib import asynccontextmanager

# Database models and engine for local dev initialization
from backend.database import engine
from backend.models.orm.base import Base
# Import models so SQLAlchemy registers tables
import backend.models.orm.task  # noqa: F401
import backend.models.orm.approval_history  # noqa: F401

from backend.ai.model_router import (ModelRouter, ProviderError,
                                     create_router_from_env)
from backend.ai.providers.base import ModelConfig

from .connection_manager import manager
from .routes import tasks
from .schemas import ChatRequest

model_router: ModelRouter | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup/shutdown lifecycle.

    - Initialize local SQLite DB schema (create tables if missing)
    - Load the AI ModelRouter from environment configuration
    """
    global model_router

    # Ensure local SQLite database has required tables (idempotent)
    try:
        Base.metadata.create_all(bind=engine)
        print("INFO:     Database tables ensured (SQLite)")
    except Exception as e:
        print(f"WARNING:  Failed to initialize database schema: {e}")

    print("INFO:     Loading model router...")
    model_router = await create_router_from_env()
    print("INFO:     Model router loaded.")

    yield

    # Clean up resources if needed
    model_router = None


app = FastAPI(title="Steve's Mom API", version="0.1.0", lifespan=lifespan)

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

# Provide /api/health alias so CRA proxy checks succeed in local preview


@app.get("/api/health")
async def api_health():
    return {"status": "ok"}


async def stream_response(req: ChatRequest):
    """Generator function to stream response from the ModelRouter."""
    if not model_router:
        yield "Error: Model router not initialized"
        return

    model_config = ModelConfig(model_name=req.model or "grok-3-mini", stream=True)
    full_response_chunks = []

    try:
        async for chunk in model_router.stream_request(req.messages, model_config):
            full_response_chunks.append(chunk)
            yield chunk

        # After streaming, parse for animation and broadcast
        final_text = "".join(full_response_chunks)
        try:
            cmd = _parse_animation_cmd(final_text)
            if cmd:
                await manager.broadcast(_json.dumps(cmd))
        except Exception as e:
            # Non-fatal if broadcast fails, but log it
            print(f"ERROR: Failed to broadcast animation command: {e}")

    except ProviderError as e:
        # If no providers are available, provide a mock response for testing
        if "No eligible providers available" in str(e):
            mock_response = (
                "Hello! I'm Steve's Mom AI assistant. I'm currently running in test "
                "mode since no AI providers are configured. This is a mock response "
                "to help with testing the streaming functionality."
            )

            # Stream the mock response word by word
            words = mock_response.split()
            for i, word in enumerate(words):
                if i == 0:
                    yield word
                else:
                    yield f" {word}"
                # Longer delay to allow cancel testing
                import asyncio
                await asyncio.sleep(0.3)
        else:
            yield f"Error: {str(e)}"
    except Exception as e:
        yield f"An unexpected error occurred: {str(e)}"


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not model_router:
        raise HTTPException(status_code=503, detail="Model router is not available")

    return StreamingResponse(stream_response(req), media_type="text/event-stream")
