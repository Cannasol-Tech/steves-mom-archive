export interface StartStreamParams {
  messages: Array<{ role: 'user' | 'assistant' | 'system'; content: string }>;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  onChunk: (text: string) => void;
  onDone: () => void;
  onError: (err: Error) => void;
}

export interface StreamHandle {
  cancel: () => void;
}

// Basic implementation using fetch streaming (ReadableStream). Tests will mock this module.
export function startStream(params: StartStreamParams): StreamHandle {
  const controller = new AbortController();
  const apiBase = (process as any).env?.REACT_APP_API_BASE as string | undefined;
  const chatUrl = apiBase ? `${apiBase}/api/chat` : '/api/chat';

  (async () => {
    try {
      const res = await fetch(chatUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: params.messages,
          model: params.model,
          temperature: params.temperature ?? 0.2,
          max_tokens: params.max_tokens ?? 512,
          stream: true,
        }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        const txt = await res.text().catch(() => '');
        throw new Error(`API ${res.status}: ${txt}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        // Assuming server sends raw text chunks or "data: ..." lines
        // Split by newlines and parse SSE-like payloads
        const lines = chunk.split(/\r?\n/);
        for (const line of lines) {
          if (!line) continue;
          const s = line.startsWith('data:') ? line.slice(5).trim() : line;
          if (s === '[DONE]') continue;
          params.onChunk(s);
        }
      }
      params.onDone();
    } catch (e: any) {
      if (controller.signal.aborted) return; // cancelled, ignore error callback
      params.onError(e instanceof Error ? e : new Error(String(e)));
    }
  })();

  return {
    cancel: () => controller.abort(),
  };
}
