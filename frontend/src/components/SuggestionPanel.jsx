import React, { useState, useEffect } from 'react';

const ALL_SUGGESTIONS = [
  { title: "Report on Japan history", prompt: "Create a comprehensive report on the history of Japan." },
  { title: "Explain quantum computing", prompt: "Explain quantum computing simply for a beginner." },
  { title: "Latest AI trends in 2025", prompt: "What are the latest AI trends in 2025?" },
  { title: "Compare Tesla vs BYD", prompt: "Compare the business models and EV sales of Tesla vs BYD." },
  { title: "Analyze global warming", prompt: "Analyze the current trajectory of global warming and its economic impacts." },
  { title: "Future of Space Exploration", prompt: "What is the future timeline for Mars colonization?" },
  { title: "Explain Blockchain tech", prompt: "How does blockchain technology actually work under the hood?" },
  { title: "History of the Roman Empire", prompt: "Summarize the rise and fall of the Roman Empire." },
  { title: "Dietary Science Overview", prompt: "What does modern science say about intermittent fasting?" },
  { title: "Stock Market Basics", prompt: "Explain how to evaluate a company's stock for a beginner." }
];

export default function SuggestionPanel({ setInput }) {
  const [activeSuggestions, setActiveSuggestions] = useState([]);

  useEffect(() => {
    // Pick 4 random suggestions on mount
    const shuffled = [...ALL_SUGGESTIONS].sort(() => 0.5 - Math.random());
    setActiveSuggestions(shuffled.slice(0, 4));
  }, []);

  const handleSuggestion = (prompt) => {
    setInput(prompt);
  };

  return (
    <div className="flex-1 flex items-center justify-center flex-col text-slate-500 gap-6 my-auto animate-fade-in-up px-4">
      <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center border border-slate-700 shadow-sm text-3xl">
        ✨
      </div>
      <h1 className="text-2xl font-bold text-slate-200">What can I help you research today?</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6 w-full max-w-2xl">
        {activeSuggestions.map((s, idx) => (
          <button 
            key={idx}
            className="text-left bg-slate-800/40 p-5 rounded-xl border border-slate-700 hover:bg-slate-750 hover:border-blue-500/50 hover:shadow-[0_0_15px_rgba(59,130,246,0.15)] transition-all duration-300 group"
            onClick={() => handleSuggestion(s.prompt)}
          >
            <div className="text-blue-400 font-semibold mb-1 group-hover:text-blue-300 transition-colors">{s.title}</div>
            <div className="text-xs text-slate-500 line-clamp-1">Click to analyze...</div>
          </button>
        ))}
      </div>
    </div>
  );
}
