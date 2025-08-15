import React from 'react';
import { TaskStatus } from '../types/tasks';

// Lightweight local icons to avoid external dependency issues in tests
export const CheckCircleIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
    <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm-1 14l-4-4 1.4-1.4L11 12.2l5.6-5.6L18 8l-7 8z" />
  </svg>
);
export const XCircleIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
    <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm-1.4 6.6L12 10l1.4-1.4L15 10.2 13.6 11.6 15 13l-1.6 1.6L12 13.2l-1.4 1.4L9 13l1.4-1.4L9 10.2l1.6-1.6z" />
  </svg>
);
export const ClockIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
    <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm1 5v5l4 2-1 1.7-5-2.7V7h2z" />
  </svg>
);

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
