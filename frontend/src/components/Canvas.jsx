import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import MermaidRenderer from './MermaidRenderer';
import CodeBlockRenderer from './CodeBlockRenderer';

export default function Canvas({ content: initialContent, title, mode, onClose, onSave }) {
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState('view'); // 'view', 'edit', 'preview'
  const [content, setContent] = useState(initialContent);

  useEffect(() => {
    setContent(initialContent);
  }, [initialContent]);

  const extractCode = (lang) => {
    if (!content || typeof content !== 'string') return '';
    const regex = new RegExp(`\`\`\`${lang}\\n([\\s\\S]*?)\`\`\``, 'ig');
    let code = '';
    let match;
    while ((match = regex.exec(content)) !== null) {
      code += match[1] + '\n';
    }
    return code;
  };

  const htmlCode = extractCode('html');
  const cssCode = extractCode('css');
  const jsCode = extractCode('javascript') || extractCode('js');
  const hasPreviewableCode = htmlCode || cssCode || jsCode;

  if (!content && activeTab !== 'edit') return null;

  const combinedSrcDoc = `
    <!DOCTYPE html>
    <html>
      <head>
        <style>${cssCode}</style>
      </head>
      <body>
        ${htmlCode}
        <script>${jsCode}</script>
      </body>
    </html>
  `;

  return (
    <div className="flex flex-col h-full bg-slate-900 border-l border-white/5 animate-slideUp shadow-2xl">
      {/* Canvas Header */}
      <div className="flex items-center justify-between p-6 border-b border-white/10 bg-black/40 backdrop-blur-md">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3">
             <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></div>
             <span className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Brain Canvas v3.2</span>
          </div>
          <h2 className="text-xl font-black text-white tracking-tight truncate max-w-[400px]">
            {title || "Intelligence Artifact"}
          </h2>
        </div>
        
        <div className="flex items-center gap-2">
           <button 
             onClick={() => setActiveTab(activeTab === 'edit' ? 'view' : 'edit')}
             className={`p-3 rounded-2xl transition-premium flex items-center gap-2 font-bold text-xs ${activeTab === 'edit' ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40' : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
             title={activeTab === 'edit' ? "View Markdown" : "Edit Content"}
           >
             <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
             {activeTab === 'edit' ? "SAVE" : "EDIT"}
           </button>

           {hasPreviewableCode && (
             <button 
               onClick={() => setActiveTab(activeTab === 'preview' ? 'view' : 'preview')}
               className={`p-3 rounded-2xl transition-premium flex items-center gap-2 font-bold text-xs ${activeTab === 'preview' ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/40' : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
               title="Preview Live Code"
             >
               <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
               PREVIEW
             </button>
           )}

           <button 
             onClick={() => {
                const blob = new Blob([content], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${title || 'artifact'}.md`;
                a.click();
             }}
             className="p-3 text-slate-500 hover:text-white hover:bg-white/5 rounded-2xl transition-premium"
             title="Download Artifact"
           >
             <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
           </button>

           <button 
             onClick={onClose}
             className="p-3 text-slate-500 hover:text-red-400 hover:bg-red-400/5 rounded-2xl transition-premium"
             title="Dismiss Canvas"
           >
             <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
           </button>
        </div>
      </div>

      {/* Canvas Content Area */}
      <div className="flex-1 overflow-hidden relative">
        {activeTab === 'edit' ? (
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full h-full p-10 bg-slate-950/50 text-slate-200 font-mono text-lg leading-relaxed focus:outline-none resize-none scrollbar-thin selection:bg-blue-500/30"
            spellCheck={false}
            placeholder="Edit your intelligence artifact here..."
          />
        ) : activeTab === 'view' ? (
          <div className="h-full overflow-y-auto p-10 scrollbar-thin bg-black/20">
            <div className="max-w-4xl mx-auto">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    h2: ({ node, ...props }) => <h2 className="text-3xl font-black text-white mt-12 mb-8 border-b border-white/5 pb-4 tracking-tighter" {...props} />,
                    h3: ({ node, ...props }) => <h3 className="text-xl font-bold text-blue-400 mt-8 mb-4 flex items-center gap-2" {...props} />,
                    p: ({ node, ...props }) => <p className="text-lg text-slate-300 leading-[1.8] mb-6 font-medium" {...props} />,
                    ul: ({ node, ...props }) => <ul className="list-disc pl-8 mb-8 space-y-3 font-medium text-slate-400" {...props} />,
                    li: ({ node, ...props }) => <li className="text-lg" {...props} />,
                    code: ({ node, inline, className, ...props }) => {
                        const match = /language-(\w+)/.exec(className || '');
                        if (!inline && match && match[1] === 'mermaid') {
                          return <MermaidRenderer chart={String(props.children).replace(/\n$/, '')} />;
                        }
                        return inline ? 
                            <code className="bg-white/10 text-blue-300 px-1.5 py-0.5 rounded font-mono text-sm" {...props} /> : 
                            <CodeBlockRenderer language={match ? match[1] : ''} value={String(props.children).replace(/\n$/, '')} />;
                    },
                    blockquote: ({ node, ...props }) => (
                        <blockquote className="border-l-4 border-indigo-500/50 pl-8 py-4 my-10 italic bg-white/5 rounded-r-3xl text-slate-300 text-xl" {...props} />
                    ),
                    table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-12 rounded-3xl border border-white/5 bg-slate-900/40 backdrop-blur-xl shadow-2xl"><table className="w-full text-left" {...props} /></div>
                    ),
                    th: ({ node, ...props }) => <th className="px-8 py-5 text-[11px] font-black uppercase tracking-[0.2em] bg-white/5 text-blue-400" {...props} />,
                    td: ({ node, ...props }) => <td className="px-8 py-6 text-base border-t border-white/5 text-slate-400" {...props} />
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
          </div>
        ) : (
          <div className="h-full bg-white relative border-2 border-white overflow-hidden">
            <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-xl border border-white/20 text-white text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-lg z-10 shadow-2xl">Live Preview Mode</div>
            <iframe
              title="Live Code Preview"
              srcDoc={combinedSrcDoc}
              className="w-full h-full border-none bg-white font-sans"
              sandbox="allow-scripts"
            />
          </div>
        )}
      </div>

      {/* Intelligence Dashboard (Footer) */}
      <div className="p-6 border-t border-white/5 bg-black/60 flex items-center justify-between">
         <div className="flex items-center gap-6">
            <div className="flex flex-col gap-1">
               <span className="text-[9px] font-black uppercase tracking-widest text-slate-600">Sync Status</span>
               <span className="text-xs font-black text-emerald-400 tracking-tighter">Live Neural Pool</span>
            </div>
            <div className="flex flex-col gap-1">
               <span className="text-[9px] font-black uppercase tracking-widest text-slate-600">Integrity</span>
               <span className="text-xs font-black text-blue-400 tracking-tighter">100% Grounded</span>
            </div>
         </div>
         <div className="bg-white/5 px-4 py-2 rounded-xl border border-white/5">
            <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] whitespace-nowrap">Neural Sync Enabled</span>
         </div>
      </div>
    </div>
  );
}
