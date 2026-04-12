import React, { useState, useEffect, useRef } from 'react';
import { FileText, Upload, Trash2, X, CheckCircle, AlertCircle, Loader, ChevronDown } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function RagPanel({ isOpen, onClose }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // {type: 'success'|'error', message: ''}
  const [loading, setLoading] = useState(false);
  const fileRef = useRef(null);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/rag/files`);
      if (res.ok) {
        const data = await res.json();
        setFiles(data.files || []);
      }
    } catch (e) {
      console.error('Failed to fetch RAG files', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) fetchFiles();
  }, [isOpen]);

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setUploadStatus(null);
    const form = new FormData();
    form.append('file', file);
    try {
      const res = await fetch(`${API_BASE}/rag/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (data.status === 'ok') {
        setUploadStatus({ type: 'success', message: `✅ Indexed ${data.chunks} chunks from "${data.file}"` });
        fetchFiles();
      } else {
        setUploadStatus({ type: 'error', message: data.message || 'Upload failed.' });
      }
    } catch (e) {
      setUploadStatus({ type: 'error', message: String(e) });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const handleDelete = async (filename) => {
    try {
      await fetch(`${API_BASE}/rag/files/${encodeURIComponent(filename)}`, { method: 'DELETE' });
      setFiles(prev => prev.filter(f => f !== filename));
    } catch (e) {
      console.error('Delete failed', e);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-end justify-center pointer-events-none px-4 pb-6">
      <div
        className="pointer-events-auto w-full max-w-sm bg-[#0a0a0a]/95 backdrop-blur-3xl border border-white/10 rounded-[28px] shadow-premium p-5 animate-slideUp"
        style={{ maxHeight: '60vh', overflowY: 'auto' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex flex-col">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Document Index</span>
            <span className="text-sm font-black text-white">📄 RAG Intelligence</span>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-white/10 text-slate-400 hover:text-white transition-all">
            <X size={16} />
          </button>
        </div>

        {/* Upload Area */}
        <div
          className="border-2 border-dashed border-white/10 rounded-[20px] p-4 flex flex-col items-center gap-2 text-center cursor-pointer hover:border-indigo-500/40 hover:bg-indigo-500/5 transition-all group mb-4"
          onClick={() => fileRef.current?.click()}
        >
          <input
            type="file"
            ref={fileRef}
            className="hidden"
            accept=".pdf,.docx,.doc,.txt"
            onChange={(e) => handleUpload(e.target.files?.[0])}
          />
          {uploading ? (
            <Loader size={20} className="text-indigo-400 animate-spin" />
          ) : (
            <Upload size={20} className="text-slate-500 group-hover:text-indigo-400 transition-colors" />
          )}
          <span className="text-[11px] font-bold text-slate-500 group-hover:text-slate-300 transition-colors">
            {uploading ? 'Processing...' : 'Click to upload PDF, DOCX, TXT'}
          </span>
        </div>

        {/* Status Message */}
        {uploadStatus && (
          <div className={`flex items-center gap-2 p-3 rounded-[16px] mb-3 text-[11px] font-bold ${
            uploadStatus.type === 'success' 
              ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' 
              : 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
          }`}>
            {uploadStatus.type === 'success' ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
            {uploadStatus.message}
          </div>
        )}

        {/* File List */}
        <div className="space-y-2">
          {loading ? (
            <div className="text-center py-4">
              <Loader size={16} className="text-slate-600 animate-spin mx-auto" />
            </div>
          ) : files.length === 0 ? (
            <div className="text-center py-4 text-[11px] text-slate-600 font-medium">
              No documents indexed yet.
            </div>
          ) : (
            files.map(file => (
              <div key={file} className="flex items-center gap-3 bg-white/5 rounded-[16px] p-3 border border-white/5 group hover:border-white/10 transition-all">
                <div className="p-2 rounded-xl bg-indigo-500/10">
                  <FileText size={14} className="text-indigo-400" />
                </div>
                <span className="flex-1 text-[11px] font-bold text-slate-300 truncate">{file}</span>
                <button
                  onClick={() => handleDelete(file)}
                  className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-rose-500/10 text-rose-400 transition-all"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))
          )}
        </div>

        <div className="mt-4 pt-3 border-t border-white/5 text-[9px] uppercase tracking-widest text-slate-600 text-center font-black">
          {files.length} document{files.length !== 1 ? 's' : ''} indexed · FAISS local store
        </div>
      </div>
    </div>
  );
}
