"""The agent loop: perceive -> plan -> act -> remember, with anti-stuck.

This ties every layer together into one cycle. It is deliberately synchronous
and easy to follow; the "multi-agent brain" can later run these stages as
separate cooperating agents.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from ..config import Config
from ..control import Controller
from ..memory import GameMemory
from ..planning import Planner
from ..schemas import Action, Scene
from ..vision import VisionPipeline
from .antistuck import AntiStuck

logger = logging.getLogger("kamil_gamer")


@dataclass
class LoopStats:
    cycles: int = 0
    recoveries: int = 0
    actions: list[str] = field(default_factory=list)


class Orchestrator:
    def __init__(
        self,
        config: Config,
        vision: Optional[VisionPipeline] = None,
        planner: Optional[Planner] = None,
        controller: Optional[Controller] = None,
        memory: Optional[GameMemory] = None,
        anti_stuck: Optional[AntiStuck] = None,
    ) -> None:
        self.config = config
        self.vision = vision or VisionPipeline(config)
        center = self._screen_center()
        self.planner = planner or Planner(screen_center=center)
        self.controller = controller or Controller(config.control)
        self.memory = memory or GameMemory(config.memory.root, config.game_name)
        self.anti_stuck = anti_stuck or AntiStuck(config.anti_stuck)
        self.stats = LoopStats()
        self._running = False

    def _screen_center(self) -> tuple[int, int]:
        try:
            frame = self.vision.capture.grab()
            return (frame.width // 2, frame.height // 2)
        except Exception:
            return (640, 360)

    def step(self, scene: Optional[Scene] = None) -> Action:
        """Run a single perceive->plan->act cycle and return the chosen action."""

        if scene is None:
            scene = self.vision.perceive()
        self.anti_stuck.observe(scene)

        if self.anti_stuck.is_stuck():
            action = self.anti_stuck.recovery_action()
            self.stats.recoveries += 1
            self.memory.log_event("recovery", {"action": action.describe()})
            logger.info("STUCK -> %s", action.describe())
        else:
            action = self.planner.plan(scene)

        self._persist_progress(scene)
        self.controller.execute(action)
        self.stats.cycles += 1
        self.stats.actions.append(action.describe())
        self.memory.log_event(
            "action", {"action": action.describe(), "notes": scene.notes}
        )
        logger.info("%s", action.describe())
        return action

    def _persist_progress(self, scene: Scene) -> None:
        for quest in scene.quests:
            if quest.progress:
                self.memory.set_goal(
                    quest.text[:80], status="active", progress=quest.progress
                )
        if scene.player_health_pct is not None:
            self.memory.remember("last_health_pct", scene.player_health_pct)

    def run(self, max_cycles: Optional[int] = None) -> LoopStats:
        """Run the loop until stopped or ``max_cycles`` is reached."""

        self._running = True
        period = 1.0 / max(0.1, self.config.loop_hz)
        self.memory.log_event("session_start", {"game": self.config.game_name})
        try:
            while self._running:
                start = time.time()
                self.step()
                if max_cycles is not None and self.stats.cycles >= max_cycles:
                    break
                elapsed = time.time() - start
                time.sleep(max(0.0, period - elapsed))
        finally:
            self.memory.log_event("session_end", {"cycles": self.stats.cycles})
        return self.stats

    def stop(self) -> None:
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def close(self) -> None:
        self.vision.close()
        self.memory.close()
