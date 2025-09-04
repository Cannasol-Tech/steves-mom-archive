"""
Unit tests for backend.models.task_models

Tests Pydantic models for task management including:
- TaskStatus enum validation
- Task model creation and validation
- ApprovalHistory model functionality
- TaskUpdate model for partial updates
- Field validation and constraints
- Serialization and deserialization

Author: Cannasol Technologies
Date: 2025-01-04
Version: 1.0.0
"""

import pytest
import uuid
from datetime import datetime, timezone
from pydantic import ValidationError

import sys
from pathlib import Path

# Ensure backend package is importable
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.models.task_models import TaskStatus, Task, ApprovalHistory, TaskUpdate


class TestTaskStatus:
    """Test TaskStatus enum functionality."""

    def test_task_status_values(self):
        """Test that all TaskStatus values are correctly defined."""
        expected_values = {
            "PENDING": "pending",
            "IN_PROGRESS": "in_progress",
            "COMPLETED": "completed",
            "FAILED": "failed",
            "CANCELLED": "cancelled",
            "PENDING_APPROVAL": "pending_approval",
            "APPROVED": "approved",
            "REJECTED": "rejected"
        }

        for attr_name, expected_value in expected_values.items():
            status = getattr(TaskStatus, attr_name)
            assert status.value == expected_value
            # Note: str(enum) returns 'EnumClass.MEMBER_NAME', not the value
            assert status == expected_value  # Test equality with string value

    def test_task_status_enum_membership(self):
        """Test TaskStatus enum membership."""
        valid_statuses = [
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.PENDING_APPROVAL,
            TaskStatus.APPROVED,
            TaskStatus.REJECTED
        ]

        for status in valid_statuses:
            assert isinstance(status, TaskStatus)
            assert status in TaskStatus

    def test_task_status_string_comparison(self):
        """Test TaskStatus string value comparison."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"
        assert TaskStatus.PENDING_APPROVAL == "pending_approval"
        assert TaskStatus.APPROVED == "approved"
        assert TaskStatus.REJECTED == "rejected"


class TestApprovalHistory:
    """Test ApprovalHistory model functionality."""

    def test_approval_history_creation(self):
        """Test creating ApprovalHistory instances."""
        history_id = uuid.uuid4()
        timestamp = datetime.now(timezone.utc)

        history = ApprovalHistory(
            id=history_id,
            status=TaskStatus.APPROVED,
            timestamp=timestamp
        )

        assert history.id == history_id
        assert history.status == TaskStatus.APPROVED
        assert history.timestamp == timestamp

    def test_approval_history_with_different_statuses(self):
        """Test ApprovalHistory with different status values."""
        history_id = uuid.uuid4()
        timestamp = datetime.now(timezone.utc)

        for status in TaskStatus:
            history = ApprovalHistory(
                id=history_id,
                status=status,
                timestamp=timestamp
            )
            assert history.status == status

    def test_approval_history_serialization(self):
        """Test ApprovalHistory serialization."""
        history_id = uuid.uuid4()
        timestamp = datetime.now(timezone.utc)

        history = ApprovalHistory(
            id=history_id,
            status=TaskStatus.APPROVED,
            timestamp=timestamp
        )

        data = history.model_dump()
        assert data["id"] == history_id
        assert data["status"] == TaskStatus.APPROVED
        assert data["timestamp"] == timestamp

    def test_approval_history_from_attributes(self):
        """Test ApprovalHistory from_attributes configuration."""
        # This tests the ConfigDict(from_attributes=True) setting
        # which allows creation from ORM objects

        # Mock ORM-like object
        class MockORM:
            def __init__(self):
                self.id = uuid.uuid4()
                self.status = TaskStatus.REJECTED
                self.timestamp = datetime.now(timezone.utc)

        orm_obj = MockORM()
        history = ApprovalHistory.model_validate(orm_obj)

        assert history.id == orm_obj.id
        assert history.status == orm_obj.status
        assert history.timestamp == orm_obj.timestamp


class TestTask:
    """Test Task model functionality."""

    def test_task_creation_with_defaults(self):
        """Test creating Task with minimal required fields."""
        task = Task(title="Test Task")

        assert task.title == "Test Task"
        assert task.description is None
        assert task.status == TaskStatus.PENDING
        assert isinstance(task.id, uuid.UUID)
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)
        assert task.approval_history == []

    def test_task_creation_with_all_fields(self):
        """Test creating Task with all fields specified."""
        task_id = uuid.uuid4()
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        approval_history = [
            ApprovalHistory(
                id=uuid.uuid4(),
                status=TaskStatus.APPROVED,
                timestamp=datetime.now(timezone.utc)
            )
        ]

        task = Task(
            id=task_id,
            title="Complete Task",
            description="A detailed description",
            status=TaskStatus.IN_PROGRESS,
            created_at=created_at,
            updated_at=updated_at,
            approval_history=approval_history
        )

        assert task.id == task_id
        assert task.title == "Complete Task"
        assert task.description == "A detailed description"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.created_at == created_at
        assert task.updated_at == updated_at
        assert task.approval_history == approval_history

    def test_task_title_validation(self):
        """Test Task title field validation."""
        # Title is required
        with pytest.raises(ValidationError) as exc_info:
            Task()

        error = exc_info.value.errors()[0]
        assert error["type"] == "missing"
        assert "title" in error["loc"]

        # Empty title should be allowed (string validation)
        task = Task(title="")
        assert task.title == ""

    def test_task_status_validation(self):
        """Test Task status field validation."""
        # Valid status values
        for status in TaskStatus:
            task = Task(title="Test", status=status)
            assert task.status == status

        # Invalid status should raise ValidationError
        with pytest.raises(ValidationError):
            Task(title="Test", status="invalid_status")

    def test_task_id_auto_generation(self):
        """Test that Task ID is auto-generated when not provided."""
        task1 = Task(title="Task 1")
        task2 = Task(title="Task 2")

        assert isinstance(task1.id, uuid.UUID)
        assert isinstance(task2.id, uuid.UUID)
        assert task1.id != task2.id  # Should be unique

    def test_task_timestamp_auto_generation(self):
        """Test that timestamps are auto-generated when not provided."""
        task = Task(title="Test Task")

        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)
        assert task.created_at.tzinfo is not None  # Should be timezone-aware
        assert task.updated_at.tzinfo is not None

    def test_task_serialization(self):
        """Test Task serialization to dict and JSON."""
        task = Task(
            title="Test Task",
            description="Test description",
            status=TaskStatus.IN_PROGRESS
        )

        data = task.model_dump()
        assert data["title"] == "Test Task"
        assert data["description"] == "Test description"
        assert data["status"] == TaskStatus.IN_PROGRESS
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "approval_history" in data

    def test_task_from_attributes(self):
        """Test Task from_attributes configuration."""
        # Mock ORM-like object
        class MockTaskORM:
            def __init__(self):
                self.id = uuid.uuid4()
                self.title = "ORM Task"
                self.description = "From ORM"
                self.status = TaskStatus.COMPLETED
                self.created_at = datetime.now(timezone.utc)
                self.updated_at = datetime.now(timezone.utc)
                self.approval_history = []

        orm_obj = MockTaskORM()
        task = Task.model_validate(orm_obj)

        assert task.id == orm_obj.id
        assert task.title == orm_obj.title
        assert task.description == orm_obj.description
        assert task.status == orm_obj.status
        assert task.created_at == orm_obj.created_at
        assert task.updated_at == orm_obj.updated_at
        assert task.approval_history == orm_obj.approval_history

    def test_task_with_approval_history(self):
        """Test Task with approval history entries."""
        approval1 = ApprovalHistory(
            id=uuid.uuid4(),
            status=TaskStatus.PENDING_APPROVAL,
            timestamp=datetime.now(timezone.utc)
        )
        approval2 = ApprovalHistory(
            id=uuid.uuid4(),
            status=TaskStatus.APPROVED,
            timestamp=datetime.now(timezone.utc)
        )

        task = Task(
            title="Task with History",
            approval_history=[approval1, approval2]
        )

        assert len(task.approval_history) == 2
        assert task.approval_history[0] == approval1
        assert task.approval_history[1] == approval2


class TestTaskUpdate:
    """Test TaskUpdate model functionality."""

    def test_task_update_creation_empty(self):
        """Test creating empty TaskUpdate."""
        update = TaskUpdate()

        assert update.title is None
        assert update.description is None
        assert update.status is None

    def test_task_update_creation_with_fields(self):
        """Test creating TaskUpdate with specific fields."""
        update = TaskUpdate(
            title="Updated Title",
            description="Updated description",
            status=TaskStatus.COMPLETED
        )

        assert update.title == "Updated Title"
        assert update.description == "Updated description"
        assert update.status == TaskStatus.COMPLETED

    def test_task_update_partial_fields(self):
        """Test TaskUpdate with only some fields set."""
        # Only title
        update1 = TaskUpdate(title="New Title")
        assert update1.title == "New Title"
        assert update1.description is None
        assert update1.status is None

        # Only status
        update2 = TaskUpdate(status=TaskStatus.FAILED)
        assert update2.title is None
        assert update2.description is None
        assert update2.status == TaskStatus.FAILED

        # Only description
        update3 = TaskUpdate(description="New description")
        assert update3.title is None
        assert update3.description == "New description"
        assert update3.status is None

    def test_task_update_status_validation(self):
        """Test TaskUpdate status field validation."""
        # Valid status values
        for status in TaskStatus:
            update = TaskUpdate(status=status)
            assert update.status == status

        # Invalid status should raise ValidationError
        with pytest.raises(ValidationError):
            TaskUpdate(status="invalid_status")

    def test_task_update_serialization(self):
        """Test TaskUpdate serialization."""
        update = TaskUpdate(
            title="Updated Title",
            status=TaskStatus.IN_PROGRESS
        )

        data = update.model_dump()
        assert data["title"] == "Updated Title"
        assert data["description"] is None
        assert data["status"] == TaskStatus.IN_PROGRESS

    def test_task_update_exclude_unset(self):
        """Test TaskUpdate serialization with exclude_unset."""
        update = TaskUpdate(title="Updated Title")

        # With exclude_unset=True, only set fields should be included
        data = update.model_dump(exclude_unset=True)
        assert data == {"title": "Updated Title"}
        assert "description" not in data
        assert "status" not in data

        # With exclude_unset=False (default), all fields should be included
        data_all = update.model_dump(exclude_unset=False)
        assert data_all["title"] == "Updated Title"
        assert data_all["description"] is None
        assert data_all["status"] is None


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_task_with_very_long_title(self):
        """Test Task with very long title."""
        long_title = "x" * 1000  # 1000 characters
        task = Task(title=long_title)
        assert task.title == long_title

    def test_task_with_very_long_description(self):
        """Test Task with very long description."""
        long_description = "x" * 10000  # 10k characters
        task = Task(title="Test", description=long_description)
        assert task.description == long_description

    def test_task_with_unicode_content(self):
        """Test Task with Unicode characters."""
        unicode_title = "Task 🚀 with émojis and 中文"
        unicode_description = "Description with special chars: ñáéíóú"

        task = Task(title=unicode_title, description=unicode_description)
        assert task.title == unicode_title
        assert task.description == unicode_description

    def test_task_with_special_characters(self):
        """Test Task with special characters."""
        special_title = 'Task with "quotes" and newlines\n'
        special_description = "Description with tabs\t and returns\r\n"

        task = Task(title=special_title, description=special_description)
        assert task.title == special_title
        assert task.description == special_description

    def test_approval_history_with_future_timestamp(self):
        """Test ApprovalHistory with future timestamp."""
        future_time = datetime(2030, 1, 1, tzinfo=timezone.utc)

        history = ApprovalHistory(
            id=uuid.uuid4(),
            status=TaskStatus.APPROVED,
            timestamp=future_time
        )

        assert history.timestamp == future_time

    def test_task_json_serialization_roundtrip(self):
        """Test Task JSON serialization and deserialization roundtrip."""
        original_task = Task(
            title="Roundtrip Task",
            description="Test roundtrip",
            status=TaskStatus.IN_PROGRESS
        )

        # Serialize to JSON
        json_str = original_task.model_dump_json()

        # Deserialize from JSON
        import json
        data = json.loads(json_str)
        restored_task = Task(**data)

        assert restored_task.title == original_task.title
        assert restored_task.description == original_task.description
        assert restored_task.status == original_task.status
        # Note: UUID and datetime objects need special handling in JSON roundtrip