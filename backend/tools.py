import os
import subprocess
import time
import re
import threading
import uuid
from datetime import datetime

import cv2
import pyautogui
from gtts import gTTS

import config

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

_tts_lock = threading.Lock()
_backend_dir = os.path.dirname(os.path.abspath(__file__))


def speak_async(text: str) -> None:
    try:
        clean_text = re.sub(r"\[.*?\]", "", text).strip()
        if not clean_text:
            return
        with _tts_lock:
            lang = "en" if clean_text.isascii() else "bn"
            filename = f"response_{uuid.uuid4().hex[:8]}.mp3"
            filepath = os.path.join(_backend_dir, filename)
            tts = gTTS(text=clean_text, lang=lang)
            tts.save(filepath)
            subprocess.Popen(
                f'cmd /c start /min "" "{filepath}"',
                shell=True,
                cwd=_backend_dir,
            )
    except Exception as e:
        print(f"[TTS ERROR] {e}")


def capture_webcam_photo() -> str:
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return "[ERROR] Webcam could not be opened."
        time.sleep(1.0)
        ret, frame = cap.read()
        cap.release()
        cv2.destroyAllWindows()
        if not ret or frame is None:
            return "[ERROR] Failed to capture frame from webcam."
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snap_{timestamp}.png"
        filepath = os.path.join(config.CAPTURES_PATH, filename)
        cv2.imwrite(filepath, frame)
        return f"[SUCCESS] Photo saved to {filepath}"
    except Exception as e:
        return f"[ERROR] Webcam capture failed: {str(e)}"


def generate_todo_app_project() -> str:
    try:
        project_dir = os.path.join(config.PROJECTS_PATH, "TodoApp")
        os.makedirs(project_dir, exist_ok=True)

        index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Todo App</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Todo App</h1>
        <div class="input-group">
            <input type="text" id="todoInput" placeholder="Enter a new task...">
            <button onclick="add()">Add</button>
        </div>
        <ul id="list"></ul>
    </div>
    <script src="app.js"></script>
</body>
</html>
"""

        style_css = """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #1a1a2e;
    color: #e0e0e0;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
}

.container {
    background-color: #16213e;
    border-radius: 12px;
    padding: 2rem;
    width: 100%;
    max-width: 500px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

h1 {
    text-align: center;
    margin-bottom: 1.5rem;
    color: #0f3460;
    background: linear-gradient(135deg, #e94560, #0f3460);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2rem;
}

.input-group {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
}

input[type="text"] {
    flex: 1;
    padding: 0.75rem 1rem;
    border: 2px solid #0f3460;
    border-radius: 8px;
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-size: 1rem;
    outline: none;
    transition: border-color 0.3s;
}

input[type="text"]:focus {
    border-color: #e94560;
}

button {
    padding: 0.75rem 1.5rem;
    background-color: #e94560;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #c73652;
}

ul {
    list-style: none;
}

ul li {
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    background-color: #1a1a2e;
    border-radius: 8px;
    border-left: 4px solid #e94560;
    transition: transform 0.2s;
}

ul li:hover {
    transform: translateX(4px);
}
"""

        app_js = """function add() {
    var input = document.getElementById("todoInput");
    var list = document.getElementById("list");
    var text = input.value.trim();
    if (text === "") {
        return;
    }
    var item = document.createElement("li");
    item.textContent = text;
    list.appendChild(item);
    input.value = "";
    input.focus();
}
"""

        with open(os.path.join(project_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(index_html)

        with open(os.path.join(project_dir, "style.css"), "w", encoding="utf-8") as f:
            f.write(style_css)

        with open(os.path.join(project_dir, "app.js"), "w", encoding="utf-8") as f:
            f.write(app_js)

        subprocess.Popen(
            "cmd /c start cursor " + project_dir,
            shell=True,
        )

        return f"[SUCCESS] TodoApp project created at {project_dir} and opened in Cursor."
    except Exception as e:
        return f"[ERROR] Failed to generate TodoApp project: {str(e)}"


def open_system_app(app_name: str) -> str:
    try:
        name = app_name.lower().strip()
        if not name:
            return "[ERROR] Empty app name provided."
        if "chrome" in name or "browser" in name:
            subprocess.Popen(["cmd", "/c", "start chrome"], shell=True)
            return "[SUCCESS] Google Chrome opened."
        elif "notepad" in name:
            subprocess.Popen(["notepad.exe"])
            return "[SUCCESS] Notepad opened."
        else:
            pyautogui.press("win")
            time.sleep(0.4)
            pyautogui.write(name)
            time.sleep(0.4)
            pyautogui.press("enter")
            return f"[SUCCESS] Executed OS search for '{name}'."
    except Exception as e:
        return f"[ERROR] App launch failed: {str(e)}"


def type_text_automation(text_to_type: str) -> str:
    try:
        clean_text = text_to_type.strip()
        pyautogui.write(clean_text, interval=0.05)
        return f"[SUCCESS] Typed out text: '{clean_text}'."
    except Exception as e:
        return f"[ERROR] Typing automation failed: {str(e)}"
