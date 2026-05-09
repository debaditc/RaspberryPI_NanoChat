"""
ui/controls.py — Interactive control widgets.

Exports
-------
MicButton(parent, command, **kw) : tk.Canvas  — animated mic button
ScrollBtn(parent, chat, **kw)    : tk.Button  — floating scroll-to-bottom
"""

import math
import tkinter as tk
from typing import Callable

from config import (
    GLASS_DARK, GLASS_MID, GLOW_CYAN, GLOW_PINK, GLOW_TEAL,
    MIC_IDLE, MIC_REC, MIC_THINK, MIC_SPEAK,
    TEXT_MID, BG_DEEP,
)


# ── Mic Button ────────────────────────────────────────────────────────────────

class MicButton(tk.Canvas):
    """
    Large circular microphone button with per-state animations:
      idle      — static cyan disc
      listening — expanding pink pulse rings
      thinking  — spinning cyan arc
      speaking  — gentle teal oscillating ring
    Only responds to taps when in the 'idle' state.
    """

    SIZE   = 130
    RADIUS = 52
    FRAME_DELAY_MS = 30   # ~33 fps

    _STATE_COLOURS: dict[str, str] = {
        "idle":      MIC_IDLE,
        "listening": MIC_REC,
        "thinking":  MIC_THINK,
        "speaking":  MIC_SPEAK,
    }
    _STATE_LABELS: dict[str, str] = {
        "idle":      "TAP TO TALK",
        "listening": "LISTENING…",
        "thinking":  "THINKING…",
        "speaking":  "SPEAKING…",
    }

    def __init__(self, parent: tk.Widget, command: Callable, **kw):
        super().__init__(
            parent,
            width=self.SIZE, height=self.SIZE,
            bg=GLASS_DARK, highlightthickness=0,
            cursor="hand2",
            **kw,
        )
        self._command = command
        self._state   = "idle"
        self._angle   = 0.0      # spinning arc angle
        self._pulse   = 0.0      # 0 → 1 oscillator
        self._pulse_d = 0.04     # direction

        self.bind("<ButtonRelease-1>", self._on_click)
        self._tick()

    def set_state(self, state: str) -> None:
        self._state = state

    # ── event ─────────────────────────────────────────────────────

    def _on_click(self, _event) -> None:
        if self._state == "idle":
            self._command()

    # ── animation loop ────────────────────────────────────────────

    def _tick(self) -> None:
        self._angle = (self._angle + 3.5) % 360
        self._pulse += self._pulse_d
        if self._pulse >= 1 or self._pulse <= 0:
            self._pulse_d *= -1
        self._draw()
        self.after(self.FRAME_DELAY_MS, self._tick)

    def _draw(self) -> None:
        self.delete("all")
        cx = cy = self.SIZE // 2
        r  = self.RADIUS
        colour = self._STATE_COLOURS.get(self._state, MIC_IDLE)

        self._draw_glow_rings(cx, cy, r)
        self._draw_base_disc(cx, cy, r, colour)
        self._draw_mic_icon(cx, cy)
        self._draw_label(cx, cy, r)

    def _draw_glow_rings(self, cx: int, cy: int, r: int) -> None:
        if self._state == "listening":
            gr = r + 6 + int(self._pulse * 14)
            for i in range(3):
                ar = gr + i * 5
                self.create_oval(
                    cx - ar, cy - ar, cx + ar, cy + ar,
                    outline=GLOW_PINK,
                    width=max(1, 3 - i),
                    stipple="gray50" if i else "",
                )
        elif self._state == "thinking":
            self.create_arc(
                cx - r - 10, cy - r - 10,
                cx + r + 10, cy + r + 10,
                start=self._angle, extent=270,
                outline=GLOW_CYAN, width=2, style="arc",
            )
        elif self._state == "speaking":
            gr = r + 4 + int(self._pulse * 10)
            self.create_oval(
                cx - gr, cy - gr, cx + gr, cy + gr,
                outline=GLOW_TEAL, width=2,
            )

    def _draw_base_disc(self, cx: int, cy: int, r: int, colour: str) -> None:
        # Layered rings for glass depth
        for dr, stipple in [(4, "gray25"), (2, "gray50"), (0, "")]:
            kw: dict = {"fill": GLASS_MID, "outline": ""}
            if stipple:
                kw["stipple"] = stipple
            self.create_oval(cx - r + dr, cy - r + dr,
                             cx + r - dr, cy + r - dr, **kw)
        self.create_oval(cx - r + 6, cy - r + 6,
                         cx + r - 6, cy + r - 6,
                         fill=colour, outline="")

    def _draw_mic_icon(self, cx: int, cy: int) -> None:
        bw = 14
        # Capsule top
        self.create_arc(cx - bw, cy - 24, cx + bw, cy - 24 + bw * 2,
                        start=0, extent=180, fill="white", outline="")
        # Capsule body
        self.create_rectangle(cx - bw, cy - 14, cx + bw, cy + 4,
                              fill="white", outline="")
        # Capsule bottom
        self.create_arc(cx - bw, cy - 10, cx + bw, cy + bw * 2 - 10,
                        start=180, extent=180, fill="white", outline="")
        # Stand
        self.create_line(cx, cy + 12, cx, cy + 22, fill="white", width=2)
        self.create_line(cx - 11, cy + 22, cx + 11, cy + 22,
                         fill="white", width=2)
        # Arc
        self.create_arc(cx - 20, cy - 6, cx + 20, cy + 36,
                        start=0, extent=180,
                        outline="white", width=2, style="arc")

    def _draw_label(self, cx: int, cy: int, r: int) -> None:
        label = self._STATE_LABELS.get(self._state, "")
        self.create_text(
            cx, cy + r + 16,
            text=label, fill=TEXT_MID,
            font=("DejaVu Sans Mono", 8),
        )


# ── Scroll-to-bottom Button ───────────────────────────────────────────────────

class ScrollBtn(tk.Button):
    """
    Floating ▼ button that appears when the chat is not scrolled to the
    bottom and disappears when it is.
    """

    POLL_DELAY_MS = 400

    def __init__(self, parent: tk.Widget, chat, **kw):
        super().__init__(
            parent,
            text="▼",
            bg=GLOW_CYAN, fg=BG_DEEP,
            font=("DejaVu Sans", 12, "bold"),
            relief="flat", cursor="hand2",
            width=3, bd=0,
            command=chat.scroll_bottom,
            **kw,
        )
        self._chat    = chat
        self._visible = False
        self._poll()

    def _poll(self) -> None:
        needs_button = not self._chat._at_bottom
        if needs_button and not self._visible:
            self.place(relx=0.93, rely=0.86, anchor="se")
            self._visible = True
        elif not needs_button and self._visible:
            self.place_forget()
            self._visible = False
        self.after(self.POLL_DELAY_MS, self._poll)
