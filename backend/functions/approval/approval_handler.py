import logging

from backend.models.task_models import TaskStatus


class Task:
    def __init__(self, id, status):
        self.id = id
        self.status = status


class ApprovalHandler:
    def __init__(self, task):
        if not hasattr(task, "status"):
            raise TypeError("Task object must have a 'status' attribute.")
        self.task = task
        self.logger = logging.getLogger(__name__)
        self.valid_transitions = {
            TaskStatus.PENDING_APPROVAL: [TaskStatus.APPROVED, TaskStatus.REJECTED],
        }

    def _can_transition_to(self, new_status):
        current_status = TaskStatus(self.task.status)
        return new_status in self.valid_transitions.get(current_status, [])

    def approve(self):
        if not self._can_transition_to(TaskStatus.APPROVED):
            raise ValueError(
                f"Cannot approve task in '{self.task.status.value}' state."
            )
        self.task.status = TaskStatus.APPROVED.value
        self._send_notification(TaskStatus.APPROVED)
        self._log_history(TaskStatus.APPROVED)

    def reject(self):
        if not self._can_transition_to(TaskStatus.REJECTED):
            raise ValueError(f"Cannot reject task in '{self.task.status.value}' state.")
        self.task.status = TaskStatus.REJECTED
        self._send_notification(TaskStatus.REJECTED)
        self._log_history(TaskStatus.REJECTED)

    def _send_notification(self, status: TaskStatus):
        """Sends a notification about the task status change."""
        self.logger.info(f"Notification: Task {self.task.id} has been {status.value}.")

    def _log_history(self, action: TaskStatus):
        """Logs the action to an audit trail."""
        self.logger.info(f"History: Task {self.task.id} was {action.value}.")
