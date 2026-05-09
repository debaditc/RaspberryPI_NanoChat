"""
ui/indicators.py — Live feedback widgets: status bar, voice visualiser,
                   and typing indicator.

Exports
-------
StatusBar(parent, **kw)      : tk.Frame   — state label + pulsing dot
SineWaveVis(parent, **kw)    : tk.Canvas  — mic-driven sine wave
TypingIndicator(parent, **kw): tk.Canvas  — three bouncing dots
"""

import math
import tkinter as tk

from config import (
    GLASS_DARK, BORDER, GLOW_CYAN, GLOW_PINK, GLOW_TEAL,
    TEXT_LOW, TEXT_MID, BOT_BG, MODEL_NAME,
)


# ── Status Bar ────────────────────────────────────────────────────────────────

class StatusBar(tk.Frame):
    """
    Horizontal bar showing the current app state (idle / listening /
    thinking / speaking) with a pulsing colour dot and model info.
    """

    STATES: dict[str, tuple[str, str]] = {
        "idle":      ("◉  Ready",       TEXT_LOW),
        "listening": ("🎙  Listening…",  GLOW_PINK),
        "thinking":  ("🧠  Thinking…",   GLOW_CYAN),
        "speaking":  ("🔊  Speaking…",   GLOW_TEAL),
    }
    PULSE_COLOURS: dict[str, str] = {
        "idle":      TEXT_LOW,
        "listening": GLOW_PINK,
        "thinking":  GLOW_CYAN,
        "speaking":  GLOW_TEAL,
    }
    PULSE_DELAY_MS = 60

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent, bg=GLASS_DARK, height=30, **kw)
        self.pack_propagate(False)

        self._dot = tk.Canvas(self, width=10, height=10,
                              bg=GLASS_DARK, highlightthickness=0)
        self._dot.pack(side="left", padx=(12, 4), pady=10)

        self._label = tk.Label(self, text="", bg=GLASS_DARK,
                               font=("DejaVu Sans Mono", 9))
        self._label.pack(side="left")

        tk.Label(
            self,
            text=f"⚡ {MODEL_NAME}  ·  streaming  ·  CoT",
            bg=GLASS_DARK, fg=TEXT_LOW,
            font=("DejaVu Sans Mono", 8),
        ).pack(side="right", padx=12)

        self._phase = 0.0
        self._state = "idle"
        self._pulse()
        self.set("idle")

    def set(self, state: str) -> None:
        """Update the displayed state."""
        self._state = state
        text, colour = self.STATES.get(state, ("◉  Ready", TEXT_LOW))
        self._label.config(text=text, fg=colour)

    def _pulse(self) -> None:
        """Animate the indicator dot with a sine-driven brightness boost."""
        self._phase = (self._phase + 0.15) % (2 * math.pi)
        base_hex = self.PULSE_COLOURS.get(self._state, TEXT_LOW).lstrip("#")
        r = int(base_hex[0:2], 16)
        g = int(base_hex[2:4], 16)
        b = int(base_hex[4:6], 16)
        boost = int(0x44 + 0x44 * abs(math.sin(self._phase)))
        col = (
            f"#{min(255, r + boost):02x}"
            f"{min(255, g + boost // 2):02x}"
            f"{min(255, b + boost // 3):02x}"
        )
        self._dot.delete("all")
        self._dot.create_oval(1, 1, 9, 9, fill=col, outline="")
        self.after(self.PULSE_DELAY_MS, self._pulse)


# ── Sine Wave Visualiser ──────────────────────────────────────────────────────

class SineWaveVis(tk.Canvas):
    """
    Draws a smooth dual-harmonic sine wave whose amplitude tracks the
    live microphone RMS level via update_rms().
    """

    WIDTH  = 340
    HEIGHT = 60
    STEPS  = 80          # number of line segments
    FRAME_DELAY_MS = 30  # ~33 fps

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(
            parent,
            width=self.WIDTH, height=self.HEIGHT,
            bg=GLASS_DARK,
            highlightthickness=1, highlightbackground=BORDER,
            **kw,
        )
        self._amplitude  = 0.0   # current smoothed amplitude
        self._target_amp = 0.0   # target amplitude (from RMS)
        self._phase      = 0.0
        self._active     = False
        self._tick()

    # ── public controls ───────────────────────────────────────────

    def start(self) -> None:
        """Begin active animation (mic is recording)."""
        self._active = True

    def stop(self) -> None:
        """Return to idle animation (mic stopped)."""
        self._active      = False
        self._target_amp  = 0.0

    def update_rms(self, normalised_rms: float) -> None:
        """Feed live RMS value in [0, 1] from the mic stream."""
        self._target_amp = normalised_rms

    # ── animation loop ────────────────────────────────────────────

    def _tick(self) -> None:
        # Smooth amplitude towards target
        self._amplitude += (self._target_amp - self._amplitude) * 0.3
        self._phase += 0.18 if self._active else 0.04
        self._draw()
        self.after(self.FRAME_DELAY_MS, self._tick)

    def _draw(self) -> None:
        self.delete("wave")
        w, h = self.WIDTH, self.HEIGHT
        centre_y = h // 2
        max_amp  = (centre_y - 6) * self._amplitude

        points = []
        for i in range(self.STEPS + 1):
            x = int(i * w / self.STEPS)
            y = int(
                centre_y
                + max_amp * math.sin(self._phase + i * 0.22)
                + max_amp * 0.4 * math.sin(self._phase * 1.7 + i * 0.41)
            )
            points.extend([x, y])

        if len(points) < 4:
            return

        colour = GLOW_CYAN if self._active else TEXT_LOW
        # Three-layer glow (widest/dimmest first)
        for width, stipple in [(5, "gray25"), (3, "gray50"), (1, "")]:
            kw: dict = {"fill": colour, "width": width,
                        "smooth": True, "tags": "wave"}
            if stipple:
                kw["stipple"] = stipple
            self.create_line(*points, **kw)


# ── Typing Indicator ──────────────────────────────────────────────────────────

class TypingIndicator(tk.Canvas):
    """Three dots that animate with staggered sine pulses."""

    DOT_COUNT      = 3
    CANVAS_W       = 56
    CANVAS_H       = 22
    CYCLE_STEPS    = 18
    FRAME_DELAY_MS = 80

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(
            parent,
            width=self.CANVAS_W, height=self.CANVAS_H,
            bg=BOT_BG, highlightthickness=0,
            **kw,
        )
        self._step   = 0
        self._active = False
        self._tick()

    def show(self) -> None:
        self._active = True
        self.pack(anchor="w", padx=20, pady=4)

    def hide(self) -> None:
        self._active = False
        self.pack_forget()

    def _tick(self) -> None:
        self.delete("all")
        self._step = (self._step + 1) % self.CYCLE_STEPS
        colour     = GLOW_CYAN if self._active else TEXT_LOW

        for i in range(self.DOT_COUNT):
            t    = ((self._step + i * 6) % self.CYCLE_STEPS) / self.CYCLE_STEPS
            size = 4 + int(4 * math.sin(t * math.pi))
            x    = 10 + i * 18
            y    = self.CANVAS_H // 2
            self.create_oval(
                x - size // 2, y - size // 2,
                x + size // 2, y + size // 2,
                fill=colour, outline="",
            )
        self.after(self.FRAME_DELAY_MS, self._tick)
