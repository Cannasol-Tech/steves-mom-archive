import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import TaskDetailPage from './TaskDetailPage';
import { Task, TaskStatus } from '../types/tasks';

global.fetch = jest.fn();

const mockTask: Task = {
  id: 'a1b2c3d4-e5f6-7890-1234-567890abcdef',
  title: 'Test Task',
  description: 'This is a test description.',
  status: TaskStatus.APPROVED,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  approval_history: [
    {
      id: 'h1',
      status: TaskStatus.PENDING_APPROVAL,
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: 'h2',
      status: TaskStatus.APPROVED,
      timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    },
  ],
};

// Suppress noisy React Router v6 deprecation/future flag warnings for this suite only
let consoleWarnSpy: jest.SpyInstance;
beforeAll(() => {
  consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation((msg?: any, ...args: any[]) => {
    const text = String(msg || '');
    if (
      text.includes('is deprecated') ||
      text.includes('Future flags are deprecated') ||
      text.includes('Relative route resolution within Splat routes')
    ) {
      return;
    }
    // Forward other warnings
    // eslint-disable-next-line no-console
    (console.warn as any).orig ? (console.warn as any).orig(text, ...args) : void 0;
  });
});

afterAll(() => {
  consoleWarnSpy.mockRestore();
});

describe('TaskDetailPage', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  it('should render task details and approval history correctly', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockTask,
    });

    render(
      <MemoryRouter initialEntries={[`/tasks/${mockTask.id}`]}>
        <Routes>
          <Route path="/tasks/:taskId" element={<TaskDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(mockTask.title)).toBeInTheDocument();
    });

    expect(screen.getByText(mockTask.description!)).toBeInTheDocument();
    expect(screen.getByText(mockTask.status.replace(/_/g, ' '))).toBeInTheDocument();
    expect(screen.getByText('Approval History')).toBeInTheDocument();
    expect(screen.getByText(/Status changed to PENDING APPROVAL/i)).toBeInTheDocument();
    expect(screen.getByText(/Status changed to APPROVED/i)).toBeInTheDocument();
  });

  it('should display a loading state initially', () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => new Promise(() => {}), // Never resolves
    });

    render(
        <MemoryRouter initialEntries={[`/tasks/${mockTask.id}`]}>
            <Routes>
                <Route path="/tasks/:taskId" element={<TaskDetailPage />} />
            </Routes>
        </MemoryRouter>
    );

    expect(screen.getByText(/Loading task.../i)).toBeInTheDocument();
  });

  it('should display an error message if the task is not found', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    render(
        <MemoryRouter initialEntries={[`/tasks/not-a-real-id`]}>
            <Routes>
                <Route path="/tasks/:taskId" element={<TaskDetailPage />} />
            </Routes>
        </MemoryRouter>
    );

    await waitFor(() => {
        expect(screen.getByText(/Task not found/i)).toBeInTheDocument();
    });
  });
});
