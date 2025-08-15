import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Task } from '../types/tasks';
import { getStatusColor, getStatusIcon } from '../utils/taskUtils';

const TaskDetailPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const [task, setTask] = useState<Task | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTask = async () => {
      try {
        const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || '';
        const response = await fetch(`${apiBaseUrl}/api/tasks/${taskId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch task details');
        }
        const data = await response.json();
        setTask(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    if (taskId) {
      fetchTask();
    }
  }, [taskId]);

  if (isLoading) {
    return <div className="p-4 sm:p-6 lg:p-8">Loading task details...</div>;
  }

  if (error) {
    return <div className="p-4 sm:p-6 lg:p-8 text-red-500">Error: {error}</div>;
  }

  if (!task) {
    return <div className="p-4 sm:p-6 lg:p-8">Task not found.</div>;
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto bg-white dark:bg-gray-800 shadow-lg rounded-lg overflow-hidden">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{task.title}</h1>
            <div className={`px-3 py-1 inline-flex items-center text-sm leading-5 font-semibold rounded-full ${getStatusColor(task.status)}`}>
              {(() => {
                const Icon = getStatusIcon(task.status);
                return Icon ? <Icon className="h-4 w-4 mr-1.5" /> : null;
              })()}
              <span>{task.status.replace(/_/g, ' ')}</span>
            </div>
          </div>
          <p className="text-md text-gray-600 dark:text-gray-400 mb-6">
            {task.description || <span className="italic">No description provided.</span>}
          </p>

          <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">Details</h2>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
              <div className="flex flex-col">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Created At</dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">{new Date(task.created_at).toLocaleString()}</dd>
              </div>
              <div className="flex flex-col">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Last Updated</dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">{new Date(task.updated_at).toLocaleString()}</dd>
              </div>
              <div className="flex flex-col">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Task ID</dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100 font-mono">{task.id}</dd>
              </div>
            </dl>
          </div>

          <div className="border-t border-gray-200 dark:border-gray-700 pt-6 mt-6">
            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">Approval History</h2>
            {task.approval_history && task.approval_history.length > 0 ? (
              <ul className="space-y-4">
                {task.approval_history.map(history => (
                  <li key={history.id} className="flex items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className={`mr-3 flex-shrink-0 flex items-center justify-center h-8 w-8 rounded-full ${getStatusColor(history.status)} text-white`}>
                      {(() => {
                        const Icon = getStatusIcon(history.status);
                        return Icon ? <Icon className="h-5 w-5" /> : null;
                      })()}
                    </div>
                    <div className="flex-grow">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        Status changed to {history.status.replace(/_/g, ' ')}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(history.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 italic">No approval history found.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskDetailPage;
