import React from 'react';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import ChatPage from '../ChatPage';
import * as chatStreamMod from '../../services/chatStream';

// Spy-based mock for startStream; store last controls for assertions
let lastControls: { emitChunk: (t: string) => void; finish: () => void; fail: (e: Error) => void } | undefined;

beforeEach(() => {
  lastControls = undefined;
  jest.spyOn(chatStreamMod, 'startStream').mockImplementation(({ onChunk, onDone, onError }: any) => {
    let cancelled = false;
    const controls = {
      emitChunk: (t: string) => { if (!cancelled) onChunk(t); },
      finish: () => { if (!cancelled) onDone(); },
      fail: (e: Error) => { if (!cancelled) onError(e); },
    };
    lastControls = controls;
    return {
      cancel: () => { cancelled = true; },
    } as any;
  });
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe('ChatPage streaming integration', () => {
  test('progressively renders streamed content and supports Cancel/Retry controls', async () => {
    render(<ChatPage />);

    // Send a user message
    const textarea = screen.getByPlaceholderText(/Ask anything/i);
    fireEvent.change(textarea, { target: { value: 'Hello there' } });
    const sendBtn = screen.getByRole('button', { name: /Send/i });
    expect(sendBtn).toBeEnabled();

    fireEvent.click(sendBtn);

    // While streaming, we expect a streaming hint and Cancel enabled
    // Stream UI will be provided by StreamRenderer once integrated
    const streamingHint = await screen.findByText(/Streaming…/);
    expect(streamingHint).toBeInTheDocument();

    // Emit chunks and verify progressive content appears
    const controls = lastControls;
    expect(controls).toBeDefined();

    await act(async () => {
      controls!.emitChunk('Hello');
    });
    await waitFor(() => expect(screen.getByTestId('stream-content')).toHaveTextContent('Hello'));

    await act(async () => {
      controls!.emitChunk(', world');
    });
    await waitFor(() => expect(screen.getByTestId('stream-content')).toHaveTextContent('Hello, world'));

    // Cancel should stop further updates
    const cancelBtn = screen.getByRole('button', { name: /Cancel/i });
    expect(cancelBtn).toBeEnabled();

    fireEvent.click(cancelBtn);
    // try to emit more after cancel; UI should not change
    await act(async () => {
      controls!.emitChunk('!');
    });
    await waitFor(() => expect(screen.getByTestId('stream-content')).toHaveTextContent('Hello, world'));

    // Retry should start a new stream (assert streaming hint appears again)
    const retryBtn = screen.getByRole('button', { name: /Retry/i });
    // handleRetry uses setTimeout to call handleSendMessage; switch to fake timers BEFORE clicking
    jest.useFakeTimers();
    fireEvent.click(retryBtn);
    // advance timers to trigger handleSendMessage
    await act(async () => {
      jest.runOnlyPendingTimers();
    });
    jest.useRealTimers();
    const prevControls = controls;
    // Wait for controls to be replaced by the new stream
    await waitFor(() => expect(lastControls && lastControls !== prevControls).toBeTruthy());
    await act(async () => {
      lastControls!.emitChunk(' Again');
    });
    await waitFor(() => expect(screen.getByTestId('stream-content')).toHaveTextContent('Again'));
  });
});
