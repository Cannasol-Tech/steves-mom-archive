import React from 'react';

interface ModelSelectorProps {
  value: string;
  onChange: (v: string) => void;
  options?: string[];
}

const DEFAULT_OPTIONS = ['grok-3-mini (proxy)', 'gpt-4o-mini (AOAI)', 'local (llama3.1:8b)'];

const ModelSelector: React.FC<ModelSelectorProps> = ({ value, onChange, options = DEFAULT_OPTIONS }) => {
  const selectId = 'model-selector';

  return (
    <div
      className="relative inline-flex items-center gap-2 text-sm rounded-full border border-gray-300 dark:border-gray-700 bg-white/80 dark:bg-gray-900/60 backdrop-blur px-3 py-1.5 shadow-sm hover:shadow transition-all focus-within:ring-2 focus-within:ring-emerald-400/60"
    >
      <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 text-white text-[10px] font-semibold shadow-sm">
        AI
      </span>

      <label htmlFor={selectId} className="text-gray-600 dark:text-gray-300/90 select-none">
        Model
      </label>

      <div className="relative">
        <select
          id={selectId}
          aria-label="Select AI model"
          className="appearance-none bg-transparent pr-8 pl-1 py-1.5 rounded-full cursor-pointer focus:outline-none focus:ring-0 text-gray-900 dark:text-gray-100"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
        {/* Chevron */}
        <svg
          className="pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500 dark:text-gray-400"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M5.23 7.21a.75.75 0 011.06.02L10 10.17l3.71-2.94a.75.75 0 11.94 1.16l-4.24 3.36a.75.75 0 01-.94 0L5.21 8.39a.75.75 0 01.02-1.18z"
            clipRule="evenodd"
          />
        </svg>
      </div>
    </div>
  );
};

export default ModelSelector;
