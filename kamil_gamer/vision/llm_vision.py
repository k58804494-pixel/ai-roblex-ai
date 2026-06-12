"""Cloud vision-LLM scene understanding.

Sends a downscaled screenshot to a multimodal model and asks for a JSON object
matching the ``Scene`` schema. Entirely optional: only used when an API key is
configured. Any failure returns ``None`` so the caller can fall back to OCR.
"""

from __future__ import annotations

import base64
import io
import json
import time
from typing import Optional

import numpy as np

from ..schemas import Entity, EntityKind, Quest, Scene

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover
    Image = None

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None


_SYSTEM_PROMPT = (
    "You are the vision system of a game-playing AI. Look at the screenshot and "
    "return ONLY a compact JSON object describing what a human player would see. "
    "Schema: {\n"
    '  "player_health_pct": number|null,\n'
    '  "entities": [{"kind": "enemy|npc|player|item|objective|unknown", '
    '"label": string, "confidence": number, "distance_m": number|null}],\n'
    '  "inventory": [string],\n'
    '  "quests": [{"text": string, "progress": string|null}],\n'
    '  "buttons": [string],\n'
    '  "chat_messages": [string],\n'
    '  "damage_numbers": [string],\n'
    '  "notes": string\n'
    "}\n"
    "Do not include any prose outside the JSON."
)


class LLMVision:
    def __init__(self, api_key: Optional[str], model: str, max_dim: int = 1280) -> None:
        self.model = model
        self.max_dim = max_dim
        self._client = None
        if api_key and OpenAI is not None and Image is not None:
            try:
                self._client = OpenAI(api_key=api_key)
            except Exception:
                self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

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
        if self._client is None:
            return None
        b64 = self._encode(image)
        if b64 is None:
            return None
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this game frame."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64}"
                                },
                            },
                        ],
                    },
                ],
            )
            content = resp.choices[0].message.content or "{}"
            return self._parse(content)
        except Exception:
            return None

    @staticmethod
    def _parse(content: str) -> Optional[Scene]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return None
        entities = []
        for raw in data.get("entities", []) or []:
            try:
                kind = EntityKind(raw.get("kind", "unknown"))
            except ValueError:
                kind = EntityKind.UNKNOWN
            entities.append(
                Entity(
                    kind=kind,
                    label=str(raw.get("label", "")),
                    confidence=float(raw.get("confidence", 0.0) or 0.0),
                    distance_m=raw.get("distance_m"),
                )
            )
        quests = [
            Quest(text=str(q.get("text", "")), progress=q.get("progress"))
            for q in data.get("quests", []) or []
        ]
        return Scene(
            timestamp=time.time(),
            player_health_pct=data.get("player_health_pct"),
            entities=entities,
            inventory=[str(i) for i in data.get("inventory", []) or []],
            quests=quests,
            buttons=[str(b) for b in data.get("buttons", []) or []],
            chat_messages=[str(c) for c in data.get("chat_messages", []) or []],
            damage_numbers=[str(d) for d in data.get("damage_numbers", []) or []],
            notes=str(data.get("notes", "")),
        )
