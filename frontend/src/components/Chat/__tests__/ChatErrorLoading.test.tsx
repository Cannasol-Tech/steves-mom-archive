import React from 'react';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import ChatPage from '../../../pages/ChatPage';
import * as chatStreamMod from '../../../services/chatStream';

// Mock toast host mounting side effects are not needed; it renders within ChatInterface

let lastControls:
  | { emitChunk: (t: string) => void; finish: () => void; fail: (e: Error) => void }
  | undefined;

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
    return { cancel: () => { cancelled = true; } } as any;
  });
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe('ChatPage loading and error/toast behavior', () => {
  test('shows Thinking… and disables input/send while streaming; re-enables after done', async () => {
    render(<ChatPage />);

    const textarea = screen.getByPlaceholderText(/Ask anything/i) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'Test loading state' } });
    const sendBtn = screen.getByRole('button', { name: /Send/i });
    expect(sendBtn).toBeEnabled();

    fireEvent.click(sendBtn);

    // Loading indicator visible
    const thinking = await screen.findAllByText(/Thinking…/);
    expect(thinking.length).toBeGreaterThan(0);

    // Input and send disabled during stream
    expect(textarea).toBeDisabled();
    expect(sendBtn).toBeDisabled();

    // Finish stream
    await act(async () => { lastControls!.finish(); });

    // Re-enabled after completion
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Ask anything/i)).not.toBeDisabled();
      expect(screen.getByRole('button', { name: /Send/i })).toBeDisabled(); // empty input resets
    });
  });

  test('shows error toast on stream error and preserves partial streamed text', async () => {
    render(<ChatPage />);

    const textarea = screen.getByPlaceholderText(/Ask anything/i) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'Cause an error' } });
    fireEvent.click(screen.getByRole('button', { name: /Send/i }));

    // Stream some partial content
    await act(async () => { lastControls!.emitChunk('Partial'); });
    await waitFor(() => expect(screen.getByTestId('stream-content')).toHaveTextContent('Partial'));

    // Trigger error
    await act(async () => { lastControls!.fail(new Error('Network down')); });

    // Toast should appear
    const toast = await screen.findByRole('alert');
    expect(toast).toHaveTextContent(/Network down/i);

    // Partial content should be preserved as a message in the transcript
    const partials = await screen.findAllByText(/Partial/);
    expect(partials.length).toBeGreaterThan(0);
  });
});
