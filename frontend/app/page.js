"use client";
import { useState } from "react";
import { Mic, MicOff, Terminal, Cpu, Play, CheckCircle } from "lucide-react";

export default function JarvisDashboard() {
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [logs, setLogs] = useState([
    { stage: "System", text: "Jarvis Lite Subsystem Active. Ollama Node Online.", type: "sys" }
  ]);

  const addLog = (stage, text, type) => {
    setLogs((prev) => [...prev, { stage, text, type }]);
  };

  const submitToBackend = async (commandText) => {
    if (!commandText.trim()) return;
    setIsLoading(true);
    addLog("User", commandText, "user");

    try {
      const response = await fetch("http://localhost:8000/api/process-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: commandText }),
      });
      
      const data = await response.json();
      
      addLog("CrewAI Agent", data.agent_decision, "agent");
      addLog("OS Executor", data.execution_result, "exec");

      // টিটিএস (ভয়েস ফিডব্যাক) ট্রিগার করা
      await fetch("http://localhost:8000/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: data.execution_result }),
      });

    } catch (error) {
      addLog("Error", "Could not connect to local FastAPI backend.", "err");
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceRecord = async () => {
    setIsRecording(true);
    addLog("Hardware", "Microphone recording for 5 seconds...", "sys");
    
    try {
      const res = await fetch("http://localhost:8000/api/record-and-transcribe", { method: "POST" });
      const data = await res.json();
      
      addLog("Faster Whisper", `Transcribed [${data.language.toUpperCase()}]: "${data.transcript}"`, "sys");
      if (data.transcript) {
        await submitToBackend(data.transcript);
      }
    } catch (err) {
      addLog("Error", "Audio processing failed.", "err");
    } finally {
      setIsRecording(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-mono p-6 flex flex-col justify-between">
      {/* Top Header */}
      <header className="border-b border-slate-800 pb-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Cpu className="text-cyan-400 animate-pulse" size={28} />
          <h1 className="text-xl font-bold tracking-wider text-cyan-400">JARVIS LITE v1.0.0</h1>
        </div>
        <div className="text-xs bg-slate-900 border border-slate-700 px-3 py-1 rounded text-slate-400">
          MODE: <span className="text-green-400 font-bold">100% LOCAL AI</span>
        </div>
      </header>

      {/* Main Grid Workstation */}
      <main className="grid grid-cols-1 lg:grid-cols-3 gap-6 my-6 flex-grow">
        {/* Left Control Deck */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-col justify-center items-center gap-6">
          <button
            onClick={handleVoiceRecord}
            disabled={isRecording || isLoading}
            className={`w-36 h-36 rounded-full flex flex-col items-center justify-center gap-2 font-bold transition-all border-4 shadow-xl ${
              isRecording
                ? "bg-red-600 border-red-400 animate-ping text-white"
                : "bg-cyan-950 border-cyan-500 hover:bg-cyan-900 text-cyan-300 disabled:opacity-50"
            }`}
          >
            {isRecording ? <MicOff size={40} /> : <Mic size={40} />}
            <span className="text-xs">{isRecording ? "LISTENING" : "PUSH TO TALK"}</span>
          </button>
          <p className="text-xs text-slate-500 text-center max-w-xs">
            Say commands like "Create folder Assignment" or "Open Chrome" in English or Bangla.
          </p>

          <div className="w-full border-t border-slate-800 pt-4 mt-2">
            <label className="text-xs text-slate-400 block mb-2">Or Type Text Command:</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Type command..."
                className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-sm flex-grow text-cyan-400 focus:outline-none focus:border-cyan-500"
              />
              <button
                onClick={() => { submitToBackend(textInput); setTextInput(""); }}
                className="bg-cyan-600 hover:bg-cyan-500 px-3 py-2 rounded text-black font-bold text-sm"
              >
                <Play size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* Right Log Console Stream (2 Cols wide) */}
        <div className="lg:col-span-2 bg-slate-950 border border-slate-800 rounded-xl p-5 flex flex-col justify-between h-[450px]">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
            <Terminal size={18} className="text-cyan-500" />
            <h2 className="text-sm font-bold text-slate-300">Agentic Orchestrator Logs</h2>
          </div>

          <div className="flex-grow overflow-y-auto space-y-3 pr-2 custom-scrollbar">
            {logs.map((log, index) => (
              <div
                key={index}
                className={`p-3 rounded text-xs border ${
                  log.type === "user" ? "bg-blue-950/40 border-blue-900 text-blue-300" :
                  log.type === "agent" ? "bg-amber-950/40 border-amber-900 text-amber-300" :
                  log.type === "exec" ? "bg-emerald-950/40 border-emerald-900 text-emerald-300" :
                  "bg-slate-900 border-slate-800 text-slate-400"
                }`}
              >
                <div className="flex items-center gap-1.5 font-bold mb-1 tracking-wider uppercase text-[10px]">
                  {log.type === "exec" && <CheckCircle size={10} />}
                  <span>[{log.stage}]</span>
                </div>
                <p className="whitespace-pre-wrap leading-relaxed">{log.text}</p>
              </div>
            ))}
            {isLoading && (
              <div className="text-xs text-cyan-500 animate-pulse">
                &gt; [SYSTEM]: Agent Swarm is reasoning with Llama 3.1 model...
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer System Stats */}
      <footer className="border-t border-slate-800 pt-3 text-[11px] text-slate-500 flex justify-between">
        <div>Host System: <span className="text-slate-400 font-bold">Localhost Architecture</span></div>
        <div>STT: <span className="text-slate-400">Faster-Whisper (Int8)</span> | LLM: <span className="text-slate-400">Llama 3.1 (Ollama)</span></div>
      </footer>
    </div>
  );
}