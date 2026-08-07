import os
import re
import time
import wave
import tempfile
import threading
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import pyttsx3

from .config import FS, CONTINUOUS_BLOCK_SEC, ACTIVE_LISTENING_SEC, WAKEWORDS, TTS_RATE
from .commands import process_command

def play_chime(chime_type='activate'):
    """Generates and plays dynamic synth chimes locally using sounddevice and numpy."""
    try:
        sample_rate = 16000
        if chime_type == 'activate':
            t1 = np.linspace(0, 0.08, int(0.08 * sample_rate), False)
            t2 = np.linspace(0, 0.12, int(0.12 * sample_rate), False)
            y1 = 0.1 * np.sin(2 * np.pi * 880 * t1) * np.exp(-t1 * 25)
            y2 = 0.08 * np.sin(2 * np.pi * 1760 * t2) * np.exp(-t2 * 12)
            audio = np.concatenate([y1, y2])
        elif chime_type == 'success':
            t = np.linspace(0, 0.2, int(0.2 * sample_rate), False)
            audio = 0.1 * np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 15)
        elif chime_type == 'error':
            t = np.linspace(0, 0.25, int(0.25 * sample_rate), False)
            audio = 0.12 * np.sin(2 * np.pi * 110 * t) * np.exp(-t * 8)
        else:
            return
        
        audio_int = (audio * 32767).astype(np.int16)
        sd.play(audio_int, sample_rate)
    except Exception as e:
        print("[SOUND ERROR] Chime failed:", e)

def is_direct_command(text):
    """Detects if a transcribed text represents a direct executable command (without wakeword)."""
    direct_phrases = [
        "play music", "pause music", "stop music", "resume music", "play pause",
        "next song", "skip song", "next track", "previous song", "go back song", "previous track",
        "mute volume", "mute audio", "unmute volume", "unmute audio", "mute", "unmute",
        "volume up", "turn up volume", "louder", "volume down", "turn down volume", "quieter", "lower volume",
        "time", "what time is it", "current time", "date", "what day is it", "today's date", "current date",
        "cpu", "ram", "memory", "system status", "diagnostics",
        "joke", "tell me a joke", "make me laugh",
        "hello", "hi", "hey",
        "who are you", "what's your name", "your name", "how are you",
        "thank you", "thanks", "good job", "well done"
    ]
    cleaned = text.lower().strip()
    # If starting with action verbs or question prefixes
    prefixes = [
        "open ", "launch ", "start ", "close ", "kill ", "exit ", "stop ", "terminate ", "search for ", "google ", "find ",
        "why ", "how ", "what ", "who ", "where ", "when ", "can you ", "could you ", "is there ", "are you ", "tell me ",
        "is it ", "does ", "do you ", "will ", "should "
    ]
    if any(cleaned.startswith(p) for p in prefixes):
        return True
    return cleaned in direct_phrases

class VoiceEngine:
    def __init__(self, log_callback, status_callback):
        self.log_callback = log_callback
        self.status_callback = status_callback
        
        self.active = False
        self.listening_thread = None
        self.lock = threading.Lock()
        self.current_state = "STANDBY"
        self.discard_current_block = False
        
        try:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            if len(voices) > 1:
                self.tts_engine.setProperty('voice', voices[1].id)
            self.tts_engine.setProperty('rate', TTS_RATE)
        except Exception as e:
            print("[TTS ERROR] Failed to initialize:", e)

    def speak(self, text):
        """Speaks the response verbally in a background thread to prevent UI freezing."""
        # Instantly lock state on the main thread to discard overlapping mic blocks
        self.current_state = "SPEAKING"
        self.discard_current_block = True
        self.status_callback("SPEAKING", "SPEAKING")
        
        def run_speech():
            import ctypes
            try:
                ctypes.windll.ole32.CoInitialize(None)
            except Exception:
                pass
            
            with self.lock:
                try:
                    engine = pyttsx3.init()
                    voices = engine.getProperty('voices')
                    if len(voices) > 1:
                        engine.setProperty('voice', voices[1].id)
                    engine.setProperty('rate', TTS_RATE)
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    print("[TTS ERROR] Speak failed:", e)
                self.current_state = "STANDBY"
                self.status_callback("ONLINE", "STANDBY")
                
            try:
                ctypes.windll.ole32.CoUninitialize()
            except Exception:
                pass
                
        threading.Thread(target=run_speech, daemon=True).start()

    def transcribe_audio_file(self, wav_path):
        """Transcribes a local WAV file using SpeechRecognition Google API."""
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
        try:
            return r.recognize_google(audio).strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print("[SPEECH API ERROR] Connection failure:", e)
            return "__ERROR__"

    def record_mic_and_boost(self, duration_sec):
        """Records from microphone, normalizes/boosts levels to 85% full range, saves to temp WAV."""
        temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(temp_fd)
        
        try:
            device_info = sd.query_devices(kind='input')
            samplerate = int(device_info['default_samplerate'])
            
            recording = sd.rec(int(duration_sec * samplerate), samplerate=samplerate, channels=1, dtype='int16')
            sd.wait()
            
            max_peak = np.max(np.abs(recording))
            if max_peak > 0:
                scale_factor = 28000.0 / max_peak
                if scale_factor > 25.0:
                    scale_factor = 25.0
                normalized = (recording * scale_factor).astype(np.int16)
            else:
                normalized = recording
            
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(samplerate)
                wf.writeframes(normalized.tobytes())
                
            return temp_path
        except Exception as e:
            print("[MIC ERROR] Capture failed:", e)
            try:
                os.remove(temp_path)
            except Exception:
                pass
            return None

    def start_listening(self):
        """Starts the continuous background listening thread."""
        self.active = True
        self.listening_thread = threading.Thread(target=self._continuous_loop, daemon=True)
        self.listening_thread.start()

    def stop_listening(self):
        self.active = False

    def _continuous_loop(self):
        self.log_callback("SYSTEM", "Yuki is listening continuously in the background...", "system")
        
        while self.active:
            if self.current_state != 'STANDBY':
                time.sleep(0.5)
                continue
                
            # Reset discard flag before starting recording block
            self.discard_current_block = False
            wav_path = self.record_mic_and_boost(CONTINUOUS_BLOCK_SEC)
            if not wav_path:
                time.sleep(0.2)
                continue
                
            # Discard block if assistant started speaking during capture
            if self.discard_current_block or self.current_state != 'STANDBY':
                try:
                    os.remove(wav_path)
                except Exception:
                    pass
                continue
                
            transcription = self.transcribe_audio_file(wav_path)
            try:
                os.remove(wav_path)
            except Exception:
                pass
                
            if not transcription or transcription == "__ERROR__":
                continue
                
            cleaned = transcription.lower().strip()
            print(f"[CONTINUOUS DETECTED] -> '{cleaned}'")
            
            # Check for wakewords
            wakeword_found = False
            wakeword_triggered = ""
            for ww in WAKEWORDS:
                if ww in cleaned:
                    wakeword_found = True
                    wakeword_triggered = ww
                    break
            
            # Check for direct executable commands (no wakeword required)
            direct_found = is_direct_command(cleaned)
            
            if wakeword_found or direct_found:
                if wakeword_found:
                    # Extract command part after the wakeword
                    parts = cleaned.split(wakeword_triggered, 1)
                    command_part = parts[1].strip() if len(parts) > 1 else ""
                    command_part = re.sub(r'^[,.\s\-]+', "", command_part).strip()
                else:
                    # Use full transcription if triggered by direct command match
                    command_part = cleaned
                
                if len(command_part) > 2:
                    # ONE-SHOT EXECUTION
                    self.log_callback("YOU (VOICE)", transcription, "user")
                    self.current_state = "PROCESSING"
                    self.status_callback("PROCESSING...", "PROCESSING")
                    
                    play_chime('success')
                    response, success = process_command(command_part)
                    
                    self.log_callback("YUKI", response, "yuki" if success else "system")
                    self.speak(response)
                elif wakeword_found:
                    # TWO-STEP EXECUTION: "Yuki"
                    self.current_state = "LISTENING"
                    self.status_callback("LISTENING...", "LISTENING")
                    self.log_callback("YOU (VOICE)", transcription, "user")
                    self.log_callback("SYSTEM", "Wakeword activated. Awaiting instruction...", "system")
                    
                    play_chime('activate')
                    
                    active_wav = self.record_mic_and_boost(ACTIVE_LISTENING_SEC)
                    if active_wav:
                        self.current_state = "PROCESSING"
                        self.status_callback("PROCESSING...", "PROCESSING")
                        command_transcription = self.transcribe_audio_file(active_wav)
                        try:
                            os.remove(active_wav)
                        except Exception:
                            pass
                            
                        if command_transcription and command_transcription != "__ERROR__":
                            clean_cmd = command_transcription.lower()
                            for ww in WAKEWORDS:
                                clean_cmd = clean_cmd.replace(ww, "")
                            clean_cmd = clean_cmd.strip()
                            
                            self.log_callback("YOU (VOICE)", command_transcription, "user")
                            
                            if len(clean_cmd) > 1:
                                play_chime('success')
                                response, success = process_command(clean_cmd)
                                self.log_callback("YUKI", response, "yuki" if success else "system")
                                self.speak(response)
                            else:
                                play_chime('error')
                                self.log_callback("SYSTEM", "Awaiting command timed out.", "system")
                                self.current_state = "STANDBY"
                                self.status_callback("ONLINE", "STANDBY")
                        else:
                            play_chime('error')
                            self.log_callback("YUKI", "I was unable to decipher your voice instruction, sir.", "system")
                            self.speak("I was unable to decipher your instruction.")
                    else:
                        self.current_state = "STANDBY"
                        self.status_callback("ONLINE", "STANDBY")
            
            time.sleep(0.1)
