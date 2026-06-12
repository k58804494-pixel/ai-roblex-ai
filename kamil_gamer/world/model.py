"""An internal map the AI builds and remembers.

Instead of only reacting to the current screen, the agent accumulates a graph of
known **places** (town, shop, quest NPC, dungeon, danger zone, secret area) and
the **connections** between them. This is what lets it plan routes ("to reach
the dungeon, go Town -> Gate -> Dungeon") and avoid known-dangerous areas.

The whole model serialises to/from a plain dict so it can be persisted in
:class:`~kamil_gamer.memory.GameMemory` between sessions.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class PlaceKind(str, Enum):
    GENERIC = "generic"
    TOWN = "town"
    SHOP = "shop"
    NPC = "npc"
    QUEST = "quest"
    DUNGEON = "dungeon"
    RESOURCE = "resource"
    DANGER = "danger"
    SECRET = "secret"
    CHECKPOINT = "checkpoint"


@dataclass
class Place:
    name: str
    kind: PlaceKind = PlaceKind.GENERIC
    position: Optional[tuple[float, float]] = None  # 2D map coords if known
    notes: str = ""
    danger: float = 0.0  # 0..1 risk estimate
    neighbors: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "position": list(self.position) if self.position else None,
            "notes": self.notes,
            "danger": self.danger,
            "neighbors": sorted(self.neighbors),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Place":
        pos = data.get("position")
        return cls(
            name=data["name"],
            kind=PlaceKind(data.get("kind", "generic")),
            position=tuple(pos) if pos else None,
            notes=data.get("notes", ""),
            danger=float(data.get("danger", 0.0)),
            neighbors=set(data.get("neighbors", [])),
        )


class WorldModel:
    def __init__(self) -> None:
        self.places: dict[str, Place] = {}

    def add_place(
        self,
        name: str,
        kind: PlaceKind = PlaceKind.GENERIC,
        position: Optional[tuple[float, float]] = None,
        notes: str = "",
        danger: float = 0.0,
    ) -> Place:
        place = self.places.get(name)
        if place is None:
            place = Place(name=name, kind=kind)
            self.places[name] = place
        # Update fields when new info arrives.
        place.kind = kind if kind != PlaceKind.GENERIC else place.kind
        if position is not None:
            place.position = position
        if notes:
            place.notes = notes
        if danger:
            place.danger = max(place.danger, danger)
        return place

    def connect(self, a: str, b: str) -> None:
        """Record a bidirectional path between two places (auto-creating them)."""

        self.add_place(a)
        self.add_place(b)
        self.places[a].neighbors.add(b)
        self.places[b].neighbors.add(a)

    def mark_danger(self, name: str, danger: float = 1.0) -> None:
        self.add_place(name, kind=PlaceKind.DANGER, danger=danger)

    def route(self, start: str, goal: str, avoid_danger: float = 1.0) -> list[str]:
        """Shortest path (BFS) from start to goal, skipping over-dangerous places.

        Returns an empty list if no route is known. The start node is always
        allowed even if dangerous; intermediate/goal nodes at or above
        ``avoid_danger`` are skipped.
        """

        if start not in self.places or goal not in self.places:
            return []
        if start == goal:
            return [start]
        visited = {start}
        queue: deque[list[str]] = deque([[start]])
        while queue:
            path = queue.popleft()
            for nxt in sorted(self.places[path[-1]].neighbors):
                if nxt in visited:
                    continue
                if nxt != goal and self.places[nxt].danger >= avoid_danger:
                    continue
                new_path = path + [nxt]
                if nxt == goal:
                    return new_path
                visited.add(nxt)
                queue.append(new_path)
        return []

    def to_dict(self) -> dict[str, Any]:
        return {name: place.to_dict() for name, place in self.places.items()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorldModel":
        model = cls()
        for name, raw in (data or {}).items():
            model.places[name] = Place.from_dict(raw)
        return model
