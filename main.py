"""
main.py — Entry point for Deb's Nano PI Chat.

Usage
-----
    python main.py

Press Escape or tap ✕ to quit.
"""

import tkinter as tk

from audio.listener import load_vosk_model
from ui.app import DebPiChatApp


def main() -> None:
    # Load the speech model before the window opens so startup is clean
    vosk_model = load_vosk_model()

    root = tk.Tk()
    _app = DebPiChatApp(root, vosk_model)
    root.mainloop()


if __name__ == "__main__":
    main()
