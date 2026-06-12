"""Adapter base class and registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

from ..schemas import Action, ActionType, Scene


@dataclass
class KeyBindings:
    """Logical-action -> physical-key map; overridable per game."""

    forward: str = "w"
    back: str = "s"
    left: str = "a"
    right: str = "d"
    jump: str = "space"
    interact: str = "e"
    open_map: str = "m"
    open_chat: str = "/"


class GameAdapter:
    """Base adapter. Subclass per game/platform.

    The default implementations are sensible no-ops/pass-throughs so a new
    adapter only needs to override what is genuinely game-specific.
    """

    name: str = "generic"
    keys: KeyBindings = KeyBindings()

    def describe(self) -> str:
        return self.name

    def normalize_scene(self, scene: Scene) -> Scene:
        """Hook to post-process raw vision output into game-specific structure."""

        return scene

    def map_action(self, action: Action) -> Action:
        """Translate a logical action into game-specific keys, if needed."""

        return action

    def recovery_hint(self) -> Action:
        """Game-appropriate first recovery move (e.g. jump for platformers)."""

        return Action(
            type=ActionType.KEY, key=self.keys.jump, duration_s=0.1, reason="recover"
        )


_REGISTRY: Dict[str, Callable[[], GameAdapter]] = {}


def register_adapter(name: str) -> Callable[[Callable[[], GameAdapter]], Callable]:
    def deco(factory: Callable[[], GameAdapter]):
        _REGISTRY[name.lower()] = factory
        return factory

    return deco


def get_adapter(name: str | None) -> GameAdapter:
    """Return an adapter instance by name, falling back to the generic adapter."""

    if name:
        factory = _REGISTRY.get(name.lower())
        if factory is not None:
            return factory()
    return GameAdapter()


# Keep a registry of generic too, so listing works predictably.
_REGISTRY.setdefault("generic", GameAdapter)
