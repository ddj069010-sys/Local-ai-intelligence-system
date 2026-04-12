import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ─── Toast Notification System ───────────────────────────────────────────────
function useToast() {
  const [toasts, setToasts] = useState([]);
  const add = (msg, type = 'info') => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  };
  return { toasts, toast: add };
}

function ToastArea({ toasts }) {
  const colors = { info: '#3b82f6', success: '#10b981', error: '#f43f5e', warning: '#f59e0b' };
  return (
    <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999, display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {toasts.map(t => (
        <div key={t.id} style={{
          background: '#1e293b', border: `1px solid ${colors[t.type]}55`,
          borderLeft: `3px solid ${colors[t.type]}`, borderRadius: '12px',
          padding: '12px 18px', color: '#e2e8f0', fontSize: '12.5px', fontWeight: 600,
          maxWidth: '320px', boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          animation: 'slideInRight 0.3s ease',
        }}>{t.msg}</div>
      ))}
    </div>
  );
}

// ─── Shared Components ────────────────────────────────────────────────────────
const SectorCard = ({ icon, title, badge, badgeColor = 'rgba(59,130,246,0.2)', badgeFg = '#93c5fd', children, status }) => (
  <div style={{
    background: 'linear-gradient(135deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01))',
    border: '1px solid rgba(255,255,255,0.07)', borderRadius: '20px', padding: '24px',
    display: 'flex', flexDirection: 'column', gap: '16px',
    backdropFilter: 'blur(12px)', boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
  }}>
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span style={{ fontSize: '22px' }}>{icon}</span>
        <span style={{ fontWeight: 900, fontSize: '12px', color: '#e2e8f0', letterSpacing: '0.08em', textTransform: 'uppercase' }}>{title}</span>
        {status && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: status === 'full' ? '#10b981' : status === 'partial' ? '#f59e0b' : '#f43f5e', boxShadow: `0 0 6px ${status === 'full' ? '#10b981' : '#f59e0b'}` }} />
            <span style={{ fontSize: '9px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>{status}</span>
          </div>
        )}
      </div>
      <span style={{ background: badgeColor, color: badgeFg, border: `1px solid ${badgeFg}44`, borderRadius: '20px', padding: '2px 10px', fontSize: '9px', fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase' }}>{badge}</span>
    </div>
    {children}
  </div>
);

const Btn = ({ onClick, loading, children, color = '#3b82f6', disabled, size = 'md' }) => (
  <button onClick={onClick} disabled={loading || disabled} style={{
    background: (loading || disabled) ? 'rgba(255,255,255,0.05)' : `linear-gradient(135deg,${color},${color}bb)`,
    color: (loading || disabled) ? '#475569' : '#fff',
    border: 'none', borderRadius: '10px',
    padding: size === 'sm' ? '6px 14px' : '9px 18px',
    fontSize: size === 'sm' ? '10px' : '11px', fontWeight: 800,
    cursor: (loading || disabled) ? 'not-allowed' : 'pointer',
    letterSpacing: '0.08em', textTransform: 'uppercase', transition: 'all 0.2s',
    display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap',
    boxShadow: (loading || disabled) ? 'none' : `0 4px 12px ${color}44`,
  }}>
    {loading && <span style={{ animation: 'spin 0.8s linear infinite', display: 'inline-block', fontSize: '13px' }}>⟳</span>}
    {children}
  </button>
);

const Input = ({ value, onChange, onKeyDown, placeholder, style = {} }) => (
  <input value={value} onChange={onChange} onKeyDown={onKeyDown} placeholder={placeholder} style={{
    flex: 1, background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.09)',
    borderRadius: '10px', padding: '9px 14px', color: '#e2e8f0', fontSize: '13px',
    outline: 'none', transition: 'border 0.2s', ...style,
  }} onFocus={e => e.target.style.borderColor = 'rgba(99,102,241,0.5)'}
    onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.09)'} />
);

const ResultBox = ({ children, color = '#3b82f6', maxH = '240px' }) => (
  <div style={{
    background: 'rgba(0,0,0,0.45)', borderRadius: '12px', border: `1px solid ${color}33`,
    padding: '14px 16px', fontSize: '12px', color: '#cbd5e1', lineHeight: '1.75',
    maxHeight: maxH, overflowY: 'auto', whiteSpace: 'pre-wrap', fontFamily: 'ui-monospace,monospace',
  }}>{children}</div>
);

const MarkdownView = ({ content }) => (
  <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
    h2: ({ ...p }) => <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#f1f5f9', margin: '12px 0 6px', borderBottom: '1px solid rgba(255,255,255,0.07)', paddingBottom: '6px' }} {...p} />,
    h3: ({ ...p }) => <h3 style={{ fontSize: '13px', fontWeight: 800, color: '#93c5fd', margin: '10px 0 4px' }} {...p} />,
    p: ({ ...p }) => <p style={{ margin: '6px 0', color: '#94a3b8', fontSize: '12.5px', lineHeight: '1.7' }} {...p} />,
    ul: ({ ...p }) => <ul style={{ paddingLeft: '20px', margin: '6px 0' }} {...p} />,
    li: ({ ...p }) => <li style={{ color: '#94a3b8', fontSize: '12.5px', marginBottom: '3px' }} {...p} />,
    strong: ({ ...p }) => <strong style={{ color: '#e2e8f0', fontWeight: 800 }} {...p} />,
    code: ({ inline, ...p }) => inline
      ? <code style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc', padding: '1px 6px', borderRadius: '4px', fontSize: '11px' }} {...p} />
      : <pre style={{ background: 'rgba(0,0,0,0.5)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px', padding: '10px', overflowX: 'auto', fontSize: '11px', margin: '8px 0' }}><code style={{ color: '#a3e635' }} {...p} /></pre>,
  }}>{content}</ReactMarkdown>
);

const Skeleton = ({ h = '40px', w = '100%' }) => (
  <div style={{ height: h, width: w, background: 'rgba(255,255,255,0.04)', borderRadius: '10px', animation: 'pulse 1.5s ease infinite' }} />
);

const WarningBanner = ({ msg }) => (
  <div style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: '10px', padding: '8px 14px', display: 'flex', gap: '8px', alignItems: 'center' }}>
    <span>⚠️</span>
    <span style={{ fontSize: '11px', color: '#fbbf24', fontWeight: 600 }}>{msg}</span>
  </div>
);

// ─── Sector 1: Neural Memory ──────────────────────────────────────────────────
function NeuralMemoryPanel({ toast, sysStatus }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(false);
  const [clustersLoading, setClustersLoading] = useState(true);
  const [engine, setEngine] = useState('');

  useEffect(() => {
    setClustersLoading(true);
    fetch(`${API}/intelligence/memory/clusters`)
      .then(r => r.json())
      .then(d => { setClusters(d.clusters || []); setClustersLoading(false); })
      .catch(() => { setClustersLoading(false); });
  }, []);

  const search = async () => {
    if (!query.trim()) return;
    setLoading(true); setResults([]);
    try {
      const res = await fetch(`${API}/intelligence/memory/search`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 6 }),
      });
      const data = await res.json();
      setResults(data.results || []);
      setEngine(data.engine || 'bm25');
      if (data.engine === 'faiss') toast('🧠 Semantic vector search used', 'success');
      else toast('🔑 Keyword search used — install faiss-cpu for semantic', 'info');
    } catch (e) { toast(`Search failed: ${e.message}`, 'error'); }
    setLoading(false);
  };

  const engineStatus = sysStatus?.sectors?.memory;

  return (
    <SectorCard icon="🧠" title="Neural Memory" badge={engineStatus === 'full' ? 'VECTOR SEARCH' : 'KEYWORD SEARCH'} badgeColor={engineStatus === 'full' ? 'rgba(16,185,129,0.2)' : 'rgba(245,158,11,0.2)'} badgeFg={engineStatus === 'full' ? '#34d399' : '#fbbf24'} status={engineStatus === 'full' ? 'full' : 'partial'}>
      {engineStatus !== 'full' && <WarningBanner msg="FAISS not installed — using keyword search. Run: pip install sentence-transformers faiss-cpu" />}
      {/* Clusters */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', minHeight: '32px' }}>
        {clustersLoading ? [1, 2, 3, 4].map(i => <Skeleton key={i} h="28px" w="80px" />) :
          clusters.map((c, i) => (
            <button key={i} onClick={() => setQuery(c.label.toLowerCase())} style={{
              background: `${c.color}1a`, border: `1px solid ${c.color}44`,
              borderRadius: '20px', padding: '5px 14px', cursor: 'pointer', display: 'flex',
              alignItems: 'center', gap: '7px', transition: 'all 0.2s',
            }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: c.color, boxShadow: `0 0 6px ${c.color}` }} />
              <span style={{ fontSize: '11px', fontWeight: 700, color: '#e2e8f0' }}>{c.label}</span>
              <span style={{ fontSize: '9px', color: '#64748b', fontWeight: 800 }}>{c.count}</span>
            </button>
          ))
        }
      </div>
      {/* Search */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <Input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && search()} placeholder='Search e.g. "AI ethics", "video analysis"...' />
        <Btn onClick={search} loading={loading} color="#8b5cf6">Search</Btn>
      </div>
      {/* Results */}
      {results.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>{results.length} results · {engine}</span>
          </div>
          {results.map((r, i) => (
            <div key={i} style={{ background: 'rgba(139,92,246,0.07)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: '10px', padding: '10px 14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '11px', fontWeight: 800, color: '#a78bfa' }}>{r.source}</span>
                <span style={{ fontSize: '10px', color: '#10b981', fontWeight: 700 }}>
                  {r.method === 'faiss_vector' ? `cos: ${r.score}` : `bm25: ${r.score}`}
                </span>
              </div>
              <p style={{ fontSize: '11.5px', color: '#94a3b8', margin: 0, lineHeight: '1.5' }}>{r.snippet}</p>
            </div>
          ))}
        </div>
      )}
    </SectorCard>
  );
}

// ─── Sector 2: Multi-Agent Debate ─────────────────────────────────────────────
function DebatePanel({ toast }) {
  const [topic, setTopic] = useState('');
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('synthesis');
  const [stage, setStage] = useState('');
  const [loading, setLoading] = useState(false);
  const [models] = useState(['gemma3:4b', 'llama3:8b', 'mistral:7b', 'gemma3:12b']);
  const [rModel, setRModel] = useState('gemma3:4b');
  const [cModel, setCModel] = useState('gemma3:4b');

  const runDebate = async () => {
    if (!topic.trim()) { toast('Enter a topic first', 'warning'); return; }
    setLoading(true); setResult(null); setStage('');
    const accumulated = { researcher: '', critic: '', synthesis: '' };
    try {
      const res = await fetch(`${API}/intelligence/debate/stream`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, researcher_model: rModel, critic_model: cModel, synthesis_model: rModel }),
      });
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop();
        for (const part of parts) {
          const lines = part.split('\n');
          const eventLine = lines.find(l => l.startsWith('event: '));
          const dataLine = lines.find(l => l.startsWith('data: '));
          if (!eventLine || !dataLine) continue;
          const event = eventLine.replace('event: ', '');
          const data = JSON.parse(dataLine.replace('data: ', ''));
          if (event === 'stage') setStage(data.message);
          if (event === 'researcher_done') { accumulated.researcher = data.text; setResult({ ...accumulated }); setActiveTab('researcher'); }
          if (event === 'critic_done') { accumulated.critic = data.text; setResult({ ...accumulated }); setActiveTab('critic'); }
          if (event === 'synthesis_done') { accumulated.synthesis = data.text; setResult({ ...accumulated }); setActiveTab('synthesis'); }
          if (event === 'complete') { toast('✅ Debate complete', 'success'); setStage(''); }
          if (event === 'error') { toast(`Debate error: ${data.message}`, 'error'); setStage(''); }
        }
      }
    } catch (e) { toast(`Debate failed: ${e.message}`, 'error'); }
    setLoading(false); setStage('');
  };

  const tabs = [
    { key: 'synthesis', label: '✅ Verified', color: '#10b981' },
    { key: 'researcher', label: '🔬 Researcher', color: '#3b82f6' },
    { key: 'critic', label: '⚠️ Critic', color: '#f59e0b' },
  ];

  return (
    <SectorCard icon="⚖️" title="Multi-Agent Debate" badge="SSE STREAMING" badgeColor="rgba(245,158,11,0.2)" badgeFg="#fbbf24" status="full">
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <Input value={topic} onChange={e => setTopic(e.target.value)} onKeyDown={e => e.key === 'Enter' && runDebate()} placeholder='e.g. "Is RAG better than fine-tuning?"' style={{ minWidth: '240px' }} />
        <Btn onClick={runDebate} loading={loading} color="#f59e0b">Debate</Btn>
      </div>
      {/* Model Selectors */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {[['🔬 Researcher', rModel, setRModel], ['⚠️ Critic', cModel, setCModel]].map(([label, val, setter], i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>{label}:</span>
            <select value={val} onChange={e => setter(e.target.value)} style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '4px 8px', color: '#e2e8f0', fontSize: '11px', outline: 'none' }}>
              {models.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
        ))}
      </div>
      {/* Live Stage */}
      {stage && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: '10px', padding: '8px 14px' }}>
          <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⟳</span>
          <span style={{ fontSize: '12px', color: '#fbbf24', fontWeight: 600 }}>{stage}</span>
        </div>
      )}
      {result && (
        <>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {tabs.map(t => (
              <button key={t.key} onClick={() => setActiveTab(t.key)} style={{
                background: activeTab === t.key ? `${t.color}22` : 'transparent',
                border: `1px solid ${activeTab === t.key ? t.color : 'rgba(255,255,255,0.08)'}`,
                borderRadius: '8px', padding: '5px 12px', color: activeTab === t.key ? t.color : '#64748b',
                fontSize: '10px', fontWeight: 800, cursor: 'pointer', transition: 'all 0.2s',
              }}>{t.label}{result[t.key] ? '' : ' …'}</button>
            ))}
          </div>
          {result[activeTab] ? (
            <div style={{ background: 'rgba(0,0,0,0.4)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.06)', padding: '16px', maxHeight: '300px', overflowY: 'auto' }}>
              <MarkdownView content={result[activeTab]} />
            </div>
          ) : <Skeleton h="120px" />}
        </>
      )}
    </SectorCard>
  );
}

// ─── Sector 3: Live Canvas ────────────────────────────────────────────────────
function LiveCanvasPanel({ toast }) {
  const [doc, setDoc] = useState('');
  const [title, setTitle] = useState('Untitled Canvas');
  const [docId] = useState('default');
  const [words, setWords] = useState(0);
  const [preview, setPreview] = useState(false);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);
  const saveTimer = useRef(null);

  // Load from server on mount
  useEffect(() => {
    fetch(`${API}/intelligence/canvas/load/${docId}`)
      .then(r => r.json())
      .then(d => {
        if (d.status === 'ok') {
          setDoc(d.content); setTitle(d.title || 'Untitled Canvas');
          setLastSaved(d.updated_at);
        } else {
          const saved = localStorage.getItem('hq_canvas_doc');
          if (saved) setDoc(saved);
          else setDoc('## 🎭 Collaborative Canvas\n\nStart writing here.\n\n### 📦 Your Notes\n- Add bullet points\n\n### 💡 Ideas\n> Pair-program your next big project here.');
        }
      })
      .catch(() => {
        const saved = localStorage.getItem('hq_canvas_doc');
        if (saved) setDoc(saved);
      });
  }, [docId]);

  // Auto-save on change (debounced 1.5s)
  useEffect(() => {
    if (!doc) return;
    setWords(doc.trim().split(/\s+/).filter(Boolean).length);
    localStorage.setItem('hq_canvas_doc', doc);
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => saveToServer(), 1500);
    return () => clearTimeout(saveTimer.current);
  }, [doc]);

  const saveToServer = async () => {
    setSaving(true);
    try {
      await fetch(`${API}/intelligence/canvas/save`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doc_id: docId, content: doc, title }),
      });
      setLastSaved(new Date().toLocaleTimeString());
    } catch { /* silent — localStorage backup already done */ }
    setSaving(false);
  };

  const download = () => {
    const blob = new Blob([doc], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `${title}.md`; a.click();
    toast('📥 Canvas exported', 'success');
  };

  return (
    <SectorCard icon="🎭" title="Live Canvas" badge="SERVER SYNC" badgeColor="rgba(16,185,129,0.2)" badgeFg="#34d399" status="full">
      {/* Title + Controls */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
        <input value={title} onChange={e => setTitle(e.target.value)} style={{
          flex: 1, background: 'transparent', border: 'none', borderBottom: '1px solid rgba(255,255,255,0.1)',
          color: '#f1f5f9', fontSize: '14px', fontWeight: 800, outline: 'none', padding: '2px 4px',
        }} />
        <Btn onClick={() => setPreview(p => !p)} color={preview ? '#6366f1' : '#334155'} size="sm">{preview ? '✏️ Edit' : '👁 Preview'}</Btn>
        <Btn onClick={download} color="#10b981" size="sm">⬇ Export</Btn>
      </div>
      {/* Status bar */}
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '10px', color: '#475569' }}>
        <span>{words} words</span>
        <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#334155' }} />
        <span style={{ color: saving ? '#f59e0b' : '#10b981' }}>{saving ? '⟳ Saving…' : lastSaved ? `✓ Saved ${lastSaved}` : 'Not saved yet'}</span>
        <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#334155' }} />
        <span>Server + localStorage</span>
      </div>
      {/* Edit / Preview */}
      {preview ? (
        <div style={{ background: 'rgba(0,0,0,0.4)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.06)', padding: '16px', maxHeight: '300px', overflowY: 'auto' }}>
          <MarkdownView content={doc} />
        </div>
      ) : (
        <textarea value={doc} onChange={e => setDoc(e.target.value)} style={{
          width: '100%', height: '260px', background: 'rgba(0,0,0,0.5)',
          border: '1px solid rgba(255,255,255,0.07)', borderRadius: '12px', padding: '14px',
          color: '#e2e8f0', fontSize: '12.5px', fontFamily: 'ui-monospace,monospace', lineHeight: '1.7',
          resize: 'none', outline: 'none', boxSizing: 'border-box',
        }} placeholder="Write your collaborative document here..." />
      )}
    </SectorCard>
  );
}

// ─── Sector 4: Docker Sandbox ─────────────────────────────────────────────────
function SandboxPanel({ toast, sysStatus }) {
  const [code, setCode] = useState('# 🛡️ Sandbox Execution\nprint("Hello from the Fortress!")\nimport platform, sys\nprint(f"Python {sys.version}")\nprint(f"Platform: {platform.system()} {platform.release()}")');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState('python');
  const [sandboxStatus, setSandboxStatus] = useState(null);

  useEffect(() => {
    fetch(`${API}/intelligence/sandbox/status`)
      .then(r => r.json())
      .then(d => setSandboxStatus(d))
      .catch(() => { });
  }, []);

  const EXAMPLES = {
    python: '# Python\nimport math, sys\nprint(f"👋 Python {sys.version[:6]}")\nprint(f"π = {math.pi:.6f}")',
    javascript: '// JavaScript\nconst msg = "👋 Hello from Node.js!";\nconsole.log(msg);\nconsole.log(`Math: ${Math.PI.toFixed(6)}`);',
    shell: '#!/bin/sh\necho "👋 Hello from Shell!"\necho "Uptime: $(date)"\nuname -a',
  };

  const run = async () => {
    setLoading(true); setResult(null);
    try {
      const res = await fetch(`${API}/intelligence/sandbox/run`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language, timeout: 15 }),
      });
      const d = await res.json();
      setResult(d);
      if (d.status === 'blocked') toast('🛡️ Dangerous command blocked', 'warning');
      else if (d.status === 'timeout') toast('⏱️ Execution timed out', 'warning');
      else if (!d.isolated) toast('⚠️ Running locally — Docker unavailable', 'warning');
      else toast('✅ Docker sandbox executed', 'success');
    } catch (e) { toast(`Sandbox error: ${e.message}`, 'error'); }
    setLoading(false);
  };

  const dockerOk = sandboxStatus?.docker_available;

  return (
    <SectorCard icon="🛡️" title="Docker Sandbox" badge={dockerOk ? 'ISOLATED' : 'LOCAL MODE'} badgeColor={dockerOk ? 'rgba(16,185,129,0.2)' : 'rgba(244,63,94,0.2)'} badgeFg={dockerOk ? '#34d399' : '#f87171'} status={dockerOk ? 'full' : 'partial'}>
      {!dockerOk && sandboxStatus && <WarningBanner msg="Docker not available — code runs locally with full filesystem access. Run: docker pull python:3.11-slim" />}
      {/* Controls */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: '6px' }}>
          {['python', 'javascript', 'shell'].map(l => (
            <button key={l} onClick={() => { setLanguage(l); setCode(EXAMPLES[l]); }} style={{
              background: language === l ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.04)',
              border: `1px solid ${language === l ? '#6366f1' : 'rgba(255,255,255,0.08)'}`,
              borderRadius: '8px', padding: '5px 12px', color: language === l ? '#a5b4fc' : '#64748b',
              fontSize: '10px', fontWeight: 800, cursor: 'pointer', textTransform: 'uppercase',
            }}>{l}</button>
          ))}
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px' }}>
          {dockerOk !== null && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: dockerOk ? '#10b981' : '#f59e0b', boxShadow: `0 0 6px ${dockerOk ? '#10b981' : '#f59e0b'}` }} />
              <span style={{ fontSize: '9px', color: '#64748b', fontWeight: 700 }}>{dockerOk ? 'Docker' : 'Local'}</span>
            </div>
          )}
          <Btn onClick={run} loading={loading} color="#f43f5e">▶ Run</Btn>
        </div>
      </div>
      {/* Code editor */}
      <textarea value={code} onChange={e => setCode(e.target.value)} style={{
        width: '100%', height: '160px', background: 'rgba(0,0,0,0.6)',
        border: '1px solid rgba(255,255,255,0.07)', borderRadius: '12px', padding: '12px 14px',
        color: language === 'python' ? '#a3e635' : language === 'javascript' ? '#fbbf24' : '#94a3b8',
        fontSize: '12px', fontFamily: 'ui-monospace,monospace', lineHeight: '1.6',
        resize: 'none', outline: 'none', boxSizing: 'border-box',
      }} />
      {/* Result */}
      {result && (
        <div>
          <div style={{ display: 'flex', gap: '6px', marginBottom: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{
              fontSize: '9px', fontWeight: 800, padding: '3px 10px', borderRadius: '8px', textTransform: 'uppercase', letterSpacing: '0.1em',
              background: result.status === 'ok' ? 'rgba(16,185,129,0.15)' : 'rgba(244,63,94,0.15)',
              color: result.status === 'ok' ? '#10b981' : '#f43f5e',
            }}>{result.status} · exit: {result.exit_code ?? '–'}</span>
            <span style={{ fontSize: '9px', fontWeight: 700, color: result.isolated ? '#10b981' : '#f59e0b' }}>
              {result.isolated ? '🛡️ Docker Isolated' : '⚠️ Local Execution'}
            </span>
          </div>
          {result.warning && <WarningBanner msg={result.warning} />}
          {result.output && <ResultBox color="#10b981">{result.output}</ResultBox>}
          {result.error && result.error.trim() && <ResultBox color="#f43f5e">{result.error}</ResultBox>}
        </div>
      )}
    </SectorCard>
  );
}

// ─── Sector 5: Screen Observer ────────────────────────────────────────────────
function ScreenObserverPanel({ toast, sysStatus }) {
  const [messages, setMessages] = useState([]);
  const [visionContext, setVisionContext] = useState('');
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  const [loading, setLoading] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [autoCapture, setAutoCapture] = useState(false);
  const [interval, setIntervalSecs] = useState(10);
  const [question, setQuestion] = useState('Describe what is happening on screen. Identify key UI elements, text, buttons, and any active processes or code.');
  const [observerStatus, setObserverStatus] = useState(null);
  const canvasRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const autoRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/intelligence/observer/status`)
      .then(r => r.json())
      .then(d => setObserverStatus(d))
      .catch(() => { });
  }, []);

  const startCapture = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: { mediaSource: 'screen' } });
      streamRef.current = stream;
      const vid = document.createElement('video');
      vid.srcObject = stream; vid.muted = true;
      await vid.play();
      videoRef.current = vid;
      setCapturing(true);
      stream.getVideoTracks()[0].addEventListener('ended', stopCapture);
      toast('📡 Screen capture started', 'success');
    } catch (e) {
      toast(e.name === 'NotAllowedError' ? '🔒 Permission denied' : `Capture failed: ${e.message}`, 'error');
    }
  };

  const stopCapture = () => {
    streamRef.current?.getTracks().forEach(t => t.stop());
    setCapturing(false); setAutoCapture(false);
    clearInterval(autoRef.current);
  };

  const captureAndAnnotate = useCallback(async () => {
    if (!videoRef.current) return;
    const canvas = canvasRef.current;
    canvas.width = videoRef.current.videoWidth || 1280;
    canvas.height = videoRef.current.videoHeight || 720;
    canvas.getContext('2d').drawImage(videoRef.current, 0, 0);
    const b64 = canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
    setLoading(true);
    try {
      const res = await fetch(`${API}/intelligence/observer/annotate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ screenshot_b64: b64, question }),
      });
      const data = await res.json();

      const newAnn = `[${new Date().toLocaleTimeString()}]\n${data.annotation}`;
      setVisionContext(data.annotation);
      setMessages([{ role: 'ai', text: newAnn }]);

      if (data.method === 'no_vlm') toast('LLaVA not installed', 'warning');
    } catch (e) { toast(`Observer error: ${e.message}`, 'error'); }
    setLoading(false);
  }, [question]);

  const sendChat = async () => {
    if (!chatInput.trim() || !visionContext) return;
    const text = chatInput.trim();
    setChatInput('');
    const newMsg = { role: 'user', text };
    const history = [...messages];
    setMessages(prev => [...prev, newMsg]);
    setChatLoading(true);
    try {
      const res = await fetch(`${API}/intelligence/observer/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          history, new_question: text, vision_context: visionContext
        }),
      });
      const data = await res.json();
      if (data.status === 'ok') setMessages(prev => [...prev, { role: 'ai', text: data.reply }]);
      else toast(`Chat error: ${data.reply}`, 'error');
    } catch (e) { toast(`Chat failed: ${e.message}`, 'error'); }
    setChatLoading(false);
  };

  useEffect(() => {
    if (autoCapture && capturing) {
      autoRef.current = setInterval(captureAndAnnotate, interval * 1000);
      toast(`🎬 Auto-capture every ${interval}s`, 'info');
    } else {
      clearInterval(autoRef.current);
    }
    return () => clearInterval(autoRef.current);
  }, [autoCapture, capturing, interval, captureAndAnnotate]);

  const vlmOk = observerStatus?.vlm_available;

  return (
    <SectorCard icon="🎬" title="Screen Observer API" badge={vlmOk ? 'LLAVA READY' : 'CAPTURE ONLY'} badgeColor={vlmOk ? 'rgba(6,182,212,0.2)' : 'rgba(245,158,11,0.2)'} badgeFg={vlmOk ? '#22d3ee' : '#fbbf24'} status={vlmOk ? 'full' : 'partial'}>
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      {!vlmOk && observerStatus && <WarningBanner msg={`LLaVA not loaded — run: ollama pull llava (~${observerStatus.model_size_gb}GB)`} />}
      {/* Privacy notice */}
      <div style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '8px', padding: '6px 12px', fontSize: '10px', color: '#a5b4fc', display: 'flex', gap: '6px' }}>
        <span>🔒</span>
        <span>Frames sent only to local Ollama (localhost:11434). Nothing leaves your machine.</span>
      </div>
      {/* Question */}
      <Input value={question} onChange={e => setQuestion(e.target.value)} placeholder="What should the AI look for on screen?" />
      {/* Capture controls */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
        {!capturing
          ? <Btn onClick={startCapture} color="#06b6d4">📡 Start Capture</Btn>
          : <Btn onClick={stopCapture} color="#f43f5e">⏹ Stop</Btn>
        }
        <Btn onClick={captureAndAnnotate} loading={loading} disabled={!capturing} color="#8b5cf6">🔍 Annotate Frame</Btn>
        {capturing && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              onClick={() => setAutoCapture(a => !a)}
              style={{ background: autoCapture ? 'rgba(244,63,94,0.15)' : 'rgba(255,255,255,0.05)', border: `1px solid ${autoCapture ? '#f43f5e55' : 'rgba(255,255,255,0.1)'}`, borderRadius: '8px', padding: '5px 12px', color: autoCapture ? '#f87171' : '#64748b', fontSize: '10px', fontWeight: 800, cursor: 'pointer', }}
            >{autoCapture ? '⏹ Stop Auto' : '▶ Auto'}</button>
            {autoCapture && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ fontSize: '10px', color: '#64748b' }}>every</span>
                <select value={interval} onChange={e => setIntervalSecs(Number(e.target.value))} style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', padding: '3px 6px', color: '#e2e8f0', fontSize: '10px', outline: 'none' }}>
                  {[5, 10, 15, 30, 60].map(v => <option key={v} value={v}>{v}s</option>)}
                </select>
              </div>
            )}
          </div>
        )}
      </div>
      {/* Live status */}
      {capturing && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#f43f5e', boxShadow: '0 0 8px #f43f5e', animation: 'pulse 1s infinite' }} />
          <span style={{ fontSize: '10px', color: '#94a3b8' }}>
            {autoCapture ? `Live — annotating every ${interval}s` : 'Capture active — click Annotate Frame'}
          </span>
        </div>
      )}

      {/* Chat Messages */}
      {messages.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '240px', overflowY: 'auto' }}>
          {messages.map((m, i) => (
            m.role === 'ai' ? <ResultBox key={i} color="#06b6d4" maxH="none">{m.text}</ResultBox>
              : <div key={i} style={{ alignSelf: 'flex-end', background: 'rgba(99,102,241,0.2)', border: '1px solid rgba(99,102,241,0.4)', padding: '8px 12px', borderRadius: '12px 12px 0 12px', color: '#e2e8f0', fontSize: '12px', maxWidth: '85%' }}>{m.text}</div>
          ))}
          {chatLoading && <div style={{ color: '#06b6d4', fontSize: '12px', padding: '8px' }}>🤖 Thinking...</div>}
        </div>
      )}

      {/* Chat Input */}
      {visionContext && (
        <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
          <Input value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendChat()} placeholder="Ask a follow-up about the screen..." style={{ background: 'rgba(0,0,0,0.6)' }} />
          <Btn onClick={sendChat} loading={chatLoading} color="#06b6d4" size="sm">Ask</Btn>
        </div>
      )}
    </SectorCard>
  );
}

// ─── Sector 6: Advanced Upgrades Roadmap ──────────────────────────────────────
function UpgradesPanel() {
  const [search, setSearch] = useState('');
  const upgrades = [
    { title: '🎨 Live Interactive Artifacts (Claude-Style Canvas)', desc: 'Right now, the Docker Sandbox returns terminal output (text/errors). We could upgrade the frontend ChatWindow so that if the AI generates HTML, CSS, React, or Javascript, it mounts an isolated, real-time <iframe /> directly inside the chat.' },
    { title: '🕵️‍♂️ Autonomous Background Task Delegation', desc: 'Upgrade the PipelineManager to support async background routing. If you tell it, "Refactor all 30 files in the frontend components folder to use Tailwind", the system silently uses a worker agent to rewrite the codebase in the background.' },
    { title: '🛡️ Multimodal Antibot Resolution IQ', desc: 'Integrated LLaVA-based visual reasoning into the Browser Sector. The agent can now "see" reCAPTCHA image grids, identify target objects, and execute coordinate-based clicks to bypass security gates.' },
    { title: '📸 Multimodal Vector Memory (Visual RAG)', desc: 'Currently, your FAISS neural memory only indexes text and code documents. We could modify the Screen Observer Sector so that every screen annotation is injected into the FAISS memory pool.' },
    { title: '🗃️ Git-Aware Context Tracking & Auto-Snapshots', desc: 'Upgrade the Deep Workspace Indexer to actively read the project\'s .git/ folder. Runs git commit -m "AI Auto-Save" automatically before executing dangerous filesystem modifications.' },
    { title: '🎙️ Ultra-Low Latency Voice Sockets (GPT-4o Style)', desc: 'Bypass the standard HTTP Request/Response cycle for chat by implementing a persistent FastAPI WebSocket connection hooked locally to Whisper.cpp and a fast local TTS model.' },
  ];

  const filtered = upgrades.filter(u => u.title.toLowerCase().includes(search.toLowerCase()) || u.desc.toLowerCase().includes(search.toLowerCase()));

  return (
    <SectorCard icon="🚀" title="Future Upgrades" badge="ROADMAP" badgeColor="rgba(139,92,246,0.2)" badgeFg="#c084fc" status="full">
      <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search specific features..." />
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '8px', maxHeight: '300px', overflowY: 'auto' }}>
        {filtered.map((u, i) => (
          <div key={i} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '10px', padding: '12px' }}>
            <h4 style={{ margin: '0 0 6px 0', fontSize: '13px', color: '#e2e8f0' }}>{u.title}</h4>
            <p style={{ margin: 0, fontSize: '11px', color: '#94a3b8', lineHeight: '1.6' }}>{u.desc}</p>
          </div>
        ))}
      </div>
    </SectorCard>
  );
}

// ─── Sector 7: Autonomous Browser Agent ─────────────────────────────────────────
function BrowserAgentPanel({ toast, sysStatus }) {
  const [url, setUrl] = useState('https://github.com');
  const [action, setAction] = useState('extract');
  const [instruction, setInstruction] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [logs, setLogs] = useState([]);
  const [cursor, setCursor] = useState(null);
  const [isClicking, setIsClicking] = useState(false);

  const addLog = (msg) => setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 5));

  useEffect(() => {
    if (result && result.actions && result.actions.length > 0) {
      let i = 0;
      const interval = setInterval(() => {
        if (i < result.actions.length) {
          const act = result.actions[i];
          setCursor(act);
          if (act.type === 'click') {
            setIsClicking(true);
            setTimeout(() => setIsClicking(false), 600);
          }
          i++;
        } else {
          setTimeout(() => setCursor(null), 2000);
          clearInterval(interval);
        }
      }, 1200);
      return () => clearInterval(interval);
    }
  }, [result]);

  const runBrowser = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setLogs([]);
    addLog(`🚀 Initiating session for ${url}...`);
    try {
      addLog(`🔍 Analyzing page structure and security gates...`);
      const res = await fetch(`${API}/intelligence/browser/act`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, action, instruction }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        setResult(data);
        addLog(`✅ Task complete. Final URL: ${(data.url || '').substring(0, 30)}...`);
      }
      else {
        toast(`Browser error: ${data.message}`, 'error');
        addLog(`❌ Error: ${data.message}`);
      }
    } catch (e) { 
      toast(`Call failed: ${e.message}`, 'error'); 
      addLog(`❌ Connection failure.`);
    }
    setLoading(false);
  };

  const browserStatus = sysStatus?.sectors?.browser;

  return (
    <SectorCard icon="🌐" title="Browser Operator Agent" badge={browserStatus === 'full' ? 'AUTONOMOUS NAVIGATION' : 'MANUAL MODE'} badgeColor={browserStatus === 'full' ? 'rgba(236,72,153,0.2)' : 'rgba(244,63,94,0.2)'} badgeFg={browserStatus === 'full' ? '#f472b6' : '#f87171'} status={browserStatus || 'offline'}>
      <div style={{ background: 'rgba(236,72,153,0.08)', border: '1px solid rgba(236,72,153,0.2)', borderRadius: '8px', padding: '6px 12px', fontSize: '10px', color: '#fbcfe8', marginBottom: '12px' }}>
        🤖 Fully Automated Headless Chromium via Playwright. <span style={{ color: '#f472b6', fontWeight: 800 }}>V-RESOLVE ACTIVE:</span> Autonomous bypass for reCAPTCHA/Turnstile via LLaVA visual coordinate clicks.
      </div>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
        <select value={action} onChange={e => setAction(e.target.value)} style={{ background: 'rgba(0,0,0,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '0 8px', color: '#e2e8f0', fontSize: '12px', outline: 'none' }}>
          <option value="extract">Extract Info (Scroll + DOM)</option>
          <option value="plan_and_execute">🎨 Plan & Execute (VLP)</option>
          <option value="goto">Navigate</option>
          <option value="click">Click Element (by text)</option>
          <option value="type">Type (selector:text)</option>
        </select>
        <Input value={url} onChange={e => setUrl(e.target.value)} placeholder="https://..." style={{ flex: 1 }} />
      </div>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
        <Input value={instruction} onChange={e => setInstruction(e.target.value)} placeholder={action === 'goto' ? '(Optional) Context' : 'Instruction e.g. "Submit" or "#search:hello"'} style={{ flex: 1 }} />
        <Btn onClick={runBrowser} loading={loading} color="#ec4899">▶ Execute</Btn>
      </div>

      {loading && <div style={{ color: '#ec4899', fontSize: '12px', padding: '8px', animation: 'pulse 1s infinite' }}>🤖 Operating headless browser... please wait</div>}

      {result && result.screenshot && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ position: 'relative', width: '100%', borderRadius: '8px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
            <img src={`data:image/jpeg;base64,${result.screenshot}`} alt="Browser Result" style={{ width: '100%', display: 'block' }} />
            {cursor && (
              <div style={{
                position: 'absolute',
                left: `${(cursor.x / 1280) * 100}%`,
                top: `${(cursor.y / 800) * 100}%`,
                width: isClicking ? '40px' : '30px',
                height: isClicking ? '40px' : '30px',
                background: isClicking ? 'rgba(236,72,153,0.6)' : 'rgba(236,72,153,0.35)',
                borderRadius: '50%',
                border: `3px solid ${isClicking ? '#ffffff' : '#f472b6'}`,
                transform: 'translate(-50%, -50%)',
                transition: 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
                pointerEvents: 'none', zIndex: 10,
                boxShadow: isClicking ? '0 0 25px #f472b6, 0 0 50px rgba(236,72,153,0.4)' : '0 0 15px #f472b6'
              }}>
                {isClicking && (
                  <div style={{
                    position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                    width: '100%', height: '100%', borderRadius: '50%',
                    border: '4px solid #f472b6', animation: 'ripple 0.6s ease-out', opacity: 0
                  }} />
                )}
                <div style={{ position: 'absolute', top: isClicking ? '45px' : '35px', left: '50%', transform: 'translateX(-50%)', background: isClicking ? '#ffffff' : '#ec4899', color: isClicking ? '#ec4899' : 'white', fontSize: '9px', padding: '2px 8px', borderRadius: '4px', whiteSpace: 'nowrap', fontWeight: 900, transition: 'all 0.3s' }}>
                  🖱️ {cursor.label}
                </div>
              </div>
            )}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>Point-Wise Visual Extraction:</div>
            {result.synced && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '12px', padding: '2px 8px' }}>
                <span style={{ fontSize: '10px', color: '#34d399', fontWeight: 800 }}>🧠 SYNCED TO NEURAL MEMORY</span>
              </div>
            )}
          </div>
          <ResultBox color="#f472b6" maxH="250px" style={{ whiteSpace: 'pre-wrap' }}>{result.analysis}</ResultBox>
        </div>
      )}

      {/* Autonomous Activity Log */}
      <div style={{ marginTop: '16px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '10px', border: '1px solid rgba(255,255,255,0.05)' }}>
        <div style={{ fontSize: '10px', color: '#64748b', fontWeight: 800, marginBottom: '6px', display: 'flex', justifyContent: 'space-between' }}>
          <span>ACTIVITY LOG</span>
          {loading && <span style={{ color: '#f472b6', animation: 'pulse 1.5s infinite' }}>PROCESSING...</span>}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {logs.length > 0 ? logs.map((l, i) => (
            <div key={i} style={{ fontSize: '10px', color: i === 0 ? '#f1f5f9' : '#94a3b8', fontFamily: 'monospace' }}>{l}</div>
          )) : (
            <div style={{ fontSize: '10px', color: '#475569', fontStyle: 'italic' }}>Waiting for instruction...</div>
          )}
        </div>
      </div>
    </SectorCard>
  );
}

// ─── Intelligence HQ Page ─────────────────────────────────────────────────────
export default function IntelligenceHQPage() {
  const { toasts, toast } = useToast();
  const [sysStatus, setSysStatus] = useState(null);

  useEffect(() => {
    fetch(`${API}/intelligence/status`)
      .then(r => r.json())
      .then(d => setSysStatus(d))
      .catch(() => { });
  }, []);

  const statusBadge = (s) => ({
    full: { bg: 'rgba(16,185,129,0.15)', color: '#34d399', label: 'FULL' },
    partial: { bg: 'rgba(245,158,11,0.15)', color: '#fbbf24', label: 'PARTIAL' },
    keyword_only: { bg: 'rgba(245,158,11,0.15)', color: '#fbbf24', label: 'KEYWORD' },
    local_only: { bg: 'rgba(245,158,11,0.15)', color: '#fbbf24', label: 'LOCAL' },
    capture_only: { bg: 'rgba(245,158,11,0.15)', color: '#fbbf24', label: 'CAPTURE' },
    isolated: { bg: 'rgba(16,185,129,0.15)', color: '#34d399', label: 'ISOLATED' },
  }[s] || { bg: 'rgba(244,63,94,0.15)', color: '#f87171', label: 'OFFLINE' });

  const sectorMeta = [
    { key: 'memory', icon: '🧠', name: 'Memory' },
    { key: 'debate', icon: '⚖️', name: 'Debate' },
    { key: 'canvas', icon: '🎭', name: 'Canvas' },
    { key: 'sandbox', icon: '🛡️', name: 'Sandbox' },
    { key: 'observer', icon: '🎬', name: 'Observer' },
    { key: 'upgrades', icon: '🚀', name: 'Upgrades' },
    { key: 'browser', icon: '🌐', name: 'Browser' },
  ];

  return (
    <div style={{ flex: 1, overflowY: 'auto', background: '#020617', padding: '32px 36px', fontFamily: 'ui-sans-serif,system-ui,sans-serif' }}>
      <ToastArea toasts={toasts} />

      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '10px' }}>
          <div style={{ padding: '10px 14px', borderRadius: '14px', background: 'linear-gradient(135deg,rgba(99,102,241,0.2),rgba(139,92,246,0.2))', border: '1px solid rgba(139,92,246,0.3)', fontSize: '22px' }}>🛰️</div>
          <div>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 900, color: '#f1f5f9', letterSpacing: '-0.03em' }}>Intelligence HQ</h1>
            <p style={{ margin: 0, fontSize: '12px', color: '#475569' }}>Neural Memory · Debate · Canvas · Sandbox · Observer</p>
          </div>
        </div>
        {/* Live sector status bar */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {sectorMeta.map(s => {
            const sStatus = sysStatus?.sectors?.[s.key];
            const badge = statusBadge(sStatus);
            return (
              <div key={s.key} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '10px', padding: '5px 12px', display: 'flex', alignItems: 'center', gap: '7px' }}>
                <span style={{ fontSize: '12px' }}>{s.icon}</span>
                <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>{s.name}</span>
                {sysStatus ? (
                  <span style={{ fontSize: '8px', fontWeight: 800, padding: '2px 7px', borderRadius: '6px', background: badge.bg, color: badge.color, letterSpacing: '0.08em' }}>{badge.label}</span>
                ) : <Skeleton h="16px" w="40px" />}
              </div>
            );
          })}
        </div>
      </div>

      {/* Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(500px,1fr))', gap: '20px' }}>
        <NeuralMemoryPanel toast={toast} sysStatus={sysStatus} />
        <DebatePanel toast={toast} />
        <LiveCanvasPanel toast={toast} />
        <SandboxPanel toast={toast} sysStatus={sysStatus} />
        <ScreenObserverPanel toast={toast} sysStatus={sysStatus} />
        <BrowserAgentPanel toast={toast} sysStatus={sysStatus} />
        <UpgradesPanel />
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
        @keyframes ripple {
          0% { transform: translate(-50%, -50%) scale(0.8); opacity: 1; }
          100% { transform: translate(-50%, -50%) scale(2.5); opacity: 0; }
        }
        @keyframes slideInRight { from { transform:translateX(40px); opacity:0; } to { transform:translateX(0); opacity:1; } }
        *::-webkit-scrollbar { width:4px; height:4px; }
        *::-webkit-scrollbar-track { background:transparent; }
        *::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.09); border-radius:4px; }
        select option { background:#1e293b; }
      `}</style>
    </div>
  );
}
