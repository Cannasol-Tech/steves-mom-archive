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
        <div className="flex items-end rounded-2xl border border-blue-100 dark:border-secondary-700 bg-white dark:bg-secondary-800 shadow-sm focus-within:ring-2 focus-within:ring-blue-200 dark:focus-within:ring-secondary-600 transition-colors duration-300">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask anything… (Shift+Enter = newline)"
            className="flex-1 p-3 sm:p-4 outline-none bg-transparent min-h-[44px] max-h-40 resize-y text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500"
            disabled={disabled}
          />
          <div className="p-2 sm:p-3">
            <button
              type="submit"
              disabled={!value.trim() || disabled}
              className="inline-flex items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500 dark:from-blue-600 dark:to-emerald-600 text-white font-medium shadow hover:opacity-95 disabled:opacity-50 disabled:cursor-not-allowed w-10 h-10 sm:w-auto sm:px-4 sm:py-2 sm:text-sm"
              aria-label="Send message"
              title="Send (Enter)"
            >
              <span className="hidden sm:inline">Send</span>
              <svg className="w-5 h-5 sm:hidden" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            </button>
          </div>
        </div>
        <div className="mt-2 text-center text-xs text-gray-500 dark:text-gray-400">Powered by Grok (Azure proxy) • Reasoning-aware</div>
      </div>
    </form>
  );
};

export default InputArea;
