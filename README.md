# ✦ Deb's Raspberry PI5 - PI Chat

> **An AI voice assistant built for Raspberry Pi — stream-powered, privacy-first, fully offline.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?style=flat-square)](https://ollama.ai)
[![Vosk](https://img.shields.io/badge/Vosk-Offline%20STT-4CAF50?style=flat-square)](https://alphacephei.com/vosk/)
[![Tkinter](https://img.shields.io/badge/UI-Tkinter%20%2F%20Glassmorphism-blueviolet?style=flat-square)]()
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%204%2F5-C51A4A?style=flat-square&logo=raspberrypi&logoColor=white)](https://raspberrypi.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

---

## 📖 What Is It?

**Deb's PI Chat** is a fully local, voice-driven AI chat assistant designed to run on a **Raspberry Pi**. It combines:

- 🎙️ **Offline speech recognition** via [Vosk](https://alphacephei.com/vosk/) — no cloud, no API key
- 🧠 **On-device LLM inference** via [Ollama](https://ollama.ai) with streaming output
- 🔊 **Text-to-speech** via `pico2wave` for natural spoken responses
- 🎨 **Glassmorphism UI** built in pure Tkinter — animated aurora background, sine-wave voice visualiser, chat bubbles, quick-reply chips, and a collapsible chain-of-thought panel

Everything runs **100% offline** on your local machine. No subscriptions, no data leaves your device.

---

## ✨ Features at a Glance

| Feature | Details |
|---|---|
| 🌊 Aurora background | Slow animated gradient mesh — pure Tkinter canvas |
| 📡 Sine-wave visualiser | Real mic RMS drives live waveform amplitude |
| 💬 Streaming chat bubbles | Words appear token-by-token as the model generates |
| 🧠 Chain-of-thought panel | `<think>` reasoning is collapsible — shown or hidden on demand |
| ⚡ Quick-reply chips | Suggested follow-ups after every bot answer |
| 🎙️ Animated mic button | 4 states: idle / listening / thinking / speaking — with pulse rings |
| ⏹ Stop Speaking button | Kill TTS mid-sentence at any time |
| 🔽 Scroll-to-bottom button | Auto-shows when chat overflows |
| 📊 Status bar | Live state indicator with model info |
| ⌨️ Typing indicator | Animated bouncing dots while AI processes |

---

## 🖥️ Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| **Board** | Raspberry Pi 4 (4 GB RAM) | Raspberry Pi 5 (8 GB RAM) |
| **Storage** | 16 GB microSD (Class 10) | 32 GB+ microSD or USB SSD |
| **Display** | Any HDMI display | 7" touchscreen or larger |
| **Microphone** | USB microphone | USB conference mic for better pickup |
| **Speaker / Audio** | 3.5mm speaker or USB audio | USB speaker with clear playback |
| **OS** | Raspberry Pi OS (64-bit, Bookworm) | Raspberry Pi OS (64-bit, Bookworm) |

> **⚠️ Note:** Running a local LLM is CPU-intensive. The Pi 4 will work but expect ~5–15 s first-token latency with `qwen2:0.5b`. The Pi 5 is noticeably faster.

---

## 📦 Software Prerequisites

### System Packages

Install via `apt`:

```bash
sudo apt update && sudo apt install -y \
    python3-pip \
    python3-tk \
    portaudio19-dev \
    libsndfile1 \
    libttspico-utils \
    alsa-utils \
    curl \
    git
```

### Python Libraries

```bash
pip3 install \
    sounddevice \
    numpy \
    requests \
    vosk
```

| Library | Purpose |
|---|---|
| `sounddevice` | Capture microphone audio |
| `numpy` | RMS calculation and audio buffer handling |
| `requests` | HTTP streaming from Ollama API |
| `vosk` | Offline speech-to-text recognition |
| `tkinter` | GUI (usually bundled with Python on Pi OS) |

### Ollama (Local LLM Runtime)

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

After installing, pull the model:

```bash
ollama pull qwen2:0.5b
```

> You can substitute any Ollama-compatible model. Smaller models (0.5B–1.5B parameters) are recommended for Pi hardware.

### Vosk Speech Model

Download the small English model (~40 MB):

```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

Place the extracted folder (`vosk-model-small-en-us-0.15/`) in the **same directory** as `main.py`.

---

## 🗂️ Project Structure

```
raspberrypi_nanochat/
├── main.py                          # Entry point — run this
├── config.py                        # All settings & colour palette
│
├── audio/
│   ├── __init__.py
│   ├── listener.py                  # Vosk mic capture & STT
│   └── speaker.py                   # pico2wave TTS playback
│
├── ai/
│   ├── __init__.py
│   └── ollama.py                    # Streaming Ollama LLM client
│
├── ui/
│   ├── __init__.py
│   ├── app.py                       # Root window & voice pipeline
│   ├── aurora.py                    # Animated aurora background
│   ├── chat.py                      # Chat canvas, bubbles & chips
│   ├── controls.py                  # Mic button & scroll button
│   ├── indicators.py                # Status bar, wave vis, typing dots
│   └── widgets.py                   # Avatar & glass frame helpers
│
├── vosk-model-small-en-us-0.15/    # Vosk speech model (download separately)
│   └── ...
└── README.md
```

---

## ⚙️ Configuration

All settings live in **`config.py`** — edit that one file to customise the app:

```python
APP_TITLE       = "Deb's Raspberry PI Chat"              # Window title (Change it accordingly)
MODEL_NAME      = "qwen2:0.5b"                      # Ollama model to use
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"     # Path to Vosk model folder
LISTEN_SECONDS  = 6                                  # How long to record speech
APLAY_DEVICE    = "plughw:0,0"                      # Your audio output device
OLLAMA_URL      = "http://localhost:11434/api/generate"
```

### Finding Your Audio Device

```bash
aplay -l
```

You'll see output like:
```
card 0: Headphones [bcm2835 Headphones], device 0: ...
card 1: Device [USB Audio Device], device 0: ...
```

Set `APLAY_DEVICE` accordingly — e.g., `"plughw:1,0"` for a USB audio device.

### Finding Your Microphone

The app auto-detects a USB mic. If detection fails, check available devices:

```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

---

## 🚀 Running the App

**Step 1 — Start Ollama:**

```bash
ollama serve &
```

**Step 2 — Launch Raspberry PI Chat:**

```bash
cd nanochat
python3 main.py
```

The app opens in **fullscreen**. Press `Esc` or tap the `✕` button to exit.

---

## 🎮 How to Use

```
┌─────────────────────────────────────────┐
│          TAP THE MIC BUTTON             │
│      Speak within 6 seconds             │
│                                         │
│  Your words appear as a chat bubble     │
│  The AI streams a response in real-time │
│  The response is read aloud             │
│                                         │
│  Tap a QUICK REPLY chip to follow up    │
│  Tap ▶ reasoning to see the AI's        │
│    internal thought process             │
│  Tap ⏹ STOP to cut off speech           │
└─────────────────────────────────────────┘
```

### Mic Button States

| Colour | State | Meaning |
|---|---|---|
| 🔵 Cyan | **Idle** | Ready — tap to start |
| 🔴 Pink | **Listening** | Recording your voice |
| 🔷 Blue | **Thinking** | Waiting for AI response |
| 🟢 Teal | **Speaking** | Playing TTS audio |

---

## 🔧 Troubleshooting

**"No microphone found"**
- Check your USB mic is plugged in before launching
- Run `arecord -l` to confirm the device is visible to ALSA

**Model takes very long to respond**
- Switch to a smaller model: `ollama pull qwen2:0.5b`
- Verify Ollama is running: `curl http://localhost:11434`

**No audio output**
- Test with: `speaker-test -t wav -c 2`
- Adjust `APLAY_DEVICE` in `config.py` to match your hardware

**Vosk model not found**
- Ensure the folder name exactly matches `VOSK_MODEL_PATH` in `config.py`
- Provide a full absolute path if needed: `/home/pi/nanochat/vosk-model-small-en-us-0.15`

**Tkinter not available**
- Install with: `sudo apt install python3-tk`

**`pico2wave` not found**
- Install with: `sudo apt install libttspico-utils`

---

## 🛣️ Possible Enhancements

- 🌐 Swap `audio/listener.py` for Whisper (higher accuracy, higher CPU cost)
- 💾 Add conversation history persistence to `ai/ollama.py`
- 🌍 Multi-language support via different Vosk models
- 📡 Optional cloud LLM fallback when local model is slow
- 🖱️ Touch-friendly UI scaling for 7" displays

---

## 📄 License

```
MIT License

Copyright (c) 2025 debaditc

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Dependency Licences

| Dependency | Licence |
|---|---|
| [Vosk](https://alphacephei.com/vosk/) | Apache 2.0 |
| [Ollama](https://ollama.ai) | MIT |
| [pico2wave](https://packages.debian.org/libttspico-utils) | Apache 2.0 |
| [sounddevice](https://python-sounddevice.readthedocs.io/) | MIT |
| [numpy](https://numpy.org/) | BSD 3-Clause |
| [requests](https://requests.readthedocs.io/) | Apache 2.0 |

---

*Built with ❤️ for Raspberry Pi tinkerers who want powerful AI without the cloud.*
