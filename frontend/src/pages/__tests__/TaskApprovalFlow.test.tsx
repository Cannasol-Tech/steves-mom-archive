import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import TaskDetailPage from '../TaskDetailPage';
import { Task, TaskStatus } from '../../types/tasks';

jest.mock('../../services/socketClient', () => {
  const handlersRef: any = { current: null };
  return {
    connectLiveUpdates: (handlers: any) => {
      handlersRef.current = handlers;
      return { disconnect: () => {} };
    },
    __handlersRef: handlersRef,
  };
});

const mockTaskPending: Task = {
  id: '11111111-2222-3333-4444-555555555555',
  title: 'Approve invoice 123',
  description: 'Please review and approve the invoice.',
  status: TaskStatus.PENDING_APPROVAL,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  approval_history: [],
};

const mockTaskApproved: Task = {
  ...mockTaskPending,
  status: TaskStatus.APPROVED,
  approval_history: [
    { id: 'h1', status: TaskStatus.APPROVED, timestamp: new Date().toISOString() },
  ],
};

// Ensure fetch is a jest mock for these tests
(global as any).fetch = jest.fn();

function renderAt(taskId: string) {
  return render(
    <MemoryRouter initialEntries={[`/tasks/${taskId}`]}>
      <Routes>
        <Route path="/tasks/:taskId" element={<TaskDetailPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('TaskApprovalFlow (UI integration)', () => {
  beforeEach(() => {
    (global.fetch as unknown as jest.Mock).mockReset();
  });

  it('shows Approve and Reject buttons for pending tasks and calls respective APIs on click', async () => {
    // Initial fetch returns a pending task
    (global.fetch as unknown as jest.Mock).mockResolvedValueOnce({ ok: true, json: async () => mockTaskPending });

    renderAt(mockTaskPending.id);

    // Expect action buttons present
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: mockTaskPending.title })).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();

    // Approve click should POST to approve endpoint
    (global.fetch as unknown as jest.Mock).mockResolvedValueOnce({ ok: true, json: async () => mockTaskApproved });
    fireEvent.click(screen.getByRole('button', { name: /approve/i }));

    await waitFor(() => {
      expect(global.fetch as any).toHaveBeenCalledWith(
        expect.stringMatching(`/api/tasks/${mockTaskPending.id}/approve`),
        expect.objectContaining({ method: 'POST' })
      );
    });

    // UI should reflect approved status (can appear in badge and history)
    await waitFor(() => {
      const approvedEls = screen.getAllByText(/approved/i);
      expect(approvedEls.length).toBeGreaterThan(0);
    });
  });

  it('updates the UI when a live task update is received over WebSocket', async () => {
    const { __handlersRef } = jest.requireMock('../../services/socketClient');

    // Initial fetch returns pending
    (global.fetch as unknown as jest.Mock).mockResolvedValueOnce({ ok: true, json: async () => mockTaskPending });

    renderAt(mockTaskPending.id);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: mockTaskPending.title })).toBeInTheDocument();
    });
    expect(screen.getByText(/pending approval/i)).toBeInTheDocument();

    // Simulate server pushing an update to APPROVED
    const handlers = __handlersRef.current;
    const updated = { ...mockTaskPending, status: TaskStatus.APPROVED } as Task;
    await act(async () => {
      handlers.onTaskUpdate(updated);
    });

    await waitFor(() => {
      expect(screen.getByText(/approved/i)).toBeInTheDocument();
    });
  });
});
