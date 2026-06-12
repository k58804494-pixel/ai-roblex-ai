"""Personality system.

A small set of traits that bias *how* the agent behaves and talks — not what it
is allowed to do (that's :mod:`kamil_gamer.safety`). Traits nudge things like
how aggressively it engages and how chatty it is, giving different playstyles.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Personality:
    competitiveness: float = 0.5  # 0 cautious .. 1 aggressive
    friendliness: float = 0.7  # how helpful/social
    humor: float = 0.3
    curiosity: float = 0.6  # how much to explore unknown areas
    chattiness: float = 0.4  # how often to volunteer chat messages

    @classmethod
    def preset(cls, name: str) -> "Personality":
        presets = {
            "competitive": cls(competitiveness=0.9, friendliness=0.4, curiosity=0.5),
            "helpful": cls(competitiveness=0.3, friendliness=0.95, chattiness=0.6),
            "funny": cls(humor=0.9, chattiness=0.7, friendliness=0.8),
            "curious": cls(curiosity=0.95, competitiveness=0.4),
            "serious": cls(humor=0.05, chattiness=0.2, competitiveness=0.7),
        }
        return presets.get(name.lower(), cls())

    def should_chat(self, roll: float) -> bool:
        return roll < self.chattiness

    def engage_distance_m(self) -> float:
        """More competitive personalities engage enemies from further away."""

        return 6.0 + self.competitiveness * 14.0
