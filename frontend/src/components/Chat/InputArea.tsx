import React from 'react';

interface InputAreaProps {
  value: string;
  disabled?: boolean;
  onChange: (v: string) => void;
  onSubmit: () => void;
  onKeyDown?: React.KeyboardEventHandler<HTMLTextAreaElement>;
}

const InputArea: React.FC<InputAreaProps> = ({ value, disabled, onChange, onSubmit, onKeyDown }) => {
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(); }} className="">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end rounded-2xl border border-blue-100 bg-white shadow-sm focus-within:ring-2 focus-within:ring-blue-200">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask anything… (Shift+Enter = newline)"
            className="flex-1 p-3 sm:p-4 outline-none bg-transparent min-h-[44px] max-h-40 resize-y text-gray-900 placeholder:text-gray-400"
            disabled={disabled}
          />
          <div className="p-2 sm:p-3">
            <button
              type="submit"
              disabled={!value.trim() || disabled}
              className="inline-flex items-center rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500 text-white px-3 py-2 text-sm font-medium shadow hover:opacity-95 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Send message"
              title="Send (Enter)"
            >
              Send
            </button>
          </div>
        </div>
        <div className="mt-2 text-center text-xs text-gray-500">Powered by Grok (Azure proxy) • Reasoning-aware</div>
      </div>
    </form>
  );
};

export default InputArea;
