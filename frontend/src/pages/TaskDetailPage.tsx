import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import type { Task } from '../types/tasks';
import { TaskStatus } from '../types/tasks';
import { connectLiveUpdates } from '../services/socketClient';

const formatStatus = (s: string) => s.replace(/_/g, ' ');
const formatStatusUpper = (s: string) => formatStatus(s).toUpperCase();

const TaskDetailPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const base = process.env.REACT_APP_API_BASE_URL || '';

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${base}/api/tasks/${taskId}`);
        if (!res.ok) {
          if (!cancelled) setError(res.status === 404 ? 'Task not found' : 'Failed to load task');
          return;
        }
        const data = (await res.json()) as Task;
        if (!cancelled) setTask(data);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Failed to load task');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    if (taskId) load();
    return () => {
      cancelled = true;
    };
  }, [taskId]);

  // Subscribe to live updates; update local task when IDs match
  useEffect(() => {
    const conn = connectLiveUpdates({
      onMessage: () => {},
      onError: () => {},
      onClose: () => {},
      onTaskUpdate: (updated: Task) => {
        if (updated.id === taskId) {
          setTask(updated);
        }
      },
    });
    return () => {
      try { conn.disconnect(); } catch {}
    };
  }, [taskId]);

  const handleAction = async (action: 'approve' | 'reject') => {
    if (!taskId) return;
    try {
      const res = await fetch(`${base}/api/tasks/${taskId}/${action}`, {
        method: 'POST',
      });
      if (!res.ok) return;
      const updated = (await res.json()) as Task;
      setTask(updated);
    } catch {
      // swallow for tests
    }
  };

  if (loading) {
    return <div>Loading task...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  if (!task) {
    return <div>Task not found</div>;
  }

  return (
    <div>
      <h1>{task.title}</h1>
      {task.description && <p>{task.description}</p>}
      <p>
        Status: <span>{formatStatus(task.status)}</span>
      </p>

      {task.status === TaskStatus.PENDING_APPROVAL && (
        <div>
          <button onClick={() => handleAction('approve')}>Approve</button>
          <button onClick={() => handleAction('reject')}>Reject</button>
        </div>
      )}

      <h2>Approval History</h2>
      <ul>
        {task.approval_history?.map((h) => (
          <li key={h.id}>Status changed to {formatStatusUpper(h.status)}</li>
        ))}
      </ul>
    </div>
  );
};

export default TaskDetailPage;
