import unittest
from unittest.mock import Mock, patch
import pytest
from backend.functions.approval.approval_handler import ApprovalHandler, Task, TaskStatus

class TestApprovalHandler(unittest.TestCase):

    def setUp(self):
        """Set up a new task for each test."""
        self.task = Task(id='task123', status=TaskStatus.PENDING_APPROVAL)

    def test_initial_state(self):
        """Test that a new task has the correct initial state."""
        self.assertEqual(self.task.status, TaskStatus.PENDING_APPROVAL)

    def test_approve_task(self):
        """Test the state transition when a task is approved."""
        handler = ApprovalHandler(self.task)
        handler.approve()
        self.assertEqual(self.task.status, TaskStatus.APPROVED)

    def test_reject_task(self):
        """Test the state transition when a task is rejected."""
        handler = ApprovalHandler(self.task)
        handler.reject()
        self.assertEqual(self.task.status, TaskStatus.REJECTED)

    def test_invalid_transition_from_approved(self):
        """Test that an approved task cannot be rejected."""
        self.task.status = TaskStatus.APPROVED
        handler = ApprovalHandler(self.task)
        with self.assertRaises(ValueError):
            handler.reject()

    def test_invalid_transition_from_rejected(self):
        """Test that a rejected task cannot be approved."""
        self.task.status = TaskStatus.REJECTED
        handler = ApprovalHandler(self.task)
        with self.assertRaises(ValueError):
            handler.approve()

    @patch('logging.Logger.info')
    def test_approve_sends_notification(self, mock_info):
        """Test that approving a task sends a notification."""
        handler = ApprovalHandler(self.task)
        handler.approve()
        mock_info.assert_any_call(f"Notification: Task {self.task.id} has been {TaskStatus.APPROVED.value}.")

    @patch('logging.Logger.info')
    def test_reject_sends_notification(self, mock_info):
        """Test that rejecting a task sends a notification."""
        handler = ApprovalHandler(self.task)
        handler.reject()
        mock_info.assert_any_call(f"Notification: Task {self.task.id} has been {TaskStatus.REJECTED.value}.")

    @patch('logging.Logger.info')
    def test_approve_logs_history(self, mock_info):
        """Test that approving a task logs the action to history."""
        handler = ApprovalHandler(self.task)
        handler.approve()
        mock_info.assert_any_call(f"History: Task {self.task.id} was {TaskStatus.APPROVED.value}.")

    @patch('logging.Logger.info')
    def test_reject_logs_history(self, mock_info):
        """Test that rejecting a task logs the action to history."""
        handler = ApprovalHandler(self.task)
        handler.reject()
        mock_info.assert_any_call(f"History: Task {self.task.id} was {TaskStatus.REJECTED.value}.")

if __name__ == '__main__':
    unittest.main()
