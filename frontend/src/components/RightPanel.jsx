import React from 'react';

export default function RightPanel({ isOpen, onClose, messages = [], activeFiles = [] }) {
  if (!isOpen) return null;

  // Mock data for sources and insights
  const insights = [
    "Analyzing React component lifecycle",
    "Tailwind CSS integration patterns",
    "State management optimization"
  ];

  const sources = [
    { title: "React Documentation", url: "https://react.dev" },
    { title: "Tailwind UI Components", url: "https://tailwindui.com" }
  ];

  return (
    <div className="w-80 h-screen bg-slate-950/90 backdrop-blur-2xl border-l border-white/5 flex flex-col transition-premium animate-fade-in-right glass shadow-premium z-40 fixed right-0 top-0">
      <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
        <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-blue-400 flex items-center gap-2">
           <span className="p-1.5 bg-blue-500/10 rounded-lg">🧠</span> Intelligence Panel
        </h2>
        <button onClick={onClose} className="text-slate-500 hover:text-white transition-premium p-1.5 hover:bg-white/5 rounded-xl">
           <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8 scrollbar-thin">
        {/* Memory Insights */}
        <section>
          <div className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-4 flex items-center gap-2">
            <span>Memory Insights</span>
            <div className="flex-1 h-[1px] bg-white/5"></div>
          </div>
          <div className="space-y-3">
            {insights.map((insight, idx) => (
              <div key={idx} className="p-4 rounded-2xl bg-white/[0.03] border border-white/5 hover:border-blue-500/30 transition-premium group shadow-inner">
                <div className="flex gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></div>
                  <span className="text-xs text-slate-300 font-medium leading-relaxed group-hover:text-blue-200">{insight}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Context & Active Files */}
        <section>
          <div className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-4 flex items-center gap-2">
            <span>Session Context</span>
            <div className="flex-1 h-[1px] bg-white/5"></div>
          </div>
          <div className="space-y-2">
            <div className="p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/10 flex items-center justify-between group cursor-pointer hover:bg-emerald-500/10 transition-premium">
              <div className="flex items-center gap-3">
                 <span className="text-emerald-400">📄</span>
                 <span className="text-xs text-emerald-200 font-bold uppercase tracking-tighter">App.jsx</span>
              </div>
              <span className="text-[9px] font-black text-emerald-500 opacity-0 group-hover:opacity-100 uppercase tracking-widest">Active</span>
            </div>
            <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/5 flex items-center justify-between group cursor-pointer hover:bg-white/10 transition-premium">
              <div className="flex items-center gap-3">
                 <span className="text-blue-400">📄</span>
                 <span className="text-xs text-slate-400 font-bold uppercase tracking-tighter">Sidebar.jsx</span>
              </div>
              <span className="text-[9px] font-black text-slate-600 uppercase tracking-widest">Last modified 2m</span>
            </div>
          </div>
        </section>

        {/* Sources & Citations */}
        <section>
          <div className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-4 flex items-center gap-2">
            <span>Sources & Citations</span>
            <div className="flex-1 h-[1px] bg-white/5"></div>
          </div>
          <div className="space-y-3">
            {sources.map((source, idx) => (
              <a 
                key={idx} 
                href={source.url} 
                target="_blank" 
                rel="noreferrer"
                className="block p-4 rounded-2xl bg-slate-900 shadow-inner border border-white/5 hover:border-blue-500/30 transition-premium group"
              >
                <div className="text-[11px] font-black text-slate-200 mb-1 group-hover:text-blue-400 tracking-tight">{source.title}</div>
                <div className="text-[10px] text-slate-600 truncate font-mono">{source.url}</div>
              </a>
            ))}
          </div>
        </section>

        {/* Debug / Token Usage */}
        <section className="bg-slate-900/50 rounded-2xl p-5 border border-white/5 shadow-inner">
           <div className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-4">Neural Performance</div>
           <div className="space-y-4">
              <div>
                <div className="flex justify-between text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                  <span>Token Budget</span>
                  <span className="text-blue-400">4,281 / 8k</span>
                </div>
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 w-[53%] shadow-[0_0_10px_rgba(59,130,246,0.4)]"></div>
                </div>
              </div>
              <div className="flex items-center justify-between text-[10px] font-black">
                 <span className="text-slate-600 uppercase tracking-widest">Latency</span>
                 <span className="text-emerald-500">142ms</span>
              </div>
           </div>
        </section>
      </div>

      <div className="p-6 bg-white/[0.02] border-t border-white/5">
         <button className="w-full py-4 bg-white/5 hover:bg-white/10 text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-white rounded-2xl border border-white/5 transition-premium shadow-inner">
            Export Intelligence Session
         </button>
      </div>
    </div>
  );
}
