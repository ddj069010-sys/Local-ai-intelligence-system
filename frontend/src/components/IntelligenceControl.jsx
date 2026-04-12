import React, { useState, useEffect } from 'react';
import { Cpu, Globe, ChevronLeft, ChevronRight, Zap, Shield, Brain, Repeat } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function IntelligenceControl({ 
  model, 
  setModel, 
  webMode, 
  setWebMode, 
  availableModels = [] 
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const toggleOpen = () => setIsOpen(!isOpen);

  // Auto-selection tiers for visual feedback
  const getTierColor = (m) => {
    if (m === 'auto') return 'text-indigo-400';
    if (m.includes('32b') || m.includes('30b') || m.includes('70b') || m.includes('large')) return 'text-rose-400';
    if (m.includes('14b') || m.includes('12b')) return 'text-amber-400';
    return 'text-emerald-400';
  };

  return (
    <div className={`fixed right-0 top-1/2 -translate-y-1/2 z-[100] flex items-center transition-all duration-500 ease-out ${isOpen ? 'mr-4' : 'mr-0'}`}>
      {/* Toggle Button */}
      <button 
        onClick={toggleOpen}
        className={`w-10 h-24 bg-slate-900/80 backdrop-blur-2xl border border-white/10 rounded-l-2xl flex flex-col items-center justify-center gap-4 group hover:bg-slate-800 transition-premium shadow-2xl ${isOpen ? 'rounded-2xl' : ''}`}
      >
        <div className="flex flex-col items-center gap-1">
            <Cpu size={14} className={`${isOpen ? 'text-indigo-400' : 'text-slate-400'} group-hover:scale-110 transition-transform`} />
            <div className="h-8 w-px bg-white/5"></div>
            {isOpen ? <ChevronRight size={14} className="text-slate-500" /> : <ChevronLeft size={14} className="text-slate-500" />}
        </div>
      </button>

      {/* Main Panel */}
      <div className={`overflow-hidden transition-all duration-500 ease-in-out ${isOpen ? 'w-64 opacity-100 translate-x-0' : 'w-0 opacity-0 translate-x-12'}`}>
        <div className="bg-slate-900/90 backdrop-blur-3xl border border-white/10 rounded-3xl p-4 shadow-premium flex flex-col gap-4">
          
          {/* Header */}
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
             <div className="flex flex-col">
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Core Engine</span>
                <span className="text-xs font-black text-white italic">SYNCHRONIZED</span>
             </div>
             <button 
               onClick={() => window.location.reload()} 
               className="p-1 hover:bg-white/5 rounded-md text-slate-500 hover:text-white transition-all"
               title="Refresh Model List"
             >
               <Repeat size={14} />
             </button>
             <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
          </div>

          {/* Web Mode Toggle */}
          <div className="flex items-center justify-between bg-white/5 p-3 rounded-2xl border border-white/5 group hover:border-blue-500/30 transition-premium">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-xl transition-all ${webMode ? 'bg-blue-600/20 text-blue-400 shadow-lg' : 'bg-slate-800 text-slate-500'}`}>
                <Globe size={16} className={webMode ? 'animate-spin-slow' : ''} />
              </div>
              <div className="flex flex-col">
                <span className="text-[11px] font-bold text-white leading-none">Web Mode</span>
                <span className="text-[9px] font-medium text-slate-500 uppercase tracking-tight">{webMode ? 'Live Access' : 'Local Only'}</span>
              </div>
            </div>
            <button 
              onClick={() => setWebMode(!webMode)}
              className={`w-10 h-5 rounded-full relative transition-all duration-300 ${webMode ? 'bg-blue-600 shadow-inner' : 'bg-slate-700'}`}
            >
              <div className={`absolute top-1 w-3 h-3 rounded-full bg-white transition-all duration-300 ${webMode ? 'left-6' : 'left-1 shadow-md'}`}></div>
            </button>
          </div>

          {/* Model Selection */}
          <div className="relative">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 ml-1 mb-2 block">Neural Intelligence</span>
            <button 
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="w-full flex items-center justify-between bg-slate-950/50 border border-white/10 rounded-2xl p-3 hover:bg-slate-950 transition-premium group"
            >
              <div className="flex items-center gap-3">
                <Brain size={16} className={getTierColor(model)} />
                <span className={`text-[13px] font-black uppercase tracking-tighter truncate max-w-[120px] ${getTierColor(model)}`}>{model}</span>
              </div>
              <ChevronRight size={14} className={`text-slate-600 transition-transform ${isDropdownOpen ? 'rotate-90' : ''}`} />
            </button>

            {isDropdownOpen && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-[#121212] border border-white/10 rounded-2xl shadow-2xl p-1 z-[110] max-h-64 overflow-y-auto custom-scrollbar animate-slideUp">
                {availableModels.map(m => (
                  <button
                    key={m}
                    onClick={() => { setModel(m); setIsDropdownOpen(false); }}
                    className={`w-full text-left px-4 py-2.5 rounded-xl text-[11px] font-bold transition-premium flex items-center justify-between group ${model === m ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
                  >
                    <span className="truncate">{m === 'auto' ? 'AUTO-ROUTER v4' : m}</span>
                    {m.includes('32b') && <Zap size={10} className="text-rose-400 group-hover:text-white" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Security Status */}
          <div className="bg-indigo-500/5 border border-indigo-500/10 rounded-2xl p-3 flex flex-col gap-1">
             <div className="flex items-center gap-2">
                <Shield size={12} className="text-indigo-400" />
                <span className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Security Active</span>
             </div>
             <p className="text-[9px] text-slate-500 leading-tight">Grounded Sync & Anti-Injection protocols are currently enforced on all outputs.</p>
          </div>
        </div>
      </div>
      
      {/* Styles for animation */}
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-slideUp {
          animation: slideUp 0.3s ease-out forwards;
        }
        .animate-spin-slow {
          animation: spin 8s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
      `}} />
    </div>
  );
}
