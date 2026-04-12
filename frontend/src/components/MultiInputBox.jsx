import React, { useState, useRef, useCallback, useEffect } from 'react';
import { 
  Plus, Mic, X, FileText, Film, Music, 
  Upload, Image, Lightbulb, Zap, ChevronRight, 
  Search, GraduationCap, Layout, Github, 
  ArrowUp, Cpu, Globe, Code, MessageSquare, Edit, 
  Layers, Repeat, Languages, BarChart2, 
  Shield, Map, Terminal, Brain, Link as LinkIcon, Paperclip
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const FILE_ICONS = {
  video: <Film size={14} />,
  audio: <Music size={14} />,
  document: <FileText size={14} />,
};

const FILE_COLORS = {
  video: '#a855f7',
  audio: '#06b6d4',
  document: '#f59e0b',
};

const MultiInputBox = ({ 
  onSend, 
  onLinkResult, 
  isLoading, 
  mode: intelligenceMode, 
  onModeChange,
  model,
  onModelChange,
  availableModels = [],
  webMode,
  setWebMode,
  onStop,
  onToggleRagPanel,
  sessionId
}) => {
  const [text, setText] = useState('');
  const [inputType, setInputType] = useState('text');
  const [dragOver, setDragOver] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileType, setFileType] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [interimText, setInterimText] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isPlusMenuOpen, setIsPlusMenuOpen] = useState(false);
  const [activeSubMenuId, setActiveSubMenuId] = useState(null);
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
  const [speedMode, setSpeedMode] = useState('auto'); // auto, fast, thinking
  const [deepSearch, setDeepSearch] = useState(false);
  const [sandboxMode, setSandboxMode] = useState(false);
  const [memorySync, setMemorySync] = useState(true);
  const [concentratedMode, setConcentratedMode] = useState(false);
  
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);
  const menuRef = useRef(null);
  const speculationTimeoutRef = useRef(null);

  // 🌩️ Speculative Pre-fetching: Prime the RAG & Memory cache while typing
  const triggerSpeculation = useCallback(async (query) => {
    if (!query || query.length < 10) return;
    try {
      await fetch(`${API_BASE}/rag/speculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query, top_k: 5 })
      });
    } catch (e) {
      console.debug("Speculation silent fail", e);
    }
  }, []);

  const onInputChange = (e) => {
    const val = e.target.value;
    setText(val);
    
    // Debounce speculation for performance
    if (speculationTimeoutRef.current) clearTimeout(speculationTimeoutRef.current);
    speculationTimeoutRef.current = setTimeout(() => {
      triggerSpeculation(val);
    }, 800);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsPlusMenuOpen(false);
        setActiveSubMenuId(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const detectFileType = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    if (['mp4', 'mkv', 'avi', 'mov', 'webm'].includes(ext)) return 'video';
    if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'].includes(ext)) return 'audio';
    if (['pdf', 'docx', 'doc', 'txt', 'md'].includes(ext)) return 'document';
    return 'unknown';
  };

  const handleFileSelect = (file) => {
    if (!file) return;
    const type = detectFileType(file.name);
    setUploadedFile(file);
    setFileType(type);
    setInputType('file');
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleTextareaDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      handleFileSelect(file);
      // Auto-trigger upload logic for immediate attachment
      handleDirectUpload(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const modeThemes = {
    'chat': { color: '#10b981', glow: 'shadow-emerald-500/10', border: 'border-emerald-500/30' },
    'direct': { color: '#10b981', glow: 'shadow-emerald-500/10', border: 'border-emerald-500/30' },
    'deep': { color: '#6366f1', glow: 'shadow-indigo-500/10', border: 'border-indigo-500/30' },
    'research': { color: '#06b6d4', glow: 'shadow-cyan-500/10', border: 'border-cyan-500/30' },
    'fast-web': { color: '#06b6d4', glow: 'shadow-cyan-500/10', border: 'border-cyan-500/30' },
    'code': { color: '#f43f5e', glow: 'shadow-rose-500/10', border: 'border-rose-500/30' },
    'write': { color: '#f59e0b', glow: 'shadow-amber-500/10', border: 'border-amber-500/30' },
    'rag': { color: '#8b5cf6', glow: 'shadow-violet-500/10', border: 'border-violet-500/30' },
    'math': { color: '#a855f7', glow: 'shadow-purple-500/10', border: 'border-purple-500/30' },
    'physics': { color: '#a855f7', glow: 'shadow-purple-500/10', border: 'border-purple-500/30' },
    'finance': { color: '#fbbf24', glow: 'shadow-yellow-500/10', border: 'border-yellow-500/30' },
    'legal': { color: '#fbbf24', glow: 'shadow-yellow-500/10', border: 'border-yellow-500/30' },
    'design': { color: '#f472b6', glow: 'shadow-pink-500/10', border: 'border-pink-500/30' },
    'arch': { color: '#38bdf8', glow: 'shadow-sky-500/10', border: 'border-sky-500/30' },
    'cyber': { color: '#f43f5e', glow: 'shadow-rose-500/10', border: 'border-rose-500/30' },
    'career': { color: '#10b981', glow: 'shadow-emerald-500/10', border: 'border-emerald-500/30' },
    'eco': { color: '#22d3ee', glow: 'shadow-cyan-500/10', border: 'border-cyan-500/30' },
    'social': { color: '#8b5cf6', glow: 'shadow-violet-500/10', border: 'border-violet-500/30' },
    'debate': { color: '#f59e0b', glow: 'shadow-amber-500/10', border: 'border-amber-500/30' },
    'philosophy': { color: '#6366f1', glow: 'shadow-indigo-500/10', border: 'border-indigo-500/30' },
    'simple': { color: '#94a3b8', glow: 'shadow-slate-500/10', border: 'border-slate-500/30' },
    'default': { color: '#6366f1', glow: 'shadow-indigo-500/10', border: 'border-indigo-500/30' }
  };

  const webEnabled = webMode;
  const setWebEnabled = setWebMode;
  const currentTheme = modeThemes[intelligenceMode] || modeThemes['default'];

  const startListening = () => {
    if (isListening) {
      if (window.recognition) window.recognition.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Browser does not support speech recognition.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = (event) => {
      console.error("Speech recognition error", event.error);
      setIsListening(false);
    };

    recognition.onresult = (event) => {
      let interim = '';
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      setInterimText(interim);
      if (final) {
        setText(prev => (prev.trim() + ' ' + final).trim());
        setInterimText('');
      }
    };

    window.recognition = recognition;
    recognition.start();
  };

  const handleSend = async () => {
    if (isLoading || processing) return;

    if (inputType === 'url' && text.trim()) {
      setProcessing(true);
      setProcessingStatus('Fetching content...');
      try {
        const res = await fetch(`${API_BASE}/link/process`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: text.trim(), model: model, chat_id: sessionId }),
        });
        const data = await res.json();
        onLinkResult && onLinkResult(data);
        setText('');
        setInputType('text');
      } catch (err) {
        onLinkResult && onLinkResult({ error: String(err) });
      } finally {
        setProcessing(false);
      }
      return;
    }

    if (inputType === 'file' && uploadedFile) {
      setProcessing(true);
      setProcessingStatus(`Analyzing ${fileType}...`);
      try {
        const form = new FormData();
        form.append('file', uploadedFile);
        form.append('model', model);
        if (sessionId) form.append('chat_id', sessionId);
        const res = await fetch(`${API_BASE}/link/upload`, {
          method: 'POST',
          body: form,
        });
        const data = await res.json();
        onLinkResult && onLinkResult(data);
        if (data.short_name) {
          setText(prev => (prev.trim() + ' @' + data.short_name).trim());
        }
        setUploadedFile(null);
        setFileType(null);
        setInputType('text');
      } catch (err) {
        onLinkResult && onLinkResult({ error: String(err) });
      } finally {
        setProcessing(false);
      }
      return;
    }

    if (text.trim()) {
      onSend && onSend(text.trim(), webEnabled, speedMode, deepSearch, sandboxMode, memorySync, concentratedMode);
      setText('');
    }
  };

  const handleDirectUpload = async (file) => {
    if (!file) return;
    setProcessing(true);
    setProcessingStatus(`Auto-attaching ${file.name}...`);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('model', model);
      if (sessionId) form.append('chat_id', sessionId);
      const res = await fetch(`${API_BASE}/link/upload`, {
        method: 'POST',
        body: form,
      });
      const data = await res.json();
      onLinkResult && onLinkResult(data);
      if (data.short_name) {
        setText(prev => (prev.trim() + ' @' + data.short_name).trim());
      }
      setUploadedFile(null);
      setFileType(null);
      setInputType('text');
    } catch (err) {
      console.error("Direct upload failed", err);
    } finally {
      setProcessing(false);
    }
  };

  const handleStop = () => {
    // This will be handled by ChatWindow through props if needed, 
    // but for now we'll trigger the abort signal via the browser's stop if not available.
    onLinkResult && onLinkResult({ type: 'abort' });
  };

  const menuItems = [
    { id: 'upload', label: 'Add photos & files', icon: <Upload size={18} />, action: () => fileInputRef.current.click() },
    { id: 'simple', label: 'Simple Intelligence', icon: <MessageSquare size={18} />, mode: 'simple', color: '#94a3b8' },
    { id: 'thinking', label: 'Default Intelligence', icon: <Lightbulb size={18} />, mode: 'chat', color: '#10b981' },
    { id: 'deep', label: 'Deep Research', icon: <Zap size={18} />, mode: 'deep', color: '#6366f1' },
    { 
      id: 'more', 
      label: 'More', 
      icon: <Layers size={18} />, 
      subMenu: [
        { id: 'intel', label: 'Intelligence', icon: <Cpu size={16} />, items: [
          { label: 'Direct Response', mode: 'direct', icon: <Zap size={14} />, color: '#10b981' },
          { label: 'Simple Intelligence', mode: 'simple', icon: <MessageSquare size={14} />, color: '#94a3b8' },
          { label: 'Fast Web Search', mode: 'fast-web', icon: <Globe size={14} />, color: '#06b6d4' },
          { label: 'Code Assistant', mode: 'code', icon: <Code size={14} />, color: '#f43f5e' },
          { label: 'Local Knowledge', mode: 'rag', icon: <Search size={14} />, color: '#8b5cf6' },
        ]},
        { id: 'sci', label: 'Scientific', icon: <GraduationCap size={16} />, items: [
          { label: 'Math Solver', mode: 'math', icon: <Layers size={14} />, color: '#a855f7' },
          { label: 'Physics Expert', mode: 'physics', icon: <Zap size={14} />, color: '#a855f7' },
          { label: 'Chemical Lab', mode: 'chemistry', icon: <Shield size={14} />, color: '#a855f7' },
          { label: 'Data Science', mode: 'data', icon: <BarChart2 size={14} />, color: '#a855f7' },
        ]},
        { id: 'prof', label: 'Professional', icon: <Shield size={16} />, items: [
          { label: 'Legal Assistant', mode: 'legal', icon: <FileText size={14} />, color: '#fbbf24' },
          { label: 'Finance Analysis', mode: 'finance', icon: <BarChart2 size={14} />, color: '#fbbf24' },
          { label: 'Marketing Strategist', mode: 'marketing', icon: <Edit size={14} />, color: '#fbbf24' },
          { label: 'SEO Optimizer', mode: 'seo', icon: <Globe size={14} />, color: '#fbbf24' },
        ]},
        { id: 'creative', label: 'Creative', icon: <Edit size={16} />, items: [
          { label: 'Writing Assistant', mode: 'write', icon: <Edit size={14} />, color: '#f59e0b' },
          { label: 'Narrative Synthesis', mode: 'creative-write', icon: <MessageSquare size={14} />, color: '#f472b6' },
          { label: 'UI/UX Design', mode: 'design', icon: <Layout size={14} />, color: '#f472b6' },
          { label: 'Music Theory', mode: 'music', icon: <Music size={14} />, color: '#f472b6' },
        ]},
        { id: 'social', label: 'Social & Career', icon: <Brain size={16} />, items: [
          { label: 'Cyber Security', mode: 'cyber', icon: <Shield size={14} />, color: '#f43f5e' },
          { label: 'Career Coach', mode: 'career', icon: <BarChart2 size={14} />, color: '#10b981' },
          { label: 'Eco Analyst', mode: 'eco', icon: <Globe size={14} />, color: '#22d3ee' },
          { label: 'Social Science', mode: 'social', icon: <MessageSquare size={14} />, color: '#8b5cf6' },
        ]},
        { id: 'tools', label: 'Advanced Tools', icon: <Terminal size={16} />, items: [
          { label: 'System Arch', mode: 'arch', icon: <Terminal size={14} />, color: '#38bdf8' },
          { label: 'Summarizer', mode: 'summarize', icon: <FileText size={14} />, color: '#38bdf8' },
          { label: 'Translator', mode: 'translate', icon: <Languages size={14} />, color: '#38bdf8' },
          { label: 'Fact Checker', mode: 'fact-check', icon: <Shield size={14} />, color: '#38bdf8' },
          { label: 'Philosophy Hub', mode: 'philosophy', icon: <Brain size={14} />, color: '#6366f1' },
          { label: 'Debate Master', mode: 'debate', icon: <Edit size={14} />, color: '#f59e0b' },
          { label: 'Planner', mode: 'plan', icon: <Map size={14} />, color: '#38bdf8' },
          { label: 'Debug Assistant', mode: 'debug', icon: <Terminal size={14} />, color: '#f43f5e' },
          { label: 'Explain Concept', mode: 'explain', icon: <MessageSquare size={14} />, color: '#10b981' },
          { label: 'Memory Insight', mode: 'memory', icon: <Brain size={14} />, color: '#8b5cf6' },
        ]}
      ]
    }
  ];

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-8">
      {/* 🧭 PREMIUM CONTROL BAR */}
      <div className="flex items-center gap-3 mb-4 px-1 animate-fade-in transition-premium">
         <div className="flex items-center bg-[#1a1a1a]/80 backdrop-blur-2xl rounded-[18px] p-1.5 border border-white/5 shadow-premium">
            <button 
              className={`flex items-center gap-2 px-4 py-2 rounded-[14px] text-[11px] font-black uppercase tracking-widest transition-all ${(!webEnabled && intelligenceMode === 'chat') ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'}`}
              onClick={() => { setWebEnabled(false); onModeChange('chat'); }}
            >
              <MessageSquare size={14} /> Chat
            </button>
            <button 
              className={`flex items-center gap-2 px-4 py-2 rounded-[14px] text-[11px] font-black uppercase tracking-widest transition-all ${webEnabled ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'}`}
              onClick={() => setWebEnabled(true)}
            >
              <Globe size={14} /> {webEnabled ? 'Web Mode Active' : 'Web'}
            </button>
            <button 
              className={`flex items-center gap-2 px-4 py-2 rounded-[14px] text-[11px] font-black uppercase tracking-widest transition-all hover:scale-[1.02] active:scale-[0.98] ${deepSearch ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30 ring-2 ring-indigo-400/50' : 'text-slate-500 bg-black/20 hover:text-indigo-300 hover:bg-indigo-500/10'}`}
              onClick={() => setDeepSearch(!deepSearch)}
              title="Deep Web Scraper"
            >
              <Zap size={14} className={deepSearch ? "animate-pulse text-indigo-100" : ""} /> {deepSearch ? 'Deep Scrape' : 'Scrape'}
            </button>
            <button 
              className={`flex items-center gap-2 px-4 py-2 rounded-[14px] text-[11px] font-black uppercase tracking-widest transition-all hover:scale-[1.02] active:scale-[0.98] ${sandboxMode ? 'bg-[#50b3a2] text-white shadow-lg shadow-[#50b3a2]/30 ring-2 ring-[#50b3a2]/50' : 'text-slate-500 bg-black/20 hover:text-[#50b3a2] hover:bg-[#50b3a2]/10'}`}
              onClick={() => setSandboxMode(!sandboxMode)}
              title="Secure Docker Code Sandbox"
            >
              <Terminal size={14} className={sandboxMode ? "animate-pulse text-white" : ""} /> {sandboxMode ? 'Exec Engine' : 'Sandbox'}
            </button>
            <button 
              className="flex items-center gap-2 px-4 py-2 rounded-[14px] text-[11px] font-black uppercase tracking-widest text-slate-500 hover:text-indigo-400 hover:bg-indigo-500/5 transition-all"
              onClick={() => onToggleRagPanel?.()}
            >
              <FileText size={14} /> Docs
            </button>
            {isLoading && (
              <button 
                className="flex items-center gap-2 px-4 py-2 rounded-[14px] text-[11px] font-black uppercase tracking-widest text-red-500 hover:bg-red-500/10 transition-all ml-1"
                onClick={onStop}
              >
                <Zap size={14} className="animate-pulse" /> Stop
              </button>
            )}
         </div>

         {/* ⚡ SPEED SELECTION */}
         <div className="flex items-center bg-[#1a1a1a]/80 backdrop-blur-2xl rounded-[18px] p-1.5 border border-white/5 shadow-premium">
            {[
              { id: 'fast', label: 'Fast', icon: <Zap size={14} />, color: '#fbbf24' },
              { id: 'thinking', label: 'Thinking', icon: <Brain size={14} />, color: '#10b981' },
              { id: 'auto', label: 'Auto', icon: <Cpu size={14} />, color: '#6366f1' }
            ].map((s) => (
              <button
                key={s.id}
                onClick={() => setSpeedMode(s.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-[12px] text-[10px] font-bold uppercase tracking-wider transition-all ${
                  speedMode === s.id 
                    ? 'bg-white/10 text-white border border-white/10 shadow-sm' 
                    : 'text-slate-500 hover:text-slate-300'
                }`}
                title={`${s.label} Intelligence`}
              >
                <span style={{ color: speedMode === s.id ? s.color : 'inherit' }}>{s.icon}</span>
                {s.label}
              </button>
            ))}
         </div>
         
          <div className="flex-1"></div>
          
          <div className="flex items-center gap-3">
             <button 
               onClick={() => setMemorySync(!memorySync)}
               className={`flex items-center gap-2 px-3 py-1.5 rounded-[12px] text-[10px] font-bold uppercase tracking-wider transition-all ${memorySync ? 'text-indigo-400 bg-indigo-500/10' : 'text-slate-600 hover:text-slate-400'}`}
               title="Agentic ChromaDB Memory Sync"
             >
               <Brain size={12} className={memorySync ? "animate-pulse" : ""} />
              {memorySync ? 'Sync' : 'Off'}
             </button>
             
             <button 
               onClick={() => setConcentratedMode(!concentratedMode)}
               className={`flex items-center gap-2 px-3 py-1.5 rounded-[12px] text-[10px] font-bold uppercase tracking-wider transition-all ${concentratedMode ? 'text-rose-400 bg-rose-500/10' : 'text-slate-600 hover:text-slate-400'}`}
               title="Concentrated Mode: Conciseness Optimized"
             >
               <Plus size={12} className={concentratedMode ? "rotate-45" : ""} />
               {concentratedMode ? 'Concise' : 'Standard'}
             </button>
          </div>
          
          <div className="relative group ml-3">
            <div className="flex items-center gap-1.5 bg-[#1a1a1a]/80 backdrop-blur-2xl rounded-[18px] p-1 border border-white/5 shadow-premium">
              <button 
                onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-[14px] text-[10px] font-bold text-slate-400 hover:text-white hover:bg-white/5 transition-premium group/mod"
              >
                MODEL: <span className="text-indigo-400 uppercase">{model === 'auto' ? 'Auto Intelligence' : (model || 'Gemma 3')}</span>
                <ChevronRight size={10} className={`transition-transform ${isModelDropdownOpen ? 'rotate-90' : ''}`} />
              </button>
              
              {model !== 'auto' && (
                <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-[12px] bg-rose-500/10 border border-rose-500/20 text-[9px] font-black uppercase text-rose-400 tracking-tighter animate-pulse shadow-[0_0_10px_rgba(244,63,94,0.1)]">
                   MANUAL
                </div>
              )}
            </div>
            
            {isModelDropdownOpen && (
              <div className="absolute bottom-full right-0 mb-3 w-56 bg-[#0c0c0c]/95 backdrop-blur-3xl border border-white/10 rounded-[24px] shadow-premium p-1.5 z-[110] max-h-72 overflow-y-auto custom-scrollbar animate-slideUp">
                <div className="px-3 py-2 text-[9px] font-black uppercase tracking-widest text-slate-600 border-b border-white/5 mb-1">Select Tier</div>
                {availableModels.map(m => (
                  <button
                    key={m}
                    onClick={() => { onModelChange(m); setIsModelDropdownOpen(false); }}
                    className={`w-full text-left px-4 py-2.5 rounded-[16px] text-[11px] font-bold transition-premium flex items-center justify-between group ${model === m ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
                  >
                    <span className="truncate">{m === 'auto' ? '🚀 AUTO-ROUTER' : m}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
      </div>

      {/* 📥 DRAG & DROP ZONE + INPUT BOX */}
      <div 
        className={`relative transition-all duration-500 ease-out border-2 rounded-[32px] overflow-visible ${isFocused ? 'bg-[#0f0f0f] border-indigo-500/40 shadow-[0_0_50px_-12px_rgba(99,102,241,0.2)]' : 'bg-[#141414] border-white/5 shadow-2xl'} ${dragOver ? 'border-dashed border-indigo-400 scale-[1.01] bg-indigo-500/5' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* DRAG-OVER OVERLAY */}
        {dragOver && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-indigo-600/10 backdrop-blur-sm rounded-[32px] pointer-events-none border-2 border-dashed border-indigo-400 animate-pulse">
            <div className="flex flex-col items-center gap-2 text-indigo-400 font-bold uppercase tracking-widest text-sm">
              <Upload size={32} />
              Drop document or image
            </div>
          </div>
        )}

        {/* FILE PREVIEW */}
        {uploadedFile && (
          <div className="flex items-center gap-3 p-4 border-b border-white/5 bg-white/[0.02]">
            <div className="p-2.5 rounded-2xl bg-white/5 flex items-center justify-center" style={{ color: FILE_COLORS[fileType] || '#94a3b8' }}>
              {FILE_ICONS[fileType] || <LinkIcon size={14} />}
            </div>
            <div className="flex-1 min-w-0">
               <div className="text-[13px] font-bold text-white truncate">{uploadedFile.name}</div>
               <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider flex items-center gap-1">
                 {fileType} File detected
                 {fileType === 'unknown' && uploadedFile.type.startsWith('image/') && <span className="text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-[6px] ml-2">Neural OCR Active</span>}
               </div>
            </div>
            <button 
              onClick={() => { setUploadedFile(null); setFileType(null); setInputType('text'); }}
              className="p-2 rounded-full hover:bg-white/10 text-slate-400 hover:text-white transition-all"
            >
              <X size={16} />
            </button>
          </div>
        )}

        <div className="flex items-end p-2 min-h-[64px]">
          {/* PLUS MENU */}
          <div className="relative mb-1 ml-1" ref={menuRef}>
            <button 
              onClick={() => setIsPlusMenuOpen(!isPlusMenuOpen)}
              className={`w-11 h-11 rounded-full flex items-center justify-center transition-premium ${isPlusMenuOpen ? 'bg-white text-black rotate-45' : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white'}`}
            >
              <Plus size={24} />
            </button>
            
            {/* PLUS MENU POPUP */}
            {isPlusMenuOpen && (
              <div className="absolute left-0 bottom-full mb-4 z-50 flex items-end gap-3 pointer-events-auto">
                <div className="w-72 bg-[#1a1a1a] border border-white/10 rounded-[28px] shadow-premium p-2 animate-slideUp">
                  {menuItems.map((item) => (
                    <div key={item.id}>
                      <button
                        onMouseEnter={() => item.subMenu && setActiveSubMenuId(item.id)}
                        onClick={() => {
                          if (item.action) item.action();
                          if (item.mode) onModeChange(item.mode);
                          if (!item.subMenu) setIsPlusMenuOpen(false);
                        }}
                        style={{ color: (intelligenceMode === item.mode || activeSubMenuId === item.id) ? (item.color || currentTheme.color) : '#94a3b8' }}
                        className={`w-full flex items-center justify-between px-4 py-3 rounded-[20px] text-sm font-semibold transition-premium group ${(intelligenceMode === item.mode || activeSubMenuId === item.id) ? 'bg-white/5' : 'hover:bg-white/5 hover:text-white'}`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="opacity-70 group-hover:opacity-100 transition-opacity">{item.icon}</span>
                          <span>{item.label}</span>
                        </div>
                        {item.subMenu && <ChevronRight size={16} />}
                      </button>
                    </div>
                  ))}
                </div>

                {/* DYNAMIC SUB MENU (Nested Level) */}
                {activeSubMenuId && menuItems.find(i => i.id === activeSubMenuId)?.subMenu && (
                  <div className="w-80 bg-[#1a1a1a] border border-white/10 rounded-[28px] shadow-premium p-3 animate-slideUp h-fit max-h-[70vh] overflow-y-auto custom-scrollbar">
                    {menuItems.find(i => i.id === activeSubMenuId).subMenu.map(category => (
                      <div key={category.id} className="mb-4 last:mb-0">
                        <div className="px-4 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-slate-600 mb-2 flex items-center gap-2">
                          {category.icon} {category.label}
                        </div>
                        <div className="grid grid-cols-1 gap-1">
                          {category.items.map(sub => (
                            <button
                              key={sub.label}
                              onClick={() => {
                                if (sub.action) sub.action();
                                if (sub.mode) onModeChange(sub.mode);
                                setIsPlusMenuOpen(false);
                                setActiveSubMenuId(null);
                              }}
                              style={{ 
                                backgroundColor: intelligenceMode === sub.mode ? (sub.color + '20') : 'transparent',
                                color: intelligenceMode === sub.mode ? sub.color : '#94a3b8'
                              }}
                              className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-[13px] font-medium transition-premium ${intelligenceMode === sub.mode ? 'shadow-lg' : 'hover:bg-white/5 hover:text-white'}`}
                            >
                              <span style={{ color: sub.color || '#94a3b8' }}>{sub.icon}</span>
                              {sub.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* INPUT AREA with INTERIM VOICE TEXT */}
          <div 
            className="flex-1 flex flex-col relative cursor-text"
            onClick={() => textareaRef.current?.focus()}
          >
            {isListening && interimText && (
              <div className="absolute top-0 left-2 text-emerald-400/50 text-[17px] font-medium animate-pulse pointer-events-none italic">
                {interimText}
              </div>
            )}
            <textarea
              ref={textareaRef}
              autoFocus
              rows="1"
              value={text}
              onChange={onInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              onDrop={handleTextareaDrop}
              placeholder={isListening ? "Listening..." : `Ask in ${intelligenceMode || 'General'} mode...`}
              className="w-full bg-transparent border-none outline-none text-white text-[17px] font-semibold placeholder:text-slate-600 py-3 px-2 resize-none max-h-[300px] transition-all"
            />
            {uploadedFile && (
              <div className="absolute -bottom-6 left-2 flex items-center gap-2 bg-indigo-600/20 border border-indigo-500/30 px-2 py-0.5 rounded-full animate-fade-in">
                <span className="text-[10px] font-black text-indigo-400">📄 File ready: {uploadedFile.name.split('.')[0].toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 15)}</span>
              </div>
            )}
          </div>

          {/* RIGHT TOOLS */}
          <div className="flex items-center gap-2 pr-1 mb-1">
            {isLoading && (
              <div className="p-2 animate-spin transition-premium" style={{ color: currentTheme.color }}>
                 <Cpu size={18} />
              </div>
            )}
            <button 
              onClick={() => setDeepSearch(!deepSearch)}
              className={`p-2 rounded-lg text-[10px] font-black tracking-widest transition-premium ${deepSearch ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
              title="Advanced Deep URL Analysis"
            >
              {deepSearch ? '🔎 DEEP' : '🌐 WEB'}
            </button>

            <button 
              onClick={startListening}
              className={`p-2.5 rounded-full transition-premium ${isListening ? 'text-red-500 bg-red-500/10' : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
            >
              <Mic size={22} className={isListening ? 'animate-pulse' : ''} />
            </button>

            <button 
              onClick={() => fileInputRef.current.click()}
              className="p-2.5 rounded-full text-slate-500 hover:text-white hover:bg-white/5 transition-premium"
              title="Attach File"
            >
              <Paperclip size={22} />
            </button>

            <button 
              onClick={handleSend}
              aria-label="Send Message"
              title="Send Prompt"
              disabled={isLoading || processing || (!text.trim() && !uploadedFile)}
              style={{ backgroundColor: (text.trim() || uploadedFile) ? currentTheme.color : '#1a1a1a' }}
              className={`w-11 h-11 rounded-full flex items-center justify-center transition-all active:scale-90 ${text.trim() || uploadedFile ? 'text-white shadow-lg ' + currentTheme.glow : 'text-slate-700 cursor-not-allowed opacity-50'}`}
            >
              <ArrowUp size={24} strokeWidth={3} />
            </button>
          </div>
        </div>

        {/* Hidden File Input */}
        <input type="file" ref={fileInputRef} className="hidden" onChange={(e) => handleFileSelect(e.target.files[0])} />
      </div>
    </div>
  );
};

export default MultiInputBox;
