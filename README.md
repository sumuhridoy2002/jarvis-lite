# Jarvis Lite – Voice-Controlled Local AI Agent System

Jarvis Lite is a 100% local, high-performance conversational and automation engine designed for cybersecurity-conscious and privacy-first environments. Powered by local LLMs via Ollama, it orchestrates multiple AI agents to execute operating system commands, perform file system management, and automate software interactions seamlessly through natural language in both **Bangla and English**.

---

## 🚀 Key Features

- **Dual-Language Speech Processing:** Powered by `Faster-Whisper` for real-time automatic speech recognition supporting both Bangla and English inputs.
- **Agentic Orchestration:** Built on `CrewAI`, separating the brain into an *Intent Classifier (System Router)* and an *OS Execution Expert* to manage system processes dynamically.
- **Deterministic Expert Layer:** Converts probabilistic LLM outputs into exact rule-based system operations (`PyAutoGUI`, `subprocess`) safely.
- **100% Local & Private:** No third-party API dependencies (OpenAI/Anthropic). Fully functional offline, ensuring ironclad data privacy.
- **Interactive Terminal UI:** A beautiful, dark-themed Next.js 15 workstation showcasing real-time execution flows and agentic logs.

---

## 🛠️ Tech Stack & Architecture

- **Frontend:** Next.js 15 (React), TailwindCSS, Lucide Icons.
- **Backend API:** FastAPI (Python) - High-performance asynchronous processing.
- **AI Core Engine:** Ollama (`Llama-3.1`), CrewAI.
- **Speech Subsystem:** Faster-Whisper (STT), gTTS / Piper (TTS).
- **Automation Pipeline:** PyAutoGUI, Native OS Subprocesses.

---

## 📂 Project Structure

```text
jarvis-lite/
│
├── backend/
│   ├── app.py                  # Main FastAPI Application & Agent Core
│   └── requirements.txt        # Python Dependencies
│
├── frontend/
│   ├── app/
│   │   └── page.js             # Terminal Dashboard Core UI
│   └── package.json            # Node Dependencies
│
└── .gitignore                  # Production Git Exclusion Settings