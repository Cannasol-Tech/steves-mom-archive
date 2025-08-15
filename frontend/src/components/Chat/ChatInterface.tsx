import React from 'react';
import MessageList, { Message } from './MessageList';
import ModelSelector from './ModelSelector';
import InputArea from './InputArea';
import StreamRenderer from './StreamRenderer';

interface ChatInterfaceProps {
  messages: Message[];
  isLoading: boolean;
  inputValue: string;
  model: string;
  onModelChange: (v: string) => void;
  onChangeInput: (v: string) => void;
  onSubmit: () => void;
  onKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement>;
  reasoningText?: string;
  // Streaming UI (optional)
  streamingContent?: string;
  streamingActive?: boolean;
  onRetryStream?: () => void;
  onCancelStream?: () => void;
  toastMessage?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  isLoading,
  inputValue,
  model,
  onModelChange,
  onChangeInput,
  onSubmit,
  onKeyDown,
  reasoningText,
  streamingContent,
  streamingActive,
  onRetryStream,
  onCancelStream,
  toastMessage
}) => {
  return (
    <div className="flex flex-col h-full max-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/30 rounded-3xl border border-white/60 shadow-2xl backdrop-blur-xl overflow-hidden">
      {/* Modern Chat Header */}
      <div className="relative bg-gradient-to-r from-blue-600/95 via-purple-600/90 to-emerald-600/95 backdrop-blur-sm">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 via-purple-600/15 to-emerald-600/20 backdrop-blur-sm"></div>
        <div className="relative px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-br from-white/90 to-white/70 rounded-2xl flex items-center justify-center shadow-lg">
                  <img
                    src="/cannasol-logo.png"
                    alt="AI Assistant"
                    className="h-7 w-7 object-contain"
                    onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
                  />
                </div>
                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-400 rounded-full border-2 border-white shadow-sm animate-pulse"></div>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white drop-shadow-sm">Steve's Mom AI</h1>
                <p className="text-white/80 text-sm font-medium">Your intelligent business assistant</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="hidden sm:block">
                <ModelSelector value={model} onChange={onModelChange} />
              </div>
              <div className="flex items-center space-x-2 text-white/70 text-sm">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                <span>Online</span>
              </div>
            </div>
          </div>
          {toastMessage && (
            <div className="mt-4 bg-red-500/90 backdrop-blur-sm text-white px-4 py-3 rounded-xl border border-red-400/30 shadow-lg animate-in slide-in-from-top-2 duration-300">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span className="font-medium">{toastMessage}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 min-h-0 relative bg-gradient-to-b from-transparent via-slate-50/30 to-white/50">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50/40 via-transparent to-transparent"></div>
        <div className="relative h-full">
          <MessageList messages={messages} isLoading={isLoading} reasoningText={reasoningText} />
          {(streamingActive || (typeof streamingContent === 'string' && streamingContent.length > 0)) && (
            <div className="px-6 py-3">
              <div className="mx-auto max-w-4xl">
                <div className="bg-gradient-to-r from-blue-50/80 to-emerald-50/80 backdrop-blur-sm rounded-2xl border border-blue-100/50 p-4 shadow-lg">
                  <StreamRenderer
                    content={streamingContent || ''}
                    isStreaming={!!streamingActive}
                    onRetry={onRetryStream || (() => {})}
                    onCancel={onCancelStream || (() => {})}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modern Input Area */}
      <div className="relative bg-gradient-to-r from-white/95 via-slate-50/90 to-white/95 backdrop-blur-xl border-t border-white/60">
        <div className="absolute inset-0 bg-gradient-to-t from-white/40 to-transparent"></div>
        <div className="relative px-6 py-5">
          <InputArea
            value={inputValue}
            disabled={isLoading}
            onChange={onChangeInput}
            onSubmit={onSubmit}
            onKeyDown={onKeyDown}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
