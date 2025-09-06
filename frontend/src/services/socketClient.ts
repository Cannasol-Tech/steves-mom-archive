import { type Task } from '../types/tasks';

export type LiveUpdateHandlers = {
  onMessage: (text: string) => void;
  onTaskUpdate: (task: Task) => void;
  onError: (err: Error) => void;
  onClose: () => void;
};

export type LiveUpdateConnection = {
  disconnect: () => void;
};

export function connectLiveUpdates(handlers: LiveUpdateHandlers): LiveUpdateConnection {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

  // Try proxy first (for development), fallback to direct backend connection
  const proxyUrl = `${wsProtocol}//${window.location.host}/ws`;
  const directUrl = `${wsProtocol}//127.0.0.1:9696/ws`;

  let socket: WebSocket | null = null;
  let retryCount = 0;
  const maxRetries = 3;

  function attemptConnection(url: string): WebSocket {
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.log(`Attempting WebSocket connection to: ${url}`);
    }
    return new WebSocket(url);
  }

  function connect() {
    const url = retryCount === 0 ? proxyUrl : directUrl;
    socket = attemptConnection(url);

    socket.onopen = () => {
      if (process.env.NODE_ENV === 'development') {
        // eslint-disable-next-line no-console
        console.log(`WebSocket connection established to: ${url}`);
      }
      retryCount = 0; // Reset retry count on successful connection
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.id && data.status) { // Simple check for task object
          handlers.onTaskUpdate(data as Task);
        } else {
          handlers.onMessage(event.data);
        }
      } catch (error) {
        handlers.onMessage(event.data);
      }
    };

    socket.onerror = (event) => {
      if (process.env.NODE_ENV === 'development') {
        // eslint-disable-next-line no-console
        console.error(`WebSocket error on ${url}:`, event);
      }

      // Try fallback URL if primary fails
      if (retryCount < maxRetries) {
        retryCount++;
        if (process.env.NODE_ENV === 'development') {
          // eslint-disable-next-line no-console
          console.log(`Retrying WebSocket connection (attempt ${retryCount}/${maxRetries})`);
        }
        setTimeout(() => {
          if (socket) {
            socket.close();
          }
          connect();
        }, 1000 * retryCount); // Exponential backoff
      } else {
        handlers.onError(new Error(`WebSocket connection failed after ${maxRetries} attempts`));
      }
    };

    socket.onclose = (event) => {
      if (process.env.NODE_ENV === 'development') {
        // eslint-disable-next-line no-console
        console.log(`WebSocket connection closed (code: ${event.code}, reason: ${event.reason})`);
      }

      // Only call onClose handler if we're not retrying
      if (retryCount >= maxRetries) {
        handlers.onClose();
      }
      socket = null;
    };
  }

  // Start initial connection
  connect();

  return {
    disconnect: () => {
      retryCount = maxRetries; // Prevent retries when manually disconnecting
      if (socket) {
        socket.close();
      }
    },
  };
}

// Testing helpers (used by jest mock in tests)
export const __testing__ = {
  // no-op in real implementation; jest will mock this module
};
