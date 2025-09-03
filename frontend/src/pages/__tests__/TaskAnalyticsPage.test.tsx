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

  // Suppress React Router future warnings in this suite only to avoid noisy logs/flaky failures
  const originalWarn = console.warn;
  beforeAll(() => {
    jest.spyOn(console, 'warn').mockImplementation((...args: unknown[]) => {
      const msg = (args[0] as unknown as string) ?? '';
      if (typeof msg === 'string' && msg.startsWith('⚠️ React Router Future Flag Warning')) {
        return; // ignore these known deprecation warnings in tests
      }
      // fall back to original warn for other messages
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (originalWarn as any)(...args);
    });
  });

  afterAll(() => {
    (console.warn as jest.Mock).mockRestore();
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
    expect(await screen.findByText(/75%/i)).toBeInTheDocument(); // Accepted
    expect(await screen.findByText(/15%/i)).toBeInTheDocument(); // Rejected
    expect(await screen.findByText(/10%/i)).toBeInTheDocument(); // Modified
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
