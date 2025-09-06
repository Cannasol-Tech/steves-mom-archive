import { startStream } from '../chatStream';

describe('chatStream.startStream', () => {
  const originalEnv = process.env;
  beforeEach(() => {
    jest.resetAllMocks();
    (global as any).fetch = jest.fn();
    process.env = { ...originalEnv } as any;
    delete (process.env as any).REACT_APP_API_BASE;
  });
  afterAll(() => {
    process.env = originalEnv as any;
  });

  async function flushAsync() {
    await Promise.resolve();
    await new Promise((r) => setTimeout(r, 0));
    await Promise.resolve();
  }



  function streamFrom(chunks: string[]) {
    let i = 0;
    return {
      getReader() {
        return {
          read: jest.fn().mockImplementation(async () => {
            if (i < chunks.length) {
              const value = new TextEncoder().encode(chunks[i++]);
              return { done: false, value };
            }
            return { done: true, value: undefined };
          }),
        };
      },
    } as any;
  }

  it('streams chunks and calls onDone', async () => {
    const body = streamFrom(['Hello ', 'world']);
    (global.fetch as jest.Mock).mockResolvedValue({ ok: true, body });

    const chunks: string[] = [];
    const onChunk = jest.fn((t: string) => chunks.push(t));
    const onDone = jest.fn();
    const onError = jest.fn();

    const finished = new Promise<void>((resolve) => {
      onDone.mockImplementation(() => resolve());
      onError.mockImplementation(() => resolve());
    });

    startStream({
      messages: [{ role: 'user', content: 'hi' }],
      onChunk,
      onDone,
      onError,
    });

    await finished;

    expect(onError).not.toHaveBeenCalled();
    expect(onChunk).toHaveBeenCalledTimes(2);
    expect(chunks.join('')).toBe('Hello world');
    expect(onDone).toHaveBeenCalled();
  });

  it('calls onError for non-OK responses', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({ ok: false, status: 500, text: async () => 'boom' });

    const onError = jest.fn();
    const finished = new Promise<void>((resolve) => {
      onError.mockImplementation(() => resolve());
    });

    startStream({ messages: [], onChunk: jest.fn(), onDone: jest.fn(), onError });

    await finished;
    expect(onError).toHaveBeenCalled();
    const err: Error = onError.mock.calls[0][0];
    expect(err.message).toMatch(/500/);
  });

  it('calls onError when response body is empty', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({ ok: true, body: null });

    const onError = jest.fn();
    const finished = new Promise<void>((resolve) => {
      onError.mockImplementation(() => resolve());
    });
    startStream({ messages: [], onChunk: jest.fn(), onDone: jest.fn(), onError });

    await finished;
    expect(onError).toHaveBeenCalled();
    const err: Error = onError.mock.calls[0][0];
    expect(err.message).toMatch(/Response body is empty/);
  });

  it('cancel aborts without calling onError', async () => {
    // A stream that never yields to simulate long-running
    const body = {
      getReader() {
        return { read: jest.fn().mockImplementation(() => new Promise(() => {})) };
      },
    } as any;

    (global.fetch as jest.Mock).mockResolvedValue({ ok: true, body });

    const onError = jest.fn();
    const onDone = jest.fn();

    const handle = startStream({ messages: [], onChunk: jest.fn(), onDone, onError });
    // Immediately cancel; implementation ignores errors when aborted
    handle.cancel();

    // Tick the micro/macro task queue a bit and ensure no callbacks fire
    await flushAsync();
    await flushAsync();
    expect(onError).not.toHaveBeenCalled();
    expect(onDone).not.toHaveBeenCalled();
  });

  it('uses REACT_APP_API_BASE when provided', async () => {
    (process.env as any).REACT_APP_API_BASE = 'http://api.local';
    const body = streamFrom(['x']);
    (global.fetch as jest.Mock).mockResolvedValue({ ok: true, body });

    startStream({ messages: [], onChunk: jest.fn(), onDone: jest.fn(), onError: jest.fn() });

    await flushAsync();

    expect((global.fetch as jest.Mock).mock.calls[0][0]).toBe('http://api.local/api/chat');
  });
});
