import React, { useEffect, useState } from 'react';
import { ShieldCheckIcon, XCircleIcon, PencilIcon } from '@heroicons/react/24/outline';

interface TaskAnalytics {
  totalTasks: number;
  accepted: number;
  rejected: number;
  modified: number;
}

const TaskAnalyticsPage: React.FC = () => {
  const [analytics, setAnalytics] = useState<TaskAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || '';
        const response = await fetch(`${apiBaseUrl}/api/tasks/analytics/`);
        if (!response.ok) {
          throw new Error('Failed to fetch task analytics');
        }
        const data = await response.json();
        // Assuming the API returns tasks in a format compatible with the Message type for now
        setAnalytics(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (isLoading) {
    return <div className="p-4">Loading analytics...</div>;
  }

  if (error || !analytics) {
    return <div className="p-4 text-red-500">Error: {error || 'Analytics data is unavailable.'}</div>;
  }

    const acceptedPercentage = analytics.totalTasks > 0 ? ((analytics.accepted / analytics.totalTasks) * 100).toFixed(0) : 0;
  const rejectedPercentage = analytics.totalTasks > 0 ? ((analytics.rejected / analytics.totalTasks) * 100).toFixed(0) : 0;
  const modifiedPercentage = analytics.totalTasks > 0 ? ((analytics.modified / analytics.totalTasks) * 100).toFixed(0) : 0;

  const stats = [
    { name: 'Accepted', stat: `${acceptedPercentage}%`, icon: ShieldCheckIcon, color: 'text-green-500' },
    { name: 'Rejected', stat: `${rejectedPercentage}%`, icon: XCircleIcon, color: 'text-red-500' },
    { name: 'Modified', stat: `${modifiedPercentage}%`, icon: PencilIcon, color: 'text-yellow-500' },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <h1 className="text-2xl font-bold mb-4">Task Analytics</h1>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((item) => (
          <div key={item.name} className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <item.icon className={`h-6 w-6 ${item.color}`} aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">{item.name}</dt>
                    <dd className="text-3xl font-semibold text-gray-900 dark:text-white">{item.stat}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
        Total Tasks Processed: {analytics.totalTasks}
      </div>
    </div>
  );
};

export default TaskAnalyticsPage;
