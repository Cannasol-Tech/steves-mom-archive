import { MemoryRouter } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';
import TaskAnalyticsPage from '../TaskAnalyticsPage';

const mockAnalytics = {
  totalTasks: 100,
  accepted: 75,
  rejected: 15,
  modified: 10,
};

describe('TaskAnalyticsPage', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

    test('shows loading then renders analytics', async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => mockAnalytics });

    render(
      <MemoryRouter>
        <TaskAnalyticsPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/loading analytics/i)).toBeInTheDocument();

    expect(await screen.findByText(/task analytics/i)).toBeInTheDocument();
    expect(screen.getByText(/75%/i)).toBeInTheDocument(); // Accepted
    expect(screen.getByText(/15%/i)).toBeInTheDocument(); // Rejected
    expect(screen.getByText(/10%/i)).toBeInTheDocument(); // Modified
  });

    test('shows error state when fetch fails', async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: false });

    render(
      <MemoryRouter>
        <TaskAnalyticsPage />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText(/error:/i)).toBeInTheDocument());
  });
});
