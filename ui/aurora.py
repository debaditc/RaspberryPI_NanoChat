"""
ui/aurora.py — Slowly animated aurora gradient mesh background.

Exports
-------
AuroraBackground(parent, **kw) : tk.Canvas
    Place this canvas at x=0, y=0, relwidth=1, relheight=1 as the
    bottom-most layer of the window.
"""

import math
import tkinter as tk

from config import BG_DEEP, BG_MID, BG_HIGH


class AuroraBackground(tk.Canvas):
    """
    Tkinter Canvas that draws a slowly shifting deep-space aurora gradient.
    Uses horizontal bands whose colours are interpolated between three
    navy/teal stops driven by a sine wave.
    """

    ANIMATION_SPEED = 0.008   # radians per frame — lower = slower drift
    FRAME_DELAY_MS  = 80      # ms between redraws (~12 fps)
    BAND_COUNT      = 10      # number of horizontal gradient bands

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent, highlightthickness=0, bg=BG_DEEP, **kw)
        self._t      = 0.0
        self._width  = 1
        self._height = 1
        self.bind("<Configure>", self._on_resize)
        self._tick()

    # ── event handlers ────────────────────────────────────────────

    def _on_resize(self, event) -> None:
        self._width  = event.width
        self._height = event.height

    # ── animation loop ────────────────────────────────────────────

    def _tick(self) -> None:
        self._t = (self._t + self.ANIMATION_SPEED) % (2 * math.pi)
        self._draw()
        self.after(self.FRAME_DELAY_MS, self._tick)

    def _draw(self) -> None:
        self.delete("aurora")
        w = max(1, self._width)
        h = max(1, self._height)
        band_h = h // self.BAND_COUNT

        for i in range(self.BAND_COUNT):
            progress = i / self.BAND_COUNT
            wave     = 0.5 + 0.5 * math.sin(self._t + progress * math.pi * 2)
            colour   = self._lerp_colour(wave)
            y0 = i * band_h
            y1 = y0 + band_h + 2          # +2 avoids hairline gaps
            self.create_rectangle(0, y0, w, y1,
                                  fill=colour, outline="", tags="aurora")

    # ── colour helpers ────────────────────────────────────────────

    @staticmethod
    def _hex_to_rgb(hex_colour: str) -> tuple[int, int, int]:
        h = hex_colour.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def _lerp_colour(self, wave: float) -> str:
        """Map *wave* in [0, 1] through BG_DEEP → BG_MID → BG_HIGH."""
        if wave < 0.5:
            t  = wave * 2
            c1 = self._hex_to_rgb(BG_DEEP)
            c2 = self._hex_to_rgb(BG_MID)
        else:
            t  = (wave - 0.5) * 2
            c1 = self._hex_to_rgb(BG_MID)
            c2 = self._hex_to_rgb(BG_HIGH)

        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        return f"#{r:02x}{g:02x}{b:02x}"
