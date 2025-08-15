import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MessageList from '../MessageList';
import StreamRenderer from '../StreamRenderer';
import ChatPage from '../../../pages/ChatPage';
import * as chatStreamMod from '../../../services/chatStream';

describe('Task 3.4 - Error/loading states and toasts', () => {
  test('[loading-state-visible] MessageList shows Thinking… when isLoading=true', () => {
    render(<MessageList messages={[]} isLoading={true} />);
    expect(screen.getAllByText(/Thinking…/i).length).toBeGreaterThan(0);
  });

  test('[cancel-disabled-when-idle] Cancel disabled when not streaming; Retry enabled', () => {
    render(
      <StreamRenderer
        content=""
        isStreaming={false}
        onRetry={() => {}}
        onCancel={() => {}}
      />
    );
    const retryBtn = screen.getByRole('button', { name: /Retry/i });
    const cancelBtn = screen.getByRole('button', { name: /Cancel/i });
    expect(retryBtn).toBeEnabled();
    expect(cancelBtn).toBeDisabled();
  });

  test('[toast-on-error] ChatPage shows a toast when stream errors', async () => {
    jest.spyOn(chatStreamMod, 'startStream').mockImplementation(({ onError }: any) => {
      // Immediately error to trigger toast
      setTimeout(() => onError(new Error('boom')), 0);
      return { cancel: () => {} } as any;
    });

    render(<ChatPage />);

    const textarea = screen.getByPlaceholderText(/Ask anything/i);
    fireEvent.change(textarea, { target: { value: 'Trigger error' } });
    const sendBtn = screen.getByRole('button', { name: /Send/i });
    fireEvent.click(sendBtn);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/Network error: boom/i);
  });

  test('[no-stale-streaming-ui] No StreamRenderer visible after cancel with no content', async () => {
    let controls: { emitChunk: (t: string) => void; finish: () => void; fail: (e: Error) => void } | undefined;
    jest.spyOn(chatStreamMod, 'startStream').mockImplementation(({ onChunk, onDone, onError }: any) => {
      let cancelled = false;
      controls = {
        emitChunk: (t: string) => { if (!cancelled) onChunk(t); },
        finish: () => { if (!cancelled) onDone(); },
        fail: (e: Error) => { if (!cancelled) onError(e); },
      };
      return { cancel: () => { cancelled = true; } } as any;
    });

    render(<ChatPage />);

    const textarea = screen.getByPlaceholderText(/Ask anything/i);
    fireEvent.change(textarea, { target: { value: 'Hi' } });
    const sendBtn = screen.getByRole('button', { name: /Send/i });
    fireEvent.click(sendBtn);

    // Immediately cancel without any chunks
    const cancelBtn = await screen.findByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelBtn);

    await waitFor(() => {
      expect(screen.queryByTestId('stream-content')).toBeNull();
    });

    // avoid unused var warning
    void controls;
  });

  test('[streaming-hint-visible] StreamRenderer shows streaming hint when isStreaming=true', () => {
    render(
      <StreamRenderer
        content={''}
        isStreaming={true}
        onRetry={() => {}}
        onCancel={() => {}}
      />
    );
    expect(screen.getByText(/Streaming…/)).toBeInTheDocument();
  });
});
