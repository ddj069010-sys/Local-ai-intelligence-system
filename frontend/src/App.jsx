import React, { useState, useEffect } from 'react';
import ChatWindow from './components/ChatWindow';
import Sidebar from './components/Sidebar';
import MemoryPage from './pages/MemoryPage';
import DatabasePage from './pages/DatabasePage';
import RightPanel from './components/RightPanel';
import WorkspacePage from './pages/WorkspacePage';
import IntelligenceControl from './components/IntelligenceControl';
import RagPanel from './components/RagPanel';
import Canvas from './components/Canvas';
import IntelligenceHQPage from './pages/IntelligenceHQPage';
import './index.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [activeChatId, setActiveChatId] = useState(localStorage.getItem('lastChatId') || 'default');
  const [chats, setChats] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [view, setView] = useState('chat'); // 'chat', 'memory', 'database', 'workspace'
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(false);
  
  // 🧠 Global Intelligence State
  const [model, setModel] = useState(localStorage.getItem('preferred_model') || 'auto');
  const [webMode, setWebMode] = useState(localStorage.getItem('web_mode_enabled') === 'true');
  const [availableModels, setAvailableModels] = useState([
    'auto', 
    'gemma3:4b', 
    'gemma3:27b', 
    'llama3:8b', 
    'llama3:70b', 
    'deepseek-r1:32b', 
    'qwen2.5-coder:7b'
  ]);
  const [ragPanelOpen, setRagPanelOpen] = useState(false);
  const [canvasContent, setCanvasContent] = useState(null);
  const [canvasTitle, setCanvasTitle] = useState('');

  const toggleRightPanel = () => setIsRightPanelOpen(!isRightPanelOpen);

  const fetchChats = async () => {
    try {
      const res = await fetch(`${API_BASE}/chats`);
      const data = await res.json();
      setChats(data);
    } catch (e) {
      console.error("Failed to fetch chats", e);
    }
  };

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch(`${API_BASE}/models`);
        if (response.ok) {
          const data = await response.json();
          const models = Array.isArray(data) ? data : [];
          if (!models.includes('auto')) {
            models.unshift('auto');
          }
          setAvailableModels(models);
        }
      } catch (e) {
        console.error("Failed to fetch models", e);
      }
    };
    fetchModels();
  }, []);

  useEffect(() => {
    fetchChats();
  }, [activeChatId]);

  useEffect(() => {
    localStorage.setItem('lastChatId', activeChatId);
  }, [activeChatId]);

  useEffect(() => {
    localStorage.setItem('preferred_model', model);
  }, [model]);

  useEffect(() => {
    localStorage.setItem('web_mode_enabled', webMode);
  }, [webMode]);

  const handleNewChat = async () => {
    try {
      const res = await fetch(`${API_BASE}/chats`, { method: 'POST' });
      const newChat = await res.json();
      setActiveChatId(newChat.chat_id);
      fetchChats();
    } catch (e) {
      console.error("Failed to create chat", e);
    }
  };

  const handleDeleteChat = async (id) => {
    try {
      await fetch(`${API_BASE}/chats/${id}`, { method: 'DELETE' });
      if (activeChatId === id) {
        setActiveChatId('default');
      }
      fetchChats();
    } catch (e) {
      console.error("Failed to delete chat", e);
    }
  };

  const handleRenameChat = async (id, newTitle) => {
    try {
      await fetch(`${API_BASE}/chats/${id}?title=${encodeURIComponent(newTitle)}`, { method: 'PATCH' });
      fetchChats();
    } catch (e) {
      console.error("Failed to rename chat", e);
    }
  };

  // Polling for auto-naming updates
  useEffect(() => {
    const hasUnnamedChats = chats.some(c => 
      c.title === "New Chat" || 
      c.title === "🌟 New Encounter" || 
      c.title === "✨ Generating..."
    );
    if (!hasUnnamedChats) return;

    const interval = setInterval(() => {
      fetchChats();
    }, 3000);

    return () => clearInterval(interval);
  }, [chats]);

  const filteredChats = chats.filter(c => 
    (c.title || c.summary || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex w-screen h-screen m-0 p-0 overflow-hidden bg-slate-900 font-sans selection:bg-blue-500/30">
      <Sidebar 
        chats={filteredChats}
        activeChatId={activeChatId}
        onSelectChat={(id) => { setActiveChatId(id); setView('chat'); }}
        onNewChat={() => { handleNewChat(); setView('chat'); }}
        onSearch={setSearchQuery}
        onDeleteChat={handleDeleteChat}
        onRenameChat={handleRenameChat}
        view={view}
        onViewChange={setView}
      />
      <div className={`flex-1 flex flex-col min-w-0 transition-premium relative ${isRightPanelOpen && view === 'chat' ? 'mr-80' : ''}`}>
        {view === 'chat' ? (
          <div className="flex h-full w-full relative overflow-hidden">
            <div className="flex-1 flex flex-col min-w-0 transition-premium">
              <ChatWindow 
                key={activeChatId} 
                sessionId={activeChatId} 
                refreshSessions={fetchChats} 
                onToggleRightPanel={toggleRightPanel}
                isRightPanelOpen={isRightPanelOpen}
                globalModel={model}
                globalWebMode={webMode}
                availableModels={availableModels}
                onModelChange={async (newModel) => {
                  if (model !== newModel && model !== 'auto') {
                    try {
                      await fetch(`${API_BASE}/models/unload?model=${encodeURIComponent(model)}`, { method: 'POST' });
                    } catch (e) { console.error("Unload failed", e); }
                  }
                  setModel(newModel);
                }}
                onWebModeChange={setWebMode}
                ragPanelOpen={ragPanelOpen}
                onToggleRagPanel={() => setRagPanelOpen(o => !o)}
                onPinToCanvas={(title, content) => { setCanvasTitle(title); setCanvasContent(content); }}
              />
            </div>
            {canvasContent && (
              <div className="w-[50%] h-full z-20 border-l border-white/5">
                <Canvas 
                  content={canvasContent} 
                  title={canvasTitle} 
                  onClose={() => setCanvasContent(null)} 
                />
              </div>
            )}
          </div>
        ) : view === 'memory' ? (
          <MemoryPage />
        ) : view === 'workspace' ? (
          <WorkspacePage />
        ) : view === 'hq' ? (
          <IntelligenceHQPage />
        ) : (
          <DatabasePage />
        )}
      </div>
      
      {/* 🧭 Global Intelligence Control (Sticky Right) */}
      {view === 'chat' && (
        <IntelligenceControl 
          model={model}
          setModel={setModel}
          webMode={webMode}
          setWebMode={setWebMode}
          availableModels={availableModels}
        />
      )}

      {view === 'chat' && (
        <RightPanel 
          isOpen={isRightPanelOpen} 
          onClose={toggleRightPanel} 
          messages={[]} 
          activeFiles={[]}
        />
      )}
      {/* 📄 RAG Document Panel */}
      <RagPanel isOpen={ragPanelOpen} onClose={() => setRagPanelOpen(false)} />

    </div>
  );
}

export default App;
