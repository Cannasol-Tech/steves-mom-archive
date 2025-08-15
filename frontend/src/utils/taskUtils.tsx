import { TaskStatus } from '../types/tasks';
import { CheckCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/24/solid';

export const getStatusIcon = (status: TaskStatus) => {
  switch (status) {
    case TaskStatus.APPROVED:
      return CheckCircleIcon;
    case TaskStatus.REJECTED:
      return XCircleIcon;
    case TaskStatus.PENDING_APPROVAL:
      return ClockIcon;
    default:
      return null;
  }
};

export const getStatusColor = (status: TaskStatus) => {
  switch (status) {
    case TaskStatus.APPROVED:
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
    case TaskStatus.REJECTED:
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
    case TaskStatus.PENDING_APPROVAL:
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  }
};
