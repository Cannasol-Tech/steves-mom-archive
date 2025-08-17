import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..task_models import TaskStatus
from .base import Base


class ApprovalHistory(Base):
    """SQLAlchemy model for the approval_history table."""

    __tablename__ = "approval_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    status = Column(SQLAlchemyEnum(TaskStatus), nullable=False)
    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    task = relationship("Task", back_populates="approval_history")

    def __repr__(self):
        return f"<ApprovalHistory(id='{self.id}', task_id='{self.task_id}', status='{self.status}')>"
