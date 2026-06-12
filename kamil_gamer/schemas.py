"""Structured data models for scene understanding and actions.

These models are the contract between layers: the vision pipeline produces a
``Scene``, the planner consumes a ``Scene`` and emits an ``Action``, and the
controller executes an ``Action``.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EntityKind(str, Enum):
    ENEMY = "enemy"
    NPC = "npc"
    PLAYER = "player"
    ITEM = "item"
    OBJECTIVE = "objective"
    UNKNOWN = "unknown"


class BoundingBox(BaseModel):
    """Pixel-space bounding box (top-left origin)."""

    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


class Entity(BaseModel):
    kind: EntityKind = EntityKind.UNKNOWN
    label: str = ""
    confidence: float = 0.0
    box: Optional[BoundingBox] = None
    distance_m: Optional[float] = Field(
        default=None, description="Estimated distance in metres, if known."
    )


class Quest(BaseModel):
    text: str
    progress: Optional[str] = None  # e.g. "3/5 apples"


class Scene(BaseModel):
    """Structured understanding of a single frame."""

    timestamp: float
    player_health_pct: Optional[float] = None
    entities: list[Entity] = Field(default_factory=list)
    inventory: list[str] = Field(default_factory=list)
    quests: list[Quest] = Field(default_factory=list)
    buttons: list[str] = Field(default_factory=list)
    chat_messages: list[str] = Field(default_factory=list)
    damage_numbers: list[str] = Field(default_factory=list)
    raw_text: str = ""
    notes: str = ""

    def enemies(self) -> list[Entity]:
        return [e for e in self.entities if e.kind == EntityKind.ENEMY]

    def nearest_enemy(self) -> Optional[Entity]:
        enemies = [e for e in self.enemies() if e.distance_m is not None]
        if not enemies:
            return None
        return min(enemies, key=lambda e: e.distance_m or float("inf"))


class ActionType(str, Enum):
    MOVE = "move"  # move toward a screen point or direction
    CLICK = "click"
    KEY = "key"  # press a key / hold for a duration
    LOOK = "look"  # turn the camera
    WAIT = "wait"
    SAY = "say"  # send a chat message
    RECOVER = "recover"  # anti-stuck recovery
    NONE = "none"


class Action(BaseModel):
    type: ActionType = ActionType.NONE
    target: Optional[tuple[int, int]] = None  # screen coords for move/click/look
    key: Optional[str] = None
    text: Optional[str] = None
    duration_s: float = 0.0
    reason: str = ""

    def describe(self) -> str:
        bits = [self.type.value]
        if self.target is not None:
            bits.append(f"@{self.target}")
        if self.key:
            bits.append(f"key={self.key}")
        if self.text:
            bits.append(f"text={self.text!r}")
        if self.reason:
            bits.append(f"({self.reason})")
        return " ".join(bits)
