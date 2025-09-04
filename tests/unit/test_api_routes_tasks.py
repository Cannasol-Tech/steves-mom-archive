"""
Unit tests for backend.api.routes.tasks

Tests FastAPI route handlers for task management including:
- CRUD operations for tasks
- Task filtering and search functionality
- Task approval and rejection workflows
- Analytics endpoint functionality
- Error handling and validation
- Database integration and session management

Author: Cannasol Technologies
Date: 2025-01-04
Version: 1.0.0
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from sqlalchemy.orm import Session

import sys
from pathlib import Path

# Ensure backend package is importable
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.api.routes.tasks import (
    create_task, read_task, read_tasks, update_task, delete_task,
    approve_task, reject_task, get_task_analytics
)
from backend.models.task_models import Task, TaskStatus, TaskUpdate
from backend.models.orm.task import Task as ORMTask
from backend.models.orm.approval_history import ApprovalHistory


class TestCreateTask:
    """Test create_task route handler."""

    def test_create_task_success(self):
        """Test successful task creation."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Create test task
        task_data = Task(title="Test Task", description="Test description")

        # Mock the ORM task that would be created
        mock_orm_task = Mock()
        mock_orm_task.id = task_data.id
        mock_orm_task.title = task_data.title
        mock_orm_task.description = task_data.description
        mock_orm_task.status = task_data.status

        # Configure mock to return the ORM task after refresh
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', mock_orm_task.id)

        with patch('backend.api.routes.tasks.orm.task.Task') as mock_orm_class:
            mock_orm_class.return_value = mock_orm_task

            result = create_task(task_data, mock_db)

            # Verify database operations
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

            # Verify ORM task creation
            mock_orm_class.assert_called_once()

            assert result == mock_orm_task

    def test_create_task_database_error(self):
        """Test task creation with database error."""
        mock_db = Mock(spec=Session)
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=Exception("Database error"))

        task_data = Task(title="Test Task")

        with patch('backend.api.routes.tasks.orm.task.Task'):
            with pytest.raises(Exception, match="Database error"):
                create_task(task_data, mock_db)


class TestReadTask:
    """Test read_task route handler."""

    def test_read_task_success(self):
        """Test successful task retrieval."""
        task_id = uuid.uuid4()
        mock_db = Mock(spec=Session)

        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_task = Mock()
        mock_task.id = task_id
        mock_task.title = "Test Task"

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_task

        with patch('backend.api.routes.tasks.orm.task.Task') as mock_orm_class:
            result = read_task(task_id, mock_db)

            # Verify query operations
            mock_db.query.assert_called_once_with(mock_orm_class)
            mock_query.filter.assert_called_once()
            mock_filter.first.assert_called_once()

            assert result == mock_task

    def test_read_task_not_found(self):
        """Test task retrieval when task doesn't exist."""
        task_id = uuid.uuid4()
        mock_db = Mock(spec=Session)

        # Mock query chain returning None
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        with patch('backend.api.routes.tasks.orm.task.Task'):
            with pytest.raises(HTTPException) as exc_info:
                read_task(task_id, mock_db)

            assert exc_info.value.status_code == 404
            assert "Task not found" in str(exc_info.value.detail)


class TestReadTasks:
    """Test read_tasks route handler with filtering."""

    def test_read_tasks_no_filters(self):
        """Test reading tasks without any filters."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_tasks = [Mock(), Mock(), Mock()]

        mock_db.query.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_tasks

        with patch('backend.api.routes.tasks.orm.task.Task') as mock_orm_class:
            result = read_tasks(db=mock_db)

            # Verify query operations
            mock_db.query.assert_called_once_with(mock_orm_class)
            mock_query.offset.assert_called_once_with(0)
            mock_query.limit.assert_called_once_with(100)
            mock_query.all.assert_called_once()

            assert result == mock_tasks

    def test_read_tasks_with_status_filter(self):
        """Test reading tasks with status filter."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_tasks = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_tasks

        with patch('backend.api.routes.tasks.orm.task.Task') as mock_orm_class:
            result = read_tasks(status=TaskStatus.COMPLETED, db=mock_db)

            # Verify filtering was applied
            mock_query.filter.assert_called_once()
            assert result == mock_tasks

    def test_read_tasks_with_date_filters(self):
        """Test reading tasks with date range filters."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_tasks = [Mock()]

        start_date = datetime.now(timezone.utc)
        end_date = datetime.now(timezone.utc)

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_tasks

        with patch('backend.api.routes.tasks.orm.task.Task') as mock_orm_class:
            result = read_tasks(
                start_date=start_date,
                end_date=end_date,
                db=mock_db
            )

            # Verify date filtering was applied (should be called twice)
            assert mock_query.filter.call_count == 2
            assert result == mock_tasks

    def test_read_tasks_with_search_filter(self):
        """Test reading tasks with search filter."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_tasks = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_tasks

        with patch('backend.api.routes.tasks.orm.task.Task') as mock_orm_class:
            result = read_tasks(search="test query", db=mock_db)

            # Verify search filtering was applied
            mock_query.filter.assert_called_once()
            assert result == mock_tasks

    def test_read_tasks_with_pagination(self):
        """Test reading tasks with custom pagination."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_tasks = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_tasks

        with patch('backend.api.routes.tasks.orm.task.Task') as mock_orm_class:
            result = read_tasks(skip=10, limit=50, db=mock_db)

            # Verify pagination parameters
            mock_query.offset.assert_called_once_with(10)
            mock_query.limit.assert_called_once_with(50)
            assert result == mock_tasks


class TestUpdateTask:
    """Test update_task route handler."""

    @pytest.mark.asyncio
    async def test_update_task_success(self):
        """Test successful task update."""
        task_id = uuid.uuid4()
        mock_db = Mock(spec=Session)

        # Mock existing task
        mock_task = Mock()
        mock_task.id = task_id
        mock_task.title = "Original Title"
        mock_task.description = "Original Description"

        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_task

        # Mock database operations
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Create update data
        update_data = TaskUpdate(title="Updated Title", status=TaskStatus.COMPLETED)

        with patch('backend.api.routes.tasks.orm.task.Task') as mock_orm_class:
            with patch('backend.api.routes.tasks.manager') as mock_manager:
                mock_manager.broadcast = AsyncMock()

                result = await update_task(task_id, update_data, mock_db)

                # Verify task was found and updated
                mock_db.query.assert_called_once_with(mock_orm_class)
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once_with(mock_task)

                # Verify broadcast was called
                mock_manager.broadcast.assert_called_once()

                assert result == mock_task

    @pytest.mark.asyncio
    async def test_update_task_not_found(self):
        """Test updating non-existent task."""
        task_id = uuid.uuid4()
        mock_db = Mock(spec=Session)

        # Mock query returning None
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        update_data = TaskUpdate(title="Updated Title")

        with patch('backend.api.routes.tasks.orm.task.Task'):
            with pytest.raises(HTTPException) as exc_info:
                await update_task(task_id, update_data, mock_db)

            assert exc_info.value.status_code == 404
            assert "Task not found" in str(exc_info.value.detail)


class TestDeleteTask:
    """Test delete_task route handler."""

    def test_delete_task_success(self):
        """Test successful task deletion."""
        task_id = uuid.uuid4()
        mock_db = Mock(spec=Session)

        # Mock existing task
        mock_task = Mock()
        mock_task.id = task_id

        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_task

        # Mock database operations
        mock_db.delete = Mock()
        mock_db.commit = Mock()

        with patch('backend.api.routes.tasks.orm.task.Task') as mock_orm_class:
            result = delete_task(task_id, mock_db)

            # Verify task was found and deleted
            mock_db.query.assert_called_once_with(mock_orm_class)
            mock_db.delete.assert_called_once_with(mock_task)
            mock_db.commit.assert_called_once()

            assert result is None  # Should return None for 204 status

    def test_delete_task_not_found(self):
        """Test deleting non-existent task."""
        task_id = uuid.uuid4()
        mock_db = Mock(spec=Session)

        # Mock query returning None
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        with patch('backend.api.routes.tasks.orm.task.Task'):
            with pytest.raises(HTTPException) as exc_info:
                delete_task(task_id, mock_db)

            assert exc_info.value.status_code == 404
            assert "Task not found" in str(exc_info.value.detail)


class TestApproveTask:
    """Test approve_task route handler."""

    @pytest.mark.asyncio
    async def test_approve_task_success(self):
        """Test successful task approval."""
        task_id = uuid.uuid4()
        mock_db = Mock(spec=Session)

        # Mock existing task
        mock_task = Mock()
        mock_task.id = task_id
        mock_task.status = TaskStatus.PENDING_APPROVAL

        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_task

        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        with patch('backend.api.routes.tasks.orm.task.Task') as mock_orm_class:
            with patch('backend.api.routes.tasks.ApprovalHistory') as mock_approval_class:
                with patch('backend.api.routes.tasks.ApprovalHandler') as mock_handler_class:
                    with patch('backend.api.routes.tasks.manager') as mock_manager:
                        # Mock approval handler
                        mock_handler = Mock()
                        mock_handler.approve = Mock()
                        mock_handler_class.return_value = mock_handler

                        mock_manager.broadcast = AsyncMock()

                        result = await approve_task(task_id, mock_db)

                        # Verify approval history was created
                        mock_approval_class.assert_called_once()
                        mock_db.add.assert_called()

                        # Verify approval handler was used
                        mock_handler_class.assert_called_once_with(mock_task)
                        mock_handler.approve.assert_called_once()

                        # Verify database operations
                        mock_db.commit.assert_called_once()
                        mock_db.refresh.assert_called_once_with(mock_task)

                        # Verify broadcast
                        mock_manager.broadcast.assert_called_once()

                        assert result == mock_task

    @pytest.mark.asyncio
    async def test_approve_task_handler_error(self):
        """Test task approval with handler error."""
        task_id = uuid.uuid4()
        mock_db = Mock(spec=Session)

        # Mock existing task
        mock_task = Mock()
        mock_task.id = task_id

        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_task

        with patch('backend.api.routes.tasks.orm.task.Task'):
            with patch('backend.api.routes.tasks.ApprovalHistory'):
                with patch('backend.api.routes.tasks.ApprovalHandler') as mock_handler_class:
                    # Mock approval handler to raise error
                    mock_handler = Mock()
                    mock_handler.approve = Mock(side_effect=ValueError("Cannot approve"))
                    mock_handler_class.return_value = mock_handler

                    with pytest.raises(HTTPException) as exc_info:
                        await approve_task(task_id, mock_db)

                    assert exc_info.value.status_code == 409
                    assert "Cannot approve" in str(exc_info.value.detail)


class TestGetTaskAnalytics:
    """Test get_task_analytics route handler."""

    def test_get_task_analytics_success(self):
        """Test successful analytics retrieval."""
        mock_db = Mock(spec=Session)

        # Mock query chains for different counts
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        # Mock filter chains
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter

        # Mock count results
        mock_query.count.return_value = 100  # total tasks
        mock_filter.count.side_effect = [25, 15, 10]  # accepted, rejected, modified

        with patch('backend.api.routes.tasks.orm.task.Task') as mock_orm_class:
            result = get_task_analytics(mock_db)

            # Verify multiple queries were made
            assert mock_db.query.call_count == 4  # total + 3 filtered queries

            # Verify result structure
            expected = {
                "totalTasks": 100,
                "accepted": 25,
                "rejected": 15,
                "modified": 10
            }
            assert result == expected