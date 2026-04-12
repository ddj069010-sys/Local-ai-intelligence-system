import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function DatabasePage() {
  const [stats, setStats] = useState({ status: 'offline', chat_count: 0, memory_count: 0 });
  const [globalSummary, setGlobalSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [memories, setMemories] = useState([]);
  const [chats, setChats] = useState([]);
  const [activeTab, setActiveTab] = useState('memories'); // 'memories' | 'chats'
  const [expandedId, setExpandedId] = useState(null);

  const fetchStats = async () => {
    try {
      const [statsRes, memRes, chatRes] = await Promise.all([
        fetch(`${API_BASE}/database/stats`),
        fetch(`${API_BASE}/memory`),
        fetch(`${API_BASE}/chats`)
      ]);
      
      const statsData = await statsRes.json();
      const memData = await memRes.json();
      const chatData = await chatRes.json();
      
      setStats(statsData);
      setMemories(memData);
      setChats(chatData);
    } catch (e) {
      setStats({ status: 'offline', chat_count: 0, memory_count: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex-1 h-screen overflow-y-auto bg-slate-900 text-slate-200 p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-10">
          <h1 className="text-4xl font-black bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent mb-2">
            Intelligence Database Pool
          </h1>
          <p className="text-slate-400 text-sm font-medium">Real-time Backend Synchronization & Knowledge Indexing</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Status Card */}
          <div className="bg-slate-800/40 border border-slate-700/50 rounded-3xl p-6 backdrop-blur-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4">
              <div className={`w-3 h-3 rounded-full ${stats.status === 'online' ? 'bg-green-500 shadow-[0_0_15px_rgba(34,197,94,0.5)]' : 'bg-red-500'} animate-pulse`} />
            </div>
            <div className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-4">System Status</div>
            <div className="text-3xl font-black text-white mb-1 capitalize">{stats.status}</div>
            <div className="text-xs text-slate-400 font-medium">Backend API Connection</div>
            <div className="mt-6 h-1 w-full bg-slate-700/50 rounded-full overflow-hidden">
               <div className="h-full bg-blue-500 w-full" />
            </div>
          </div>

          {/* Chats Count */}
          <div className="bg-slate-800/40 border border-slate-700/50 rounded-3xl p-6 backdrop-blur-xl relative overflow-hidden group">
            <div className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-4">Chat Persistence</div>
            <div className="text-3xl font-black text-white mb-1">{stats.chat_count}</div>
            <div className="text-xs text-slate-400 font-medium">JSON Sessions in /data/chats</div>
            <div className="mt-8 flex items-center gap-2 text-blue-400 text-xs font-bold">
               <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
               <span>Durable Storage Active</span>
            </div>
          </div>

          {/* Memory Count */}
          <div className="bg-slate-800/40 border border-slate-700/50 rounded-3xl p-6 backdrop-blur-xl relative overflow-hidden group">
            <div className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-4">Knowledge Pool</div>
            <div className="text-3xl font-black text-white mb-1">{stats.memory_count}</div>
            <div className="text-xs text-slate-400 font-medium">Indexed Memory Fragments</div>
            <div className="mt-8 flex items-center gap-2 text-indigo-400 text-xs font-bold">
               <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
               <span>RAG Extraction Online</span>
            </div>
          </div>
        </div>

        <section className="bg-gradient-to-br from-indigo-500/10 to-blue-500/10 border border-indigo-500/20 rounded-[2.5rem] p-10 backdrop-blur-sm mb-12">
           <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center text-indigo-400 border border-indigo-500/30">
                 <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">Knowledge Core Summary</h2>
                <p className="text-indigo-300 text-sm font-medium">Condensed Intelligence from all synced sessions</p>
              </div>
           </div>
           
           <div className="bg-slate-900/60 rounded-3xl p-8 border border-slate-700/50">
              <p className="text-slate-300 leading-relaxed text-lg">
                Your local intelligence pool currently tracks <span className="text-white font-bold">{stats.chat_count}</span> active conversations. 
                The system has synthesized <span className="text-indigo-400 font-bold">{stats.memory_count}</span> high-value knowledge fragments across your technical research, technical questions, and general chats. 
                <br /><br />
                <span className="text-slate-400 italic text-base">"This database acts as your persistent second brain, bridging insights across different sessions to ensure context is never lost."</span>
              </p>
           </div>
        </section>

        <section className="bg-slate-800/20 border border-slate-700/30 rounded-[2.5rem] p-10 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-white mb-1">Data Explorer</h2>
              <p className="text-slate-500 text-sm font-medium">Browse raw intelligence fragments and persisted sessions</p>
            </div>
            <div className="flex gap-2">
              <div className="bg-slate-900/50 p-1.5 rounded-2xl border border-slate-700/50 flex gap-1">
                <button 
                  onClick={() => setActiveTab('memories')}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${activeTab === 'memories' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  Knowledge Pool
                </button>
                <button 
                  onClick={() => setActiveTab('chats')}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${activeTab === 'chats' ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/20' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  Chat History
                </button>
              </div>
              <button 
                onClick={fetchStats}
                className="px-4 py-2.5 bg-slate-700/40 hover:bg-slate-700/60 border border-slate-600/30 rounded-2xl text-xs font-bold text-slate-200 transition-all active:scale-95"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="inline mr-2"><path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                Refresh
              </button>
            </div>
          </div>

          <div className="space-y-3 min-h-[400px]">
             {activeTab === 'memories' ? (
                memories.length > 0 ? (
                  memories.map((mem) => (
                    <div 
                      key={mem.id} 
                      className={`group border transition-all duration-300 rounded-3xl overflow-hidden ${expandedId === mem.id ? 'bg-slate-900 border-indigo-500/40' : 'bg-slate-900/30 border-slate-800 hover:border-slate-700'}`}
                    >
                       <div 
                         onClick={() => setExpandedId(expandedId === mem.id ? null : mem.id)}
                         className="p-5 flex items-center gap-4 cursor-pointer"
                       >
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center border transition-all ${expandedId === mem.id ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30' : 'bg-slate-800 text-slate-500 border-slate-700'}`}>
                             <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
                          </div>
                          <div className="flex-1 min-w-0">
                             <h4 className="text-sm font-bold text-slate-100 truncate">{mem.summary}</h4>
                             <div className="flex gap-2 mt-1">
                                {mem.tags?.map(tag => (
                                  <span key={tag} className="text-[9px] font-black uppercase tracking-widest text-indigo-400/80 bg-indigo-500/5 px-2 py-0.5 rounded border border-indigo-500/10">{tag}</span>
                                ))}
                             </div>
                          </div>
                          <div className="text-[10px] font-bold text-slate-500">
                             {new Date(mem.created_at).toLocaleDateString()}
                          </div>
                          <svg 
                            xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" 
                            className={`text-slate-600 transition-transform duration-300 ${expandedId === mem.id ? 'rotate-180' : ''}`}
                          >
                            <polyline points="6 9 12 15 18 9"></polyline>
                          </svg>
                       </div>
                       {expandedId === mem.id && (
                         <div className="px-5 pb-5 pt-0 animate-in fade-in slide-in-from-top-2 duration-300">
                            <div className="h-px w-full bg-slate-800 mb-4" />
                            <div className="text-slate-400 text-sm leading-relaxed font-medium bg-slate-800/30 p-4 rounded-2xl border border-slate-700/30">
                               {mem.content}
                            </div>
                            <div className="mt-4 flex items-center justify-between">
                               <div className="text-[10px] text-slate-500 font-bold">SOURCE: {mem.chat_title}</div>
                               <button 
                                 className="text-[10px] text-red-400 font-bold hover:text-red-300 transition-colors"
                                 onClick={async (e) => {
                                   e.stopPropagation();
                                   if (confirm('Delete this memory fragment?')) {
                                      await fetch(`${API_BASE}/memory/${mem.id}`, { method: 'DELETE' });
                                      fetchStats();
                                   }
                                 }}
                               >
                                 REMOVE FRAGMENT
                               </button>
                            </div>
                         </div>
                       )}
                    </div>
                  ))
                ) : (
                  <div className="h-64 flex flex-col items-center justify-center text-slate-500 border-2 border-dashed border-slate-800 rounded-3xl">
                     <p className="font-bold">No intelligence fragments found</p>
                     <p className="text-xs">Start chatting to build your knowledge core</p>
                  </div>
                )
             ) : (
                chats.length > 0 ? (
                  chats.map((chat) => (
                    <div 
                      key={chat.chat_id} 
                      className={`group border transition-all duration-300 rounded-3xl overflow-hidden ${expandedId === chat.chat_id ? 'bg-slate-900 border-blue-500/40' : 'bg-slate-900/30 border-slate-800 hover:border-slate-700'}`}
                    >
                       <div 
                         onClick={() => setExpandedId(expandedId === chat.chat_id ? null : chat.chat_id)}
                         className="p-5 flex items-center gap-4 cursor-pointer"
                       >
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center border transition-all ${expandedId === chat.chat_id ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : 'bg-slate-800 text-slate-500 border-slate-700'}`}>
                             <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                          </div>
                          <div className="flex-1 min-w-0">
                             <h4 className="text-sm font-bold text-slate-100 truncate">{chat.title || "Untitled Session"}</h4>
                             <div className="text-[9px] font-black uppercase tracking-widest text-slate-500 mt-1">{chat.messages?.length || 0} MESSAGES</div>
                          </div>
                          <div className="text-[10px] font-bold text-slate-500 text-right">
                             <div>{new Date(chat.updated_at).toLocaleDateString()}</div>
                             <div className="opacity-60">{new Date(chat.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                          </div>
                          <svg 
                            xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" 
                            className={`text-slate-600 transition-transform duration-300 ${expandedId === chat.chat_id ? 'rotate-180' : ''}`}
                          >
                            <polyline points="6 9 12 15 18 9"></polyline>
                          </svg>
                       </div>
                       {expandedId === chat.chat_id && (
                         <div className="px-5 pb-5 pt-0 animate-in fade-in slide-in-from-top-2 duration-300">
                            <div className="h-px w-full bg-slate-800 mb-4" />
                            <div className="max-h-60 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                               {chat.messages?.slice(-3).map((m, i) => (
                                 <div key={i} className="text-[11px] leading-relaxed">
                                    <span className={`font-black uppercase tracking-tighter mr-2 ${m.role === 'user' ? 'text-blue-400' : 'text-indigo-400'}`}>{m.role}:</span>
                                    <span className="text-slate-300">{m.content?.substring(0, 150)}{m.content?.length > 150 ? '...' : ''}</span>
                                 </div>
                               ))}
                               {chat.messages?.length > 3 && (
                                 <div className="text-[10px] text-slate-500 font-bold italic pt-2">... {chat.messages.length - 3} older messages hidden</div>
                               )}
                            </div>
                            <div className="mt-6 flex items-center justify-between">
                               <div className="text-[10px] text-slate-500 font-bold">UUID: {chat.chat_id}</div>
                               <div className="flex gap-4">
                                  <button 
                                    className="text-[10px] text-blue-400 font-bold hover:text-blue-300 transition-colors"
                                    onClick={() => window.location.href = `/chat?session=${chat.chat_id}`}
                                  >
                                    RESTORE SESSION
                                  </button>
                                  <button 
                                    className="text-[10px] text-red-400 font-bold hover:text-red-300 transition-colors"
                                    onClick={async (e) => {
                                      e.stopPropagation();
                                      if (confirm('Permanently delete this session and all its messages?')) {
                                          await fetch(`${API_BASE}/chats/${chat.chat_id}`, { method: 'DELETE' });
                                          fetchStats();
                                      }
                                    }}
                                  >
                                    PURGE DATA
                                  </button>
                               </div>
                            </div>
                         </div>
                       )}
                    </div>
                  ))
                ) : (
                  <div className="h-64 flex flex-col items-center justify-center text-slate-500 border-2 border-dashed border-slate-800 rounded-3xl">
                     <p className="font-bold">No chat sessions found</p>
                     <p className="text-xs">Initial sync required to populate database</p>
                  </div>
                )
             )}
          </div>
        </section>
      </div>
    </div>
  );
}
