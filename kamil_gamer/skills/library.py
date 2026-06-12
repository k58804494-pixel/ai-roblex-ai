"""Reusable skills.

A *skill* is a named, self-contained policy: given the current :class:`Scene`
(and the active game's key bindings) it proposes an :class:`Action`. Skills are
the building blocks the planner can compose ("need parkour? load the parkour
skill") instead of relearning movement for every new game.

``applicable(scene)`` lets the planner ask which skills are relevant right now;
``step(scene, keys)`` produces the next action for that skill.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from ..adapters.base import KeyBindings
from ..schemas import Action, ActionType, Scene

StepFn = Callable[[Scene, KeyBindings], Action]
ApplicableFn = Callable[[Scene], bool]


@dataclass
class Skill:
    name: str
    description: str
    step: StepFn
    applicable: ApplicableFn = lambda scene: True
    tags: tuple[str, ...] = ()


class SkillLibrary:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def names(self) -> list[str]:
        return sorted(self._skills)

    def applicable(self, scene: Scene) -> list[Skill]:
        return [s for s in self._skills.values() if _safe_applicable(s, scene)]


def _safe_applicable(skill: Skill, scene: Scene) -> bool:
    try:
        return bool(skill.applicable(scene))
    except Exception:
        return False


# --- built-in skills ---------------------------------------------------------
def _parkour_step(scene: Scene, keys: KeyBindings) -> Action:
    return Action(
        type=ActionType.KEY, key=keys.jump, duration_s=0.1, reason="parkour: jump gap"
    )


def _combat_step(scene: Scene, keys: KeyBindings) -> Action:
    enemy = scene.nearest_enemy()
    if enemy is not None and enemy.box is not None:
        return Action(
            type=ActionType.CLICK, target=enemy.box.center, reason="combat: strike"
        )
    return Action(
        type=ActionType.KEY, key=keys.forward, duration_s=0.3, reason="combat: close in"
    )


def _explore_step(scene: Scene, keys: KeyBindings) -> Action:
    return Action(
        type=ActionType.KEY, key=keys.forward, duration_s=0.5, reason="explore: advance"
    )


def _trade_step(scene: Scene, keys: KeyBindings) -> Action:
    return Action(
        type=ActionType.KEY, key=keys.interact, duration_s=0.1, reason="trade: interact"
    )


def builtin_library() -> SkillLibrary:
    lib = SkillLibrary()
    lib.register(
        Skill(
            name="parkour",
            description="Jump across gaps and platforms.",
            step=_parkour_step,
            tags=("movement", "platformer"),
        )
    )
    lib.register(
        Skill(
            name="combat",
            description="Engage the nearest enemy.",
            step=_combat_step,
            applicable=lambda scene: scene.nearest_enemy() is not None,
            tags=("fighting",),
        )
    )
    lib.register(
        Skill(
            name="explore",
            description="Move forward to discover the map.",
            step=_explore_step,
            tags=("movement",),
        )
    )
    lib.register(
        Skill(
            name="trade",
            description="Interact to trade with an NPC.",
            step=_trade_step,
            tags=("social", "economy"),
        )
    )
    return lib
