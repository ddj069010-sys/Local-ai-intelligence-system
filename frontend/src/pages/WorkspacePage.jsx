import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000/workspace';

export default function WorkspacePage() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');

  const fetchFiles = async () => {
    try {
      const res = await fetch(`${API_BASE}/files`);
      const data = await res.json();
      setFiles(data.files || []);
    } catch (e) {
      console.error("Failed to fetch files", e);
    } finally {
      setLoading(false);
    }
  };

  const readFile = async (name) => {
    try {
      const res = await fetch(`${API_BASE}/files/${name}`);
      const data = await res.json();
      setSelectedFile(name);
      setFileContent(data.content);
    } catch (e) {
      console.error("Failed to read file", e);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-200 overflow-hidden">
      <div className="p-6 border-b border-slate-800 bg-slate-900/50">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <span className="text-emerald-400 text-3xl">📁</span> Workspace
        </h1>
        <p className="text-slate-400 text-sm mt-1">Manage files created and used by JARVIS agent.</p>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* File List */}
        <div className="w-1/3 border-r border-slate-800 overflow-y-auto p-4 space-y-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-500">Files</h2>
            <button onClick={fetchFiles} className="text-slate-500 hover:text-white transition">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 8V2h6"></path></svg>
            </button>
          </div>
          
          {loading ? (
            <div className="text-slate-600 text-xs italic animate-pulse">Loading workspace...</div>
          ) : files.length === 0 ? (
            <div className="text-slate-600 text-xs italic">No files in workspace.</div>
          ) : (
            files.map(f => (
              <div 
                key={f}
                onClick={() => readFile(f)}
                className={`p-3 rounded-xl cursor-pointer transition-all border flex items-center gap-3 ${
                  selectedFile === f 
                    ? 'bg-blue-600/10 border-blue-500/30 text-blue-400' 
                    : 'bg-slate-900/30 border-transparent hover:bg-slate-800/50 text-slate-400'
                }`}
              >
                <span className="text-lg">📄</span>
                <span className="text-xs font-medium truncate">{f}</span>
              </div>
            ))
          )}
        </div>

        {/* File Viewer */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {selectedFile ? (
            <>
              <div className="p-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300 font-mono">{selectedFile}</span>
                <div className="flex gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500/50"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/50"></div>
                </div>
              </div>
              <div className="flex-1 p-6 overflow-auto font-mono text-sm leading-relaxed text-slate-300 bg-[#0d1117] selection:bg-blue-500/30">
                <pre>{fileContent}</pre>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-600 gap-4 opacity-50">
              <span className="text-6xl">📂</span>
              <p className="text-sm">Select a file to view its content.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
