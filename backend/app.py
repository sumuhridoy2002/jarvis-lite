import os
import subprocess
import pyautogui
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from faster_whisper import WhisperModel
from gtts import gTTS
from crewai import Agent, Task, Crew, Process
from langchain_community.llms import Ollama

app = FastAPI(title="Jarvis Lite Core Engine")

# CORS এনাবল করা (Next.js ফ্রন্টএন্ড থেকে কানেক্ট করার জন্য)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# গ্লোবাল কনফিগারেশন এবং মডেল লোডিং
MODEL_SIZE = "tiny"  # স্পিড অপ্টিমাইজেশনের জন্য tiny বা base ব্যবহার করুন
whisper_model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
local_llm = Ollama(model="llama3.1", base_url="http://localhost:11434")

# ওএস সেফটি কনফিগারেশন (PyAutoGUI এরর এড়ানোর জন্য)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

# --- কাস্টম অটোমেশন টুলস (Determininstic Python Functions) ---
def create_desktop_folder(folder_name: str) -> str:
    try:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", folder_name.strip())
        os.makedirs(desktop_path, exist_ok=True)
        return f"[SUCCESS] Created folder '{folder_name}' on Desktop."
    except Exception as e:
        return f"[ERROR] Failed to create folder: {str(e)}"

def open_system_app(app_name: str) -> str:
    name = app_name.lower().strip()
    try:
        if "chrome" in name:
            if os.name == 'nt': # Windows
                subprocess.Popen(["start", "chrome"], shell=True)
            else: # Mac/Linux
                subprocess.Popen(["google-chrome"])
            return "[SUCCESS] Google Chrome opened."
        elif "notepad" in name or "notepad++" in name:
            subprocess.Popen(["notepad.exe"])
            return "[SUCCESS] Notepad opened."
        else:
            # জেনারেল ওএস সার্চ রান করা
            pyautogui.press('win')
            pyautogui.sleep(0.5)
            pyautogui.write(name)
            pyautogui.sleep(0.5)
            pyautogui.press('enter')
            return f"[SUCCESS] Executed OS search and launch trigger for '{app_name}'."
    except Exception as e:
        return f"[ERROR] App launch failed: {str(e)}"

def type_text_automation(text_to_type: str) -> str:
    try:
        pyautogui.write(text_to_type, interval=0.05)
        return f"[SUCCESS] Typed out text: '{text_to_type}'."
    except Exception as e:
        return f"[ERROR] Typing automation failed: {str(e)}"

# --- CrewAI Multi-Agent Architecture Set Up ---
system_router = Agent(
    role="Intent Classifier",
    goal="Accurately split user prompts into OS_AUTOMATION, WEB_RESEARCH, or GENERAL_TALK.",
    backstory="You analyze text commands. You are conservative and route system tasks strictly.",
    llm=local_llm,
    verbose=True
)

os_executor = Agent(
    role="OS Execution Expert",
    goal="Map user requests into deterministic actions like creating folders, opening apps, or typing.",
    backstory="You translate natural commands into system actions. You never run destructive code.",
    llm=local_llm,
    verbose=True
)

# --- API Models ---
class TextCommandRequest(BaseModel):
    command: str

@app.post("/api/process-text")
async def process_text_command(request: TextCommandRequest):
    user_prompt = request.command
    
    # ক্রু টাস্ক তৈরি
    execution_task = Task(
        description=f"""
        Analyze the user input: "{user_prompt}".
        Decide the action:
        1. If it mentions creating a folder/directory, output string exactly: FOLDER_CREATE: <folder_name>
        2. If it mentions opening/launching an application, output string exactly: APP_OPEN: <app_name>
        3. If it requests to write or type text, output string exactly: TYPE_TEXT: <text>
        4. Otherwise, respond naturally as a helpful assistant.
        """,
        expected_output="A structured command trigger or natural text answer.",
        agent=os_executor
    )
    
    crew = Crew(
        agents=[system_router, os_executor],
        tasks=[execution_task],
        process=Process.sequential
    )
    
    agent_output = crew.kickoff()
    output_str = str(agent_output).strip()
    
    # এক্সপার্ট রুলস ইঞ্জিন পার্সিং (Rule-Based Expert System Layer)
    execution_status = "Natural Response Generated"
    
    if "FOLDER_CREATE:" in output_str:
        f_name = output_str.split("FOLDER_CREATE:")[1]
        execution_status = create_desktop_folder(f_name)
    elif "APP_OPEN:" in output_str:
        a_name = output_str.split("APP_OPEN:")[1]
        execution_status = open_system_app(a_name)
    elif "TYPE_TEXT:" in output_str:
        t_content = output_str.split("TYPE_TEXT:")[1]
        execution_status = type_text_automation(t_content)
    else:
        execution_status = output_str

    return {
        "raw_prompt": user_prompt,
        "agent_decision": output_str,
        "execution_result": execution_status
    }

@app.post("/api/record-and-transcribe")
async def record_and_transcribe():
    # ৫ সেকেন্ড লাইভ অডিও রেকর্ডিং (Hardware Input)
    fs = 16000  # Whisper এর জন্য ১৬কিলোহার্টজ স্ট্যান্ডার্ড
    seconds = 5
    filename = "live_input.wav"
    
    try:
        recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        wav.write(filename, fs, recording)
        
        # Faster Whisper দিয়ে ট্রান্সক্রিপশন (বাংলা ও ইংরেজি অটো-ডিটেক্ট করবে)
        segments, info = whisper_model.transcribe(filename, beam_size=5)
        transcript = "".join([segment.text for segment in segments])
        
        return {"transcript": transcript, "language": info.language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio Hardware Error: {str(e)}")

@app.post("/api/tts")
async def text_to_speech(request: TextCommandRequest):
    try:
        # Piper এর জায়গায় প্রোটেটাইপিংয়ের জন্য gTTS (লাইভ স্পিকার প্লেব্যাক কোড)
        tts = gTTS(text=request.command, lang='en' if request.command.isascii() else 'bn')
        tts.save("output.mp3")
        
        # ওএস নেটিভ প্লেয়ার দিয়ে অডিও প্লে করা
        if os.name == 'nt':
            os.system("start output.mp3")
        else:
            os.system("afplay output.mp3 || mpg123 output.mp3")
            
        return {"status": "Speech played successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)