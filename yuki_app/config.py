# Yuki Voice Assistant Configuration File

# UI Color Palette (Hex format compatible with Tkinter)
CYAN_COLOR = "#00F0FF"
AMBER_COLOR = "#FFAA00"
BG_DARK = "#0B0E14"
BORDER_DARK = "#1E293B"
TEXT_WHITE = "#E2E8F0"
TEXT_DIM = "#64748B"
CONSOLE_BG = "#0F172A"

# Audio & Voice Settings
FS = 16000                     # Audio sampling rate for speech recognition
CONTINUOUS_BLOCK_SEC = 3.5      # Record window size in seconds for background listening
ACTIVE_LISTENING_SEC = 5.0     # Time to listen for command after wakeword
WAKEWORDS = ["yuki"]           # ONLY Yuki
TTS_RATE = 165                 # SAPI5 voice speed
TTS_PITCH = 90                 # SAPI5 voice pitch

# App Map (Mapping friendly names to Windows executables or URI protocol schemes)
APP_MAP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",
    "browser": "chrome.exe",
    "cmd": "cmd.exe",
    "task manager": "taskmgr.exe",
    "settings": "start ms-settings:",
    "spotify": "start spotify:",  # Updated to launch via Windows Protocol URI scheme
}

# Programmer Jokes
JOKES = [
    "Why do programmers wear glasses? Because they can't C#!",
    "There are 10 types of people in the world: those who understand binary, and those who don't.",
    "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
    "Why did the computer go to the doctor? Because it had a virus!",
    "An SQL query walks into a bar, walks up to two tables and asks, 'Can I join you?'",
    "What do you call a programmer from Finland? Nerdic.",
    "Why did the developer go broke? Because they used up all their cache."
]
