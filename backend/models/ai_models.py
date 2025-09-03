"""
Pydantic Models for AI System - Steve's Mom AI Chatbot

This module defines all Pydantic models for structured AI outputs,
ensuring type safety and validation across the entire system.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class MessageRole(str, Enum):
    """Enumeration of message roles in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Task status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskCategory(str, Enum):
    """Task categories for agent specialization."""

    EMAIL = "email"
    DOCUMENT = "document"
    INVENTORY = "inventory"
    DATABASE = "database"
    SCHEDULING = "scheduling"
    REPORTING = "reporting"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"


class AIProvider(str, Enum):
    """Supported AI providers."""

    GROK = "grok"
    OPENAI = "openai"
    CLAUDE = "claude"
    AZURE_OPENAI = "azure_openai"


class ChatMessage(BaseModel):
    """Structured chat message with validation."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str = Field(..., min_length=1, max_length=10000)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class AIModelConfig(BaseModel):
    """Configuration for AI model requests."""

    provider: AIProvider = AIProvider.GROK
    model_name: str = "grok-3-mini"
    max_tokens: int = Field(default=4096, ge=1, le=32000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    stop_sequences: List[str] = Field(default_factory=list)
    stream: bool = False
    enable_tools: bool = True

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v, info):
        """Validate model name matches provider."""
        provider = info.data.get("provider") if info.data else None
        if provider == AIProvider.GROK and not v.startswith("grok"):
            raise ValueError("GROK provider requires grok model name")
        return v


class TaskRequest(BaseModel):
    """Structured task request from user input."""

    description: str = Field(..., min_length=1, max_length=1000)
    category: Optional[TaskCategory] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    user_id: str
    session_id: str


class GeneratedTask(BaseModel):
    """AI-generated task with structured output."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    category: TaskCategory
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    estimated_duration_minutes: Optional[int] = Field(
        None, ge=1, le=10080
    )  # Max 1 week
    required_tools: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "steves_mom"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v):
        """Ensure confidence score is reasonable."""
        if v < 0.3:
            raise ValueError("Confidence score too low for task generation")
        return v


class ToolCall(BaseModel):
    """Structured tool/function call."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = Field(..., min_length=1)
    arguments: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolResult(BaseModel):
    """Result from tool execution."""

    tool_call_id: str
    success: bool
    result: Any = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AIResponse(BaseModel):
    """Structured AI response with validation."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(..., min_length=1)
    provider: AIProvider
    model: str
    usage: Dict[str, int] = Field(default_factory=dict)  # tokens, cost, etc.
    tool_calls: List[ToolCall] = Field(default_factory=list)
    finish_reason: Optional[str] = None
    response_time_ms: Optional[int] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    generated_tasks: List[GeneratedTask] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ConversationSession(BaseModel):
    """Structured conversation session."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("message_count", "total_tokens")
    @classmethod
    def validate_non_negative(cls, v):
        """Ensure counts are non-negative."""
        if v < 0:
            raise ValueError("Count values must be non-negative")
        return v


class BusinessIntegration(BaseModel):
    """Configuration for business system integrations."""

    integration_type: Literal["email", "inventory", "database", "document", "calendar"]
    name: str = Field(..., min_length=1, max_length=100)
    enabled: bool = True
    configuration: Dict[str, Any] = Field(default_factory=dict)
    last_sync: Optional[datetime] = None
    error_count: int = 0

    @field_validator("error_count")
    @classmethod
    def validate_error_count(cls, v):
        """Ensure error count is non-negative."""
        if v < 0:
            raise ValueError("Error count must be non-negative")
        return v


class InventoryItem(BaseModel):
    """Structured inventory item for tool integration."""

    item_id: str
    name: str = Field(..., min_length=1, max_length=200)
    sku: Optional[str] = None
    quantity_on_hand: int = Field(..., ge=0)
    quantity_on_order: int = Field(default=0, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    unit_cost: Optional[float] = Field(None, ge=0.0)
    location: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class EmailRequest(BaseModel):
    """Structured email request for tool integration."""

    recipient: str = Field(
        ..., pattern=r"^[^@]+@[^@]+\.[^@]+$"
    )  # Basic email validation
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=10000)
    cc: List[str] = Field(default_factory=list)
    bcc: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)
    priority: Literal["low", "normal", "high"] = "normal"

    @field_validator("cc", "bcc")
    @classmethod
    def validate_email_lists(cls, v):
        """Validate email addresses in CC and BCC."""
        import re

        email_pattern = r"^[^@]+@[^@]+\.[^@]+$"
        for email in v:
            if not re.match(email_pattern, email):
                raise ValueError(f"Invalid email address: {email}")
        return v


class DocumentRequest(BaseModel):
    """Structured document generation request."""

    template_name: str = Field(..., min_length=1, max_length=100)
    output_format: Literal["pdf", "docx", "html", "txt"] = "pdf"
    data: Dict[str, Any] = Field(default_factory=dict)
    output_filename: Optional[str] = None
    classification_level: Literal[
        "public", "internal", "confidential", "secret", "top_secret"
    ] = "internal"


class DatabaseQuery(BaseModel):
    """Structured database query request with safety validation."""

    query_type: Literal["select", "count", "aggregate"] = (
        "select"  # Only safe operations
    )
    table_name: str = Field(..., min_length=1, max_length=100)
    columns: List[str] = Field(default_factory=list)
    where_conditions: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=100, ge=1, le=1000)

    @field_validator("query_type")
    @classmethod
    def validate_safe_query(cls, v):
        """Ensure only safe query types are allowed."""
        safe_types = ["select", "count", "aggregate"]
        if v not in safe_types:
            raise ValueError(f"Only safe query types allowed: {safe_types}")
        return v


class SystemHealth(BaseModel):
    """System health status with structured metrics."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    overall_status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    ai_provider_status: Dict[str, bool] = Field(default_factory=dict)
    database_status: bool = True
    cache_status: bool = True
    storage_status: bool = True
    active_sessions: int = Field(default=0, ge=0)
    total_requests_today: int = Field(default=0, ge=0)
    average_response_time_ms: Optional[float] = Field(None, ge=0.0)
    error_rate_percent: float = Field(default=0.0, ge=0.0, le=100.0)

    @model_validator(mode="before")
    @classmethod
    def validate_overall_status(cls, values):
        """Determine overall status based on component health."""
        if isinstance(values, dict):
            ai_status = values.get("ai_provider_status", {})
            db_status = values.get("database_status", True)
            cache_status = values.get("cache_status", True)
            storage_status = values.get("storage_status", True)
            error_rate = values.get("error_rate_percent", 0.0)

            # Determine overall health
            if not db_status or not any(ai_status.values()) if ai_status else False:
                values["overall_status"] = "unhealthy"
            elif not cache_status or not storage_status or error_rate > 10.0:
                values["overall_status"] = "degraded"
            else:
                values["overall_status"] = "healthy"

        return values


# Response models for API endpoints
class ChatResponse(BaseModel):
    """API response for chat endpoints."""

    message_id: str
    content: str
    session_id: str
    timestamp: datetime
    generated_tasks: List[GeneratedTask] = Field(default_factory=list)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskListResponse(BaseModel):
    """API response for task listing."""

    tasks: List[GeneratedTask]
    total_count: int
    page: int = 1
    page_size: int = 50
    has_more: bool = False


class HealthResponse(BaseModel):
    """API response for health check."""

    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    details: SystemHealth
