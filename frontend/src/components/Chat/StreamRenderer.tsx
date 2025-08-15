import React from 'react';

export interface StreamRendererProps {
  content: string;
  isStreaming: boolean;
  onRetry: () => void;
  onCancel: () => void;
}

/**
 * StreamRenderer
 * Renders progressively streamed assistant content with Retry/Cancel controls.
 * - content: current accumulated text to display
 * - isStreaming: when true, show a cancel action and streaming hint
 * - onRetry: callback to retry the last request
 * - onCancel: callback to cancel the current stream
 */
const StreamRenderer: React.FC<StreamRendererProps> = ({ content, isStreaming, onRetry, onCancel }) => {
  return (
    <div className="rounded-2xl px-4 py-3 shadow-sm bg-white border border-emerald-100 text-gray-900 max-w-[80%] w-full">
      <div className="text-xs text-gray-500 mb-2" aria-live="polite">
        Steve's Mom AI {isStreaming ? '• Streaming…' : ''}
      </div>
      <div data-testid="stream-content" className="whitespace-pre-wrap">{content}</div>
      <div className="mt-3 flex gap-2">
        <button
          type="button"
          onClick={onRetry}
          className="text-sm px-2 py-1 rounded-md border border-gray-200 hover:bg-gray-50"
          aria-label="Retry"
        >
          Retry
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={!isStreaming}
          className="text-sm px-2 py-1 rounded-md border border-gray-200 hover:bg-gray-50 disabled:opacity-50"
          aria-label="Cancel"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

export default StreamRenderer;
