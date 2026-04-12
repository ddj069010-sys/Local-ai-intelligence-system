import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';
import InputBox from './InputBox';
import MessageBubble from './MessageBubble';
import LoaderStatus from './LoaderStatus';
import { MODE_CONFIG } from '../constants/modes';

const API_BASE = 'http://localhost:8000';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [model, setModel] = useState('gemma3:4b');
  const [mode, setMode] = useState('chat');
  const [loading, setLoading] = useState(false);
  const [currentThought, setCurrentThought] = useState([]);
  const [sessionId, setSessionId] = useState('');

  // Initialize Session ID
  useEffect(() => {
    const savedSession = localStorage.getItem('chat_session_id');
    if (savedSession) {
      setSessionId(savedSession);
    } else {
      const newSession = `sess_${Math.random().toString(36).substring(2, 11)}`;
      localStorage.setItem('chat_session_id', newSession);
      setSessionId(newSession);
    }
  }, []);

  const currentMode = MODE_CONFIG[mode] || MODE_CONFIG['chat'];

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    const newMsg = { role: 'user', content: input };
    const updatedMsgs = [...messages, newMsg];
    setMessages(updatedMsgs);
    setInput('');
    setLoading(true);
    setCurrentThought([]);

    try {
      const res = await fetch(`${API_BASE}/chat_stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          model, 
          mode, 
          messages: updatedMsgs,
          session_id: sessionId 
        })
      });

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let aiContent = "";
      let metadata = {};
      let thoughts = [];
      let scenes = [];
      let executionResults = [];
      let fileResults = [];
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6).trim();
            if (dataStr) {
              try {
                const data = JSON.parse(dataStr);
                if (data.type === 'thought') {
                  // Gap 2 Fix: Dedup guard — SSE chunks can emit same event twice at byte boundaries
                  if (!thoughts.includes(data.text)) {
                    thoughts.push(data.text);
                    setCurrentThought(prev => [...prev, data.text]);
                  }
                } else if (data.type === 'message') {
                  aiContent += data.text;
                  setMessages(prev => {
                    const lastMsg = prev[prev.length - 1];
                    if (lastMsg && lastMsg.role === 'assistant') {
                      return [...prev.slice(0, -1), { ...lastMsg, content: aiContent }];
                    } else {
                      return [...prev, { role: 'assistant', content: aiContent, thoughts }];
                    }
                  });
                } else if (data.type === 'metadata') {
                  metadata = { ...metadata, ...data.data };
                } else if (data.type === 'execution_result') {
                  executionResults.push(data);
                } else if (data.type === 'file_result') {
                  fileResults.push(data);
                }
              } catch (e) {
                console.error("JSON parse error on stream", e);
              }
            }
          }
        }
      }
      
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.role === 'assistant') {
          return [...prev.slice(0, -1), { 
            ...lastMsg, 
            content: aiContent, 
            thoughts, 
            ...metadata,
            executionResults,
            fileResults
          }];
        }
        return prev;
      });

    } catch (err) {
      console.error(err);
      setMessages([...updatedMsgs, { role: 'assistant', content: 'Error: Could not reach backend or pipeline failed.' }]);
    }
    setLoading(false);
    setCurrentThought([]);
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-200 overflow-hidden relative">
      {/* Header */}
      <header className="px-6 py-4 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md flex justify-between items-center z-20">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-2">
            AI SYSTEMS <span className="text-slate-500 font-medium">/</span> 
            <span className={mode === 'deep' ? 'text-blue-400' : mode === 'fast-web' ? 'text-yellow-400' : 'text-emerald-400'}>
              {currentMode.title.toUpperCase()}
            </span>
          </h1>
        </div>
        
        <div className="flex items-center gap-3">
          <select 
            value={model} 
            onChange={(e) => setModel(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-[11px] font-bold text-slate-300 py-1.5 px-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/40 appearance-none cursor-pointer hover:bg-slate-750 transition-colors"
          >
            <option value="llama3.1:8b">llama3.1:8b</option>
            <option value="dolphin3:8b">dolphin3:8b</option>
            <option value="deepseek-r1:32b">deepseek-r1:32b</option>
            <option value="gemma3:4b">gemma3:4b</option>
            <option value="qwen3:14b">qwen3:14b</option>
          </select>
          <button 
            onClick={() => {
              setMessages([]);
              const newSession = `sess_${Math.random().toString(36).substring(2, 11)}`;
              localStorage.setItem('chat_session_id', newSession);
              setSessionId(newSession);
            }}
            className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-all tooltip"
            title="New Session"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"></path><path d="M12 5v14"></path></svg>
          </button>
        </div>
      </header>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 md:px-6 py-6 space-y-6 scroll-smooth scrollbar-thin scrollbar-thumb-slate-800">
        <div className="max-w-5xl mx-auto w-full flex flex-col gap-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center py-20 text-center animate-fade-in">
              <div className="w-16 h-16 bg-blue-600/10 rounded-3xl flex items-center justify-center mb-6 border border-blue-500/20 shadow-lg shadow-blue-500/5">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-500"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">How can I help you today?</h2>
              <p className="text-slate-400 text-sm max-w-sm mb-10 leading-relaxed">
                Select a specialized mode or just start typing to begin your research journey.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
                {[
                  { m: "compare", q: "Compare Tesla vs BYD" },
                  { m: "explain", q: "Explain quantum computing simply" },
                  { m: "fast-web", q: "What are the latest AI news?" },
                  { m: "code", q: "Create a Python script for data scraping" }
                ].map((s, i) => (
                  <button 
                    key={i}
                    onClick={() => {
                      setMode(s.m);
                      setInput(s.q);
                    }}
                    className="flex items-center gap-4 p-4 bg-slate-900 border border-slate-800 rounded-2xl hover:border-blue-500/50 hover:bg-slate-800/80 transition-all text-left group shadow-sm"
                  >
                    <div className="p-2 bg-slate-800 rounded-lg group-hover:bg-blue-600/20 group-hover:text-blue-400 transition-colors">
                      <span className="text-lg">{MODE_CONFIG[s.m].title.split(' ')[0]}</span>
                    </div>
                    <div>
                      <div className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-0.5">{MODE_CONFIG[s.m].title.split(' ').slice(1).join(' ')}</div>
                      <div className="text-sm font-medium text-slate-300">{s.q}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m, i) => (
              <MessageBubble 
                key={i} 
                message={m} 
                copyToClipboard={copyToClipboard}
                isLatestAssistant={i === messages.length - 1 && m.role === 'assistant'}
                mode={mode}
                setInput={setInput}
              />
            ))
          )}
          
          {loading && (
            <LoaderStatus currentThought={currentThought} />
          )}
        </div>
      </div>

      {/* Input */}
      <InputBox 
        input={input}
        setInput={setInput}
        sendMessage={sendMessage}
        loading={loading}
        mode={mode}
        setMode={setMode}
      />
    </div>
  );
}
