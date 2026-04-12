import React from 'react';
import { FileText } from 'lucide-react';

export default function RagBadge({ onClick }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 px-2.5 py-1 rounded-[10px] bg-indigo-500/10 border border-indigo-500/20 text-[9px] font-black uppercase tracking-wider text-indigo-400 hover:bg-indigo-500/20 transition-all animate-pulse shadow-[0_0_10px_rgba(99,102,241,0.1)]"
      title="RAG Mode Active – Click to manage documents"
    >
      <FileText size={10} />
      Using Docs
    </button>
  );
}
