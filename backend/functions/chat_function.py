"""
Azure Function for Steve's Mom Chat API

This module implements the Azure Function endpoint for the Steve's Mom
AI agent with LangChain and Pydantic integration.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict

import azure.functions as func
from azure.functions import HttpRequest, HttpResponse

# Import our AI agent and models
from ..ai.steves_mom_agent import create_steves_mom
from ..models.ai_models import (AIModelConfig, AIResponse, ChatMessage,
                                ChatResponse, HealthResponse, SystemHealth,
                                TaskRequest)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance (initialized on first request)
_agent = None


def get_agent():
    """Get or create the Steve's Mom agent instance."""
    global _agent
    if _agent is None:
        try:
            _agent = create_steves_mom(
                api_key=os.environ.get("CUSTOM_OPENAI_API_KEY"),
                enable_tools=True,
                memory_size=10,
            )
            logger.info("Steve's Mom agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    return _agent


async def main(req: HttpRequest) -> HttpResponse:
    """
    Main Azure Function entry point for chat API.

    Supports:
    - POST /api/chat - Chat with Steve's Mom
    - GET /api/health - Health check
    - POST /api/tasks - Generate tasks from request
    """
    try:
        method = req.method
        route = req.route_params.get("route", "chat")

        logger.info(f"Received {method} request for route: {route}")

        if method == "GET" and route == "health":
            return await handle_health_check(req)
        elif method == "POST" and route == "chat":
            return await handle_chat_request(req)
        elif method == "POST" and route == "tasks":
            return await handle_task_request(req)
        else:
            return HttpResponse(
                json.dumps({"error": "Endpoint not found"}),
                status_code=404,
                mimetype="application/json",
            )

    except Exception as e:
        logger.error(f"Unhandled error in main function: {e}")
        return HttpResponse(
            json.dumps(
                {
                    "error": "Internal server error",
                    "message": "Oh darling, something went terribly wrong! Let me fix this for you. 💋",
                }
            ),
            status_code=500,
            mimetype="application/json",
        )


async def handle_chat_request(req: HttpRequest) -> HttpResponse:
    """Handle chat requests with the Steve's Mom Agent."""
    try:
        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            return HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json",
            )

        if not body:
            return HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json",
            )

        # Extract required fields
        message = body.get("message", "").strip()
        user_id = body.get("user_id", "anonymous")
        session_id = body.get("session_id", "default")

        if not message:
            return HttpResponse(
                json.dumps({"error": "Message is required"}),
                status_code=400,
                mimetype="application/json",
            )

        # Validate message length
        if len(message) > 10000:
            return HttpResponse(
                json.dumps({"error": "Message too long (max 10,000 characters)"}),
                status_code=400,
                mimetype="application/json",
            )

        # Get agent and process request
        agent = get_agent()

        # Chat with Steve's Mom
        ai_response = await agent.chat(
            message=message, user_id=user_id, session_id=session_id
        )

        # Create API response
        chat_response = ChatResponse(
            message_id=ai_response.id,
            content=ai_response.content,
            session_id=session_id,
            timestamp=ai_response.timestamp,
            generated_tasks=ai_response.generated_tasks,
            tool_calls=ai_response.tool_calls,
            metadata=ai_response.metadata,
        )

        # Return structured response
        return HttpResponse(
            chat_response.json(), status_code=200, mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Error in chat request: {e}")
        return HttpResponse(
            json.dumps(
                {
                    "error": "Chat processing failed",
                    "message": "Oh sweetie, I had a little hiccup processing your request. Let me try again! 😘",
                }
            ),
            status_code=500,
            mimetype="application/json",
        )


async def handle_task_request(req: HttpRequest) -> HttpResponse:
    """Handle task generation requests."""
    try:
        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            return HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json",
            )

        if not body:
            return HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json",
            )

        # Validate task request with Pydantic
        try:
            task_request = TaskRequest(**body)
        except Exception as e:
            return HttpResponse(
                json.dumps({"error": f"Invalid task request: {e}"}),
                status_code=400,
                mimetype="application/json",
            )

        # Get agent and process task request
        agent = get_agent()

        # Create a message for task generation
        task_message = f"Please help me with this task: {task_request.description}"
        if task_request.category:
            task_message += f" (Category: {task_request.category.value})"
        if task_request.priority:
            task_message += f" (Priority: {task_request.priority.value})"

        # Process with agent
        ai_response = await agent.chat(
            message=task_message,
            user_id=task_request.user_id,
            session_id=task_request.session_id,
        )

        # Return task response
        return HttpResponse(
            json.dumps(
                {
                    "message": ai_response.content,
                    "generated_tasks": [
                        task.dict() for task in ai_response.generated_tasks
                    ],
                    "tool_calls": [call.dict() for call in ai_response.tool_calls],
                    "timestamp": ai_response.timestamp.isoformat(),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error in task request: {e}")
        return HttpResponse(
            json.dumps(
                {
                    "error": "Task processing failed",
                    "message": "Darling, I had trouble processing that task. Let me try a different approach! 💋",
                }
            ),
            status_code=500,
            mimetype="application/json",
        )


async def handle_health_check(req: HttpRequest) -> HttpResponse:
    """Handle health check requests."""
    try:
        # Check agent status
        agent_healthy = False
        agent_error = None

        try:
            agent = get_agent()
            # Simple health check - verify agent is responsive
            memory_summary = agent.get_memory_summary()
            agent_healthy = True
        except Exception as e:
            agent_error = str(e)
            logger.error(f"Agent health check failed: {e}")

        # Check environment variables
        env_healthy = bool(os.environ.get("CUSTOM_OPENAI_API_KEY"))

        # Determine overall health
        overall_healthy = agent_healthy and env_healthy

        # Create health response
        system_health = SystemHealth(
            overall_status="healthy" if overall_healthy else "unhealthy",
            ai_provider_status={"grok": agent_healthy},
            database_status=True,  # Would check actual DB connection
            cache_status=True,  # Would check Redis connection
            storage_status=True,  # Would check Azure Storage
            active_sessions=0,  # Would get from session manager
            total_requests_today=0,  # Would get from metrics
            error_rate_percent=0.0 if agent_healthy else 100.0,
        )

        health_response = HealthResponse(
            status=system_health.overall_status,
            timestamp=system_health.timestamp,
            details=system_health,
        )

        status_code = 200 if overall_healthy else 503

        return HttpResponse(
            health_response.json(), status_code=status_code, mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return HttpResponse(
            json.dumps(
                {
                    "status": "unhealthy",
                    "error": "Health check failed",
                    "timestamp": "2025-08-13T18:00:00Z",
                }
            ),
            status_code=503,
            mimetype="application/json",
        )


# Additional utility functions for Azure Functions
def create_cors_response(response: HttpResponse) -> HttpResponse:
    """Add CORS headers to response."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


# Azure Function binding configuration
def get_function_json() -> Dict[str, Any]:
    """Generate function.json configuration for Azure Functions."""
    return {
        "scriptFile": "chat_function.py",
        "bindings": [
            {
                "authLevel": "function",
                "type": "httpTrigger",
                "direction": "in",
                "name": "req",
                "methods": ["get", "post", "options"],
                "route": "api/{route?}",
            },
            {"type": "http", "direction": "out", "name": "$return"},
        ],
    }
