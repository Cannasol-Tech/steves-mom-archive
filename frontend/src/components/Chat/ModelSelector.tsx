import React from 'react';

interface ModelSelectorProps {
  value: string;
  onChange: (v: string) => void;
  options?: string[];
}

const DEFAULT_OPTIONS = ['grok-3-mini (proxy)', 'gpt-4o-mini (AOAI)', 'local (llama3.1:8b)'];

const ModelSelector: React.FC<ModelSelectorProps> = ({ value, onChange, options = DEFAULT_OPTIONS }) => {
  return (
    <div className="inline-flex items-center text-sm rounded-full border border-emerald-200 bg-white/80 shadow-sm px-2 py-1">
      <span className="mr-2 inline-flex items-center justify-center h-6 w-6 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 text-white text-[10px] font-semibold">AI</span>
      <span className="mr-2 text-gray-600">Model</span>
      <select
        className="appearance-none bg-transparent pr-6 pl-2 py-1 rounded-full focus:outline-none focus:ring-2 focus:ring-emerald-200 text-gray-900"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
      <span className="-ml-5 pointer-events-none text-gray-400">▾</span>
    </div>
  );
};

export default ModelSelector;
