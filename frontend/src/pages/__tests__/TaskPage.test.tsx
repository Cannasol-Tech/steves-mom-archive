import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';
import TaskPage from '../TaskPage';

const mockTasks = [
  {
    id: 1,
    title: 'First task',
    description: 'Do the first thing',
    status: 'in_progress',
    updated_at: new Date('2024-01-01T12:00:00Z').toISOString(),
  },
  {
    id: 2,
    title: 'Second task',
    description: '',
    status: 'completed',
    updated_at: new Date('2024-01-02T12:00:00Z').toISOString(),
  },
];

describe('TaskPage', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  test('shows loading then renders tasks', async () => {
    // @ts-expect-error global fetch mock
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => mockTasks });

    render(
      <MemoryRouter>
        <TaskPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/loading tasks/i)).toBeInTheDocument();

    expect(await screen.findByText(/task list/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /first task/i })).toHaveAttribute('href', '/tasks/1');
    expect(screen.getByRole('link', { name: /second task/i })).toHaveAttribute('href', '/tasks/2');
  });

  test('shows error state when fetch fails', async () => {
    // @ts-expect-error global fetch mock
    global.fetch = jest.fn().mockResolvedValue({ ok: false });

    render(
      <MemoryRouter>
        <TaskPage />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText(/error:/i)).toBeInTheDocument());
  });
});
