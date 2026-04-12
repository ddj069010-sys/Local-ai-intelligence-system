# ⚡ Local AI Intelligence System: Alpha-DNA Enterprise Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg)](https://reactjs.org/)
[![Performance](https://img.shields.io/badge/VRAM-Optimized-green.svg)](https://github.com/ddj069010-sys/local-ai-intelligence-system)

An enterprise-grade, high-fidelity AI research platform designed for autonomous intelligence gathering and complex data synthesis. Built with a focus on **privacy-first local execution**, this project demonstrates advanced capabilities in LLM orchestration, RAG architecture, and multimodal analysis.

---

## 📺 Project Showcase & Visuals

### **System Capabilities & UI Flow**

<https://github.com/ddj069010-sys/local-ai-intelligence-system/blob/main/assets/demo/walkthrough.mp4?raw=true>

| Feature | Visual Preview | Engineering Detail |
| :--- | :--- | :--- |
| **Main Interface** | ![Main UI](./assets/screenshots/ui_main.png) | High-fidelity React Bento UI with dynamic theme synchronization. |
| **User Interaction** | ![Interaction](./assets/screenshots/user_interaction.png) | Real-time chat dialogue and contextual response generation. |
| **Research Logic** | ![Thinking UI](./assets/screenshots/research_thinking.png) | Visualizing recursive Chain-of-Thought (CoT) and discovery loops. |
| **Model Catalog** | ![Modes Menu](./assets/screenshots/modes_and_models.png) | Access point for 20+ specialized intelligence personas. |
| **Multimodal Hub** | ![Video Analysis](./assets/screenshots/multimodal_analysis.png) | Backend processing for video transcripts and external links. |
| **Backend Engine**  | ![Backend Terminal](./assets/screenshots/backend_terminal.png) | High-concurrency FastAPI controller and resource management. |
| **Operational Logs** | ![Execution Logs](./assets/screenshots/execution_logs.png) | Detailed execution traces during research tasks. |


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

### **3. Strategic Guardrails**

- **Self-Healing Ambiguity Controller**: A logic-gate that detects low-confidence or vague intent, halting execution to request precision parameters.
- **Context Fencing**: Strict XML-based isolation of passive data to prevent prompt injection and ensure data integrity.

## 🛠️ Comprehensive Technology Stack & AI Models

### **1. AI & LLM Orchestration**

- **LLM Engine**: **Ollama** (Local execution for privacy and speed).
- **Primary Models**:
  - **Gemma 2 (2b/9b)**: Core reasoning and synthesis.
  - **Llama 3 (8b)**: Complex logical instruction following.
  - **Dolphin 2.9 (8b)**: Uncensored, creative research tasks.
  - **Phi-3 Mini**: Ultra-fast extraction and simple classification.
- **Embedding Models**: **BGE-Small-EN-v1.5** & **Snowflake-Arctic** for high-precision semantic search.

### **2. Backend Intelligence (Python Ecosystem)**

- **Framework**: **FastAPI** (Asynchronous, high-performance API).
- **Vector Database**: **FAISS** (Facebook AI Similarity Search) for local vector sharding.
- **Speech & Media**:
  - **OpenAI Whisper**: Local Speech-to-Text (STT).
  - **Edge-TTS**: Microsoft Azure based Neural Text-to-Speech.
  - **yt-dlp**: YouTube transcript and metadata extraction.
- **Data Scavenging**: **Trafilatura**, **BeautifulSoup4**, and **DuckDuckGo API**.
- **Document Intelligence**: **PyMuPDF**, **python-docx**, **openpyxl**, and **python-pptx**.

### **3. Frontend Experience (Modern Web Tech)**

- **Framework**: **React 18** powered by **Vite**.
- **Styling**: **Tailwind CSS** with custom **Bento UI** glassmorphism.
- **Visualization**: **Mermaid.js** (Live diagrams) & **Monaco Editor** (Code syntax highlighting).
- **Connectivity**: **Axios** with real-time SSE (Server-Sent Events) for streaming AI tokens.

### **4. System & Infrastructure**

- **Environment**: Python 3.10+ / Node.js 18+.
- **OS Support**: Optimized for **Linux (Ubuntu/Debian)** and **macOS**.
- **VRAM Management**: Integrated `pynvml` and `psutil` for dynamic memory scavenging.

---

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
