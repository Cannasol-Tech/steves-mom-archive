import React, { useEffect, useState } from 'react';
import { Task } from '../types/tasks';

const TaskPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || '';
        const response = await fetch(`${apiBaseUrl}/api/tasks/`);
        if (!response.ok) {
          throw new Error('Failed to fetch tasks');
        }
        const data = await response.json();
        // Assuming the API returns tasks in a format compatible with the Message type for now
        setTasks(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTasks();
  }, []);

  if (isLoading) {
    return <div className="p-4">Loading tasks...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">Error: {error}</div>;
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <h1 className="text-2xl font-bold mb-4">Task List</h1>
      <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg">
        <ul className="divide-y divide-gray-200 dark:divide-gray-700">
          {tasks.map(task => (
            <li key={task.id} className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-indigo-600 dark:text-indigo-400 truncate">{task.title}</p>
                <div className="ml-2 flex-shrink-0 flex">
                  <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full`}>
                    {task.status}
                  </p>
                </div>
              </div>
              <div className="mt-2 sm:flex sm:justify-between">
                <div className="sm:flex">
                  <p className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                    {task.description}
                  </p>
                </div>
                <div className="mt-2 flex items-center text-sm text-gray-500 dark:text-gray-400 sm:mt-0">
                  <p>Updated at: {new Date(task.updated_at).toLocaleString()}</p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default TaskPage;
