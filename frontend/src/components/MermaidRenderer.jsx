import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'Inter, sans-serif'
});

const MermaidRenderer = ({ chart }) => {
  const mermaidRef = useRef(null);

  useEffect(() => {
    if (mermaidRef.current && chart) {
      mermaidRef.current.removeAttribute('data-processed');
      mermaid.contentLoaded();
    }
  }, [chart]);

  return (
    <div className="mermaid-chart-container my-8 p-6 bg-slate-900/50 rounded-3xl border border-blue-500/20 shadow-premium overflow-x-auto flex justify-center">
      <div ref={mermaidRef} className="mermaid">
        {chart}
      </div>
    </div>
  );
};

export default MermaidRenderer;
