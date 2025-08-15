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
        <div className="px-4 sm:px-6 py-4 bg-white dark:bg-secondary-800 border-t border-gray-200 dark:border-secondary-700 transition-colors duration-300">
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
              className="absolute right-1.5 top-1/2 -translate-y-1/2 h-9 w-9 sm:w-auto sm:px-4 sm:py-2 bg-primary-600 text-white rounded-full flex items-center justify-center hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-300 ease-in-out transform hover:scale-105 active:scale-95 shadow-lg hover:shadow-primary-300/50 dark:shadow-primary-900/50 disabled:opacity-50 disabled:cursor-not-allowed"
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
        <div className="mt-2 text-center text-xs text-gray-500">Powered by Grok (Azure proxy) • Reasoning-aware</div>
      </div>
    </form>
  );
};

export default InputArea;
