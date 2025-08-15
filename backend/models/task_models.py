from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Optional
import uuid

class TaskStatus(str, Enum):
    """Enumeration for the status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task(BaseModel):
    """Schema for a task."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for the task.")
    title: str = Field(..., description="The title of the task.")
    description: Optional[str] = Field(None, description="A detailed description of the task.")
    status: TaskStatus = Field(TaskStatus.PENDING, description="The current status of the task.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the task was created.")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the task was last updated.")

    model_config = ConfigDict(from_attributes=True)
