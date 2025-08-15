import React from 'react';
import MessageList, { Message } from './MessageList';
import ModelSelector from './ModelSelector';
import InputArea from './InputArea';

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
  reasoningText
}) => {
  return (
    <div className="flex flex-col bg-white/85 backdrop-blur rounded-2xl border border-emerald-100 shadow-xl w-full">
      {/* Chat Header */}
      <div className="bg-white/80 rounded-t-2xl border-b border-gray-200 px-6 py-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="mb-2">
              <ModelSelector value={model} onChange={onModelChange} />
            </div>
            <div className="flex items-center gap-2">
              <img
                src="/cannasol-logo.png"
                alt="Cannasol Technologies"
                className="h-6 w-6 object-contain hidden sm:block"
                onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
              />
              <h2 className="text-lg font-semibold text-gray-900">Chat with Steve's Mom AI</h2>
            </div>
            <p className="text-sm text-gray-600">Ask me about inventory, documents, or business tasks — background inventory agent handles data.</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 min-h-0 h-[70vh] overflow-hidden">
        <MessageList messages={messages} isLoading={isLoading} reasoningText={reasoningText} />
      </div>

      {/* Input */}
      <div className="bg-white/80 rounded-b-2xl border-t border-gray-200 px-6 py-4">
        <InputArea
          value={inputValue}
          disabled={isLoading}
          onChange={onChangeInput}
          onSubmit={onSubmit}
          onKeyDown={onKeyDown}
        />
      </div>
    </div>
  );
};

export default ChatInterface;
