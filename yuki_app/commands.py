import re
import time
import ctypes
import subprocess
import webbrowser
from datetime import datetime

from .config import APP_MAP, JOKES
from .diagnostics import get_cpu_usage, get_ram_usage

import os

# Load .env file variables manually into os.environ
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# Media Key Windows API Simulation
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_STOP = 0xB2
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

def press_key(vk_code):
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)

joke_index = 0

def process_command(cmd_text):
    global joke_index
    cmd = cmd_text.lower().strip()
    
    # 1. Media key presses
    if any(x in cmd for x in ["play music", "pause music", "stop music", "resume music", "play pause"]):
        press_key(VK_MEDIA_PLAY_PAUSE)
        return "Toggling music playback, sir.", True
        
    elif cmd.startswith("play "):
        query = cmd[5:].strip()
        if query == "something" or not query:
            query = "today's top hits"
        try:
            webbrowser.open(f"spotify:search:{query}")
            
            # Autoplay keyboard simulation in background thread
            import threading
            def trigger_autoplay():
                time.sleep(1.8) # Wait for Spotify window to load and focus
                # Simulate Tab (0x09) then Enter (0x0D) to select and play top result
                press_key(0x09)
                time.sleep(0.1)
                press_key(0x0D)
                
            threading.Thread(target=trigger_autoplay, daemon=True).start()
            return f"Playing {query} on Spotify, sir.", True
        except Exception as e:
            return f"Failed to query Spotify. {str(e)}", False
        
    elif any(x in cmd for x in ["next song", "skip song", "next track"]):
        press_key(VK_MEDIA_NEXT_TRACK)
        return "Skipping to next track, sir.", True
        
    elif any(x in cmd for x in ["previous song", "go back song", "previous track"]):
        press_key(VK_MEDIA_PREV_TRACK)
        return "Playing previous track.", True
        
    # 2. Volume controls
    elif any(x in cmd for x in ["mute volume", "mute audio", "unmute volume", "unmute audio", "mute"]):
        press_key(VK_VOLUME_MUTE)
        return "Toggling system mute, sir.", True
        
    elif any(x in cmd for x in ["volume up", "turn up volume", "louder"]):
        for _ in range(5):
            press_key(VK_VOLUME_UP)
            time.sleep(0.01)
        return "Increasing system volume.", True
        
    elif any(x in cmd for x in ["volume down", "turn down volume", "quieter", "lower volume"]):
        for _ in range(5):
            press_key(VK_VOLUME_DOWN)
            time.sleep(0.01)
        return "Decreasing system volume, sir.", True
        
    # 3. Open applications
    open_match = re.search(r'(?:open|launch|start)\s+([a-zA-Z0-9\s]+)', cmd)
    if open_match:
        app_name = open_match.group(1).strip()
        executable = APP_MAP.get(app_name)
        
        if executable:
            try:
                if executable.startswith("start "):
                    subprocess.Popen(executable, shell=True)
                else:
                    subprocess.Popen(executable)
                return f"Opening {app_name}, sir.", True
            except Exception as e:
                return f"Failed to launch {app_name}. {str(e)}", False
        elif app_name == "chrome" or app_name == "google chrome" or app_name == "browser":
            try:
                webbrowser.open("https://google.com")
                return "Opening your web browser, sir.", True
            except Exception:
                pass

        try:
            subprocess.Popen(f'start {app_name}', shell=True)
            return f"Attempting to launch {app_name}, sir.", True
        except Exception:
            return f"I was unable to find an application named {app_name} on your system.", False

    # 4. Close applications
    close_match = re.search(r'(?:close|kill|exit|stop|terminate)\s+([a-zA-Z0-9\s]+)', cmd)
    if close_match:
        app_name = close_match.group(1).strip()
        proc_name = app_name
        if app_name in APP_MAP:
            proc_name = APP_MAP[app_name].replace(".exe", "")
        if proc_name.startswith("start "):
            proc_name = proc_name.replace("start ", "")
        if not proc_name.endswith(".exe") and "." not in proc_name:
            proc_name += ".exe"

        try:
            result = subprocess.run(["taskkill", "/f", "/im", proc_name], capture_output=True, text=True)
            if result.returncode == 0:
                return f"Closed {app_name}, sir.", True
            else:
                return f"It seems {app_name} is not currently running.", True
        except Exception as e:
            return f"Error terminating process: {str(e)}", False

    # 5. Search Web
    search_match = re.search(r'(?:search for|google|find)\s+(.+)', cmd)
    if search_match:
        query = search_match.group(1).strip()
        try:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching Google for {query}, sir.", True
        except Exception as e:
            return f"Failed to execute web search. {str(e)}", False

    # 6. Time & Date
    if any(x in cmd for x in ["time", "what time is it", "current time"]):
        now = datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}, sir.", True
        
    elif any(x in cmd for x in ["date", "what day is it", "today's date", "current date"]):
        now = datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}, sir.", True

    # 7. System Diagnostics
    elif any(x in cmd for x in ["cpu", "ram", "memory", "system status", "diagnostics"]):
        cpu = get_cpu_usage()
        ram = get_ram_usage()
        return f"System diagnostics indicate CPU usage is at {cpu} percent, and RAM consumption is at {ram['load_percent']} percent, with {ram['total_gb'] - ram['used_gb']:.1f} gigabytes free.", True

    # 8. Jokes
    elif any(x in cmd for x in ["joke", "tell me a joke", "make me laugh"]):
        joke = JOKES[joke_index]
        joke_index = (joke_index + 1) % len(JOKES)
        return joke, True

    # 9. Conversational Fallbacks
    elif any(x in cmd for x in ["hello", "hi", "hey"]):
        return "Hello, sir. Yuki is online and ready. How may I assist you?", True
        
    elif any(x in cmd for x in ["who are you", "what's your name", "your name"]):
        return "I am Yuki, your voice-activated personal environment assistant. I monitor your system, control applications, and perform automation routines.", True
        
    elif "how are you" in cmd:
        return "I am operating at peak efficiency, sir. All core directories are stable and responsive.", True
        
    elif any(x in cmd for x in ["thank you", "thanks", "good job", "well done"]):
        return "At your service, sir. It is a pleasure to assist.", True

    # Default conversational fallback (Wired to Google Gemini API)
    import os
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            chat_response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"You are Yuki, a voice assistant. Respond concisely to the user in one or two sentences: {cmd_text}"
            )
            return chat_response.text.strip(), True
        except Exception:
            return "I had trouble querying my cognitive cloud brain, sir.", False
    else:
        return f"I've recorded your query: '{cmd_text}'. Please set the GEMINI_API_KEY environment variable to let me speak answers.", True
