import React from 'react';
import ReactMarkdown from 'react-markdown';
import LinkPreview from './LinkPreview';

export default function ReportRenderer({ content }) {
  // Strip the Confidence string from the bottom if it exists so we can render it cleanly
  // But wait, MessageBubble already extracts confidence. We will just render whatever is passed.
  
  return (
    <div className="bg-slate-800/40 border border-slate-700/80 rounded-2xl overflow-hidden shadow-lg mt-2 w-full max-w-[800px] mx-auto">
      <div className="bg-slate-800/80 px-5 py-3 border-b border-slate-700/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-blue-400 text-lg">🔎</span>
          <span className="font-semibold text-slate-200 tracking-wide text-xs uppercase">Deep Research Report</span>
        </div>
      </div>
      <div className="p-6 md:p-8 text-[15.5px] leading-[1.75] max-w-[700px] mx-auto">
        <ReactMarkdown
          components={{
            h1: ({node, ...props}) => <h1 className="text-3xl font-extrabold text-white mb-6 mt-2 border-b border-slate-700/60 pb-3 block" {...props} />,
            h2: ({node, ...props}) => <h2 className="text-xl font-bold text-blue-100 mt-10 mb-4 block" {...props} />,
            h3: ({node, ...props}) => <h3 className="text-lg font-semibold text-emerald-200 mt-8 mb-3 block" {...props} />,
            p: ({node, ...props}) => <p className="text-slate-300 mb-6 block" {...props} />,
            ul: ({node, ...props}) => <ul className="list-disc pl-6 mb-6 space-y-2.5 text-slate-300 block" {...props} />,
            ol: ({node, ...props}) => <ol className="list-decimal pl-6 mb-6 space-y-2.5 text-slate-300 block" {...props} />,
            li: ({node, ...props}) => <li className="pl-1" {...props} />,
            code: ({node, inline, className, ...props}) => 
              inline ? <code className="bg-slate-900/80 text-blue-300 px-1.5 py-0.5 rounded-md text-[13px] font-mono border border-slate-700" {...props} />
                     : <pre className="bg-[#0d1117] border border-slate-700/80 p-4 rounded-xl overflow-x-auto mb-6 shadow-inner"><code className="text-[13px] font-mono text-slate-300" {...props} /></pre>,
            blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-blue-500/60 pl-4 py-1.5 my-6 italic bg-blue-900/10 rounded-r-xl text-slate-400" {...props} />,
            a: ({node, ...props}) => <LinkPreview {...props} />
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
