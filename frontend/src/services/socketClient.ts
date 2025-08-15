import { type Message } from '../components/Chat/MessageList';

export type LiveUpdateHandlers = {
  onMessage: (text: string) => void;
  onTaskUpdate: (task: Message) => void;
  onError: (err: Error) => void;
  onClose: () => void;
};

export type LiveUpdateConnection = {
  disconnect: () => void;
};

export function connectLiveUpdates(handlers: LiveUpdateHandlers): LiveUpdateConnection {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/ws`;

  let socket: WebSocket | null = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log('WebSocket connection established');
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.id && data.status) { // Simple check for task object
        handlers.onTaskUpdate(data as Message);
      } else {
        handlers.onMessage(event.data);
      }
    } catch (error) {
      handlers.onMessage(event.data);
    }
  };

  socket.onerror = (event) => {
    console.error('WebSocket error:', event);
    handlers.onError(new Error('WebSocket error'));
  };

  socket.onclose = () => {
    console.log('WebSocket connection closed');
    handlers.onClose();
    socket = null;
  };

  return {
    disconnect: () => {
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
