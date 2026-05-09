"""
audio/speaker.py — Text-to-speech playback via pico2wave + aplay.

Public API
----------
speak(text)      Synthesise and play text (blocking).
stop_speaking()  Kill the current aplay process immediately.
"""

import os
import subprocess
import tempfile

from config import APLAY_DEVICE

# Module-level handle to the running aplay process
_speak_proc: subprocess.Popen | None = None


def speak(text: str) -> None:
    """
    Convert *text* to speech with pico2wave and play it through aplay.
    Blocks until playback is complete or stop_speaking() is called.
    """
    global _speak_proc

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name

    try:
        subprocess.run(
            ["pico2wave", "-w", tmp_path, text],
            check=True,
            capture_output=True,
        )
        _speak_proc = subprocess.Popen(
            ["aplay", "-D", APLAY_DEVICE, tmp_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _speak_proc.wait()
    except FileNotFoundError as e:
        print(f"[speaker] Missing binary: {e}. Is pico2wave/aplay installed?")
    except subprocess.CalledProcessError as e:
        print(f"[speaker] pico2wave error: {e}")
    except Exception as e:
        print(f"[speaker] Unexpected error: {e}")
    finally:
        _speak_proc = None
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def stop_speaking() -> None:
    """Terminate the current aplay process if one is running."""
    global _speak_proc
    if _speak_proc is not None and _speak_proc.poll() is None:
        _speak_proc.terminate()
        _speak_proc = None
