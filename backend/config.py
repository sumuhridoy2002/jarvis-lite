import os
from faster_whisper import WhisperModel
from crewai import LLM

DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
CAPTURES_PATH = os.path.join(DESKTOP_PATH, "Captures")
PROJECTS_PATH = os.path.join(DESKTOP_PATH, "JarvisProjects")

os.makedirs(CAPTURES_PATH, exist_ok=True)
os.makedirs(PROJECTS_PATH, exist_ok=True)

SAMPLING_RATE = 16000
CHANNELS = 1
VAD_SILENCE_DURATION = 1.5
AUDIO_THRESHOLD = 0.02

whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")

local_llm = LLM(
    model="ollama/llama3.1",
    base_url="http://localhost:11434",
    api_key="NA",
)
