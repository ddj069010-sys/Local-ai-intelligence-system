import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ReportRenderer from './ReportRenderer';
import LinkPreview from './LinkPreview';
import MermaidRenderer from './MermaidRenderer';
import CodeBlockRenderer from './CodeBlockRenderer';
import * as Icons from 'lucide-react';

const IconMap = {
  'summary': 'FileText',
  'explanation': 'Info',
  'key points': 'ListChecks',
  'process': 'Activity',
  'comparison': 'Columns',
  'code': 'Code2',
  'architecture': 'Boxes',
  'conclusion': 'CheckCircle2',
  'objective': 'Target',
  'takeaways': 'Lightbulb',
  'primary links': 'ExternalLink',
  'solution': 'Zap',
  'proof': 'Binary',
  'data cleaning': 'Eraser',
  'legal': 'Scale',
  'risk': 'AlertTriangle',
  'threat': 'ShieldAlert',
  'career': 'Briefcase',
  'resume': 'UserSquare2',
  'sustainability': 'Leaf',
  'cultural': 'Globe2',
  'argument': 'MessageSquareQuote',
  'fallacy': 'Crosshair'
};

const SmartIcon = ({ title, className }) => {
  const cleanTitle = title.trim().toLowerCase().replace(/[^a-z0-9\s]/g, '');
  const iconName = IconMap[cleanTitle];
  if (iconName && Icons[iconName]) {
    const LucideIcon = Icons[iconName];
    return <LucideIcon className={className} size={18} />;
  }
  return null;
};

export default function MessageBubble({ message, copyToClipboard, isLatestAssistant, mode, setInput, onSaveToMemory, handleAbort, handleRegenerate, prevMessageContent, onPinToCanvas }) {
  const isUser = message.role === 'user';

  // Typing effect state
  const isStreaming = message.streaming;
  const isAgent = mode === 'agent';
  const shouldSkipTyping = !isLatestAssistant || isStreaming || isAgent;

  // Pre-process message content (Silent Filters)
  let cleanedContent = message.content || "";
  
  // 1. Silent Cleanup: Intercept open/closed <think> boxes to prevent showing raw logic
  const thinkMatch = cleanedContent.match(/<think>([\s\S]*?)<\/think>/i);
  if (thinkMatch) {
    cleanedContent = cleanedContent.replace(/<think>[\s\S]*?<\/think>/i, "").trim();
  } else {
    const openThinkMatch = cleanedContent.match(/<think>([\s\S]*)/i);
    if (openThinkMatch) {
      cleanedContent = cleanedContent.replace(/<think>[\s\S]*/i, "").trim();
    }
  }

  // 2. Silent Cleanup: Deduplicate heavily repetitive markdown headers (e.g., repeating 'Summary' twice)
  let seenHeaders = new Set();
  cleanedContent = cleanedContent.split('\n').filter(line => {
    const headerMatch = line.match(/^(###?)\s+(.*)/);
    if (headerMatch) {
      const headerTitle = headerMatch[2].trim().toLowerCase().replace(/[^a-z0-9\s]/g, ''); // strip emojis
      if (seenHeaders.has(headerTitle)) return false;
      seenHeaders.add(headerTitle);
    }
    return true;
  }).join('\n');

  const [displayedContent, setDisplayedContent] = useState(cleanedContent);
  const [feedback, setFeedback] = useState(null); // 'like' or 'dislike'

  const handleFeedback = async (type) => {
    const newFeedback = feedback === type ? null : type;
    setFeedback(newFeedback);

    if (newFeedback) {
      try {
        await fetch('http://localhost:8000/api/chat/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: message.session_id || 'unknown',
            message_content: message.content,
            is_liked: type === 'like'
          })
        });
      } catch (err) {
        console.error("Failed to send feedback:", err);
      }
    }
  };

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([message.content], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `DeepSearch_Response_${new Date().getTime()}.txt`;
    document.body.appendChild(element);
    element.click();
  };

  useEffect(() => {
    if (shouldSkipTyping) {
      setDisplayedContent(cleanedContent);
      return;
    }

    // Animate typing effect
    setDisplayedContent('');
    let i = 0;
    const interval = setInterval(() => {
      if (i < cleanedContent.length) {
        setDisplayedContent(cleanedContent.slice(0, i + 1));
        i += 15;
      } else {
        clearInterval(interval);
        setDisplayedContent(cleanedContent);
      }
    }, 15);

  }, [cleanedContent, isLatestAssistant, isStreaming, isAgent, shouldSkipTyping]);

  const [isPinned, setIsPinned] = useState(false);
  const [isStarred, setIsStarred] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Auto-collapse long inactive messages
  useEffect(() => {
    if (!isStreaming && cleanedContent.length > 1500) {
      setIsCollapsed(true);
    } else {
      setIsCollapsed(false);
    }
  }, [isStreaming, cleanedContent.length]);

  const toggleSpeak = () => {
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(message.content);
    utterance.onend = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
    setIsSpeaking(true);
  };

  useEffect(() => {
    return () => window.speechSynthesis.cancel();
  }, []);

  if (message.role === 'system' || message.role === 'status') {
    return (
      <div className="flex justify-center my-4 animate-fade-in-up">
        <span className="text-xs text-slate-400 bg-slate-800/80 px-4 py-1.5 rounded-full border border-slate-700">{message.content}</span>
      </div>
    );
  }

  // Intercept the failure message
  const isFailure = cleanedContent.includes("Insufficient reliable information available");

  if (isFailure && !isUser) {
    return (
      <div className={`flex flex-col max-w-full md:max-w-[85%] animate-fade-in-up self-start bg-slate-800/50 border border-red-900/50 text-slate-100 py-4 px-5 rounded-2xl rounded-tl-sm shadow-md`}>
        <div className="flex items-center gap-2 mb-3 text-red-400 font-semibold">
          <span>⚠️</span> Couldn't find strong sources for this query.
        </div>
        <div className="text-sm text-slate-300 mb-2">Suggestions:</div>
        <ul className="list-disc pl-5 text-sm text-slate-400 space-y-1 mb-4">
          <li>Try a broader topic</li>
          <li>Rephrase your request</li>
          <li>Ask for a simpler explanation</li>
        </ul>
        {message.onRetry && (
          <button
            onClick={message.onRetry}
            className="self-start text-sm bg-slate-700 hover:bg-slate-600 text-slate-200 py-1.5 px-4 rounded-lg transition-colors border border-slate-600 focus:outline-none focus:ring-2 focus:ring-slate-500"
          >
            🔄 Retry Request
          </button>
        )}
      </div>
    );
  }

  // Check if we should use the Deep Search Report format
  const isReport = !isUser && (mode === 'research' || mode === 'deep') && displayedContent.length > 200;

  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <div
      className={`flex flex-col w-full animate-fade-in-up ${isUser ? 'items-end mb-4' : 'items-start py-2 mb-6'}`}
      onMouseLeave={() => !isMenuOpen && setIsMenuOpen(false)}
    >

      {isUser ? (
        <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-3xl rounded-tr-sm text-white px-6 py-4 shadow-xl whitespace-pre-wrap leading-relaxed text-[18px] max-w-[85%] md:max-w-[60%] border border-white/10">
          {message.content}
        </div>
      ) : (
        <div className="flex flex-col w-full md:max-w-[90%]">
          {/* Main Content Area */}
          <div className="flex flex-col group/msg relative">
            {/* 🧠 THOUGHT PROCESS SECTION (User Request) */}
            {message.thoughts && message.thoughts.length > 0 && (
              <div className="mb-4 self-start w-full md:max-w-[700px]">
                <details className="group/thought bg-white/[0.03] border border-white/5 rounded-2xl overflow-hidden transition-premium hover:bg-white/[0.05]">
                  <summary className="flex items-center justify-between px-5 py-3 cursor-pointer list-none">
                    <div className="flex items-center gap-3">
                      <div className="flex -space-x-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse delay-100"></div>
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-300 animate-pulse delay-200"></div>
                      </div>
                      <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 group-hover/thought:text-blue-400 transition-colors">
                        View Intelligence Trace
                      </span>
                    </div>
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-slate-600 transition-transform group-open/thought:rotate-180" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                  </summary>
                  <div className="px-6 pb-6 space-y-6 border-t border-white/5 bg-black/60 backdrop-blur-xl mt-1">
                    <div className="pt-6">
                      {/* Premium Thinking Trace Header */}
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)] animate-pulse"></div>
                          <span className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-200">Thinking Trace</span>
                        </div>
                        <div className="bg-white/5 px-3 py-1 rounded-full border border-white/10">
                          <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Step {message.thoughts.length}</span>
                        </div>
                      </div>

                      {/* Active Thought Highlight */}
                      <div className="bg-blue-600/5 border border-blue-500/10 rounded-2xl p-5 mb-6 shadow-inner transition-premium hover:bg-blue-600/10">
                        <div className="text-[13px] font-medium text-blue-100 leading-relaxed italic">
                          "{message.thoughts[message.thoughts.length - 1]}"
                        </div>
                        <div className="mt-4 h-1.5 w-full bg-slate-800 rounded-full overflow-hidden shadow-inner relative">
                          <div className="absolute top-0 left-0 h-full bg-blue-600 shadow-[0_0_12px_rgba(37,99,235,0.6)] animate-loading-bar w-[60%]"></div>
                        </div>
                      </div>

                      <div className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-4 flex items-center gap-2">
                        <div className="w-4 h-px bg-white/5"></div>
                        Neural Chain history
                      </div>

                      <div className="space-y-3.5 pl-2 border-l border-white/5 max-h-[300px] overflow-y-auto scrollbar-none">
                        {message.thoughts.map((t, i) => {
                          const isLatest = i === message.thoughts.length - 1;
                          const isExecution = t.includes("Executing") || t.includes("Processing") || t.includes("Fetching");
                          return (
                            <div key={i} className={`flex gap-4 animate-fade-in transition-premium ${isLatest ? 'opacity-100' : 'opacity-40 hover:opacity-100'}`} style={{ animationDelay: `${i * 30}ms` }}>
                              <span className={`font-mono text-[9px] mt-1 ${isExecution ? 'text-blue-400 font-black' : 'text-slate-600'}`}>
                                {String(i + 1).padStart(2, '0')}
                              </span>
                              <div className="flex flex-col flex-1">
                                <p className={`text-[12px] font-medium leading-relaxed ${isExecution ? 'text-blue-100' : 'text-slate-400'}`}>
                                  {t}
                                </p>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="pt-4 flex items-center justify-between border-t border-white/5 mt-4 opacity-50">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                        <span className="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em]">Neural Sequence Active</span>
                      </div>
                      <span className="text-[9px] font-mono text-slate-700 tracking-tighter uppercase">Trace Engine v2.4</span>
                    </div>
                  </div>
                </details>
              </div>
            )}

            {mode === 'deep' && !isUser && (
              <div className="flex items-center gap-2 mb-4 text-blue-400 font-bold tracking-tight text-xs uppercase bg-blue-500/5 self-start px-3 py-1 rounded-full border border-blue-500/20 shadow-sm animate-pulse">
                <span>🔎</span> Deep Research Report
              </div>
            )}

            {isReport ? (
              <div className={isCollapsed ? 'max-h-[600px] overflow-hidden relative pb-12' : 'relative'}>
                <ReportRenderer content={isCollapsed ? displayedContent.slice(0, 1200) + "..." : displayedContent} />
                {isCollapsed && (
                  <div className="absolute bottom-0 left-0 w-full h-40 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent flex items-end justify-center pb-8 z-10">
                    <button
                      onClick={() => setIsCollapsed(false)}
                      className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-black uppercase tracking-[0.2em] rounded-full shadow-2xl shadow-indigo-900/40 transition-all active:scale-95 border border-white/20 animate-bounce-subtle"
                    >
                      Expand Deep Intelligence Report
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className={`bg-transparent text-slate-200 text-[18px] leading-[1.7] max-w-[850px] w-full transition-premium ${isCollapsed ? 'max-h-[600px] overflow-hidden relative pb-12' : ''}`}>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ node, ...props }) => <h1 className="text-2xl font-black text-white mb-6 mt-4 tracking-tight flex items-center gap-3" {...props} />,
                    h2: ({ node, ...props }) => {
                      const text = String(props.children);
                      return (
                        <h2 className="text-xl font-black text-blue-400 mt-8 mb-4 border-l-4 border-blue-600 pl-4 flex items-center gap-3 group/h2" {...props}>
                          <SmartIcon title={text} className="text-blue-500 group-hover/h2:scale-110 transition-transform" />
                          {props.children}
                        </h2>
                      );
                    },
                    h3: ({ node, ...props }) => {
                      const text = String(props.children);
                      return (
                        <h3 className="text-lg font-bold text-emerald-400 mt-6 mb-2 flex items-center gap-3 group/h3" {...props}>
                          <SmartIcon title={text} className="text-emerald-500 group-hover/h3:scale-110 transition-transform" />
                          {props.children}
                        </h3>
                      );
                    },
                    p: ({ node, ...props }) => <p className="mb-5 block font-medium opacity-90" {...props} />,
                    ul: ({ node, ...props }) => <ul className="list-disc pl-6 mb-6 space-y-3 block" {...props} />,
                    ol: ({ node, ...props }) => <ol className="list-decimal pl-6 mb-6 space-y-3 block" {...props} />,
                    table: ({ node, ...props }) => (
                      <div className="overflow-x-auto my-8 rounded-2xl border border-white/5 shadow-premium glass hover:border-blue-500/30 hover:-translate-y-1 hover:shadow-blue-500/10 transition-premium group/bento">
                        <table className="w-full text-left border-collapse" {...props} />
                      </div>
                    ),
                    thead: ({ node, ...props }) => <thead className="bg-white/5 border-b border-white/10" {...props} />,
                    th: ({ node, ...props }) => <th className="px-5 py-4 text-[10px] font-black uppercase tracking-widest text-blue-500" {...props} />,
                    td: ({ node, ...props }) => <td className="px-5 py-4 text-sm border-b border-white/5 text-slate-400 font-medium" {...props} />,
                    tr: ({ node, ...props }) => <tr className="hover:bg-white/[0.02] transition-premium" {...props} />,
                    code: ({ node, inline, className, ...props }) => {
                      const match = /language-(\w+)/.exec(className || '');
                      if (!inline && match && match[1] === 'mermaid') {
                        return <MermaidRenderer chart={String(props.children).replace(/\n$/, '')} />;
                      }
                      return inline ?
                        <code className="bg-slate-800 text-blue-400 px-1.5 py-0.5 rounded-md text-[13px] font-mono border border-white/5" {...props} /> :
                        <CodeBlockRenderer language={match ? match[1] : ''} value={String(props.children).replace(/\n$/, '')} />;
                    },
                    blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-blue-500/80 pl-6 py-4 my-6 italic bg-blue-500/5 rounded-r-2xl text-slate-400 font-medium" {...props} />,
                    a: ({ node, ...props }) => <LinkPreview {...props} />
                  }}
                >
                  {isCollapsed ? displayedContent.split('\n\n👉')[0].slice(0, 1200) + "..." : displayedContent.split('\n\n👉')[0]}
                </ReactMarkdown>

                {/* 🎯 GPT FOLLOW-UP COMPONENT */}
                {displayedContent.includes('👉') && (
                  <div className="mt-8 animate-fade-in-up">
                    <div className="flex items-center gap-2 mb-3 text-[10px] font-black text-blue-500/60 uppercase tracking-[0.2em] px-1">
                      Neural suggestion
                    </div>
                    <button 
                      onClick={() => setInput(displayedContent.split('👉')[1].replace(/\*/g, '').trim())}
                      className="group flex items-center gap-3 bg-white/5 hover:bg-blue-500/10 border border-white/10 hover:border-blue-500/30 p-4 rounded-2xl transition-all active:scale-[0.98] text-left w-full shadow-lg"
                    >
                      <span className="text-lg group-hover:scale-125 transition-transform">👉</span>
                      <span className="text-[14px] font-bold text-slate-200 group-hover:text-blue-200 transition-colors">
                        {displayedContent.split('👉')[1].replace(/\*/g, '').trim()}
                      </span>
                    </button>
                  </div>
                )}

                {isCollapsed && (
                  <div className="absolute bottom-0 left-0 w-full h-40 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent flex items-end justify-center pb-8 z-10">
                    <button
                      onClick={() => setIsCollapsed(false)}
                      className="px-8 py-3 bg-white/5 hover:bg-white/10 text-slate-300 text-[11px] font-black uppercase tracking-[0.2em] rounded-full shadow-2xl transition-all active:scale-95 border border-white/10 hover:text-white"
                    >
                      Read Full Content
                    </button>
                  </div>
                )}

                {/* 🎥 MULTIMODAL SCENE BREAKDOWN (Sight & Sound) */}
                {message.scenes && message.scenes.length > 0 && (
                  <div className="mt-8 mb-4">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-1.5 h-6 bg-blue-500 rounded-full shadow-[0_0_12px_rgba(59,130,246,0.6)]"></div>
                      <span className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-200">Temporal Scene Breakdown</span>
                    </div>
                    <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-premium">
                      {message.scenes.map((scene, idx) => (
                        <div key={idx} className="flex-shrink-0 w-[280px] bg-white/[0.03] border border-white/5 rounded-2xl p-4 transition-premium hover:bg-white/5 hover:border-blue-500/20 group/scene">
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-[10px] font-mono text-blue-400 bg-blue-400/10 px-2 py-0.5 rounded-full border border-blue-400/20">
                              {Math.floor(scene.timestamp / 60)}:{(scene.timestamp % 60).toString().padStart(2, '0')}
                            </span>
                            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                          </div>
                          <p className="text-[12px] font-medium text-slate-200 leading-relaxed mb-3 line-clamp-2">
                            {scene.visual}
                          </p>
                          <div className="text-[11px] text-slate-500 italic bg-black/40 p-2.5 rounded-xl border border-white/[0.02]">
                            "{scene.dialogue || "Ambient sequence"}"
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 🧠 KNOWLEDGE GRAPH ENTITIES */}
                {message.kg_entities && message.kg_entities.length > 0 && (
                  <div className="mt-6 mb-2">
                    <div className="text-[9px] font-black text-slate-600 uppercase tracking-widest mb-3 flex items-center gap-2">
                      <div className="w-4 h-px bg-white/5"></div>
                      Intelligence Mapping (KG)
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {message.kg_entities.map((ent, idx) => (
                        <div key={idx} className="px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-[11px] font-bold text-slate-400 transition-premium hover:border-emerald-500/40 hover:text-emerald-400 cursor-help flex items-center gap-2">
                          <span className="w-1 h-1 rounded-full bg-slate-600"></span>
                          {ent}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Execution Results Rendering */}
                {message.executionResults && message.executionResults.length > 0 && (
                  <div className="mt-8 space-y-6">
                    {message.executionResults.map((res, idx) => (
                      <div key={idx} className="bg-slate-950 rounded-2xl border border-white/5 overflow-hidden shadow-premium animate-fade-in transition-premium hover:border-blue-500/30">
                        <div className="bg-white/5 px-6 py-3 flex items-center justify-between border-b border-white/5">
                          <div className="flex items-center gap-3 text-blue-400 font-black text-[11px] uppercase tracking-[0.2em]">
                            <span className="p-1 bg-blue-500/10 rounded">⚙️</span> Executed ({res.language})
                          </div>
                          <div className="text-[10px] text-slate-600 font-mono font-bold tracking-tighter">PID: {Math.floor(Math.random() * 9000) + 1000} • READY</div>
                        </div>
                        <div className="p-6 space-y-4">
                          {res.output && (
                            <div>
                              <div className="text-[10px] text-slate-600 uppercase font-black mb-2 tracking-widest">Standard Output</div>
                              <pre className="text-emerald-400 text-[12.5px] font-mono bg-emerald-500/5 p-4 rounded-xl overflow-x-auto border border-emerald-500/10 whitespace-pre-wrap leading-relaxed shadow-inner">{res.output}</pre>
                            </div>
                          )}
                          {res.error && (
                            <div>
                              <div className="text-[10px] text-red-400 uppercase font-black mb-2 tracking-widest">Error Log</div>
                              <pre className="text-red-400 text-[12.5px] font-mono bg-red-500/5 p-4 rounded-xl overflow-x-auto border border-red-500/20 whitespace-pre-wrap leading-relaxed shadow-inner">{res.error}</pre>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* File Results Rendering */}
                {message.fileResults && message.fileResults.length > 0 && (
                  <div className="mt-8 space-y-6">
                    {message.fileResults.map((res, idx) => (
                      <div key={idx} className="bg-slate-950 rounded-2xl border border-white/5 overflow-hidden shadow-premium animate-fade-in border-l-4 border-emerald-500 transition-premium hover:border-emerald-500/30">
                        <div className="bg-white/5 px-6 py-3 flex items-center justify-between border-b border-white/5">
                          <div className="flex items-center gap-3 text-emerald-400 font-black text-[11px] uppercase tracking-[0.2em]">
                            <span className="p-1 bg-emerald-500/10 rounded">📁</span> FileSystem
                          </div>
                          <div className="text-[10px] text-slate-600 font-mono font-bold italic truncate ml-4">{res.operation}: {res.file || "workspace"}</div>
                        </div>
                        <div className="p-6">
                          <div className="text-slate-400 text-[12.5px] font-mono bg-slate-900/50 p-4 rounded-xl border border-white/5 whitespace-pre-wrap leading-relaxed shadow-inner">
                            {res.result}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {isLatestAssistant && displayedContent.length < message.content.length && (
                  <div className="flex items-center gap-3 mt-4 animate-fade-in">
                    <span className="inline-block w-3 h-5 bg-blue-500 animate-pulse align-middle rounded-sm shadow-[0_0_8px_rgba(59,130,246,0.5)]"></span>
                    <button
                      onClick={handleAbort}
                      className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-[10px] font-black uppercase tracking-widest rounded-lg border border-red-500/20 transition-premium group/stop"
                    >
                      <div className="w-2 h-2 bg-red-500 rounded-sm group-hover/stop:scale-125 transition-transform" />
                      Stop Intelligence Synthesis
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 🔘 PREMIUM CHATBOT ACTION BAR */}
          {!isUser && !isStreaming && (
            <div className="mt-4 flex items-center gap-1 opacity-100 transition-premium animate-fade-in-up">
              <button
                className={`p-2 rounded-lg transition-premium ${feedback === 'like' ? 'text-emerald-400 bg-emerald-400/10' : 'text-slate-500 hover:text-emerald-400 hover:bg-emerald-400/5'}`}
                onClick={() => handleFeedback('like')}
                title="Like Response"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={feedback === 'like' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
              </button>

              <button
                className={`p-2 rounded-lg transition-premium ${feedback === 'dislike' ? 'text-red-400 bg-red-400/10' : 'text-slate-500 hover:text-red-400 hover:bg-red-400/5'}`}
                onClick={() => handleFeedback('dislike')}
                title="Dislike Response"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={feedback === 'dislike' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path></svg>
              </button>

              <button
                className={`p-2 rounded-lg transition-premium ${isSpeaking ? 'text-emerald-400 bg-emerald-400/10 animate-pulse' : 'text-slate-500 hover:text-emerald-400 hover:bg-emerald-400/5'}`}
                onClick={toggleSpeak}
                title={isSpeaking ? "Stop Reading" : "Read Aloud"}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={isSpeaking ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
              </button>

              <div className="w-px h-3 bg-white/10 mx-1"></div>

              <button
                className="p-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-premium"
                onClick={() => copyToClipboard(message.content)}
                title="Copy Message"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              </button>

              <button
                className="p-2 rounded-lg text-slate-500 hover:text-blue-400 hover:bg-blue-400/10 transition-premium"
                onClick={() => prevMessageContent && handleRegenerate(prevMessageContent)}
                title="Regenerate"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M3 22v-6h6"></path><path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path></svg>
              </button>

              <button
                className="p-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-premium"
                onClick={() => { copyToClipboard(`Intelligence Report: ${message.content}`); alert('Formatted output copied to clipboard!'); }}
                title="Share Response"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path><polyline points="16 6 12 2 8 6"></polyline><line x1="12" y1="2" x2="12" y2="15"></line></svg>
              </button>

              <button
                className="p-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-premium"
                onClick={handleDownload}
                title="Download Response"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              </button>

              <button
                className="p-2 rounded-lg text-slate-500 hover:text-blue-400 hover:bg-blue-400/10 transition-premium"
                onClick={() => onPinToCanvas(message.content.split('\n')[0].replace(/#/g, '').trim() || 'Intelligence Artifact', message.content)}
                title="Pin to Canvas"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path><polyline points="10 17 15 12 10 7"></polyline><line x1="15" y1="12" x2="3" y2="12"></line></svg>
              </button>

              <div className="ml-auto flex items-center gap-4">
                {message.generationTime && (
                  <div className="flex items-center gap-1.5">
                    <div className="text-[9px] font-black px-2 py-1 rounded-lg border bg-blue-500/10 border-blue-500/20 flex items-center gap-1.5 text-blue-400 tracking-widest uppercase transition-premium hover:bg-blue-500/20" title="Token Generation Velocity">
                      ⚡ {message.tokensPerSecond || 0} t/s
                    </div>
                    <div className="text-[9px] font-black px-2 py-1 rounded-lg border bg-slate-900/50 border-white/10 flex items-center gap-1.5 text-slate-400 tracking-widest uppercase" title="Model Used">
                      🧠 {message.model || 'Local Model'}
                    </div>
                    <div className="text-[9px] font-black px-2 py-1 rounded-lg border bg-slate-950/30 border-white/5 flex items-center gap-1.5 text-slate-500 tracking-widest uppercase" title="Latency">
                      ⏱ {message.generationTime}s
                    </div>
                  </div>
                )}
                {message.content.includes("Confidence:") && (
                  <div className="text-[9px] font-black px-2 py-1 rounded-lg border bg-slate-950/30 border-white/5 flex items-center gap-1.5 text-slate-500 tracking-widest uppercase transition-premium hover:border-emerald-500/30 group/confidence">
                    {message.content.includes("High") ? <span className="text-emerald-500/70 flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] group-hover/confidence:animate-ping"></span> Verified Result</span> :
                      message.content.includes("Medium") ? <span className="text-yellow-500/70 flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-yellow-500"></span> Probable Signal</span> :
                        <span className="text-red-500/70 flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-red-500"></span> Unverified Logic</span>}
                  </div>
                )}

                <button
                  onClick={() => setIsMenuOpen(!isMenuOpen)}
                  className={`p-2 rounded-lg transition-premium ${isMenuOpen ? 'text-white bg-white/10' : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="1"></circle><circle cx="19" cy="12" r="1"></circle><circle cx="5" cy="12" r="1"></circle></svg>
                </button>
              </div>
            </div>
          )}

          {/* Action Bar (Legacy hidden version - removing to avoid duplication) */}
          <div className="mt-8 flex items-center group/msg-actions overflow-visible relative">
            <div className="hidden group-hover/msg:flex bg-slate-900/80 backdrop-blur-xl rounded-2xl p-1.5 border border-white/10 shadow-premium opacity-0 group-hover/msg:opacity-100 transition-premium">
              {isStreaming ? (
                <button
                  className="p-3 rounded-xl text-red-400 hover:bg-red-500/10 transition-premium animate-pulse flex items-center gap-2"
                  onClick={handleAbort}
                  title="Stop Generation"
                >
                  <div className="w-3 h-3 bg-red-500 rounded-sm" />
                  <span className="text-[10px] font-black uppercase tracking-tight">Stop</span>
                </button>
              ) : (
                <>
                  <button
                    className={`p-3 rounded-xl transition-premium ${feedback === 'like' ? 'text-emerald-400 bg-emerald-400/10' : 'text-slate-400 hover:text-emerald-400 hover:bg-emerald-400/5'}`}
                    onClick={() => handleFeedback('like')}
                    title="Like Response"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill={feedback === 'like' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
                  </button>

                  <button
                    className={`p-3 rounded-xl transition-premium ${feedback === 'dislike' ? 'text-red-400 bg-red-400/10' : 'text-slate-400 hover:text-red-400 hover:bg-red-400/5'}`}
                    onClick={() => handleFeedback('dislike')}
                    title="Dislike Response"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill={feedback === 'dislike' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path></svg>
                  </button>

                  <button
                    className="p-3 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-premium"
                    onClick={handleDownload}
                    title="Download Response"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                  </button>

                  <button
                    className="p-3 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-premium"
                    onClick={() => copyToClipboard(message.content)}
                    title="Copy Message"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                  </button>

                  <button
                    className="p-3 rounded-xl text-slate-400 hover:text-blue-400 hover:bg-blue-400/10 transition-premium"
                    onClick={() => prevMessageContent && handleRegenerate(prevMessageContent)}
                    title="Regenerate"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M3 22v-6h6"></path><path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path></svg>
                  </button>

                  <button
                    className="p-3 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-premium"
                    onClick={() => { copyToClipboard(`Intelligence Report: ${message.content}`); alert('Formatted output copied to clipboard!'); }}
                    title="Share Response"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path><polyline points="16 6 12 2 8 6"></polyline><line x1="12" y1="2" x2="12" y2="15"></line></svg>
                  </button>
                </>
              )}

              {/* Dropdown Menu (⋯) - CLICK TO TOGGLE */}
              <div className="relative group/menu">
                <button
                  onClick={() => setIsMenuOpen(!isMenuOpen)}
                  className={`p-3 rounded-xl transition-premium ${isMenuOpen ? 'text-white bg-white/10' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="1"></circle><circle cx="19" cy="12" r="1"></circle><circle cx="5" cy="12" r="1"></circle></svg>
                </button>

                {isMenuOpen && (
                  <div className="absolute bottom-full right-0 mb-3 w-56 glass shadow-premium rounded-2xl border border-white/10 p-2 animate-fade-in-up z-50">
                    <button
                      onClick={() => { setIsPinned(!isPinned); setIsMenuOpen(false); }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-premium ${isPinned ? 'text-blue-400 bg-blue-400/10' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={isPinned ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l2-1.14"></path><line x1="12" y1="22" x2="12" y2="12"></line></svg>
                      {isPinned ? 'Pinned' : 'Pin Message'}
                    </button>

                    <button
                      onClick={() => { setIsStarred(!isStarred); setIsMenuOpen(false); }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-premium ${isStarred ? 'text-yellow-400 bg-yellow-400/10' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={isStarred ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                      {isStarred ? 'Important' : 'Mark Important'}
                    </button>

                    <button
                      onClick={() => { toggleSpeak(); setIsMenuOpen(false); }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-premium ${isSpeaking ? 'text-emerald-400 bg-emerald-400/10' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
                      {isSpeaking ? 'Reading...' : 'Read Aloud'}
                    </button>

                    <button
                      className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold text-slate-400 hover:text-white hover:bg-white/5 transition-premium"
                      onClick={() => { onSaveToMemory(message.content); setIsMenuOpen(false); }}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline></svg>
                      Add to Memorypool
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="ml-auto flex items-center gap-2">
              {message.generationTime && (
                <div className="text-[10px] font-black px-3 py-2 rounded-xl border bg-slate-950/50 border-white/5 flex items-center gap-2 shadow-premium text-slate-400 tracking-widest uppercase" title="Generation Time">
                  ⏱ {message.generationTime}s
                </div>
              )}
              {message.content.includes("Confidence:") && (
                <div className="text-[10px] font-black px-3 py-2 rounded-xl border bg-slate-950/50 border-white/5 flex items-center gap-2 shadow-premium text-slate-400 tracking-widest uppercase">
                  {message.content.includes("High") ? <span className="text-emerald-500 flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Verified</span> :
                    message.content.includes("Medium") ? <span className="text-yellow-500 flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-yellow-500"></span> Probable</span> :
                      <span className="text-red-500 flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-red-500"></span> Unverified</span>}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
