import time
import math
import random
import threading
from datetime import datetime
import tkinter as tk
import customtkinter as ctk

from .config import (
    CYAN_COLOR, AMBER_COLOR, BG_DARK, BORDER_DARK, TEXT_WHITE, TEXT_DIM, CONSOLE_BG,
    APP_MAP
)
from .diagnostics import get_cpu_usage, get_ram_usage, get_active_window_title
from .commands import process_command
from .voice import VoiceEngine, play_chime

class YukiApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure Window
        self.title("Yuki Assistant")
        self.geometry("1100x650")
        self.resizable(False, False)
        
        # Variables
        self.assistant_state = "STANDBY"
        self.angle = 0
        self.stats_running = True
        
        # Setup Layout
        self.setup_ui()
        
        # Instantiate and Start Voice Engine
        self.voice = VoiceEngine(
            log_callback=self.log_msg,
            status_callback=self.update_status_callback
        )
        self.voice.start_listening()
        
        # Start background polling threads
        threading.Thread(target=self.poll_stats_loop, daemon=True).start()
        
        # Start visualizer animation
        self.animate_visualizer()

    def setup_ui(self):
        # Grid Configuration (1 Column Header, 1 Row Body with 3 Columns)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=3) # Diagnostics
        self.grid_columnconfigure(1, weight=4) # Visualizer Center
        self.grid_columnconfigure(2, weight=3) # Chat Log

        # 1. Header Frame
        self.header_frame = ctk.CTkFrame(self, height=70, corner_radius=0, border_width=1, border_color=BORDER_DARK)
        self.header_frame.grid(row=0, column=0, columnspan=3, sticky="new", padx=10, pady=(10, 5))
        self.header_frame.grid_propagate(False)
        
        self.header_title = ctk.CTkLabel(self.header_frame, text="YUKI ASSISTANT", font=ctk.CTkFont(family="Orbitron", size=22, weight="bold"), text_color=CYAN_COLOR)
        self.header_title.pack(side="left", padx=20)
        
        self.header_subtitle = ctk.CTkLabel(self.header_frame, text="NATIVE ENVIRONMENT AUTOMATION GUI", font=ctk.CTkFont(family="Share Tech Mono", size=10), text_color=TEXT_DIM)
        self.header_subtitle.pack(side="left", pady=(5, 0))
        
        self.header_time = ctk.CTkLabel(self.header_frame, text="00:00:00", font=ctk.CTkFont(family="Share Tech Mono", size=18), text_color=CYAN_COLOR)
        self.header_time.pack(side="right", padx=20)
        
        self.status_dot = ctk.CTkLabel(self.header_frame, text="●", font=ctk.CTkFont(size=14), text_color=CYAN_COLOR)
        self.status_dot.pack(side="right", padx=(0, 5))
        
        self.status_label = ctk.CTkLabel(self.header_frame, text="ONLINE", font=ctk.CTkFont(family="Share Tech Mono", size=12), text_color=TEXT_WHITE)
        self.status_label.pack(side="right", padx=(0, 5))

        # 2. Left Panel: Diagnostics
        self.left_panel = ctk.CTkFrame(self, border_width=1, border_color=BORDER_DARK)
        self.left_panel.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(5, 5))
        
        self.diag_title = ctk.CTkLabel(self.left_panel, text="SYSTEM DIAGNOSTICS", font=ctk.CTkFont(family="Orbitron", size=14, weight="bold"), text_color=TEXT_WHITE)
        self.diag_title.pack(pady=15)
        
        # CPU Info
        self.cpu_label_group = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.cpu_label_group.pack(fill="x", padx=20, pady=5)
        self.cpu_lbl = ctk.CTkLabel(self.cpu_label_group, text="CPU UTILITY", font=ctk.CTkFont(family="Share Tech Mono", size=12))
        self.cpu_lbl.pack(side="left")
        self.cpu_val = ctk.CTkLabel(self.cpu_label_group, text="0%", font=ctk.CTkFont(family="Share Tech Mono", size=12), text_color=CYAN_COLOR)
        self.cpu_val.pack(side="right")
        
        self.cpu_bar = ctk.CTkProgressBar(self.left_panel, progress_color=CYAN_COLOR)
        self.cpu_bar.set(0)
        self.cpu_bar.pack(fill="x", padx=20, pady=(0, 15))
        
        # RAM Info
        self.ram_label_group = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.ram_label_group.pack(fill="x", padx=20, pady=5)
        self.ram_lbl = ctk.CTkLabel(self.ram_label_group, text="RAM LOAD", font=ctk.CTkFont(family="Share Tech Mono", size=12))
        self.ram_lbl.pack(side="left")
        self.ram_val = ctk.CTkLabel(self.ram_label_group, text="0%", font=ctk.CTkFont(family="Share Tech Mono", size=12), text_color=CYAN_COLOR)
        self.ram_val.pack(side="right")
        
        self.ram_bar = ctk.CTkProgressBar(self.left_panel, progress_color=CYAN_COLOR)
        self.ram_bar.set(0)
        self.ram_bar.pack(fill="x", padx=20, pady=(0, 5))
        
        self.ram_details = ctk.CTkLabel(self.left_panel, text="0.0 GB / 0.0 GB USED", font=ctk.CTkFont(family="Share Tech Mono", size=10), text_color=TEXT_DIM)
        self.ram_details.pack(anchor="e", padx=20, pady=(0, 15))
        
        # Active Window
        self.act_lbl = ctk.CTkLabel(self.left_panel, text="ACTIVE APPLICATION", font=ctk.CTkFont(family="Share Tech Mono", size=11), text_color=TEXT_DIM)
        self.act_lbl.pack(anchor="w", padx=20, pady=(10, 2))
        self.active_window_txt = ctk.CTkLabel(self.left_panel, text="Desktop", fg_color=CONSOLE_BG, corner_radius=3, height=35, font=ctk.CTkFont(family="Share Tech Mono", size=12), text_color=CYAN_COLOR)
        self.active_window_txt.pack(fill="x", padx=20, pady=(0, 25))
        
        # Empty space buffer at bottom
        self.bottom_spacer = ctk.CTkLabel(self.left_panel, text="", fg_color="transparent")
        self.bottom_spacer.pack(fill="both", expand=True)

        # 3. Center Panel: Visualizer Core
        self.center_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.center_panel.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Animated Canvas
        self.canvas = tk.Canvas(self.center_panel, width=380, height=380, bg=BG_DARK, highlightthickness=1, highlightbackground=BORDER_DARK)
        self.canvas.pack(pady=(20, 10))
        
        # Status Label inside GUI
        self.core_status_lbl = ctk.CTkLabel(self.center_panel, text="STANDBY", font=ctk.CTkFont(family="Orbitron", size=18, weight="bold"), text_color=CYAN_COLOR)
        self.core_status_lbl.pack(pady=5)
        
        # Center Status Panel (Purely visual)
        self.ctrl_frame = ctk.CTkFrame(self.center_panel, height=50, border_width=1, border_color=BORDER_DARK)
        self.ctrl_frame.pack(fill="x", padx=40, pady=10)
        self.ctrl_frame.pack_propagate(False)
        
        # Center the voice online label
        self.voice_status_indicator = ctk.CTkLabel(self.ctrl_frame, text="⚡ VOICE DETECTION ACTIVE", text_color=CYAN_COLOR, font=ctk.CTkFont(family="Orbitron", size=12, weight="bold"))
        self.voice_status_indicator.pack(expand=True)

        # 4. Right Panel: Chat Log & Text Console
        self.right_panel = ctk.CTkFrame(self, border_width=1, border_color=BORDER_DARK)
        self.right_panel.grid(row=1, column=2, sticky="nsew", padx=(5, 10), pady=(5, 5))
        
        self.log_title = ctk.CTkLabel(self.right_panel, text="COMMUNICATION LOG", font=ctk.CTkFont(family="Orbitron", size=14, weight="bold"), text_color=TEXT_WHITE)
        self.log_title.pack(pady=15)
        
        # Scrolled Text Box for logs (Expanded to fill panel)
        self.log_box = tk.Text(self.right_panel, bg=CONSOLE_BG, fg=TEXT_WHITE, font=("Share Tech Mono", 10), state="disabled", wrap="word", borderwidth=0, highlightthickness=1, highlightbackground=BORDER_DARK)
        self.log_box.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Setup colors in text box
        self.log_box.tag_config('system', foreground=TEXT_DIM)
        self.log_box.tag_config('user', foreground=AMBER_COLOR)
        self.log_box.tag_config('yuki', foreground=CYAN_COLOR)

    # Thread-Safe GUI Log Writer
    def log_msg(self, sender, message, level="system"):
        self.after(0, lambda: self._log_msg_main_thread(sender, message, level))

    def _log_msg_main_thread(self, sender, message, level):
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, f"{sender.upper()}: {message}\n\n", level)
        self.log_box.configure(state="disabled")
        self.log_box.see(tk.END)

    # Thread-safe callback for VoiceEngine state updates
    def update_status_callback(self, text, state_code):
        self.after(0, lambda: self._update_status_ui_state(text, state_code))

    def _update_status_ui_state(self, text, state_code):
        self.assistant_state = state_code
        self.core_status_lbl.configure(text=state_code)
        
        if state_code == "LISTENING":
            self.core_status_lbl.configure(text_color=AMBER_COLOR)
            self.status_dot.configure(text_color=AMBER_COLOR)
            self.status_label.configure(text=text)
            self.voice_status_indicator.configure(text="⚡ LISTENING...", text_color=AMBER_COLOR)
        elif state_code == "PROCESSING":
            self.core_status_lbl.configure(text_color=CYAN_COLOR)
            self.status_dot.configure(text_color=CYAN_COLOR)
            self.status_label.configure(text=text)
            self.voice_status_indicator.configure(text="⚡ PROCESSING...", text_color=CYAN_COLOR)
        elif state_code == "SPEAKING":
            self.core_status_lbl.configure(text_color=CYAN_COLOR)
            self.status_dot.configure(text_color=CYAN_COLOR)
            self.status_label.configure(text=text)
            self.voice_status_indicator.configure(text="⚡ TRANSMITTING...", text_color=CYAN_COLOR)
        else: # STANDBY
            self.core_status_lbl.configure(text_color=CYAN_COLOR)
            self.status_dot.configure(text_color=CYAN_COLOR)
            self.status_label.configure(text="ONLINE")
            self.voice_status_indicator.configure(text="⚡ VOICE DETECTION ACTIVE", text_color=CYAN_COLOR)

    # --- UI System Monitoring Loop ---
    def poll_stats_loop(self):
        while self.stats_running:
            cpu = get_cpu_usage()
            ram = get_ram_usage()
            win = get_active_window_title()
            
            # Update UI on main thread
            self.after(10, lambda c=cpu, r=ram, w=win: self.update_stats_ui(c, r, w))
            
            # System Clock update
            now = datetime.now()
            time_str = now.strftime("%H:%M:%S")
            self.after(10, lambda t=time_str: self.header_time.configure(text=t))
            
            time.sleep(2.0)

    def update_stats_ui(self, cpu, ram, win):
        self.cpu_val.configure(text=f"{cpu}%")
        self.cpu_bar.set(cpu / 100.0)
        
        self.ram_val.configure(text=f"{ram['load_percent']}%")
        self.ram_bar.set(ram['load_percent'] / 100.0)
        self.ram_details.configure(text=f"{ram['used_gb']:.1f} GB / {ram['total_gb']:.1f} GB USED")
        
        self.active_window_txt.configure(text=win.upper())

    # --- Canvas Visualizer Animation ---
    def animate_visualizer(self):
        # Clear Canvas
        self.canvas.delete("all")
        
        # Initialize equalizer heights array if not present
        if not hasattr(self, 'eq_heights'):
            self.eq_heights = [0.0] * 16
            
        # Draw retro rack border and decibel grid
        self.canvas.create_rectangle(35, 75, 345, 295, outline=BORDER_DARK, width=2)
        
        # Grid parameters
        num_cols = 16
        col_w = 14
        gap_x = 4
        start_x = 48
        
        num_segs = 14
        seg_h = 10
        gap_y = 3
        start_y = 88
        
        # Draw background reference decibel grid lines and text
        db_levels = [(12, "+6dB", "#FF3B30"), (9, "0dB", "#FFAA00"), (5, "-12dB", "#00F0FF")]
        for lvl, label, col in db_levels:
            y = start_y + (num_segs - 1 - lvl) * (seg_h + gap_y) + (seg_h // 2)
            self.canvas.create_line(48, y, 332, y, fill="#1A2436", dash=(3, 3))
            self.canvas.create_text(26, y, text=label, fill=col, font=("Share Tech Mono", 8), anchor="w")

        # Determine target heights based on assistant state
        if self.assistant_state == "STANDBY":
            # Slow, gentle wave (idle)
            target_heights = [
                int(2 + math.sin(time.time() * 2.5 + i * 0.5) * 1.5)
                for i in range(num_cols)
            ]
        elif self.assistant_state == "LISTENING":
            # Amber active pulsing wave
            target_heights = [
                int(5 + math.sin(time.time() * 10 + i * 0.7) * 4)
                for i in range(num_cols)
            ]
        elif self.assistant_state == "PROCESSING":
            # Cylon-like scan bar sweeping left to right
            sweep_idx = int((time.time() * 15) % num_cols)
            target_heights = [
                int(12 if i == sweep_idx else (7 if abs(i - sweep_idx) == 1 else 1))
                for i in range(num_cols)
            ]
        elif self.assistant_state == "SPEAKING":
            # Dynamic retro frequency spectrum bouncing for vocal speech
            target_heights = []
            for i in range(num_cols):
                if i < 4:
                    # Bass frequencies (moderate bounce)
                    target_heights.append(random.randint(4, 11))
                elif i < 11:
                    # Vocal frequencies (high dynamic bounce)
                    target_heights.append(random.randint(5, 14))
                else:
                    # Treble frequencies (faster low/mid bounce)
                    target_heights.append(random.randint(2, 8))
        else:
            target_heights = [1] * num_cols

        # Interpolate heights for smooth fluid movement
        for i in range(num_cols):
            self.eq_heights[i] += (target_heights[i] - self.eq_heights[i]) * 0.35

        # Draw LED segments
        for i in range(num_cols):
            active_segs = int(self.eq_heights[i])
            for j in range(num_segs):
                # Calculate bounding box
                x1 = start_x + i * (col_w + gap_x)
                y1 = start_y + (num_segs - 1 - j) * (seg_h + gap_y)
                x2 = x1 + col_w
                y2 = y1 + seg_h
                
                # Emissive Color Rules
                if j < active_segs:
                    # Lit LED
                    if j >= 11:
                        color = "#FF3B30"  # Top 3 (Red)
                    elif j >= 7:
                        color = "#FFAA00"  # Middle 4 (Amber)
                    else:
                        color = "#00F0FF"  # Bottom 7 (Cyan)
                else:
                    # Unlit LED grille segment (very dim background color)
                    color = "#101824"
                    
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                
        # Draw status text header and label inside visualizer area
        text_col = CYAN_COLOR if self.assistant_state != "LISTENING" else AMBER_COLOR
        self.canvas.create_text(190, 320, text="RETROWAVE SPECTRUM ANALYZER", fill="#64748B", font=("Share Tech Mono", 10), anchor="center")
        self.canvas.create_text(190, 345, text=f"STATE: {self.assistant_state}", fill=text_col, font=("Orbitron", 12, "bold"), anchor="center")

        # Trigger next frame in 30ms (~33 FPS)
        self.after(30, self.animate_visualizer)

    def destroy(self):
        # Stop statistics thread
        self.stats_running = False
        # Stop voice background listening loop
        self.voice.stop_listening()
        super().destroy()
