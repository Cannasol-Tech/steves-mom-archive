import unittest
from unittest.mock import Mock, patch
import pytest
from backend.functions.approval.approval_handler import ApprovalHandler, Task

class TestApprovalHandler(unittest.TestCase):

    def setUp(self):
        """Set up a new task for each test."""
        self.task = Task(id='task123', status='pending_approval')

    def test_initial_state(self):
        """Test that a new task has the correct initial state."""
        self.assertEqual(self.task.status, 'pending_approval')

    def test_approve_task(self):
        """Test the state transition when a task is approved."""
        handler = ApprovalHandler(self.task)
        handler.approve()
        self.assertEqual(self.task.status, 'approved')

    def test_reject_task(self):
        """Test the state transition when a task is rejected."""
        handler = ApprovalHandler(self.task)
        handler.reject()
        self.assertEqual(self.task.status, 'rejected')

    def test_invalid_transition_from_approved(self):
        """Test that an approved task cannot be rejected."""
        self.task.status = 'approved'
        handler = ApprovalHandler(self.task)
        with self.assertRaises(ValueError):
            handler.reject()

    def test_invalid_transition_from_rejected(self):
        """Test that a rejected task cannot be approved."""
        self.task.status = 'rejected'
        handler = ApprovalHandler(self.task)
        with self.assertRaises(ValueError):
            handler.approve()

    @patch('backend.functions.approval.approval_handler.ApprovalHandler._send_notification')
    def test_approve_sends_notification(self, mock_send_notification):
        """Test that approving a task sends a notification."""
        handler = ApprovalHandler(self.task)
        handler.approve()
        mock_send_notification.assert_called_once_with('approved')

    @patch('backend.functions.approval.approval_handler.ApprovalHandler._send_notification')
    def test_reject_sends_notification(self, mock_send_notification):
        """Test that rejecting a task sends a notification."""
        handler = ApprovalHandler(self.task)
        handler.reject()
        mock_send_notification.assert_called_once_with('rejected')

    @patch('backend.functions.approval.approval_handler.ApprovalHandler._log_history')
    def test_approve_logs_history(self, mock_log_history):
        """Test that approving a task logs the action to history."""
        handler = ApprovalHandler(self.task)
        handler.approve()
        mock_log_history.assert_called_once_with('approved')

    @patch('backend.functions.approval.approval_handler.ApprovalHandler._log_history')
    def test_reject_logs_history(self, mock_log_history):
        """Test that rejecting a task logs the action to history."""
        handler = ApprovalHandler(self.task)
        handler.reject()
        mock_log_history.assert_called_once_with('rejected')

if __name__ == '__main__':
    unittest.main()
