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
      const res = await fetch(chatUrl, {
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

      if (!res.ok) {
        const txt = await res.text().catch(() => '');
        throw new Error(`API ${res.status}: ${txt}`);
      }

      // Parse JSON response from backend
      const data = await res.json();
      
      // Extract message content and reasoning
      const messageContent = data.message?.content || '';
      const reasoningContent = data.reasoning_content || '';
      
      // Only send content if it's not empty or "(no content)"
      if (messageContent && messageContent.trim() !== '(no content)') {
        params.onChunk(messageContent);
      }
      
      params.onDone(reasoningContent);
    } catch (e: any) {
      if (controller.signal.aborted) return; // cancelled, ignore error callback
      params.onError(e instanceof Error ? e : new Error(String(e)));
    }
  })();

  return {
    cancel: () => controller.abort(),
  };
}
