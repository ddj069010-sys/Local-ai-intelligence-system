import React, { useState } from 'react';

export default function Sidebar({ 
  chats, 
  activeChatId, 
  onSelectChat, 
  onNewChat, 
  onSearch,
  onDeleteChat,
  onRenameChat,
  view,
  onViewChange
}) {
  const [isResourcesOpen, setIsResourcesOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState('');

  const handleStartEdit = (chat) => {
    setEditingId(chat.id);
    setEditValue(chat.title || chat.summary || '');
  };

  const handleSaveEdit = (id) => {
    if (editValue.trim()) {
      onRenameChat(id, editValue.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="w-80 h-screen bg-slate-950 flex flex-col border-r border-white/5 transition-premium relative glass-dark shadow-premium">
      {/* 1. PRIMARY: NEW CHAT (Top, Prominent) */}
      <div className="p-6">
        <button 
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-gradient-to-br from-blue-600 to-indigo-700 hover:from-blue-500 hover:to-indigo-600 text-white rounded-2xl shadow-lg shadow-blue-900/40 transition-premium group active:scale-[0.98] border border-white/10"
        >
          <svg className="group-hover:rotate-90 transition-transform duration-300" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          <span className="text-sm font-black uppercase tracking-widest">New Session</span>
        </button>
      </div>

      {/* 2. SEARCH (Sticky) */}
      <div className="px-6 pb-4 sticky top-0 bg-slate-950/80 backdrop-blur-md z-10">
        <div className="relative group">
          <svg className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-500 transition-colors" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <input 
            type="text" 
            placeholder="Search intelligence..."
            onChange={(e) => onSearch(e.target.value)}
            className="w-full bg-slate-900/50 border border-white/5 text-slate-200 text-xs rounded-xl py-3 pl-11 pr-4 focus:outline-none focus:border-blue-500/50 focus:bg-slate-900 transition-premium placeholder:text-slate-600 font-medium font-sans"
          />
        </div>
      </div>

      {/* 4. RESOURCES DROPDOWN (Advanced Tools) - CLICK TO TOGGLE */}
      <div className="px-6 py-4 border-t border-white/5 relative">
        <button 
          onClick={() => setIsResourcesOpen(!isResourcesOpen)}
          className={`w-full flex items-center justify-between px-5 py-3.5 rounded-2xl border transition-premium shadow-premium ${isResourcesOpen ? 'bg-white/10 border-white/20 text-white' : 'bg-white/5 border-white/5 text-slate-400 hover:text-white hover:bg-white/10'}`}
        >
          <div className="flex items-center gap-3">
             <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>
             <span className="text-xs font-black uppercase tracking-widest">Resources</span>
          </div>
          <svg className={`transition-transform duration-300 ${isResourcesOpen ? 'rotate-180' : ''}`} xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
        </button>
        
        {isResourcesOpen && (
          <div className="absolute left-6 right-6 bottom-full mb-2 glass shadow-premium rounded-2xl border border-white/10 p-2 animate-fade-in-up z-50">
             <button 
              onClick={() => { onViewChange('memory'); setIsResourcesOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-premium ${view === 'memory' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
              <span className="text-sm font-bold">Intelligence Pool</span>
            </button>

            <button 
              onClick={() => { onViewChange('database'); setIsResourcesOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-premium ${view === 'database' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
              <span className="text-sm font-bold">Database Pool</span>
            </button>

            <button 
              onClick={() => { onViewChange('workspace'); setIsResourcesOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-premium ${view === 'workspace' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
              <span className="text-sm font-bold">Workspace</span>
            </button>

            <button 
              onClick={() => { onViewChange('hq'); setIsResourcesOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-premium ${view === 'hq' ? 'bg-violet-600 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
            >
              <span style={{ fontSize: '16px' }}>🛰️</span>
              <span className="text-sm font-bold">Intelligence HQ</span>
              <span style={{ marginLeft: 'auto', fontSize: '9px', fontWeight: 800, background: 'rgba(139,92,246,0.2)', color: '#a78bfa', padding: '2px 8px', borderRadius: '8px', letterSpacing: '0.1em' }}>5 SECTORS</span>
            </button>
          </div>
        )}
      </div>

      {/* 3. CHATS: RECENT (Scrollable) */}
      <div className="flex-1 overflow-y-auto mt-2 px-4 scrollbar-thin">
        <div className="flex items-center justify-between px-2 mb-4">
          <div className="text-[10px] font-black text-slate-600 uppercase tracking-[0.25em]">Recent Chats</div>
          <button className="text-slate-600 hover:text-blue-400 transition-premium" title="Filter Chats">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>
          </button>
        </div>
        <div className="space-y-1.5">
          {chats.map((chat) => (
            <div 
              key={chat.id || chat.chat_id}
              className={`group flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-premium border ${
                activeChatId === (chat.id || chat.chat_id) 
                  ? 'bg-slate-900 text-white border-white/10 shadow-lg' 
                  : 'text-slate-500 hover:bg-white/5 hover:text-slate-300 border-transparent'
              }`}
              onClick={() => onSelectChat(chat.id || chat.chat_id)}
            >
              <div className={`p-1.5 rounded-lg ${activeChatId === (chat.id || chat.chat_id) ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-500'} transition-premium`}>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
              </div>
              
              {editingId === (chat.id || chat.chat_id) ? (
                <input 
                  autoFocus
                  className="flex-1 bg-slate-950 border border-blue-500/50 text-xs text-white rounded px-2 py-1 outline-none font-medium"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onBlur={() => handleSaveEdit(chat.id || chat.chat_id)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSaveEdit(chat.id || chat.chat_id)}
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <div className="flex flex-col flex-1 min-w-0">
                  <span className="text-xs truncate font-bold">{chat.title || chat.summary}</span>
                  <span className="text-[9px] text-slate-600 font-bold uppercase tracking-tighter">Modified {chat.updated_at ? "Recently" : "2m ago"}</span>
                </div>
              )}

              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-premium">
                <button 
                  onClick={(e) => { e.stopPropagation(); handleStartEdit(chat); }}
                  className="p-1.5 hover:text-blue-400 hover:bg-blue-400/10 rounded-md transition-premium"
                  title="Rename"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                </button>
                <button 
                  onClick={(e) => { e.stopPropagation(); onDeleteChat(chat.id || chat.chat_id); }}
                  className="p-1.5 hover:text-red-400 hover:bg-red-400/10 rounded-md transition-premium"
                  title="Delete"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. MEMORY USAGE INDICATOR */}
      <div className="px-6 py-6 border-t border-white/5 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>
            Memory Usage
          </span>
          <span className="text-[10px] font-black text-blue-400 tracking-tighter">64%</span>
        </div>
        <div className="memory-bar-bg overflow-hidden shadow-inner">
          <div className="memory-bar-fill w-[64%] shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>
        </div>
        <div className="text-[9px] text-slate-600 font-bold uppercase tracking-tighter">3.2 GB / 5 GB AVAILABLE</div>
      </div>

      {/* Profile Section */}
      <div className="p-4 bg-slate-900/40 backdrop-blur-md">
        <div className="flex items-center gap-3 p-3 rounded-2xl hover:bg-white/5 transition-premium cursor-pointer group border border-transparent hover:border-white/5 shadow-inner">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-white/10 flex items-center justify-center text-blue-400 font-black text-sm transition-premium group-hover:scale-105 group-hover:border-blue-500/50 shadow-premium">
              IA
            </div>
            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 border-2 border-slate-950 rounded-full shadow-lg"></div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-black text-slate-200 truncate tracking-tight">Ishtiyaq Ansari</div>
            <div className="text-[9px] text-slate-500 font-black uppercase tracking-widest">Premium Plan</div>
          </div>
          <button className="text-slate-600 hover:text-white transition-premium p-1.5">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          </button>
        </div>
      </div>
    </div>
  );
}
