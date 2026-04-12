import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import vscDarkPlus from 'react-syntax-highlighter/dist/esm/styles/prism/vsc-dark-plus';

export default function CodeBlockRenderer({ language, value }) {
  const [copied, setCopied] = useState(false);
  const [isPreview, setIsPreview] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getPreviewHtml = () => {
    const codeLang = (language || '').toLowerCase();
    if (codeLang === 'html' || codeLang === 'svg' || codeLang === 'xml') {
      return value;
    }
    if (codeLang === 'css') {
      return `<html><head><style>${value}</style></head><body style="padding:20px;display:flex;justify-content:center;align-items:center;min-height:90vh;background:#f8f9fa;"><div class="preview-box" id="preview-box" style="padding:40px;border:2px dashed #cbd5e1;border-radius:16px;font-family:sans-serif;color:#64748b;text-align:center;">CSS Applied<br/><span style="font-size:12px;opacity:0.7">Target this element with tags or classes</span></div></body></html>`;
    }
    if (codeLang === 'javascript' || codeLang === 'js') {
      return `<html><body style="font-family:sans-serif;padding:20px;background:#f8f9fa;"><h3>Live Execution</h3><p style="color:#64748b;font-size:12px;margin-bottom:12px;">DOM output will appear below. Check DevTools for console.logs.</p><div id="root"></div><script>${value}</script></body></html>`;
    }
    
    // Fallback for non-renderable code (python, rust, etc.)
    const escapedValue = (value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
    return `<html><body style="font-family:monospace;background:#f8f9fa;padding:20px;color:#334155;white-space:pre-wrap;margin:0;">${escapedValue}</body></html>`;
  };

  return (
    <div className="relative group my-8 border border-white/5 bg-[#050505] rounded-2xl overflow-hidden shadow-2xl">
      <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/5">
        <span className="text-[10px] uppercase font-black text-slate-400 tracking-widest">{language || 'text'}</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsPreview(!isPreview)}
            className={`flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-bold rounded-lg transition-all ${isPreview ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' : 'text-slate-400 hover:text-white bg-white/5 hover:bg-white/10'}`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
            {isPreview ? 'CODE' : 'PREVIEW'}
          </button>
          
          <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-bold text-slate-400 hover:text-white bg-white/5 hover:bg-white/10 rounded-lg transition-all"
        >
          {copied ? (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-400"><polyline points="20 6 9 17 4 12"></polyline></svg>
              <span className="text-emerald-400">COPIED</span>
            </>
          ) : (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              COPY
            </>
          )}
        </button>
        </div>
      </div>
      <div className={`overflow-x-auto text-sm ${isPreview ? 'bg-black p-0' : ''}`}>
        {isPreview ? (
           <iframe
             title="Universal Code Preview"
             srcDoc={getPreviewHtml()}
             className="w-full h-[400px] border-none bg-white font-sans"
             sandbox="allow-scripts"
           />
        ) : (
          <SyntaxHighlighter
            language={language || 'text'}
            style={vscDarkPlus}
            customStyle={{ margin: 0, padding: '1.5rem', background: 'transparent', fontSize: '0.85rem', lineHeight: '1.6' }}
            showLineNumbers={value ? value.split('\n').length > 10 : false}
          >
            {value || ''}
          </SyntaxHighlighter>
        )}
      </div>
    </div>
  );
}
