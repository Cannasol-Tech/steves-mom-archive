import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, Enum):
    """Enumeration for the status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalHistory(BaseModel):
    """Schema for an approval history entry."""

    id: uuid.UUID
    status: TaskStatus
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class Task(BaseModel):
    """Schema for a task."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, description="Unique identifier for the task."
    )
    title: str = Field(..., description="The title of the task.")
    description: Optional[str] = Field(
        None, description="A detailed description of the task."
    )
    status: TaskStatus = Field(
        TaskStatus.PENDING, description="The current status of the task."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the task was created.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the task was last updated.",
    )
    approval_history: List[ApprovalHistory] = Field(
        [], description="A log of approval actions for the task."
    )

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    """Schema for updating a task. All fields are optional."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
