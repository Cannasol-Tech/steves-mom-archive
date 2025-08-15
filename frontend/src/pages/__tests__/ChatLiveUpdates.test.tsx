import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import ChatPage from '../ChatPage';

// We will TDD a socket client living at src/services/socketClient.ts
// The mock below simulates a connection and lets tests emit events

type Handlers = {
  onMessage: (text: string) => void;
  onError: (err: Error) => void;
  onClose: () => void;
};

let lastHandlers: Handlers | null = null;
let isConnected = false;

jest.mock('../../services/socketClient', () => ({
  connectLiveUpdates: (handlers: Handlers) => {
    lastHandlers = handlers;
    isConnected = true;
    return {
      disconnect: () => {
        isConnected = false;
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
}));

// Access our test helpers
const socketMock = require('../../services/socketClient').__testing__ as {
  getConnected: () => boolean;
  emitMessage: (t: string) => void;
  emitError: (e: Error) => void;
  emitClose: () => void;
  reset: () => void;
};

beforeEach(() => {
  socketMock.reset();
});

afterEach(() => {
  jest.restoreAllMocks();
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
    });

    await waitFor(() =>
      expect(
        screen.getByRole('alert', { name: '' }) || screen.getByText(/Live updates error:/i)
      ).toBeTruthy()
    );
  });
});
