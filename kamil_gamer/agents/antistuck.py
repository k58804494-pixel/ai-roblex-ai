"""Anti-stuck detection and recovery.

Tracks a scalar "progress signal" derived from the scene (quest progress, health
changes, how much the perceived text changes frame-to-frame). If nothing
meaningful changes for ``stuck_seconds``, we declare the agent stuck and emit a
recovery action that differs from recent behaviour (turn around, open map,
jump), cycling through strategies so we don't repeat the same failed move.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..config import AntiStuckConfig
from ..schemas import Action, ActionType, Scene


def _scene_signature(scene: Scene) -> str:
    quest = "|".join(f"{q.text}:{q.progress}" for q in scene.quests)
    return f"{scene.player_health_pct}|{len(scene.entities)}|{quest}|{scene.raw_text[:200]}"


# Recovery strategies, tried in order then cycled.
_RECOVERY_STRATEGIES: list[Action] = [
    Action(type=ActionType.KEY, key="space", duration_s=0.1, reason="recover: jump"),
    Action(type=ActionType.KEY, key="s", duration_s=0.6, reason="recover: back up"),
    Action(type=ActionType.KEY, key="a", duration_s=0.6, reason="recover: turn left"),
    Action(type=ActionType.KEY, key="d", duration_s=0.6, reason="recover: turn right"),
    Action(type=ActionType.KEY, key="m", duration_s=0.1, reason="recover: open map"),
]


@dataclass
class AntiStuck:
    config: AntiStuckConfig
    _last_sig: str = ""
    _last_progress_at: float = field(default_factory=time.time)
    _strategy_idx: int = 0

    def observe(self, scene: Scene, now: float | None = None) -> None:
        now = time.time() if now is None else now
        sig = _scene_signature(scene)
        if sig != self._last_sig:
            self._last_sig = sig
            self._last_progress_at = now

    def is_stuck(self, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        return (now - self._last_progress_at) >= self.config.stuck_seconds

    def recovery_action(self) -> Action:
        action = _RECOVERY_STRATEGIES[self._strategy_idx % len(_RECOVERY_STRATEGIES)]
        self._strategy_idx += 1
        # Reset the timer so we give the new strategy time to take effect.
        self._last_progress_at = time.time()
        return action

    def reset(self) -> None:
        self._last_sig = ""
        self._last_progress_at = time.time()
        self._strategy_idx = 0
