"""Shared parsing of a model's JSON description of a frame into a ``Scene``.

Both the cloud LLM backend and the local Ollama backend ask a model for the same
JSON schema, so they share this tolerant parser. It accepts either a raw JSON
string or an already-decoded dict, and never raises on malformed input.
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional, Union

from ..schemas import Entity, EntityKind, Quest, Scene

# The JSON schema we ask vision models to produce.
SCENE_JSON_INSTRUCTIONS = (
    "Return ONLY a compact JSON object describing what a human player would see. "
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


def parse_scene_json(content: Union[str, dict[str, Any], None]) -> Optional[Scene]:
    if content is None:
        return None
    if isinstance(content, str):
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return None
    else:
        data = content
    if not isinstance(data, dict):
        return None

    entities = []
    for raw in data.get("entities", []) or []:
        if not isinstance(raw, dict):
            continue
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
        if isinstance(q, dict)
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
