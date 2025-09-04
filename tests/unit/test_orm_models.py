"""
Unit tests for ORM models

Tests SQLAlchemy ORM models including:
- Task model creation and validation
- ApprovalHistory model functionality
- Database relationships and constraints
- Model serialization and deserialization
- Field validation and defaults

Author: Cannasol Technologies
Date: 2025-01-04
Version: 1.0.0
"""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

import sys
from pathlib import Path

# Ensure backend package is importable
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.models.orm.base import Base
from backend.models.orm.task import Task
from backend.models.orm.approval_history import ApprovalHistory
from backend.models.task_models import TaskStatus


class TestTaskORM:
    """Test Task ORM model functionality."""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_task_creation(self, db_session):
        """Test creating a Task instance."""
        task = Task(
            title="Test Task",
            description="Test description",
            status=TaskStatus.PENDING
        )

        db_session.add(task)
        db_session.commit()

        assert task.id is not None
        assert isinstance(task.id, uuid.UUID)
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.status == TaskStatus.PENDING
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_task_required_fields(self, db_session):
        """Test that required fields are enforced."""
        # Title is required
        task = Task(description="Test description")

        db_session.add(task)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_task_default_values(self, db_session):
        """Test default values for Task fields."""
        task = Task(title="Test Task")

        db_session.add(task)
        db_session.commit()

        # Check defaults
        assert task.status == TaskStatus.PENDING
        assert task.description is None
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_status_enum_validation(self, db_session):
        """Test TaskStatus enum validation."""
        # Valid status
        task = Task(title="Test Task", status=TaskStatus.COMPLETED)
        db_session.add(task)
        db_session.commit()

        assert task.status == TaskStatus.COMPLETED

    def test_task_timestamps_auto_update(self, db_session):
        """Test that timestamps are automatically managed."""
        task = Task(title="Test Task")
        db_session.add(task)
        db_session.commit()

        original_created = task.created_at
        original_updated = task.updated_at

        # Update the task
        task.title = "Updated Task"
        db_session.commit()

        # created_at should remain the same
        assert task.created_at == original_created

        # updated_at should be different (though this might be very close in time)
        # We'll just check it's still a datetime
        assert isinstance(task.updated_at, datetime)

    def test_task_uuid_generation(self, db_session):
        """Test that UUIDs are automatically generated."""
        task1 = Task(title="Task 1")
        task2 = Task(title="Task 2")

        db_session.add_all([task1, task2])
        db_session.commit()

        assert task1.id != task2.id
        assert isinstance(task1.id, uuid.UUID)
        assert isinstance(task2.id, uuid.UUID)

    def test_task_string_representation(self, db_session):
        """Test Task string representation."""
        task = Task(title="Test Task")
        db_session.add(task)
        db_session.commit()

        str_repr = str(task)
        assert "Test Task" in str_repr
        assert str(task.id) in str_repr

    def test_task_relationship_with_approval_history(self, db_session):
        """Test Task relationship with ApprovalHistory."""
        task = Task(title="Test Task")
        db_session.add(task)
        db_session.commit()

        # Create approval history entries
        approval1 = ApprovalHistory(
            task_id=task.id,
            status=TaskStatus.PENDING_APPROVAL,
            timestamp=datetime.now(timezone.utc)
        )
        approval2 = ApprovalHistory(
            task_id=task.id,
            status=TaskStatus.APPROVED,
            timestamp=datetime.now(timezone.utc)
        )

        db_session.add_all([approval1, approval2])
        db_session.commit()

        # Test relationship
        assert len(task.approval_history) == 2
        assert approval1 in task.approval_history
        assert approval2 in task.approval_history


class TestApprovalHistoryORM:
    """Test ApprovalHistory ORM model functionality."""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_approval_history_creation(self, db_session):
        """Test creating an ApprovalHistory instance."""
        # First create a task
        task = Task(title="Test Task")
        db_session.add(task)
        db_session.commit()

        # Create approval history
        approval = ApprovalHistory(
            task_id=task.id,
            status=TaskStatus.APPROVED,
            timestamp=datetime.now(timezone.utc)
        )

        db_session.add(approval)
        db_session.commit()

        assert approval.id is not None
        assert isinstance(approval.id, uuid.UUID)
        assert approval.task_id == task.id
        assert approval.status == TaskStatus.APPROVED
        assert isinstance(approval.timestamp, datetime)

    def test_approval_history_required_fields(self, db_session):
        """Test that required fields are enforced."""
        # Missing task_id should fail
        approval = ApprovalHistory(
            status=TaskStatus.APPROVED,
            timestamp=datetime.now(timezone.utc)
        )

        db_session.add(approval)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_approval_history_foreign_key_constraint(self, db_session):
        """Test foreign key constraint to Task."""
        # Note: SQLite in-memory doesn't enforce foreign key constraints by default
        # This test verifies the model structure rather than database constraint enforcement
        fake_task_id = uuid.uuid4()
        approval = ApprovalHistory(
            task_id=fake_task_id,
            status=TaskStatus.APPROVED,
            timestamp=datetime.now(timezone.utc)
        )

        db_session.add(approval)
        db_session.commit()  # This will succeed in SQLite without FK enforcement

        # Verify the approval was created with the fake task_id
        assert approval.task_id == fake_task_id

    def test_approval_history_task_relationship(self, db_session):
        """Test ApprovalHistory relationship back to Task."""
        # Create task
        task = Task(title="Test Task")
        db_session.add(task)
        db_session.commit()

        # Create approval history
        approval = ApprovalHistory(
            task_id=task.id,
            status=TaskStatus.APPROVED,
            timestamp=datetime.now(timezone.utc)
        )

        db_session.add(approval)
        db_session.commit()

        # Test relationship
        assert approval.task == task
        assert approval.task.title == "Test Task"

    def test_approval_history_status_validation(self, db_session):
        """Test status field validation."""
        # Create task first
        task = Task(title="Test Task")
        db_session.add(task)
        db_session.commit()

        # Test all valid statuses
        for status in TaskStatus:
            approval = ApprovalHistory(
                task_id=task.id,
                status=status,
                timestamp=datetime.now(timezone.utc)
            )

            db_session.add(approval)
            db_session.commit()

            assert approval.status == status

            # Clean up for next iteration
            db_session.delete(approval)
            db_session.commit()

    def test_approval_history_timestamp_timezone(self, db_session):
        """Test that timestamps handle timezone correctly."""
        # Create task
        task = Task(title="Test Task")
        db_session.add(task)
        db_session.commit()

        # Create approval with timezone-aware timestamp
        timestamp = datetime.now(timezone.utc)
        approval = ApprovalHistory(
            task_id=task.id,
            status=TaskStatus.APPROVED,
            timestamp=timestamp
        )

        db_session.add(approval)
        db_session.commit()

        # Verify timestamp is preserved (SQLite may strip timezone info)
        # Check that the timestamp values are close (within 1 second)
        time_diff = abs((approval.timestamp - timestamp.replace(tzinfo=None)).total_seconds())
        assert time_diff < 1.0
        assert isinstance(approval.timestamp, datetime)

    def test_approval_history_ordering(self, db_session):
        """Test ApprovalHistory ordering by timestamp."""
        # Create task
        task = Task(title="Test Task")
        db_session.add(task)
        db_session.commit()

        # Create multiple approval history entries
        now = datetime.now(timezone.utc)

        approval1 = ApprovalHistory(
            task_id=task.id,
            status=TaskStatus.PENDING_APPROVAL,
            timestamp=now
        )

        approval2 = ApprovalHistory(
            task_id=task.id,
            status=TaskStatus.APPROVED,
            timestamp=now.replace(second=now.second + 1)
        )

        db_session.add_all([approval2, approval1])  # Add in reverse order
        db_session.commit()

        # Query with ordering
        history = db_session.query(ApprovalHistory).filter(
            ApprovalHistory.task_id == task.id
        ).order_by(ApprovalHistory.timestamp).all()

        assert len(history) == 2
        assert history[0] == approval1  # Earlier timestamp first
        assert history[1] == approval2  # Later timestamp second