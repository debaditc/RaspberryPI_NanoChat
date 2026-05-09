"""
ai/ollama.py — Streaming Ollama LLM client with chain-of-thought parsing.

Public API
----------
query_ollama_stream(prompt, on_token, on_done)
    Stream a response from the local Ollama server.
    - on_token(str)            called for each visible token chunk
    - on_done(think, answer)   called once when the stream is complete
"""

import json
import re
from typing import Callable

import requests

from config import COT_SYSTEM, MODEL_NAME, OLLAMA_URL

# Type aliases for readability
TokenCallback = Callable[[str], None]
DoneCallback  = Callable[[str, str], None]


def _parse_cot(raw: str) -> tuple[str, str]:
    """
    Split raw LLM output into (think_text, answer_text).
    If no <think> block is found, think_text is empty.
    """
    match = re.search(r"<think>(.*?)</think>", raw, re.DOTALL)
    if match:
        think  = match.group(1).strip()
        answer = raw[match.end():].strip()
    else:
        think  = ""
        answer = raw.strip()
    return think, answer


def query_ollama_stream(
    prompt: str,
    on_token: TokenCallback,
    on_done: DoneCallback,
) -> None:
    """
    POST a prompt to Ollama with streaming enabled.

    Tokens are buffered so that <think>…</think> content is suppressed
    from on_token; only the visible answer is streamed to the caller.
    on_done is always called exactly once with the parsed think / answer.
    """
    full_prompt = f"{COT_SYSTEM}\n\nUser: {prompt}\nAssistant:"
    raw_buffer  = ""

    try:
        with requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": full_prompt, "stream": True},
            stream=True,
            timeout=120,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    chunk   = payload.get("response", "")
                except (json.JSONDecodeError, KeyError):
                    continue

                raw_buffer += chunk
                _dispatch_visible_token(raw_buffer, chunk, on_token)

                if payload.get("done"):
                    break

    except requests.RequestException as e:
        error_msg = f"[Ollama error] {e}"
        raw_buffer += error_msg
        on_token(error_msg)

    think, answer = _parse_cot(raw_buffer)
    on_done(think, answer)


def _dispatch_visible_token(buffer: str, chunk: str, on_token: TokenCallback) -> None:
    """
    Decide whether to forward *chunk* to on_token based on whether we are
    currently inside a <think>…</think> block.
    """
    think_closed = re.search(r"<think>.*?</think>", buffer, re.DOTALL)
    if think_closed:
        # Think block is complete — stream everything after it
        on_token(chunk)
    elif "<think>" in buffer:
        # Still inside the think block — suppress
        pass
    else:
        # No think block at all — stream normally
        on_token(chunk)
