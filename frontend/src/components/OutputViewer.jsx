import React, { useState } from 'react';
import { Volume2, Globe, Film, Music, FileText, AlertTriangle } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const TYPE_ICONS = {
  youtube: <Film size={16} color="#ff4444" />,
  video: <Film size={16} color="#a855f7" />,
  audio: <Music size={16} color="#06b6d4" />,
  document: <FileText size={16} color="#f59e0b" />,
  webpage: <Globe size={16} color="#22d3ee" />,
};

const OutputViewer = ({ data }) => {
  const [speaking, setSpeaking] = useState(false);

  if (!data) return null;

  const { formatted, title, source, content_type, key_points, insights, warning, error } = data;

  const handleSpeak = async () => {
    if (!formatted) return;
    setSpeaking(true);
    try {
      // Extract just the summary text for TTS
      const lines = formatted.split('\n');
      const summaryStart = lines.findIndex(l => l.includes('### Summary'));
      const summaryEnd = lines.findIndex((l, i) => i > summaryStart && l.startsWith('###'));
      const summaryText = lines
        .slice(summaryStart + 1, summaryEnd > 0 ? summaryEnd : summaryStart + 5)
        .join(' ')
        .trim();

      const res = await fetch(
        `${API_BASE}/voice/tts?text=${encodeURIComponent(summaryText)}&voice=en-US-AriaNeural`
      );
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => { setSpeaking(false); URL.revokeObjectURL(url); };
      audio.play();
    } catch (err) {
      console.error('TTS error:', err);
      setSpeaking(false);
    }
  };

  return (
    <div className="output-viewer">
      {/* Header */}
      <div className="output-header">
        <span className="output-type-badge">
          {TYPE_ICONS[content_type] || <Globe size={16} />}
          <span>{content_type?.toUpperCase() || 'CONTENT'}</span>
        </span>
        <span className="output-source">{source}</span>
        <button
          className={`tts-btn ${speaking ? 'speaking' : ''}`}
          onClick={handleSpeak}
          title="Read Summary Aloud"
          disabled={speaking}
        >
          <Volume2 size={14} /> {speaking ? 'Speaking...' : 'Read'}
        </button>
      </div>

      {/* Warning */}
      {warning && (
        <div className="output-warning">
          <AlertTriangle size={14} />
          {warning}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="output-error">
          <AlertTriangle size={14} />
          Processing error: {error}
        </div>
      )}

      {/* Key Points quick view */}
      {key_points && key_points.length > 0 && (
        <div className="output-quick-points">
          <strong>⚡ Key Points</strong>
          <ul>
            {key_points.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </div>
      )}

      {/* Full Formatted Output (rendered as pre-formatted markdown-ready text) */}
      {formatted && (
        <div className="output-full-content">
          <pre>{formatted}</pre>
        </div>
      )}
    </div>
  );
};

export default OutputViewer;
