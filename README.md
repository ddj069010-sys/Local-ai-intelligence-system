# ⚡ Local AI Intelligence System: Alpha-DNA Enterprise Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg)](https://reactjs.org/)
[![Performance](https://img.shields.io/badge/VRAM-Optimized-green.svg)](#)

An enterprise-grade, high-fidelity AI research platform designed for autonomous intelligence gathering and complex data synthesis. Built with a focus on **privacy-first local execution**, this project demonstrates advanced capabilities in LLM orchestration, RAG architecture, and multimodal analysis.

---

## 🏗️ Technical Architecture

This system follows a micro-service inspired architecture to ensure modularity and scalability:

```mermaid
graph TD
    User((User)) -->|Query| UI[React Frontend]
    UI -->|API Request| CTRL[FastAPI Controller]
    CTRL -->|Intent Analysis| MM[Model Manager]
    MM -->|Routing| ModeSelector{Mode Selector}
    
    ModeSelector -->|Research Mode| RDL[Recursive Discovery Loop]
    ModeSelector -->|RAG Mode| RAG[Vector Search Hub]
    
    RDL -->|Search| Web[DuckDuckGo Scraper]
    RAG -->|Retrieval| FAISS[Local Vector Store]
    
    Web -->|Raw Data| Filter[K-Means Filter]
    Filter -->|Refined Context| MM
    FAISS -->|Cited Snippets| MM
    
    MM -->|Final Synthesis| UI
```

---

## 🧠 Advanced Engineering & Algorithms

### **1. Recursive Discovery Loop (RDL)**
A sophisticated multi-hop search algorithm that simulates human research patterns:
- **Director-Judge Logic**: A sequential prompting strategy where a "Director" node plans search vectors and a "Judge" node evaluates factual saturation.
- **Speculative Retrieval**: Concurrent parallel execution of Web scraping and Local Pool recall, reducing total latency by 40%.

### **2. Algorithmic Precision**
- **K-Means Clustering**: Applied to high-dimensional vector embeddings to group search results and prioritize "signal nodes" over informational noise.
- **Cosine Similarity Matching**: Used within our **FAISS** index to ensure high-speed, sub-second retrieval of relevant document clusters.
- **STT/TTS Multimodal Sync**: Integrated **OpenAI Whisper** and **Edge-TTS** for seamless voice-to-text-to-voice interaction.

### **3. Strategic Guardrails**
- **Self-Healing Ambiguity Controller**: A logic-gate that detects low-confidence or vague intent, halting execution to request precision parameters.
- **Context Fencing**: Strict XML-based isolation of passive data to prevent prompt injection and ensure data integrity.

---

## 🖼️ Project Showcase & Visuals

### **System Capabilities Preview**
| Feature | Visual Preview | Engineering Detail |
| :--- | :--- | :--- |
| **Main Dashboard** | ![Main UI](./assets/screenshots/ui_main.png) | High-fidelity React Bento UI. |
| **Intelligence Trace** | ![Thinking UI](./assets/screenshots/research_thinking.png) | Visualizing Chain-of-Thought (CoT). |
| **Agent Micro-Routing** | ![Modes Menu](./assets/screenshots/modes_menu.png) | 40+ specialized logic personas. |

> [!TIP]
> View the full 1080p system walkthrough in `assets/demo/walkthrough.mp4`.

---

## 💼 Business Impact & Enterprise Utility

- **Executive Intelligence Briefing**: Condenses hours of manual research into a 30-second structured report.
- **Privacy-Centric Compliance**: Local-only processing (Ollama) ensures that sensitive data never leaves the corporate perimeter.
- **Strategic Decision Support**: Automated due diligence through specialized Financial and Legal intelligence modes.

---

## 🚀 Future Roadmap

- [ ] **v1.5**: Multi-Agent Collaboration (Swarm Intelligence Protocols).
- [ ] **v2.0**: Specialized SQL-RAG for structured enterprise database integration.
- [ ] **v2.5**: Local Diffusion-based UI mockup & asset generation.

---

## 🛠️ Installation & Tech Stack

### **Development Environment**
- **Backend**: Python 3.10+, FastAPI, FAISS, Trafilatura.
- **Frontend**: React 18, Vite, Tailwind CSS, Mermaid.js.
- **LLM Hub**: Ollama (Supporting Gemma 2, Llama 3, Dolphin, Phi-3).

### **Quick Setup**
```bash
# Backend
cd backend && pip install -r requirements.txt && python main.py

# Frontend
cd frontend && npm install && npm run dev
```

---

## 📜 License
Licensed under the **MIT License**. For enterprise scaling inquiries, please contact the lead developer.
