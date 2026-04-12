import React from 'react';

export default function LinkPreview({ href, children }) {
  try {
    const url = new URL(href);
    const domain = url.hostname.replace('www.', '');
    
    return (
      <a 
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 px-2 py-0.5 mt-1 bg-slate-800/60 rounded border border-slate-700 text-blue-400 hover:text-blue-300 hover:bg-slate-700/80 hover:border-blue-500/50 transition-colors no-underline group text-sm"
        title={href}
      >
        <span className="opacity-80 group-hover:opacity-100">🔗</span>
        <span className="font-medium">{children}</span>
        <span className="text-slate-500 text-xs ml-1">({domain})</span>
      </a>
    );
  } catch (e) {
    // Fallback if URL is invalid
    return <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">{children}</a>;
  }
}
