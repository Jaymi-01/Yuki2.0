import threading
import pyttsx3
import time
import ctypes

def run_speech():
    print("Background thread started. Initializing COM...")
    try:
        # Initialize COM library for the current thread
        ctypes.windll.ole32.CoInitialize(None)
        
        print("Initializing TTS engine...")
        engine = pyttsx3.init()
        print("Saying text...")
        engine.say("Testing thread speech synthesis.")
        engine.runAndWait()
        print("Speech completed successfully!")
    except Exception as e:
        print("[ERROR] Speech thread failed:", e)

# Start speech in thread
t = threading.Thread(target=run_speech)
t.start()
t.join()
print("Main thread exiting.")
