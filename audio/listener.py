"""
audio/listener.py — Microphone capture & offline speech-to-text via Vosk.

Public API
----------
load_vosk_model() -> Model          Load and return the Vosk model (call once at startup).
listen_once(model, on_rms) -> str   Record for LISTEN_SECONDS, return transcribed text.
"""

import json
import numpy as np
import sounddevice as sd
from vosk import Model, KaldiRecognizer

from config import VOSK_MODEL_PATH, LISTEN_SECONDS


def load_vosk_model() -> Model:
    """Load the Vosk speech model from disk. Blocks until ready."""
    print(f"[listener] Loading Vosk model from '{VOSK_MODEL_PATH}' …")
    model = Model(VOSK_MODEL_PATH)
    print("[listener] Vosk ready.")
    return model


def _get_usb_mic_index() -> int | None:
    """Return the index of the first USB microphone, or any input device."""
    devices = sd.query_devices()
    # prefer USB
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0 and "USB" in dev["name"]:
            return i
    # fallback: first input device
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            return i
    return None


def listen_once(model: Model, on_rms=None) -> str:
    """
    Record audio for LISTEN_SECONDS seconds and return the recognised text.

    Parameters
    ----------
    model   : Vosk Model instance (from load_vosk_model)
    on_rms  : optional callable(float) — called each chunk with normalised RMS
              in [0, 1]; used to drive the waveform visualiser.

    Returns
    -------
    Transcribed string, or an error message if no mic is found.
    """
    idx = _get_usb_mic_index()
    if idx is None:
        return "No microphone found."

    info       = sd.query_devices(idx, "input")
    samplerate = int(info["default_samplerate"])
    recogniser = KaldiRecognizer(model, samplerate)
    chunk_size = samplerate // 20                     # 50 ms chunks
    total_frames = int(samplerate * LISTEN_SECONDS)
    collected  = []

    with sd.InputStream(samplerate=samplerate, device=idx,
                        channels=1, dtype="int16") as stream:
        frames_read = 0
        while frames_read < total_frames:
            n = min(chunk_size, total_frames - frames_read)
            data, _ = stream.read(n)
            collected.append(data)
            frames_read += n

            if on_rms is not None:
                rms = float(np.sqrt(np.mean(data.astype(np.float32) ** 2)))
                on_rms(min(1.0, rms / 3500.0))

    raw = np.concatenate(collected, axis=0)
    if recogniser.AcceptWaveform(raw.tobytes()):
        return json.loads(recogniser.Result())["text"]
    return json.loads(recogniser.FinalResult())["text"]
