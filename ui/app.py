"""
ui/app.py — Root application window and voice/text pipeline orchestration.

Exports
-------
DebPiChatApp(root, vosk_model) : main application class
"""

import threading
import time
import tkinter as tk
from vosk import Model

from config import (
    APP_TITLE,
    BG_DEEP, GLASS_DARK, BORDER, GLOW_CYAN, GLOW_PINK,
    TEXT_MID,
)
from audio.listener import listen_once
from audio.speaker  import speak, stop_speaking
from ai.ollama      import query_ollama_stream
from ui.aurora      import AuroraBackground
from ui.chat        import ChatCanvas
from ui.controls    import MicButton, ScrollBtn
from ui.indicators  import StatusBar, SineWaveVis


class DebPiChatApp:
    """
    Top-level application.

    Responsibilities
    ----------------
    - Build the window layout (aurora, topbar, statusbar, chat, bottom panel)
    - Own the voice pipeline thread (listen → think → speak)
    - Coordinate state changes across all child widgets
    """

    # Layout constants (px)
    TOPBAR_H  = 52
    STATUS_H  = 30
    BOTTOM_H  = 190

    def __init__(self, root: tk.Tk, vosk_model: Model):
        self.root        = root
        self._vosk_model = vosk_model
        self.busy        = False

        root.title(APP_TITLE)
        root.configure(bg=BG_DEEP)
        root.attributes("-fullscreen", True)
        root.bind("<Escape>", lambda _: root.destroy())

        self._build_ui()

    # ════════════════════════════════════════════
    #  UI construction
    # ════════════════════════════════════════════

    def _build_ui(self) -> None:
        self._build_aurora()
        self._build_topbar()
        self._build_statusbar()
        self._build_chat()
        self._build_bottom_panel()
        # Floating helpers (created after chat so they can reference it)
        self._scroll_btn = ScrollBtn(self.root, self._chat)
        self.root.bind("<Configure>", lambda _: self._on_resize())

        self._chat.add_status(
            f"Welcome to {APP_TITLE}  ·  tap the mic and speak  ·  Esc to quit",
            colour=TEXT_MID,
        )

    def _build_aurora(self) -> None:
        self._aurora = AuroraBackground(self.root)
        self._aurora.place(x=0, y=0, relwidth=1, relheight=1)

    def _build_topbar(self) -> None:
        topbar = tk.Frame(self.root, bg=GLASS_DARK, height=self.TOPBAR_H)
        topbar.place(x=0, y=0, relwidth=1)
        topbar.pack_propagate(False)

        tk.Label(
            topbar,
            text=f"  ✦  {APP_TITLE}",
            bg=GLASS_DARK, fg=GLOW_CYAN,
            font=("DejaVu Sans Mono", 15, "bold"),
        ).pack(side="left", padx=10)

        tk.Button(
            topbar, text="✕",
            bg=GLASS_DARK, fg=GLOW_PINK,
            font=("DejaVu Sans", 13, "bold"),
            relief="flat", cursor="hand2", bd=0,
            command=self.root.destroy,
        ).pack(side="right", padx=10)

    def _build_statusbar(self) -> None:
        self._status = StatusBar(self.root)
        self._status.place(x=0, y=self.TOPBAR_H, relwidth=1)

    def _build_chat(self) -> None:
        self._chat = ChatCanvas(self.root, on_quick_reply=self._on_quick_reply)
        self._chat.place(
            x=0,
            y=self.TOPBAR_H + self.STATUS_H,
            relwidth=1,
            height=self._chat_height(),
        )

    def _build_bottom_panel(self) -> None:
        bottom = tk.Frame(self.root, bg=GLASS_DARK, height=self.BOTTOM_H)
        bottom.place(x=0, rely=1.0, anchor="sw", relwidth=1)
        bottom.pack_propagate(False)

        # Top separator line
        tk.Frame(bottom, bg=BORDER, height=1).pack(fill="x", side="top")

        inner = tk.Frame(bottom, bg=GLASS_DARK)
        inner.pack(expand=True)

        # Waveform visualiser
        self._wave = SineWaveVis(inner)
        self._wave.pack(pady=(8, 4))

        # Mic + stop button row
        btn_row = tk.Frame(inner, bg=GLASS_DARK)
        btn_row.pack(pady=(0, 8))

        self._mic = MicButton(btn_row, command=self._on_mic_tap)
        self._mic.pack(side="left", padx=(0, 12))

        self._stop_btn = tk.Button(
            btn_row,
            text="⏹\nSTOP",
            bg=GLOW_PINK, fg=BG_DEEP,
            font=("DejaVu Sans Mono", 10, "bold"),
            relief="flat", cursor="hand2", bd=0,
            width=6, height=3,
            activebackground="#ff6090",
            activeforeground=BG_DEEP,
            command=self._on_stop_speak,
        )
        self._stop_btn_visible = False

    # ════════════════════════════════════════════
    #  Layout helpers
    # ════════════════════════════════════════════

    def _chat_height(self) -> int:
        sh = self.root.winfo_screenheight()
        return sh - self.TOPBAR_H - self.STATUS_H - self.BOTTOM_H

    def _on_resize(self) -> None:
        self._chat.place_configure(height=self._chat_height())

    # ════════════════════════════════════════════
    #  Event handlers
    # ════════════════════════════════════════════

    def _on_quick_reply(self, text: str) -> None:
        if self.busy:
            return
        self._chat.add_bubble("user", text)
        self.busy = True
        threading.Thread(
            target=self._pipeline_text, args=(text,), daemon=True
        ).start()

    def _on_mic_tap(self) -> None:
        if self.busy:
            return
        self.busy = True
        threading.Thread(target=self._pipeline_voice, daemon=True).start()

    def _on_stop_speak(self) -> None:
        stop_speaking()
        self._set_state("idle")
        self.busy = False
        self.root.after(0, self._chat.add_status,
                        "⏹  Stopped speaking.", TEXT_MID)

    # ════════════════════════════════════════════
    #  Pipeline
    # ════════════════════════════════════════════

    def _pipeline_voice(self) -> None:
        """Full voice pipeline: record → transcribe → respond → speak."""
        self._set_state("listening")
        self._wave.start()
        transcript = listen_once(self._vosk_model, on_rms=self._wave.update_rms)
        self._wave.stop()

        if not transcript.strip():
            self.root.after(
                0, self._chat.add_status,
                "Didn't catch that — try again.", GLOW_PINK,
            )
            self._set_state("idle")
            self.busy = False
            return

        self.root.after(0, self._chat.add_bubble, "user", transcript)
        self._pipeline_text(transcript)

    def _pipeline_text(self, prompt: str) -> None:
        """Text pipeline: show typing → stream LLM response → speak."""
        self._set_state("thinking")
        self.root.after(0, self._chat.show_typing)
        time.sleep(0.2)
        self.root.after(0, self._chat.hide_typing)

        # Create streaming bubble on the main thread
        stream_label_holder: list[tk.Label | None] = [None]

        def create_stream_label() -> None:
            stream_label_holder[0] = self._chat.start_stream_bubble()

        self.root.after(0, create_stream_label)
        time.sleep(0.05)   # let the widget be created

        think_holder  = [""]
        answer_holder = [""]
        done_event    = threading.Event()

        def on_token(chunk: str) -> None:
            self.root.after(0, self._chat.append_stream, chunk)

        def on_done(think: str, answer: str) -> None:
            think_holder[0]  = think
            answer_holder[0] = answer
            done_event.set()

        query_ollama_stream(prompt, on_token, on_done)
        done_event.wait(timeout=120)

        self.root.after(
            0, self._chat.finalise_stream,
            think_holder[0], answer_holder[0], True,
        )

        self._set_state("speaking")
        speak(answer_holder[0])

        self._set_state("idle")
        self.busy = False

    # ════════════════════════════════════════════
    #  State management
    # ════════════════════════════════════════════

    def _set_state(self, state: str) -> None:
        """Propagate state change to all relevant widgets (thread-safe)."""
        self.root.after(0, self._status.set, state)
        self.root.after(0, self._mic.set_state, state)
        self.root.after(0, self._show_stop_btn, state == "speaking")

    def _show_stop_btn(self, show: bool) -> None:
        if show and not self._stop_btn_visible:
            self._stop_btn.pack(side="left")
            self._stop_btn_visible = True
        elif not show and self._stop_btn_visible:
            self._stop_btn.pack_forget()
            self._stop_btn_visible = False
