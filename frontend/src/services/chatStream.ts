export interface StartStreamParams {
  messages: Array<{ role: 'user' | 'assistant' | 'system'; content: string }>;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  onChunk: (text: string) => void;
  onDone: (reasoning?: string) => void;
  onError: (err: Error) => void;
}

export interface StreamHandle {
  cancel: () => void;
}

// Handle non-streaming JSON response from backend
export function startStream(params: StartStreamParams): StreamHandle {
  const controller = new AbortController();
  const apiBase = (process as any).env?.REACT_APP_API_BASE as string | undefined;
  const chatUrl = apiBase ? `${apiBase}/api/chat` : '/api/chat';

  (async () => {
    try {
      const response = await fetch(chatUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: params.messages,
          model: params.model,
          temperature: params.temperature ?? 0.2,
          max_tokens: params.max_tokens ?? 512,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const txt = await response.text().catch(() => '');
        throw new Error(`API ${response.status}: ${txt}`);
      }

      if (!response.body) {
        throw new Error('Response body is empty');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        const chunk = decoder.decode(value, { stream: true });
        params.onChunk(chunk);
      }

      params.onDone();

    } catch (e: any) {
      if (controller.signal.aborted) return; // Cancelled, ignore error callback
      params.onError(e instanceof Error ? e : new Error(String(e)));
    }
  })();

  return {
    cancel: () => controller.abort(),
  };
}
