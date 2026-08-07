# Yuki - Hands-Free Voice Desktop Assistant

Yuki is a native voice-activated desktop assistant for Windows. Built using `customtkinter` and standard Windows libraries, it operates inside a standalone HUD GUI window featuring an animated canvas visualizer and real-time performance diagnostics.

Yuki is designed to be **completely hands-free**: there are no microphone buttons to click. The voice recognition engine is active in the background, continuously listening for you to say **"Yuki"** and automatically amplifying quiet microphone signals.

```
yuki/
├── main.py                       # Console Entry Script
├── yuki_architecture_and_plan.md # System Architecture Document
├── README.md                     # Documentation & Setup Guide
└── yuki_app/
    ├── __init__.py               # Package Initializer
    ├── config.py                 # Color and Audio Mappings Configuration
    ├── diagnostics.py            # Windows System Metrics queries
    ├── commands.py               # Text Parsing & OS Execution commands
    ├── voice.py                  # Auto-Gain Audio Loop & Speech Synthesis
    └── gui.py                    # CustomTkinter HUD Window & Visualizer Core
```

---

## 🚀 How to Run

1. Open your terminal in the project folder:
   ```powershell
   cd C:\Users\Jaymi\source\repos\yuki
   ```
2. Start the assistant:
   ```powershell
   python main.py
   ```
3. The standalone desktop window will boot up instantly, and Yuki will confirm vocally: *"Yuki is online and operational. Continuous voice detection activated, sir."*

---

## 🎙️ Hands-Free Interaction

Yuki runs a continuous microphone listening loop with **digital audio normalization**:
* **Auto-Gain Boost**: If your microphone level is set very low in Windows, Yuki automatically boosts the captured audio by up to 25x so Google's speech recognition can decipher your command clearly.
* **One-Shot Mode**: Say a combined command like *"Yuki, open calculator"* or *"Yuki, turn up the volume"*. Yuki will immediately perform the action and speak its response.
* **Two-Step Mode**: Say just **"Yuki"**. Yuki will play an activation tone, wait for you to speak your instruction, and execute it.
* **Mute Toggle**: If you need privacy (e.g. during a meeting), you can type commands manually in the console box at the bottom.

---

## 🛠️ Supported Commands

| Command Category | Example Spoken Commands | Action Performed |
| :--- | :--- | :--- |
| **Media Controls** | `"play music"`, `"pause music"`, `"next song"`, `"previous track"` | Control Windows global media players. |
| **Volume Controls**| `"volume up"`, `"volume down"`, `"mute volume"`, `"unmute"` | Adjust system volume levels or toggle mute. |
| **App Management** | `"open notepad"`, `"launch paint"`, `"close calculator"` | Launch or terminate local applications. |
| **Diagnostics** | `"system status"`, `"cpu"`, `"ram"`, `"diagnostics"` | Read system utilization metrics. |
| **Information** | `"what time is it?"`, `"what day is it?"`, `"tell me a joke"` | Say local time, date, or a tech joke. |
| **Web Searches** | `"search for deep learning"`, `"google astronomy"` | Search queries in your default browser. |

---

## 🧠 Connecting to Gemini API (LLM Integration)

To connect Yuki to Gemini for answering open-ended questions:

1. Install Google GenAI SDK:
   ```powershell
   pip install google-genai
   ```
2. Edit [yuki_app/commands.py](file:///C:/Users/Jaymi/source/repos/yuki/yuki_app/commands.py) to replace the default fallback at the bottom of the `process_command` function:
   ```python
   # Replace the bottom return:
   # return f"I've recorded your query: '{cmd_text}'...", True
   
   # With:
   from google import genai
   try:
       client = genai.Client()
       chat_response = client.models.generate_content(
           model='gemini-2.5-flash',
           contents=f"You are Yuki, a voice assistant. Respond concisely to the user: {cmd_text}"
       )
       return chat_response.text.strip(), True
   except Exception:
       return "I had trouble querying my cognitive brain, sir.", False
   ```
3. Set your key and run:
   ```powershell
   $env:GEMINI_API_KEY="YOUR_API_KEY"
   python main.py
   ```
