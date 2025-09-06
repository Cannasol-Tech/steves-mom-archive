import React from 'react';
import { TaskStatus } from '../types/tasks';
import { Message } from './Chat/MessageList';

interface AgentTasksPanelProps {
  isOpen: boolean;
  onClose: () => void;
  tasks: (Message & { taskId: string; taskStatus: TaskStatus })[];
  onApprove: (taskId: string) => void;
  onReject: (taskId: string) => void;
}

const AgentTasksPanel: React.FC<AgentTasksPanelProps> = ({ isOpen, onClose, tasks, onApprove, onReject }) => {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white dark:bg-gray-800 shadow-lg z-50 p-4 transform transition-transform duration-300 ease-in-out" role="dialog">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Agent Tasks</h2>
        <button onClick={onClose} aria-label="Close panel">&times;</button>
      </div>
            <div className="mt-4 flow-root">
        <ul className="-my-5 divide-y divide-gray-200 dark:divide-gray-700">
          {tasks.length > 0 ? (
            tasks.map(task => (
              <li key={task.taskId} className="py-4">
                <div className="flex items-center space-x-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate dark:text-white">
                      {task.content}
                    </p>
                    <p className="text-sm text-gray-500 truncate dark:text-gray-400">
                      Status: {task.taskStatus.replace(/_/g, ' ')}
                    </p>
                  </div>
                  {task.taskStatus === TaskStatus.PENDING_APPROVAL && (
                    <div className="flex items-center space-x-2">
                      <button onClick={() => onApprove(task.taskId)} className="px-2 py-1 text-xs font-medium text-white bg-green-600 rounded-md hover:bg-green-700">Approve</button>
                      <button onClick={() => onReject(task.taskId)} className="px-2 py-1 text-xs font-medium text-white bg-red-600 rounded-md hover:bg-red-700">Reject</button>
                    </div>
                  )}
                </div>
              </li>
            ))
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">No tasks for this session yet.</p>
          )}
        </ul>
      </div>
    </div>
  );
};

export default AgentTasksPanel;
