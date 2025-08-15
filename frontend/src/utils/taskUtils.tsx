import React from 'react';
import { TaskStatus } from '../types/tasks';

// Lightweight local icons to avoid external dependency issues in tests
export const CheckCircleIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
    <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm-1.293 13.293a1 1 0 0 1-1.414 0l-2.293-2.293a1 1 0 1 1 1.414-1.414l1.586 1.586 4.586-4.586a1 1 0 0 1 1.414 1.414l-5.293 5.293z" />
  </svg>
);
export const XCircleIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
    <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm4.24 13.17l-1.41 1.41L12 13.41l-2.83 2.83-1.41-1.41L10.59 12 7.76 9.17l1.41-1.41L12 10.59l2.83-2.83 1.41 1.41L13.41 12l2.83 2.83z" />
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
