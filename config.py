"""
config.py — Central configuration for Deb's Nano PI Chat
All tuneable settings and the colour palette live here.
Edit this file to customise the app without touching any logic.
"""

# ── App identity ───────────────────────────────────────────────
APP_TITLE       = "Deb's Nano PI Chat"
APP_VERSION     = "3.0.0"

# ── AI model ───────────────────────────────────────────────────
MODEL_NAME      = "qwen2:0.5b"           # any Ollama model
OLLAMA_URL      = "http://localhost:11434/api/generate"
MAX_SENTENCES   = 3                       # max sentences in bot reply

# ── Speech recognition ─────────────────────────────────────────
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
LISTEN_SECONDS  = 6

# ── Text-to-speech ─────────────────────────────────────────────
APLAY_DEVICE    = "plughw:0,0"           # run `aplay -l` to find yours

# ── Quick-reply chips shown after every bot answer ─────────────
QUICK_REPLIES = [
    "Tell me more",
    "Explain simply",
    "Give an example",
    "Summarise that",
]

# ── Chain-of-thought system prompt ─────────────────────────────
COT_SYSTEM = (
    f"You are {APP_TITLE}, a smart voice assistant. "
    "Think briefly inside <think>…</think>, then give a SHORT spoken answer. "
    f"Max {MAX_SENTENCES} sentences in your final answer."
)

# ════════════════════════════════════════════════════════════════
#  COLOUR PALETTE  — glassmorphism deep-space theme
# ════════════════════════════════════════════════════════════════

# Background layers
BG_DEEP     = "#050a12"
BG_MID      = "#0a1628"
BG_HIGH     = "#0d2137"

# Glass surfaces
GLASS_DARK  = "#0e1c2f"
GLASS_MID   = "#112440"
GLASS_LIGHT = "#1a3354"

# Borders & glows
BORDER      = "#1e4976"
GLOW_CYAN   = "#00d4ff"
GLOW_TEAL   = "#00ffcc"
GLOW_PINK   = "#ff2d78"
GLOW_AMBER  = "#ffb300"

# Text hierarchy
TEXT_HI     = "#e8f4ff"
TEXT_MID    = "#7eb8d4"
TEXT_LOW    = "#2d5068"
TEXT_THINK  = "#6dd5b8"

# Chat bubble tints
USER_BG     = "#0d2c52"
USER_BORDER = "#1a6498"
BOT_BG      = "#0a2218"
BOT_BORDER  = "#1a5c3a"

# Mic button state colours
MIC_IDLE    = "#00c8f0"
MIC_REC     = "#ff2d78"
MIC_THINK   = "#4a90d9"
MIC_SPEAK   = "#00ffaa"
