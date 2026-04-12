import React from 'react';
import ModeSelector from './ModeSelector';
import { MODE_CONFIG } from '../constants/modes';

export default function InputBox({ input, setInput, sendMessage, loading, mode, setMode, onStop }) {
  const currentMode = MODE_CONFIG[mode] || MODE_CONFIG['chat'];
  
  return (
    <div className="p-4 md:p-6 bg-slate-900 border-t border-slate-700 flex flex-col gap-4 items-center relative z-10 w-full max-w-5xl mx-auto font-sans">
      <div className="flex w-full gap-4 items-end">
        {/* Mode Selector beside input */}
        <div className="hidden md:block">
          <ModeSelector mode={mode} setMode={setMode} />
        </div>
        
        <div className="relative flex-1 group">
          <textarea
            className="w-full bg-slate-800 border border-slate-600 text-slate-100 px-5 py-4 pl-4 pr-12 rounded-2xl text-[15px] outline-none transition-all resize-none min-h-[56px] max-h-[200px] leading-relaxed focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 shadow-inner block"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (input.trim() && !loading) {
                  sendMessage();
                }
              }
            }}
            placeholder={`e.g., ${currentMode.example || 'Ask anything...'}`}
            rows={1}
          />
          
          {loading ? (
            <button
               className="absolute right-3 bottom-3 p-2 bg-red-600/90 text-white hover:bg-red-500 rounded-xl transition-all shadow-md transform hover:scale-105 flex items-center justify-center animate-pulse"
               onClick={onStop}
               title="Stop Generation"
             >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><rect x="6" y="6" width="12" height="12"></rect></svg>
             </button>
          ) : (
            <button
              className={`absolute right-3 bottom-3 p-2 rounded-xl transition-all flex items-center justify-center ${
                input.trim() 
                  ? 'bg-blue-600 text-white hover:bg-blue-500 shadow-md transform hover:scale-105' 
                  : 'bg-slate-700 text-slate-500 cursor-not-allowed'
              }`}
              onClick={sendMessage}
              disabled={!input.trim()}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            </button>
          )}
        </div>
      </div>
      
      {/* Mobile Mode Selector */}
      <div className="md:hidden w-full">
        <ModeSelector mode={mode} setMode={setMode} />
      </div>
    </div>
  );
}
