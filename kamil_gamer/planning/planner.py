"""Rule-based planner: turn a Scene into the next Action.

This is intentionally simple and deterministic so the loop is debuggable and
testable. It encodes a sensible default policy:

1. If health is critically low -> retreat (move back / heal key).
2. If an enemy is visible and close -> engage (look/click toward it).
3. If a quest objective is known -> move toward it / interact.
4. Otherwise -> explore (small forward movement) so we keep making progress.

The architecture leaves room to swap this for an LLM "reasoning" planner later;
the interface is just ``plan(scene) -> Action``.
"""

from __future__ import annotations

import random
from typing import Optional

from ..schemas import Action, ActionType, Scene


class Planner:
    def __init__(self, screen_center: Optional[tuple[int, int]] = None) -> None:
        self.screen_center = screen_center or (640, 360)

    def plan(self, scene: Scene) -> Action:
        low_health = (
            scene.player_health_pct is not None and scene.player_health_pct < 25
        )
        if low_health:
            return Action(
                type=ActionType.KEY,
                key="s",
                duration_s=0.4,
                reason="health critical: retreat",
            )

        enemy = scene.nearest_enemy()
        if enemy is not None and enemy.box is not None:
            return Action(
                type=ActionType.CLICK,
                target=enemy.box.center,
                reason=f"engage {enemy.label or 'enemy'}",
            )
        if enemy is not None:
            # Known enemy but no box: face forward and attack.
            return Action(
                type=ActionType.CLICK,
                target=self.screen_center,
                reason=f"engage {enemy.label or 'enemy'} (no box)",
            )

        objective = self._objective_target(scene)
        if objective is not None:
            return Action(
                type=ActionType.MOVE,
                target=objective,
                reason="move toward objective",
            )

        if scene.quests:
            # We can see a quest but not a target: walk forward to discover it.
            return Action(
                type=ActionType.KEY,
                key="w",
                duration_s=0.6,
                reason=f"pursue quest: {scene.quests[0].text[:40]}",
            )

        return self._explore()

    def _objective_target(self, scene: Scene) -> Optional[tuple[int, int]]:
        for entity in scene.entities:
            if entity.kind.value in ("objective", "npc", "item") and entity.box:
                return entity.box.center
        return None

    def _explore(self) -> Action:
        # Small forward movement with occasional turns keeps us unstuck-ish.
        if random.random() < 0.25:
            return Action(
                type=ActionType.KEY,
                key="d" if random.random() < 0.5 else "a",
                duration_s=0.3,
                reason="explore: turn",
            )
        return Action(
            type=ActionType.KEY, key="w", duration_s=0.5, reason="explore: forward"
        )
