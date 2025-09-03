import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import ChatPage from '../ChatPage';

// Local type for handler signatures
type Handlers = {
  onMessage: (text: string) => void;
  onError: (err: Error) => void;
  onClose: () => void;
};

// Silence React Router v6 deprecation/future warnings for this suite only
let consoleWarnSpy: jest.SpyInstance;
beforeAll(() => {
  consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation((msg?: any, ...args: any[]) => {
    const text = String(msg || '');
    if (
      text.includes('Future Flag Warning') ||
      text.includes('is deprecated') ||
      text.includes('Future flags are deprecated') ||
      text.includes('Relative route resolution within Splat routes')
    ) {
      return;
    }
    // Let other warnings through
    console.warn = console.warn;
  });
});

afterAll(() => {
  consoleWarnSpy.mockRestore();
});

// IMPORTANT: Keep mock state INSIDE the mock factory (mocks are hoisted)
jest.mock('../../services/socketClient', () => {
  let lastHandlers: Handlers | null = null;
  let isConnected = false;
  return {
    connectLiveUpdates: (handlers: Handlers) => {
      lastHandlers = handlers;
      isConnected = true;
      return {
        disconnect: () => {
          isConnected = false;
          lastHandlers?.onClose();
        },
      } as any;
    },
    __testing__: {
      getConnected: () => isConnected,
      emitMessage: (text: string) => lastHandlers?.onMessage(text),
      emitError: (err: Error) => lastHandlers?.onError(err),
      emitClose: () => lastHandlers?.onClose(),
      reset: () => {
        lastHandlers = null;
        isConnected = false;
      },
    },
  };
});

// Access our test helpers
const socketMock = require('../../services/socketClient').__testing__ as {
  getConnected: () => boolean;
  emitMessage: (t: string) => void;
  emitError: (e: Error) => void;
  emitClose: () => void;
  reset: () => void;
};

beforeEach(() => {
  jest.useFakeTimers();
  socketMock.reset();
});

afterEach(() => {
  jest.restoreAllMocks();
  jest.useRealTimers();
});

describe('ChatPage live updates wiring', () => {
  test('appends incoming live update messages to the chat UI', async () => {
    render(<ChatPage />);

    // connection should be established on mount
    await waitFor(() => expect(socketMock.getConnected()).toBe(true));

    // Emit a live update and expect it to appear in the message list
    const text = 'Stock updated: SKU-123 now has 42 units';
    await act(async () => {
      socketMock.emitMessage(text);
    });

    // MessageList should render the new text somewhere
    await waitFor(() => expect(screen.getByText(text)).toBeInTheDocument());
  });

  test('shows a toast when live updates encounter an error', async () => {
    render(<ChatPage />);
    await waitFor(() => expect(socketMock.getConnected()).toBe(true));

    const error = new Error('socket disconnected');
    await act(async () => {
      socketMock.emitError(error);
      // Advance timers to pass the 50ms toast delay in ChatPage.onError
      jest.advanceTimersByTime(60);
    });

    // Prefer findByText to avoid race conditions
    expect(await screen.findByText(/Live updates error:/i)).toBeInTheDocument();
  });
});
