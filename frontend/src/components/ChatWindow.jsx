import React, { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import MultiInputBox from './MultiInputBox';
import LoaderStatus from './LoaderStatus';
import SettingsPanel from './SettingsPanel';
import OutputViewer from './OutputViewer';
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function ChatWindow({ 
  sessionId, 
  refreshSessions, 
  onToggleRightPanel, 
  isRightPanelOpen,
  globalModel,
  globalWebMode,
  availableModels = [],
  onModelChange,
  onWebModeChange,
  onToggleRagPanel,
  onPinToCanvas
}) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState('chat');
  const [loading, setLoading] = useState(false);
  const [currentThought, setCurrentThought] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const [autoSaved, setAutoSaved] = useState(false);
  const [linkResult, setLinkResult] = useState(null);
  const [syncData, setSyncData] = useState(() => {
    return localStorage.getItem('chat_sync_enabled') !== 'false';
  });
  const [status, setStatus] = useState('online');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState(true);
  const [sessionTitle, setSessionTitle] = useState('New Chat');

  
  const messagesEndRef = useRef(null);
  const scrollRef = useRef(null);
  const abortControllerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    // If user is within 150px of bottom, keep auto-scroll enabled
    const atBottom = scrollHeight - scrollTop - clientHeight < 150;
    setIsAutoScrollEnabled(atBottom);
  };

  useEffect(() => {
    if (isAutoScrollEnabled) {
      scrollToBottom();
    }
  }, [messages, currentThought, loading, isAutoScrollEnabled]);

  useEffect(() => {
    if (loading) setStatus('processing');
    else setStatus('online');
  }, [loading]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch(`${API_BASE}/chats/${sessionId}`);
        if (response.ok) {
          const data = await response.json();
          setMessages(data.messages || []);
          if (data.title) setSessionTitle(data.title);
        } else {

          const saved = localStorage.getItem(`chat_history_${sessionId}`);
          setMessages(saved ? JSON.parse(saved) : []);
        }
      } catch (e) {
        console.error("Failed to fetch backend chat history", e);
        const saved = localStorage.getItem(`chat_history_${sessionId}`);
        setMessages(saved ? JSON.parse(saved) : []);
      }
    };
    fetchHistory();
  }, [sessionId]);

  useEffect(() => {
    if (syncData && messages.length > 0) {
      // 1. Save to Local Storage layer
      localStorage.setItem(`chat_history_${sessionId}`, JSON.stringify(messages));
      
      // 2. Synchronize to Backend UUID Store for Persistent Reloading & Auto Naming
      if (sessionId && sessionId !== 'undefined') {
        fetch(`${API_BASE}/chats/${sessionId}/sync`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages })
        })
        .then(res => res.json())
        .then(data => {
           if (refreshSessions && data.title) {
              refreshSessions();
           }
        })
        .catch(e => console.error("Sync error:", e));
      }
    }
  }, [messages, syncData, sessionId]);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const clearChat = () => {
    setMessages([]);
    setCurrentThought([]);
  };

  const reloadChat = () => {
    window.location.reload();
  };

  const deleteSessionData = async () => {
    try {
      await fetch(`${API_BASE}/chats/${sessionId}`, { method: 'DELETE' });
      setMessages([]);
      setCurrentThought([]);
      localStorage.removeItem(`chat_history_${sessionId}`);
      if (refreshSessions) refreshSessions();
    } catch (e) {
      console.error("Failed to delete chat", e);
    }
  };

  const handleSaveToMemory = async (content) => {
    try {
      const response = await fetch(`${API_BASE}/memory`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: `Saved from ${sessionId.slice(0, 8)}`,
          content: content,
          chat_id: sessionId,
          tags: ["saved"]
        })
      });
      const data = await response.json();
      if (data.status === 'added') {
        alert('Saved to Memory Pool!');
      }
    } catch (e) {
      console.error("Failed to save to memory", e);
    }
  };

  const handleAbort = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setLoading(false);
      setStatus('online');
    }
  };

  const handleRegenerate = (lastQuery) => {
    setInput(lastQuery);
    // Submit logic will be handled by the user or auto-trigger if desired.
    // To make it fully automatic, we call triggerSearch directly.
    const historyWithoutLast = messages.slice(0, -1);
    triggerSearch(lastQuery, historyWithoutLast);
  };

  const triggerSearch = async (queryText, historyMsgs, webEnabled = false, speedMode = 'auto', deepSearch = false, concentrated = false, images = null) => {
    setLoading(true);
    setCurrentThought([]);
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const startTime = Date.now();
      const currentMessages = [...historyMsgs, { role: 'user', content: queryText }];
      const res = await fetch(`${API_BASE}/chat_stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          model: globalModel, 
          mode, 
          messages: currentMessages, 
          session_id: sessionId,
          web_enabled: webEnabled,
          speed_mode: speedMode,
          deep_search: deepSearch,
          concentrated: concentrated,
          images: images
        }),
        signal: controller.signal
      });

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let aiContent = "";
      let executionResults = [];
      let fileResults = [];
      let buffer = "";
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '', 
        images: images,
        thoughts: [],
        executionResults: [], 
        fileResults: [],
        streaming: true 
      }]);
      // 🧠 FORCED IMMEDIATE THOUGHT: Provide instant feedback before entering the loop
      setCurrentThought(["Initiating local intelligence sequence..."]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith('data: ')) {
            const dataStr = trimmedLine.substring(6).trim();
            if (dataStr) {
               try {
                const data = JSON.parse(dataStr);
                if (data.type === 'thought') {
                  setCurrentThought(prev => [...prev, data.text]);
                  setMessages(prev => {
                    const newMsgs = [...prev];
                    const last = newMsgs[newMsgs.length - 1];
                    if (last && last.role === 'assistant') {
                      if (!last.thoughts) last.thoughts = [];
                      last.thoughts.push(data.text);
                    }
                    return newMsgs;
                  });
                } else if (data.type === 'message') {
                  aiContent += data.text;
                } else if (data.type === 'final_message') {
                  // 🟢 HYBRID OUTPUT: Replace with high-fidelity version immediately
                  if (data.text) {
                    aiContent = data.text;
                  }
                } else if (data.type === 'execution_result') {
                  executionResults.push(data);
                } else if (data.type === 'file_result') {
                  fileResults.push(data);
                } else if (data.type === 'error') {
                   aiContent += `\n\n⚠️ **Error:** ${data.text}`;
                }
                
                setMessages(prev => {
                  const newMsgs = [...prev];
                  const last = newMsgs[newMsgs.length - 1];
                  if (last && last.role === 'assistant') {
                    last.content = aiContent;
                    last.executionResults = [...executionResults];
                    last.fileResults = [...fileResults];
                  }
                  return newMsgs;
                });
              } catch (e) {}
            }
          }
        }
      }
      
      setMessages(prev => {
        const newMsgs = [...prev];
        const last = newMsgs[newMsgs.length - 1];
        if (last && last.role === 'assistant') {
          last.content = aiContent;
          last.generationTime = ((Date.now() - startTime) / 1000).toFixed(2);
          last.streaming = false;
        }
        return newMsgs;
      });

      // 🧠 AUTO-NAME UPGRADE
      let titleToSync = sessionTitle;
      if (messages.length === 1 && (sessionTitle === 'New Chat' || sessionTitle === 'Restored Session')) {
        try {
          const titleResp = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              model: 'gemma3:4b',
              messages: [{ role: 'user', content: `Summarize this user query into 3-5 words for a chat title: "${messages[0].content}"` }]
            })
          });
          const titleData = await titleResp.json();
          if (titleData.message && titleData.message.content) {
            titleToSync = titleData.message.content.replace(/["']/g, '').replace(/[.]$/, '').trim();
            setSessionTitle(titleToSync);
          }
        } catch (e) { console.error("Auto-naming failed", e); }
      }

      // Sync with backend
      try {
        await fetch(`${API_BASE}/chats/${sessionId}/sync`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: titleToSync,
            messages: [...messages, { 
              role: 'assistant', 
              content: aiContent, 
              thoughts: [], 
              executionResults, 
              fileResults, 
              generationTime: ((Date.now() - startTime) / 1000).toFixed(2) 
            }]
          })
        });
      } catch (e) { console.error("Session sync failed", e); }

    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error(err);
      }
      setMessages(prev => {
        const newMsgs = [...prev];
        const last = newMsgs[newMsgs.length -1];
        if (last && last.role === 'assistant') {
          last.streaming = false;
        }
        return newMsgs;
      });
    } finally {
      abortControllerRef.current = null;
      // Allow the 'Finished' state to be visible for a moment
      setTimeout(() => {
        setLoading(false);
        setCurrentThought([]);
      }, 500);
      if (refreshSessions) refreshSessions();
    }
  };

  const sendMessage = async (overrideText, webEnabled = false, speedMode = 'auto', deepSearch = false, sandboxMode = false, memorySync = true, concentrated = false, images = null) => {
    const queryText = overrideText || input.trim();
    if ((!queryText && !images) || loading) return;
    
    const newMsg = { role: 'user', content: queryText, images: images };
    const updatedMsgs = [...messages, newMsg];
    
    setMessages(updatedMsgs);
    setInput('');
    if (refreshSessions) refreshSessions();
    
    // Determine web state from hidden flags or pass current state if MultiInputBox is controlled
    await triggerSearch(queryText, updatedMsgs, webEnabled, speedMode, deepSearch, concentrated, images);
  };

  return (
    <div className="flex flex-col h-full w-full bg-slate-900 overflow-hidden font-sans relative">
      {/* 1. TOP BAR */}
      <div className="h-16 border-b border-white/5 bg-slate-950/40 backdrop-blur-xl flex items-center justify-between px-8 z-30 shadow-sm transition-premium">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
             <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-black text-sm shadow-lg shadow-indigo-900/20">D</div>
             <span className="text-sm font-black tracking-tighter text-white">Deep Search AI</span>
          </div>
          <div className="w-px h-4 bg-white/10"></div>
          <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-[10px] font-black uppercase tracking-widest text-emerald-500">{status.toUpperCase()}</span>
          </div>
          {loading && (
            <div className="flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full animate-pulse transition-premium">
              <div className="flex gap-1">
                <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce"></span>
              </div>
              <span className="text-[9px] font-black uppercase tracking-widest text-blue-400">Thinking</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-3">
          {/* Model Switcher Pill */}
          <div className="relative">
            <button 
              onClick={() => setIsSettingsOpen(!isSettingsOpen)}
              className="flex items-center gap-3 px-4 py-2 bg-white/5 border border-white/5 rounded-2xl hover:bg-white/10 transition-premium shadow-inner active:scale-95 group"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-500 group-hover:text-indigo-400 group-hover:rotate-12 transition-all"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="15" x2="23" y2="15"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="15" x2="4" y2="15"></line></svg>
              <div className="flex flex-col items-start leading-none gap-1">
                <span className="text-[9px] font-black uppercase tracking-[0.1em] text-slate-500">Neural Model</span>
                <span className="text-xs font-bold text-white tracking-tighter truncate max-w-[100px] uppercase">{globalModel}</span>
              </div>
              <svg xmlns="http://www.w3.org/2000/svg" className={`transition-transform duration-300 ${isSettingsOpen ? 'rotate-180' : ''}`} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </button>
            
            {isSettingsOpen && (
              <div className="absolute top-full right-0 mt-3 w-64 bg-[#1a1a1a] border border-white/10 rounded-[24px] shadow-premium p-2 animate-slideUp z-[60]">
                <div className="px-4 py-2 text-[10px] font-black uppercase tracking-widest text-slate-600 border-b border-white/5 mb-2">Available Intelligence</div>
                {availableModels.length === 0 ? (
                  <div className="p-4 text-xs font-bold text-red-400 animate-pulse">NO MODELS FOUND</div>
                ) : (
                  availableModels.map(m => (
                    <button
                      key={m}
                      onClick={() => { onModelChange(m); setIsSettingsOpen(false); }}
                      className={`w-full text-left px-4 py-3 rounded-2xl text-xs font-bold transition-premium flex items-center justify-between group ${globalModel === m ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
                    >
                      <span className="truncate">{m === 'auto' ? 'AUTO-ROUTER' : m}</span>
                      {globalModel === m && <div className="w-2 h-2 rounded-full bg-white"></div>}
                    </button>
                  ))
                )}
                <div className="h-px bg-white/5 my-2"></div>
                <button 
                  onClick={() => { onToggleRightPanel(); setIsSettingsOpen(false); }}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-2xl text-xs font-bold text-slate-400 hover:text-white hover:bg-white/5 transition-premium"
                >
                  Configure Local Intelligence
                </button>
              </div>
            )}
          </div>
          
          <button 
            onClick={reloadChat}
            className="p-3 text-slate-500 hover:text-white hover:bg-white/5 rounded-2xl transition-premium active:scale-95" 
            title="Purge Intelligence Session"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M3 22v-6h6"></path><path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path></svg>
          </button>
        </div>
      </div>

      {/* 2. MESSAGES AREA */}
      <div 
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 md:px-0 bg-slate-950 scroll-smooth relative"
      >
        <div className="max-w-5xl mx-auto space-y-12 py-12 pb-32">
          {messages.length === 0 && (
            <div className="h-[60vh] flex flex-col items-center justify-center text-center animate-fade-in mt-12 px-6">
               <div className="w-20 h-20 rounded-[2rem] bg-indigo-600 flex items-center justify-center text-white text-3xl font-black shadow-2xl shadow-indigo-900/40 mb-8 border-4 border-white/10 animate-pulse">D</div>
               <h1 className="text-4xl md:text-5xl font-black text-white mb-4 tracking-tight">Intelligence Reimagined.</h1>
               <p className="text-slate-500 text-lg md:text-xl font-medium max-w-xl mb-12 italic leading-relaxed">Start a session to explore local neural research, code synthesis, and global data extraction.</p>
               
               {/* 🚀 DYNAMIC TRENDING TOPICS UPGRADE */}
               <div className="w-full max-w-3xl">
                  <div className="flex items-center justify-center gap-2 mb-6">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></div>
                    <span className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Trending Intelligence</span>
                  </div>
                  <div className="flex flex-wrap justify-center gap-3">
                    {[
                      "Future of Agentic AI", "NextJS 15 Features", "Ollama Performance 2026", 
                      "Quantum Computing Basics", "Modern CSS Trends", "HuggingFace Transformers",
                      "Local LLM Benchmarks", "Deep Search Architecture"
                    ].sort(() => Math.random() - 0.5).slice(0, 5).map(topic => (
                      <button 
                        key={topic}
                        onClick={() => sendMessage(topic)}
                        className="px-6 py-3 bg-white/5 border border-white/5 rounded-2xl text-[13px] font-bold text-slate-400 hover:bg-white/10 hover:text-white hover:border-white/10 hover:scale-[1.03] active:scale-95 transition-premium shadow-inner"
                      >
                         {topic}
                      </button>
                    ))}
                  </div>
               </div>
            </div>
          )}
          {messages.map((msg, idx) => (
            <MessageBubble 
              key={idx} 
              message={msg} 
              copyToClipboard={copyToClipboard}
              isLatestAssistant={!msg.role.includes('user') && idx === messages.length - 1}
              onSaveToMemory={handleSaveToMemory}
              handleAbort={handleAbort}
              handleRegenerate={sendMessage}
              prevMessageContent={idx > 0 ? messages[idx-1].content : null}
              onPinToCanvas={onPinToCanvas}
            />
          ))}
          
          {linkResult && (
            <div className="w-full animate-fade-in-up">
              <OutputViewer data={linkResult} />
              <button onClick={() => setLinkResult(null)} className="mt-3 text-[11px] font-bold text-slate-500 hover:text-red-400 transition-premium px-3 py-1 bg-slate-800/50 rounded-lg border border-white/5">✕ Dismiss</button>
            </div>
          )}
          
          <div ref={messagesEndRef} className="h-8" />
        </div>

        {/* 🧠 DYNAMIC THINKING TRACKER (Small Box Only) */}
        {loading && currentThought.length > 0 && (
          <div className="fixed bottom-32 right-8 w-64 glass-dark border border-white/10 rounded-2xl p-4 shadow-2xl animate-fade-in-up z-40 transition-premium">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Thinking Trace</span>
              </div>
              <span className="text-[9px] font-bold text-slate-600 bg-white/5 px-2 py-0.5 rounded-md">Step {currentThought.length}</span>
            </div>
            <div className="text-[11px] font-medium text-blue-100 leading-relaxed italic truncate">
              "{currentThought[currentThought.length - 1]}"
            </div>
            <div className="mt-3 h-1 w-full bg-white/5 rounded-full overflow-hidden">
               <div className="h-full bg-blue-600 animate-loading-bar"></div>
            </div>
          </div>
        )}
      </div>

      {/* 3. INPUT AREA */}
      <div className="w-full glass-dark border-t border-white/5 shadow-premium">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <MultiInputBox
            onSend={sendMessage}
            onLinkResult={setLinkResult}
            isLoading={loading}
            mode={mode}
            onModeChange={setMode}
            model={globalModel}
            onModelChange={onModelChange}
            webMode={globalWebMode}
            setWebMode={onWebModeChange}
            availableModels={availableModels}
            onStop={handleAbort}
            onToggleRagPanel={onToggleRagPanel}
            sessionId={sessionId}
            hasMessages={messages.length > 0}
          />
        </div>
      </div>
    </div>
  );
}
