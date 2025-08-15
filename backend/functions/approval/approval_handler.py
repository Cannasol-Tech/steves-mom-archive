class Task:
    def __init__(self, id, status):
        self.id = id
        self.status = status

class ApprovalHandler:
    def __init__(self, task):
        if not hasattr(task, 'status'):
            raise TypeError("Task object must have a 'status' attribute.")
        self.task = task
        self.valid_transitions = {
            'pending_approval': ['approved', 'rejected'],
        }

    def _can_transition_to(self, new_status):
        current_status = self.task.status
        allowed_statuses = self.valid_transitions.get(current_status, [])
        return new_status in allowed_statuses

    def approve(self):
        if not self._can_transition_to('approved'):
            raise ValueError(f"Cannot approve task in '{self.task.status}' state.")
        self.task.status = 'approved'
        self._send_notification('approved')
        self._log_history('approved')

    def reject(self):
        if not self._can_transition_to('rejected'):
            raise ValueError(f"Cannot reject task in '{self.task.status}' state.")
        self.task.status = 'rejected'
        self._send_notification('rejected')
        self._log_history('rejected')

    def _send_notification(self, status):
        """Placeholder for sending a notification."""
        print(f"Notification: Task {self.task.id} has been {status}.")

    def _log_history(self, action):
        """Placeholder for logging the action to an audit trail."""
        print(f"History: Task {self.task.id} was {action}.")
