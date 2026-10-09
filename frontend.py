import asyncio
import math
import threading
import time
import tkinter as tk

import customtkinter as ctk

from main import record_audio, transcribe_audio, ask_ai, speak


# -------------------- THEME --------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#080B16"
PANEL = "#101629"
CHAT_BG = "#0D1221"
BLUE = "#62A5FF"
PURPLE = "#A678FF"
GREEN = "#69E6BB"
TEXT = "#EDF2FF"
MUTED = "#8A96B2"


class AIVoiceAssistantUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AURA | AI Voice Assistant")
        self.geometry("1100x760")
        self.minsize(850, 620)
        self.configure(fg_color=BG)

        self.history = []
        self.busy = False
        self.listening = False
        self.closing = False
        self.orb_state = "idle"
        self.animation_started = time.monotonic()
        self.mic_level = 0.0  # Updated by the active recording stream.

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_area()
        self.add_message(
            "AURA",
            "Welcome back. I'm ready when you are. Type a message or start a voice conversation.",
            "assistant",
        )
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.animate_orb()

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=225, corner_radius=0, fg_color=PANEL)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar, text="✦  A U R A",
            font=("Segoe UI", 27, "bold"), text_color=BLUE,
        ).pack(pady=(32, 4))
        ctk.CTkLabel(
            self.sidebar, text="PERSONAL AI COMPANION",
            font=("Segoe UI", 10, "bold"), text_color=MUTED,
        ).pack(pady=(0, 34))

        ctk.CTkButton(
            self.sidebar, text="＋   New conversation", height=42,
            corner_radius=12, fg_color="#1B2741", hover_color="#293A5D",
            command=self.new_conversation,
        ).pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(
            self.sidebar, text="WORKSPACE", font=("Segoe UI", 10, "bold"),
            text_color=MUTED, anchor="w",
        ).pack(fill="x", padx=20, pady=(35, 12))
        for label in ("◆   AI Conversation", "◉   Voice Mode"):
            ctk.CTkLabel(
                self.sidebar, text=label, font=("Segoe UI", 13),
                text_color=TEXT, anchor="w",
            ).pack(fill="x", padx=22, pady=9)

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#27314A").pack(
            fill="x", padx=18, pady=24
        )
        ctk.CTkLabel(
            self.sidebar, text="SYSTEM STATUS", font=("Segoe UI", 10, "bold"),
            text_color=MUTED, anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 10))

        self.sidebar_status = ctk.CTkLabel(
            self.sidebar, text="●  SYSTEM READY",
            font=("Segoe UI", 11, "bold"), text_color=GREEN, anchor="w",
        )
        self.sidebar_status.pack(side="bottom", fill="x", padx=20, pady=25)

    def create_main_area(self):
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color=BG)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self.main_area, fg_color=BG)
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(18, 4))
        ctk.CTkLabel(
            header, text="AURA", font=("Segoe UI", 25, "bold"), text_color=TEXT
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="YOUR INTELLIGENT VOICE ASSISTANT",
            font=("Segoe UI", 10, "bold"), text_color=MUTED,
        ).pack(anchor="w", pady=(0, 3))

        orb_panel = ctk.CTkFrame(self.main_area, fg_color=BG)
        orb_panel.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 2))
        self.orb_canvas = tk.Canvas(
            orb_panel, height=190, bg=BG, highlightthickness=0, bd=0
        )
        self.orb_canvas.pack(fill="x")
        self.orb_status = ctk.CTkLabel(
            orb_panel, text="●  STANDBY",
            font=("Segoe UI", 11, "bold"), text_color=BLUE,
        )
        self.orb_status.pack(pady=(0, 5))

        self.chat_frame = ctk.CTkScrollableFrame(
            self.main_area, fg_color=CHAT_BG, corner_radius=18
        )
        self.chat_frame.grid(row=2, column=0, sticky="nsew", padx=25, pady=(5, 10))

        input_frame = ctk.CTkFrame(
            self.main_area, fg_color="#151D30", corner_radius=16
        )
        input_frame.grid(row=3, column=0, sticky="ew", padx=25, pady=(4, 22))
        input_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = ctk.CTkEntry(
            input_frame, placeholder_text="Message AURA...", height=48,
            border_width=0, fg_color="transparent", font=("Segoe UI", 14),
        )
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=(15, 5), pady=10)
        self.message_entry.bind("<Return>", self.send_message)

        self.send_button = ctk.CTkButton(
            input_frame, text="Send", width=75, height=40, corner_radius=11,
            command=self.send_message,
        )
        self.send_button.grid(row=0, column=1, padx=5, pady=10)

        self.mic_button = ctk.CTkButton(
            input_frame, text="🎙  Talk", width=105, height=40, corner_radius=11,
            fg_color="#334B89", hover_color="#4565B5", command=self.start_voice,
        )
        self.mic_button.grid(row=0, column=2, padx=(5, 12), pady=10)

    # -------------------- ORB: REACTS TO LIVE MIC LEVEL --------------------
    def animate_orb(self):
        if self.closing:
            return

        canvas = self.orb_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 300)
        height = 190
        cx, cy = width / 2, height / 2
        elapsed = time.monotonic() - self.animation_started

        speeds = {"idle": 1.3, "listening": 3.8, "thinking": 2.6, "speaking": 4.5}
        pulse = (math.sin(elapsed * speeds.get(self.orb_state, 1.3)) + 1) / 2

        if self.orb_state == "listening":
            core, glow = "#78C5FF", "#284F9E"
            # Mic RMS is normalized and smoothed in the audio callback.
            mic_boost = min(max(self.mic_level * 420, 0.0), 1.0)
        elif self.orb_state == "thinking":
            core, glow = "#C2A0FF", "#583A9C"
            mic_boost = 0.0
        elif self.orb_state == "speaking":
            core, glow = "#79F0D0", "#216B82"
            mic_boost = 0.0
        else:
            core, glow = "#8AB6FF", "#283D7D"
            mic_boost = 0.0

        # The orb grows with the actual recorded microphone signal.
        growth = 17 * mic_boost
        for i in range(5):
            radius = 45 + i * 10 + pulse * 4 + growth * (0.15 + i * 0.07)
            canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                outline=glow, width=1,
            )

        for i in range(3):
            angle = elapsed * (0.7 + i * 0.18) + i * 2.1
            orbit_radius = 66 + i * 8 + growth * 0.15
            dx = cx + math.cos(angle) * orbit_radius
            dy = cy + math.sin(angle) * orbit_radius * 0.55
            dot_radius = 3 + pulse * 2 + mic_boost * 2
            canvas.create_oval(
                dx - dot_radius, dy - dot_radius, dx + dot_radius, dy + dot_radius,
                fill=core, outline="",
            )

        layers = [
            (43 + pulse * 5 + growth, glow),
            (34 + pulse * 4 + growth * 0.7, "#192E5A"),
            (25 + pulse * 3 + growth * 0.4, "#244A83"),
            (16 + pulse * 2 + growth * 0.2, core),
        ]
        for radius, color in layers:
            canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill=color, outline="",
            )

        canvas.create_oval(cx - 11, cy - 13, cx - 1, cy - 3, fill="#FFFFFF", outline="")

        if self.orb_state in ("listening", "thinking", "speaking"):
            bar_count, bar_width, gap = 13, 4, 5
            total_width = bar_count * (bar_width + gap) - gap
            start_x = cx - total_width / 2
            for i in range(bar_count):
                wave = math.sin(elapsed * 6 + i * 0.8)
                base = 9 + pulse * 9
                bar_height = 5 + abs(wave) * base
                if self.orb_state == "listening":
                    bar_height += mic_boost * (8 + (i % 4) * 3)
                x1 = start_x + i * (bar_width + gap)
                canvas.create_rectangle(
                    x1, 174 - bar_height, x1 + bar_width, 174,
                    fill=core, outline="",
                )

        # Fade the stored level between audio blocks so the orb settles naturally.
        self.mic_level *= 0.82
        self.after(45, self.animate_orb)

    def set_orb_state(self, state, label):
        if self.closing:
            return
        self.orb_state = state
        self.orb_status.configure(text=label)
        colors = {"idle": BLUE, "listening": BLUE, "thinking": PURPLE, "speaking": GREEN}
        self.orb_status.configure(text_color=colors.get(state, BLUE))
        if state != "listening":
            self.mic_level = 0.0

    # -------------------- CHAT MESSAGES --------------------
    def add_message(self, sender, message, kind):
        if self.closing:
            return
        is_user = kind == "user"
        bubble = ctk.CTkFrame(
            self.chat_frame, fg_color="#203D68" if is_user else "#192235",
            corner_radius=14,
        )
        bubble.pack(anchor="e" if is_user else "w", padx=12, pady=8, fill="x")
        ctk.CTkLabel(
            bubble, text=sender, font=("Segoe UI", 11, "bold"),
            text_color="#8DB8FF" if is_user else GREEN, anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(
            bubble, text=message, font=("Segoe UI", 13), text_color=TEXT,
            wraplength=620, justify="left", anchor="w",
        ).pack(fill="x", padx=14, pady=(2, 12))
        self.after(
            100,
            lambda: self.chat_frame._parent_canvas.yview_moveto(1.0)
            if not self.closing else None,
        )

    def set_status(self, message, ready=False):
        if self.closing:
            return
        if ready:
            self.sidebar_status.configure(text="●  SYSTEM READY", text_color=GREEN)
        elif self.listening:
            self.sidebar_status.configure(text="●  LISTENING", text_color=BLUE)
        else:
            self.sidebar_status.configure(text="●  PROCESSING", text_color=PURPLE)

    # -------------------- TEXT CHAT --------------------
    def send_message(self, event=None):
        if self.busy or self.closing:
            return
        question = self.message_entry.get().strip()
        if not question:
            return
        self.message_entry.delete(0, "end")
        self.add_message("You", question, "user")
        self.busy = True
        self.send_button.configure(state="disabled")
        self.mic_button.configure(state="disabled")
        self.set_orb_state("thinking", "◌  THINKING")
        self.set_status("AURA is thinking...")
        threading.Thread(target=self.process_text, args=(question,), daemon=True).start()

    def process_text(self, question):
        try:
            answer = ask_ai(question, self.history)
            self.after(0, self.show_answer, answer)
        except Exception as error:
            self.after(0, self.show_error, str(error))

    # -------------------- CONTINUOUS VOICE --------------------
    def start_voice(self):
        if self.closing:
            return
        if self.listening:
            self.listening = False
            self.mic_button.configure(text="Stopping...", fg_color="#7D3038")
            self.set_status("Stopping after the current operation...")
            return
        if self.busy:
            return
        self.listening = True
        self.busy = True
        self.send_button.configure(state="disabled")
        self.mic_button.configure(text="⏹  Stop", fg_color="#B93838", hover_color="#922B2B")
        self.set_orb_state("listening", "◉  LISTENING")
        self.set_status("Listening for your question...")
        threading.Thread(target=self.continuous_voice_loop, daemon=True).start()

    def continuous_voice_loop(self):
        try:
            while self.listening and not self.closing:
                self.after(0, self.set_orb_state, "listening", "◉  LISTENING")
                self.after(0, self.set_status, "Listening — speak now")
                # This callback receives RMS levels from the SAME recording stream.
                filename = record_audio(volume_callback=self.update_mic_level)
                self.mic_level = 0.0

                if not self.listening or self.closing:
                    break

                self.after(0, self.set_orb_state, "thinking", "◌  UNDERSTANDING")
                question = transcribe_audio(filename)
                if not self.listening or self.closing:
                    break
                if not question:
                    continue

                self.after(0, self.add_message, "You", question, "user")
                self.after(0, self.set_orb_state, "thinking", "◌  THINKING")
                self.after(0, self.set_status, "AURA is preparing an answer...")
                answer = ask_ai(question, self.history)
                if not self.listening or self.closing:
                    break

                self.after(0, self.add_message, "AURA", answer, "assistant")
                self.after(0, self.set_orb_state, "speaking", "♫  SPEAKING")
                self.after(0, self.set_status, "AURA is speaking...")
                asyncio.run(speak(answer))
        except Exception as error:
            if not self.closing:
                self.after(0, self.show_voice_error, str(error))
        finally:
            self.listening = False
            if not self.closing:
                self.after(0, self.finish_voice_loop)

    def update_mic_level(self, level):
        # Called on the audio thread; no Tk widgets are touched here.
        try:
            self.mic_level = max(0.0, min(float(level), 0.03))
        except (TypeError, ValueError):
            self.mic_level = 0.0

    def finish_voice_loop(self):
        if self.closing:
            return
        self.busy = False
        self.mic_button.configure(
            text="🎙  Talk", state="normal",
            fg_color="#334B89", hover_color="#4565B5",
        )
        self.send_button.configure(state="normal")
        self.set_orb_state("idle", "●  STANDBY")
        self.set_status("Ready when you are", ready=True)

    # -------------------- SPEECH PLAYBACK --------------------
    def show_answer(self, answer):
        if self.closing:
            return
        self.add_message("AURA", answer, "assistant")
        self.set_orb_state("speaking", "♫  SPEAKING")
        self.set_status("AURA is speaking...")
        threading.Thread(target=self.play_answer, args=(answer,), daemon=True).start()

    def play_answer(self, answer):
        try:
            asyncio.run(speak(answer))
        except Exception as error:
            self.after(0, self.show_error, str(error))
            return
        self.after(0, self.finish_turn)

    def finish_turn(self):
        if self.closing:
            return
        self.busy = False
        self.send_button.configure(state="normal")
        self.mic_button.configure(state="normal")
        self.set_orb_state("idle", "●  STANDBY")
        self.set_status("Ready when you are", ready=True)

    # -------------------- ERRORS --------------------
    def show_error(self, message):
        if self.closing:
            return
        self.add_message("AURA", "Something went wrong:\n" + message, "assistant")
        self.finish_turn()

    def show_voice_error(self, message):
        if self.closing:
            return
        self.add_message("AURA", "Voice error:\n" + message, "assistant")

    # -------------------- NEW CONVERSATION --------------------
    def new_conversation(self):
        if self.busy or self.closing:
            return
        self.history.clear()
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self.add_message(
            "AURA", "Fresh conversation! What would you like to talk about?", "assistant"
        )
        self.set_orb_state("idle", "●  STANDBY")
        self.set_status("Ready when you are", ready=True)

    # -------------------- CLOSE APP --------------------
    def close_app(self):
        self.closing = True
        self.listening = False
        try:
            self.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    app = AIVoiceAssistantUI()
    app.mainloop()
