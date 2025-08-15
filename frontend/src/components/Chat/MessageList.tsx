import React from 'react';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  reasoning?: string; // optional reasoning attached to assistant replies
}

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  reasoningText?: string;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isLoading, reasoningText }) => {
  return (
    <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6">
      <div className="mx-auto max-w-3xl space-y-4">
        {messages.map((m) => {
          const fromUser = m.role === 'user';
          return (
            <div key={m.id} className={`flex items-start ${fromUser ? 'justify-end' : 'justify-start'}`}>
              {!fromUser && (
                <div className="mr-3 w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 text-white flex items-center justify-center text-xs font-semibold flex-shrink-0">AI</div>
              )}
              <div
                className={`rounded-2xl px-4 py-3 shadow-sm whitespace-pre-wrap ${
                  fromUser
                    ? 'bg-blue-50 border border-blue-100 text-gray-900 max-w-[80%]'
                    : 'bg-white border border-emerald-100 text-gray-900 max-w-[80%]'
                }`}
              >
                <div className="text-xs text-gray-500 mb-1">
                  {fromUser ? 'You' : "Steve's Mom AI"} • {m.timestamp.toLocaleTimeString()}
                </div>
                {m.content}
                {!fromUser && m.reasoning && (
                  <div className="mt-3">
                    <details className="group">
                      <summary className="cursor-pointer select-none text-xs text-emerald-700 hover:text-emerald-800 flex items-center">
                        <span className="mr-1 inline-block h-2 w-2 rounded-full bg-emerald-400"></span>
                        Show reasoning
                        <span className="ml-1 text-gray-400 group-open:rotate-180 transition-transform">▾</span>
                      </summary>
                      <div className="mt-2 bg-emerald-50/60 border border-emerald-200 rounded-md p-3 text-sm text-emerald-900 whitespace-pre-wrap">
                        {m.reasoning}
                      </div>
                    </details>
                  </div>
                )}
              </div>
              {fromUser && (
                <div className="ml-3 w-9 h-9 rounded-full bg-gray-400 text-white flex items-center justify-center text-xs font-semibold flex-shrink-0">U</div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-start justify-start">
            <div className="mr-3 w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 text-white flex items-center justify-center text-xs font-semibold flex-shrink-0">AI</div>
            <div className="rounded-2xl px-4 py-3 shadow-sm bg-white border border-emerald-100 text-gray-900 max-w-[80%] w-full">
              <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                <img
                  src="/cannasol-logo.png"
                  alt="Cannasol"
                  className="h-4 w-4 object-contain hidden sm:block"
                  onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
                />
                <span>Steve's Mom AI • Thinking…</span>
              </div>
              <div className="flex items-center space-x-2 text-gray-500">
                <span className="inline-block h-2 w-2 rounded-full bg-blue-400 animate-pulse"></span>
                <span>Thinking…</span>
              </div>
              {reasoningText && (
                <div className="mt-3">
                  <details className="group">
                    <summary className="cursor-pointer select-none text-xs text-emerald-700 hover:text-emerald-800 flex items-center">
                      <span className="mr-1 inline-block h-2 w-2 rounded-full bg-emerald-400"></span>
                      Show live reasoning
                      <span className="ml-1 text-gray-400 group-open:rotate-180 transition-transform">▾</span>
                    </summary>
                    <div className="mt-2 bg-emerald-50/60 border border-emerald-200 rounded-md p-3 text-sm text-emerald-900 whitespace-pre-wrap max-h-60 overflow-auto">
                      {reasoningText}
                    </div>
                  </details>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageList;
