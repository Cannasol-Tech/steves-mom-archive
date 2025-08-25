import React from 'react';

interface InputAreaProps {
  value: string;
  disabled?: boolean;
  loading?: boolean;
  onChange: (v: string) => void;
  onSubmit: () => void;
  onKeyDown?: React.KeyboardEventHandler<HTMLTextAreaElement>;
  textareaRef?: React.Ref<HTMLTextAreaElement>;
}

const MAX_CHARS = 2000;

const InputArea: React.FC<InputAreaProps> = ({ value, disabled, loading, onChange, onSubmit, onKeyDown, textareaRef }) => {
  // Combine external textareaRef with an internal ref for autosize
  const internalRef = React.useRef<HTMLTextAreaElement | null>(null);
  const setRefs = React.useCallback((node: HTMLTextAreaElement | null) => {
    internalRef.current = node;
    if (typeof textareaRef === 'function') {
      textareaRef(node);
    } else if (textareaRef && typeof (textareaRef as any) === 'object') {
      (textareaRef as any).current = node;
    }
  }, [textareaRef]);

  const autosize = React.useCallback(() => {
    const el = internalRef.current;
    if (!el) return;
    // Reset height then set to scrollHeight within a reasonable max
    el.style.height = 'auto';
    const maxPx = 320; // ~20rem
    const next = Math.min(el.scrollHeight, maxPx);
    el.style.height = `${next}px`;
  }, []);

  React.useEffect(() => { autosize(); }, [value, autosize]);

  const length = value.length;
  const overLimit = length > MAX_CHARS;
  const remaining = MAX_CHARS - length;
  const nearLimit = remaining <= 100 && remaining >= 0;

  const handleChange = (v: string) => {
    onChange(v);
    // Defer autosize until after value applies
    requestAnimationFrame(autosize);
  };

  return (
    <form onSubmit={(e) => { e.preventDefault(); if (!overLimit) onSubmit(); }} className="">
      <div className="mx-auto max-w-3xl">
        <div className={`flex items-end rounded-2xl border ${overLimit ? 'border-red-300 dark:border-red-600' : 'border-blue-100 dark:border-secondary-700'} bg-white dark:bg-secondary-800 shadow-sm focus-within:ring-2 ${overLimit ? 'focus-within:ring-red-200 dark:focus-within:ring-red-500' : 'focus-within:ring-blue-200 dark:focus-within:ring-secondary-600'} transition-colors duration-300 motion-safe:transition-shadow motion-safe:duration-200`}>
          <textarea
            ref={setRefs}
            value={value}
            onChange={(e) => handleChange(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask anything… (Shift+Enter newline • Cmd/Ctrl+Enter send • Esc cancel)"
            className="flex-1 p-3 sm:p-4 outline-none bg-transparent min-h-[44px] max-h-[20rem] resize-none text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500 transition-colors duration-150"
            disabled={disabled}
            aria-busy={!!loading}
            aria-invalid={overLimit ? 'true' : undefined}
            aria-describedby="chat-input-hint"
          />
          <div className="p-2 sm:p-3">
            <button
              type="submit"
              disabled={!value.trim() || disabled || overLimit || !!loading}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500 dark:from-blue-600 dark:to-emerald-600 text-white font-medium shadow hover:opacity-95 disabled:opacity-50 disabled:cursor-not-allowed w-10 h-10 sm:w-auto sm:px-4 sm:py-2 sm:text-sm transition ease-out duration-150 active:scale-[0.98] motion-reduce:transition-none motion-reduce:transform-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-300 dark:focus-visible:ring-secondary-500"
              aria-label="Send message"
              title={overLimit ? `Message too long by ${Math.abs(remaining)} characters` : 'Send (Enter)'}
              aria-busy={!!loading}
            >
              {loading ? (
                <>
                  <svg className="w-4 h-4 motion-safe:animate-spin" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                  </svg>
                  <span className="hidden sm:inline">Sending…</span>
                </>
              ) : (
                <>
                  <span className="hidden sm:inline">Send</span>
                  <svg className="w-5 h-5 sm:hidden" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </div>
        {/* Screen-reader hint for keyboard shortcuts */}
        <p id="chat-input-hint" className="sr-only" aria-live="polite">
          Tip: Press Command or Control and Enter to send. Press Shift and Enter for a new line. Press Escape to cancel streaming.
        </p>
        <div id="chat-input-help" className="mt-2 text-center text-xs">
          <div className="sr-only" role="status" aria-live="polite">
            {overLimit ? `Over character limit by ${Math.abs(remaining)} characters.` : `Characters remaining: ${remaining}.`}
          </div>
          <div className={`${overLimit ? 'text-red-600 dark:text-red-400' : nearLimit ? 'text-amber-600 dark:text-amber-400' : 'text-gray-500 dark:text-gray-400'}`}>
            {overLimit ? (
              <>Too long by <strong>{Math.abs(remaining)}</strong> chars • Max {MAX_CHARS}</>
            ) : (
              <>Powered by Grok (Azure proxy) • Reasoning-aware • <span className="tabular-nums">{remaining}</span> left</>
            )}
          </div>
        </div>
      </div>
    </form>
  );
};

export default InputArea;

