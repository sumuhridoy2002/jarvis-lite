import asyncio
import threading
import time

import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
from crewai import Agent, Task, Crew, Process

import config
import tools

audio_buffer = []
is_listening = True
_buffer_lock = threading.Lock()
_command_queue: asyncio.Queue = asyncio.Queue()
_agent_lock = asyncio.Lock()
_last_processed = {"text": "", "time": 0.0}

os_executor = Agent(
    role="OS Execution Expert",
    goal="Map user intents precisely to deterministic system tokens without any chatting or conversational filler.",
    backstory="You control a Windows OS machine. You respond strictly with structured system commands.",
    llm=config.local_llm,
    verbose=False,
)


def _should_process(transcript: str) -> bool:
    normalized = transcript.lower().strip()
    now = time.time()
    if (
        normalized == _last_processed["text"]
        and now - _last_processed["time"] < 5.0
    ):
        print(f"[TRANSCRIPT] Skipping duplicate: {transcript}")
        return False
    _last_processed["text"] = normalized
    _last_processed["time"] = now
    return True


async def _command_worker() -> None:
    while True:
        user_command = await _command_queue.get()
        try:
            async with _agent_lock:
                await _run_agent_logic(user_command)
        except Exception as e:
            print(f"[WORKER ERROR] {e}")
            tools.speak_async(f"Agent processing error: {str(e)}")
        finally:
            _command_queue.task_done()


async def _run_agent_logic(user_command: str) -> None:
    execution_task = Task(
        description=f"""
        Evaluate the user command: "{user_command}".
        Output ONLY ONE of these exact formats without markdown, lists, or notes:
        - CAMERA_CAPTURE (if user wants to take a photo or use the webcam)
        - DEVELOP_TODO_APP (if user wants to create or build a todo application project)
        - APP_OPEN: <app_name> (if user wants to open or launch an application)
        - TYPE_TEXT: <payload> (if user wants to type or write text into the active window)
        If no automation matches, return a natural short phrase response.

        CRITICAL: Output only a single line. No explanations. No numbered lists. No markdown.
        """,
        expected_output="A single structured command token or a natural short phrase.",
        agent=os_executor,
    )

    crew = Crew(
        agents=[os_executor],
        tasks=[execution_task],
        process=Process.sequential,
    )

    agent_output = await crew.kickoff_async()
    output_str = str(agent_output).strip()
    first_line = output_str.split("\n")[0].strip()

    execution_result = first_line

    if first_line == "CAMERA_CAPTURE":
        execution_result = tools.capture_webcam_photo()
    elif first_line == "DEVELOP_TODO_APP":
        execution_result = tools.generate_todo_app_project()
    elif first_line.startswith("APP_OPEN:"):
        app_name = first_line.split("APP_OPEN:", 1)[1].strip()
        app_name = app_name.replace('"', "").replace("'", "").strip()
        execution_result = tools.open_system_app(app_name)
    elif first_line.startswith("TYPE_TEXT:"):
        payload = first_line.split("TYPE_TEXT:", 1)[1].strip()
        execution_result = tools.type_text_automation(payload)
    else:
        execution_result = first_line

    tools.speak_async(execution_result)


async def process_agent_logic(user_command: str) -> None:
    if not _should_process(user_command):
        return
    await _command_queue.put(user_command)


def audio_callback(indata, frames, time_info, status) -> None:
    try:
        if status:
            print(f"[AUDIO STATUS] {status}")
        with _buffer_lock:
            audio_buffer.append(indata.copy())
    except Exception as e:
        print(f"[CALLBACK ERROR] {e}")


async def monitor_microphone_loop() -> None:
    global is_listening

    print("[DAEMON] Voice automation daemon started. Listening continuously...")
    print(f"[DAEMON] Captures path: {config.CAPTURES_PATH}")
    print(f"[DAEMON] Projects path: {config.PROJECTS_PATH}")

    POLL_INTERVAL = 0.1

    worker_task = asyncio.create_task(_command_worker())

    try:
        with sd.InputStream(
            samplerate=config.SAMPLING_RATE,
            channels=config.CHANNELS,
            dtype="int16",
            callback=audio_callback,
        ):
            while is_listening:
                try:
                    segment_chunks = []
                    silence_elapsed = 0.0
                    speaking_started = False

                    while is_listening:
                        await asyncio.sleep(POLL_INTERVAL)

                        with _buffer_lock:
                            if not audio_buffer:
                                if speaking_started:
                                    silence_elapsed += POLL_INTERVAL
                                    if silence_elapsed >= config.VAD_SILENCE_DURATION:
                                        break
                                continue
                            chunk = np.concatenate(audio_buffer, axis=0)
                            audio_buffer.clear()

                        segment_chunks.append(chunk)

                        rms = np.sqrt(np.mean(chunk.astype(np.float64) ** 2)) / 32768.0

                        if rms >= config.AUDIO_THRESHOLD:
                            speaking_started = True
                            silence_elapsed = 0.0
                        elif speaking_started:
                            silence_elapsed += POLL_INTERVAL
                            if silence_elapsed >= config.VAD_SILENCE_DURATION:
                                break
                        else:
                            segment_chunks.clear()

                    if not segment_chunks:
                        continue

                    recording = np.concatenate(segment_chunks, axis=0)
                    wav_filename = "daemon_input.wav"
                    wavfile.write(wav_filename, config.SAMPLING_RATE, recording)

                    segments, info = config.whisper_model.transcribe(
                        wav_filename, beam_size=1
                    )
                    transcript = "".join(segment.text for segment in segments).strip()

                    if transcript:
                        print(f"[TRANSCRIPT] {transcript}")
                        await process_agent_logic(transcript)
                    else:
                        print("[TRANSCRIPT] Empty transcript, skipping.")

                except Exception as e:
                    print(f"[LOOP ERROR] {e}")
                    segment_chunks = []
                    with _buffer_lock:
                        audio_buffer.clear()

    except Exception as e:
        print(f"[STREAM ERROR] {e}")
    finally:
        worker_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(monitor_microphone_loop())
    except Exception as e:
        print(f"Fatal daemon error: {e}")
