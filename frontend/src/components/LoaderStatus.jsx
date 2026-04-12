import React, { useState, useEffect } from 'react';

const SIMULATED_STEPS = [
  "🔍 Searching for relevant sources...",
  "🌐 Fetching data from trusted websites...",
  "📄 Extracting and analyzing content...",
  "🧠 Generating report...",
  "✅ Verifying accuracy..."
];

export default function LoaderStatus({ currentThought, isStreaming }) {
  const [stepIndex, setStepIndex] = useState(0);

  // Auto-progress simulated steps if backend is silent or slow
  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex(prev => (prev < SIMULATED_STEPS.length - 1 ? prev + 1 : prev));
    }, 1200); // Progress every 1.2s
    return () => clearInterval(interval);
  }, []);

  const backendThoughts = currentThought.filter(t => t && t.trim().length > 0);
  const isActuallyFinished = !isStreaming && currentThought.length > 0;
  return (
    <div className="flex flex-col self-start opacity-0 animate-fade-in-up max-w-[85%] mt-6 mb-8">
      <div className="glass-dark border border-white/5 rounded-3xl p-6 shadow-premium relative overflow-hidden group transition-premium hover:border-blue-500/20">
        {/* Animated Background Pulse */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-blue-500/50 to-transparent animate-shimmer"></div>
        
         <div className="flex items-center gap-4 mb-5">
            <div className="relative">
              <div className={`w-10 h-10 rounded-xl ${isActuallyFinished ? 'bg-emerald-500/20' : 'bg-blue-600/10'} border ${isActuallyFinished ? 'border-emerald-500/40' : 'border-blue-500/20'} flex items-center justify-center transition-all duration-500`}>
                {isActuallyFinished ? (
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-500 animate-fade-in"><polyline points="20 6 9 17 4 12"></polyline></svg>
                ) : (
                  <div className="w-5 h-5 border-2 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
                )}
              </div>
              {!isActuallyFinished && <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.6)]"></div>}
            </div>
            
            <div className="flex flex-col">
              <span className={`text-[10px] font-black uppercase tracking-[0.2em] ${isActuallyFinished ? 'text-emerald-500' : 'text-slate-500'} mb-1 transition-colors duration-500`}>
                {isActuallyFinished ? 'Intelligence Verified' : 'Neural Processing'}
              </span>
              <span className="text-sm font-black text-white tracking-tight leading-none">
                {isActuallyFinished ? 'Synthesis Successfully Completed' : 'Intelligence Synthesis In Progress'}
              </span>
            </div>
         </div>
         
         {/* Active Step Indicator */}
         <div className={`bg-white/[0.03] border border-white/5 rounded-2xl p-4 mb-5 flex items-center justify-between group-hover:bg-white/[0.05] transition-premium ${isActuallyFinished ? 'border-emerald-500/20 bg-emerald-500/5' : ''}`}>
            <div className="flex items-center gap-3">
              <span className={`text-lg ${!isActuallyFinished && 'animate-bounce duration-1000'}`}>
                {isActuallyFinished ? '✨' : SIMULATED_STEPS[stepIndex].split(' ')[0]}
              </span>
              <span className={`text-sm font-bold ${isActuallyFinished ? 'text-emerald-400' : 'text-blue-400'} tracking-tight`}>
                {isActuallyFinished ? 'Optimization and verification finalized.' : SIMULATED_STEPS[stepIndex].split(' ').slice(1).join(' ')}
              </span>
            </div>
            <div className="text-[9px] font-black text-slate-600 uppercase tracking-widest flex items-center gap-1">
              {backendThoughts.some(t => t.includes('🌐')) && <span className="text-blue-400">🌐</span>}
              {isActuallyFinished ? 'DONE' : `Step ${stepIndex + 1}/5`}
            </div>
         </div>

        
        {/* Live Thought Stream */}
        {backendThoughts.length > 0 && (
          <div className="space-y-2 pt-4 border-t border-white/5 max-h-40 overflow-y-auto pr-2 custom-scrollbar">
            <div className="text-[9px] font-black text-slate-700 uppercase tracking-widest mb-1 flex items-center justify-between sticky top-0 bg-[#0a0c10] py-1">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/50"></span>
                Intelligence Audit Log
              </div>
              <span className="text-[8px] opacity-40">{backendThoughts.length} Steps</span>
            </div>
            {backendThoughts.map((thought, idx) => (
              <div key={idx} className="flex gap-3 animate-fade-in py-1 border-b border-white/[0.02] last:border-0">
                <span className="text-slate-600 font-mono text-[9px] mt-0.5 shrink-0">
                  {idx + 1}.
                </span>
                <span className="text-[11px] text-slate-400 font-medium tracking-tight leading-relaxed">
                  {thought}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
