"""
ui/chat.py — Scrollable chat canvas: bubbles, quick-reply chips,
             streaming support, and typing indicator.

Exports
-------
ChatCanvas(parent, on_quick_reply, **kw) : tk.Frame
"""

import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
from typing import Callable

from config import (
    APP_TITLE, QUICK_REPLIES,
    BG_DEEP, GLASS_DARK, GLASS_MID, GLASS_LIGHT,
    GLOW_CYAN, GLOW_TEAL,
    TEXT_HI, TEXT_MID, TEXT_LOW, TEXT_THINK,
    USER_BG, USER_BORDER, BOT_BG, BOT_BORDER,
)
from ui.widgets import make_avatar
from ui.indicators import TypingIndicator


class ChatCanvas(tk.Frame):
    """
    Scrollable area that holds all chat bubbles.
    Supports token-by-token streaming into a live bubble.
    """

    def __init__(self, parent: tk.Widget, on_quick_reply: Callable, **kw):
        super().__init__(parent, bg=BG_DEEP, **kw)
        self._on_quick_reply = on_quick_reply
        self._at_bottom      = True
        self._stream_label: tk.Label | None = None

        self._build_scroll_area()
        self._build_fonts()

        self._typing = TypingIndicator(self._frame)

    # ── construction ──────────────────────────────────────────────

    def _build_scroll_area(self) -> None:
        self._canvas = tk.Canvas(self, bg=BG_DEEP, highlightthickness=0)
        self._scrollbar = tk.Scrollbar(
            self, orient="vertical",
            command=self._canvas.yview,
            bg=GLASS_DARK, troughcolor=BG_DEEP,
            activebackground=GLOW_CYAN, width=6,
        )
        self._canvas.configure(yscrollcommand=self._on_scroll_update)
        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._frame = tk.Frame(self._canvas, bg=BG_DEEP)
        self._window_id = self._canvas.create_window(
            (0, 0), window=self._frame, anchor="nw")

        self._frame.bind("<Configure>", lambda _: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._window_id, width=e.width))
        self._canvas.bind_all("<MouseWheel>", lambda e: self._canvas.yview_scroll(
            int(-e.delta / 120), "units"))

    def _build_fonts(self) -> None:
        self._font_body   = tkfont.Font(family="DejaVu Sans",      size=12)
        self._font_small  = tkfont.Font(family="DejaVu Sans Mono", size=8)
        self._font_think  = tkfont.Font(family="DejaVu Sans Mono", size=9)
        self._font_name   = tkfont.Font(family="DejaVu Sans",      size=9,
                                        weight="bold")

    # ── scrolling ─────────────────────────────────────────────────

    def _on_scroll_update(self, first: str, last: str) -> None:
        self._scrollbar.set(first, last)
        self._at_bottom = float(last) >= 0.999

    def scroll_bottom(self) -> None:
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(1.0)
        self._at_bottom = True

    # ── typing indicator ──────────────────────────────────────────

    def show_typing(self) -> None:
        self._typing.pack_forget()
        self._typing.pack(in_=self._frame, anchor="w", padx=20, pady=4)
        self._typing.show()
        self.scroll_bottom()

    def hide_typing(self) -> None:
        self._typing.hide()

    # ── public bubble API ─────────────────────────────────────────

    def add_bubble(
        self,
        who: str,
        text: str = "",
        think_text: str = "",
        show_chips: bool = False,
    ) -> tk.Label:
        """
        Add a chat bubble.  Returns the text Label so callers can stream
        tokens into it via .config(text=…).
        """
        is_user = who == "user"
        timestamp = datetime.now().strftime("%H:%M")

        row = tk.Frame(self._frame, bg=BG_DEEP)
        row.pack(fill="x", padx=10, pady=(4, 0),
                 anchor="e" if is_user else "w")

        if not is_user:
            av = make_avatar(row, "D", BOT_BG, GLOW_TEAL, 34)
            av.pack(side="left", padx=(0, 6), anchor="n", pady=4)

        card_bg     = USER_BG     if is_user else BOT_BG
        card_border = USER_BORDER if is_user else BOT_BORDER
        card_outer  = tk.Frame(row, bg=card_border, padx=1, pady=1)
        card_outer.pack(side="right" if is_user else "left", anchor="n")

        card = tk.Frame(card_outer, bg=card_bg, padx=12, pady=8)
        card.pack()

        # Header row: name + timestamp
        hdr = tk.Frame(card, bg=card_bg)
        hdr.pack(fill="x")
        name = "You" if is_user else APP_TITLE
        tk.Label(hdr, text=name, bg=card_bg, fg=TEXT_MID,
                 font=self._font_name).pack(side="left")
        tk.Label(hdr, text=f"  {timestamp}", bg=card_bg, fg=TEXT_LOW,
                 font=self._font_small).pack(side="left")

        if think_text and not is_user:
            self._add_think_panel(card, card_bg, think_text)

        label = tk.Label(
            card, text=text,
            bg=card_bg, fg=TEXT_HI,
            font=self._font_body,
            wraplength=320, justify="left", anchor="w",
        )
        label.pack(fill="x", pady=(4, 0))

        if is_user:
            av = make_avatar(row, "U", USER_BG, GLOW_CYAN, 34)
            av.pack(side="right", padx=(6, 0), anchor="n", pady=4)

        if show_chips:
            self._add_quick_chips(self._frame)

        self.scroll_bottom()
        return label

    def add_status(self, text: str, colour: str = TEXT_LOW) -> None:
        """Add a small italic status message (not a bubble)."""
        tk.Label(
            self._frame, text=text,
            bg=BG_DEEP, fg=colour,
            font=("DejaVu Sans", 9, "italic"),
        ).pack(pady=3)
        self.scroll_bottom()

    # ── streaming support ─────────────────────────────────────────

    def start_stream_bubble(self) -> tk.Label:
        """Create an empty bot bubble and return its label for streaming."""
        label = self.add_bubble("bot", text="")
        self._stream_label = label
        return label

    def append_stream(self, token: str) -> None:
        """Append a token to the currently streaming bubble."""
        if self._stream_label:
            current = self._stream_label.cget("text")
            self._stream_label.config(text=current + token)
            self.scroll_bottom()

    def finalise_stream(
        self,
        think_text: str,
        answer: str,
        show_chips: bool = True,
    ) -> None:
        """Lock in the final answer text and optionally add quick-reply chips."""
        if self._stream_label:
            self._stream_label.config(text=answer)
            self._stream_label = None
        if show_chips:
            self._add_quick_chips(self._frame)
        self.scroll_bottom()

    # ── private helpers ───────────────────────────────────────────

    def _add_think_panel(
        self, parent: tk.Widget, bg: str, text: str
    ) -> None:
        """Collapsible reasoning panel shown below the bubble header."""
        is_visible = tk.BooleanVar(value=False)
        panel = tk.Frame(parent, bg=GLASS_DARK, padx=8, pady=4)
        tk.Label(
            panel, text=text,
            bg=GLASS_DARK, fg=TEXT_THINK,
            font=self._font_think, wraplength=300, justify="left",
        ).pack(anchor="w")

        def toggle() -> None:
            if is_visible.get():
                panel.pack_forget()
                toggle_btn.config(text="▶  reasoning")
                is_visible.set(False)
            else:
                panel.pack(fill="x", pady=(2, 4))
                toggle_btn.config(text="▼  reasoning")
                is_visible.set(True)
            self.scroll_bottom()

        toggle_btn = tk.Button(
            parent, text="▶  reasoning",
            bg=bg, fg=TEXT_THINK,
            font=("DejaVu Sans", 8, "italic"),
            relief="flat", cursor="hand2", bd=0,
            command=toggle,
        )
        toggle_btn.pack(anchor="w", pady=(2, 0))

    def _add_quick_chips(self, parent: tk.Widget) -> None:
        """Row of quick-reply suggestion buttons."""
        row = tk.Frame(parent, bg=BG_DEEP)
        row.pack(anchor="w", padx=52, pady=(2, 6))
        for label in QUICK_REPLIES:
            btn = tk.Button(
                row, text=label,
                bg=GLASS_MID, fg=GLOW_CYAN,
                font=("DejaVu Sans", 9),
                relief="flat", cursor="hand2",
                padx=10, pady=4, bd=0,
                activebackground=GLASS_LIGHT,
                activeforeground=TEXT_HI,
                command=lambda l=label: self._on_quick_reply(l),
            )
            btn.pack(side="left", padx=(0, 6))
