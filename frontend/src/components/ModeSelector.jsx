import React, { useState } from 'react';
import { MODE_CONFIG } from '../constants/modes';

export default function ModeSelector({ mode, setMode }) {
  const [isOpen, setIsOpen] = useState(false);

  const selectedMode = MODE_CONFIG[mode] || MODE_CONFIG['chat'];

  return (
    <div className="relative group">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 bg-slate-800 border border-slate-700 hover:border-blue-500/50 px-4 py-2 rounded-xl transition-all shadow-sm min-w-[200px] justify-between group"
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">{selectedMode.title.split(' ')[0]}</span>
          <div className="flex flex-col items-start">
            <span className="text-xs font-bold text-white leading-none mb-0.5">
              {selectedMode.title.split(' ').slice(1).join(' ')}
            </span>
            <span className="text-[10px] text-slate-400 leading-none truncate max-w-[120px]">
              {selectedMode.short}
            </span>
          </div>
        </div>
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          width="14" height="14" 
          viewBox="0 0 24 24" fill="none" stroke="currentColor" 
          strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
          className={`text-slate-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        >
          <path d="m6 9 6 6 6-6"/>
        </svg>

        {/* Hover Tooltip for Detailed Prediction */}
        {!isOpen && (
          <div className="absolute bottom-full left-0 mb-3 w-64 p-3 bg-slate-900 border border-slate-700 rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 pointer-events-none">
            <div className="text-xs font-bold text-blue-400 mb-1">{selectedMode.title}</div>
            <div className="text-[11px] text-slate-300 leading-relaxed mb-2">
              {selectedMode.description}
            </div>
            <div className="text-[10px] text-slate-500 italic">
              Use Case: {selectedMode.use_case}
            </div>
            {/* Arrow */}
            <div className="absolute top-full left-6 -mt-1 border-8 border-transparent border-t-slate-900"></div>
          </div>
        )}
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          ></div>
          <div className="absolute bottom-full left-0 mb-2 w-72 max-h-96 overflow-y-auto bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl z-50 animate-fade-in-up scrollbar-thin scrollbar-thumb-slate-700">
            <div className="p-2 space-y-1">
              {Object.entries(MODE_CONFIG).map(([key, config]) => (
                <button
                  key={key}
                  onClick={() => {
                    setMode(key);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left p-3 rounded-xl transition-all flex items-start gap-3 hover:bg-slate-800 group/item ${
                    mode === key ? 'bg-blue-600/10 border border-blue-500/20' : 'border border-transparent'
                  }`}
                >
                  <span className="text-xl mt-0.5">{config.title.split(' ')[0]}</span>
                  <div className="flex flex-col">
                    <span className={`text-sm font-bold ${mode === key ? 'text-blue-400' : 'text-slate-200'} group-hover/item:text-blue-400 transition-colors`}>
                      {config.title.split(' ').slice(1).join(' ')}
                    </span>
                    <span className="text-[11px] text-slate-400 line-clamp-1">
                      {config.short}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
