export type LiveUpdateHandlers = {
  onMessage: (text: string) => void;
  onError: (err: Error) => void;
  onClose: () => void;
};

export type LiveUpdateConnection = {
  disconnect: () => void;
};

// Minimal stub for MVP; can be swapped for real WebSocket/EventSource later
export function connectLiveUpdates(handlers: LiveUpdateHandlers): LiveUpdateConnection {
  // Placeholder: no real network connection yet
  let active = true;
  return {
    disconnect: () => {
      active = false;
      if (handlers && typeof handlers.onClose === 'function') {
        try { handlers.onClose(); } catch {}
      }
    },
  };
}

// Testing helpers (used by jest mock in tests)
export const __testing__ = {
  // no-op in real implementation; jest will mock this module
};
