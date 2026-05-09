"""
ui/widgets.py — Reusable low-level Tkinter widget helpers.

Exports
-------
make_avatar(parent, letter, bg_col, fg_col, size) -> Canvas
glass_frame(parent, bg, border, **kw) -> (outer_frame, inner_frame)
"""

import tkinter as tk

from config import GLASS_DARK, BORDER


def make_avatar(
    parent: tk.Widget,
    letter: str,
    bg_col: str,
    fg_col: str,
    size: int = 32,
) -> tk.Canvas:
    """
    Draw a circular avatar with a single letter centred inside.

    Parameters
    ----------
    parent  : parent widget
    letter  : single character to display
    bg_col  : fill colour of the circle
    fg_col  : colour of the letter and circle outline
    size    : diameter in pixels
    """
    canvas = tk.Canvas(
        parent,
        width=size,
        height=size,
        bg=parent["bg"],
        highlightthickness=0,
    )
    radius = size // 2
    canvas.create_oval(2, 2, size - 2, size - 2,
                       fill=bg_col, outline=fg_col, width=1)
    canvas.create_text(
        radius, radius,
        text=letter,
        fill=fg_col,
        font=("DejaVu Sans", int(size * 0.38), "bold"),
    )
    return canvas


def glass_frame(
    parent: tk.Widget,
    bg: str = GLASS_DARK,
    border: str = BORDER,
    **kw,
) -> tuple[tk.Frame, tk.Frame]:
    """
    Create a simulated glassmorphism card: a 1 px border frame wrapping
    an inner content frame.

    Returns
    -------
    (outer_frame, inner_frame)
        Pack/place *outer_frame* in your layout; add children to *inner_frame*.
    """
    outer = tk.Frame(parent, bg=border, padx=1, pady=1)
    inner = tk.Frame(outer, bg=bg, **kw)
    inner.pack(fill="both", expand=True)
    return outer, inner
