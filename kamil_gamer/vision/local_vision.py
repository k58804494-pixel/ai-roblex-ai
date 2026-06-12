"""Local LLM backend via Ollama — no API key, runs on your machine.

Talks to a local `ollama serve` HTTP endpoint (default `http://localhost:11434`)
using only the standard library, so it adds no dependency. A vision model (e.g.
``llava``, ``moondream``) does scene understanding; a text model (e.g.
``llama3.2``, ``qwen2.5``) handles reasoning/chat.

Setup on the machine that runs the game:

    # https://ollama.com/download
    ollama pull llava       # vision
    ollama pull llama3.2    # text

Everything degrades gracefully: if Ollama is not running or a model is missing,
``available`` is False and ``understand``/``chat`` return ``None`` so the
pipeline falls back to YOLO+OCR.
"""

from __future__ import annotations

import base64
import io
import json
import urllib.error
import urllib.request
from typing import Optional

import numpy as np

from ..schemas import Scene
from .scene_json import SCENE_JSON_INSTRUCTIONS, parse_scene_json

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover
    Image = None

_VISION_PROMPT = (
    "You are the vision system of a game-playing AI. Look at the screenshot. "
    + SCENE_JSON_INSTRUCTIONS
)


class LocalLLM:
    def __init__(
        self,
        host: str = "http://localhost:11434",
        vision_model: str = "llava",
        text_model: str = "llama3.2",
        max_dim: int = 1280,
        timeout_s: float = 60.0,
    ) -> None:
        self.host = host.rstrip("/")
        self.vision_model = vision_model
        self.text_model = text_model
        self.max_dim = max_dim
        self.timeout_s = timeout_s

    # --- availability --------------------------------------------------------
    @property
    def available(self) -> bool:
        """True if an Ollama server responds at ``host``."""

        try:
            with urllib.request.urlopen(
                f"{self.host}/api/tags", timeout=2.0
            ) as resp:
                return resp.status == 200
        except Exception:
            return False

    # --- vision --------------------------------------------------------------
    def _encode(self, image: np.ndarray) -> Optional[str]:
        if Image is None:
            return None
        pil = Image.fromarray(image)
        w, h = pil.size
        scale = min(1.0, self.max_dim / max(w, h))
        if scale < 1.0:
            pil = pil.resize((int(w * scale), int(h * scale)))
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")

    def understand(self, image: np.ndarray) -> Optional[Scene]:
        b64 = self._encode(image)
        if b64 is None:
            return None
        payload = {
            "model": self.vision_model,
            "format": "json",
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": _VISION_PROMPT,
                    "images": [b64],
                }
            ],
        }
        content = self._post("/api/chat", payload)
        if content is None:
            return None
        return parse_scene_json(content)

    # --- text reasoning / chat ----------------------------------------------
    def chat(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.text_model, "stream": False, "messages": messages}
        return self._post("/api/chat", payload)

    # --- transport -----------------------------------------------------------
    def _post(self, path: str, payload: dict) -> Optional[str]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None
        return self._extract(body)

    @staticmethod
    def _extract(body: object) -> Optional[str]:
        """Pull the text content out of an Ollama chat/generate response."""

        if not isinstance(body, dict):
            return None
        # /api/chat -> {"message": {"content": ...}}; /api/generate -> {"response": ...}
        message = body.get("message")
        if isinstance(message, dict) and "content" in message:
            return message["content"]
        if "response" in body:
            return body["response"]
        return None
