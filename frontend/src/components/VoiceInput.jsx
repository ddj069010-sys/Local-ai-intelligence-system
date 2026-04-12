import React, { useState, useRef, useCallback } from 'react';
import { Mic, MicOff, StopCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const VoiceInput = ({ onTranscript, onError }) => {
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        setProcessing(true);
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('audio', blob, 'recording.webm');

        try {
          const res = await fetch(`${API_BASE}/voice/stt`, {
            method: 'POST',
            body: formData,
          });
          const data = await res.json();
          if (data.text) {
            onTranscript && onTranscript(data.text);
          } else {
            onError && onError('Could not transcribe audio');
          }
        } catch (err) {
          onError && onError(String(err));
        } finally {
          setProcessing(false);
          // Release microphone
          stream.getTracks().forEach((t) => t.stop());
        }
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (err) {
      onError && onError('Microphone access denied: ' + String(err));
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  if (processing) {
    return (
      <button className="voice-btn processing" title="Transcribing...">
        <span className="pulse-dot" />
      </button>
    );
  }

  return (
    <button
      className={`voice-btn ${recording ? 'recording' : ''}`}
      onClick={recording ? stopRecording : startRecording}
      title={recording ? 'Stop Recording' : 'Start Voice Input'}
    >
      {recording ? <StopCircle size={18} color="#ff4b4b" /> : <Mic size={18} />}
    </button>
  );
};

export default VoiceInput;
