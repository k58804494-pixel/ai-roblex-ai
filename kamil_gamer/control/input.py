"""Mouse/keyboard execution of Actions.

Uses ``pynput`` when available. In ``dry_run`` mode (the default) nothing is
actually sent to the OS; actions are recorded so the loop can be exercised
safely and tested headlessly.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from ..config import ControlConfig
from ..schemas import Action, ActionType
from . import humanize

try:
    from pynput.keyboard import Controller as _KbController  # type: ignore
    from pynput.keyboard import Key  # type: ignore
    from pynput.mouse import Button  # type: ignore
    from pynput.mouse import Controller as _MouseController  # type: ignore
except Exception:  # pragma: no cover - depends on host
    _KbController = None
    _MouseController = None
    Key = None
    Button = None


def humanize_duration(config: ControlConfig) -> float:
    """A randomised mouse-move duration within the configured bounds."""

    return random.uniform(config.move_min_duration_s, config.move_max_duration_s)


@dataclass
class ExecutedAction:
    action: Action
    at: float = field(default_factory=time.time)


class Controller:
    def __init__(self, config: ControlConfig) -> None:
        self.config = config
        self.log: list[ExecutedAction] = []
        self._kb = None
        self._mouse = None
        if not config.dry_run and _KbController is not None:
            try:
                self._kb = _KbController()
                self._mouse = _MouseController()
            except Exception:
                self._kb = None
                self._mouse = None

    @property
    def live(self) -> bool:
        return self._kb is not None and self._mouse is not None

    def execute(self, action: Action) -> ExecutedAction:
        time.sleep(
            humanize.reaction_delay(
                self.config.min_reaction_ms, self.config.max_reaction_ms
            )
        )
        handler = {
            ActionType.MOVE: self._do_move,
            ActionType.CLICK: self._do_click,
            ActionType.KEY: self._do_key,
            ActionType.LOOK: self._do_move,
            ActionType.SAY: self._do_say,
            ActionType.WAIT: self._do_wait,
        }.get(action.type)
        if handler is not None:
            handler(action)
        record = ExecutedAction(action=action)
        self.log.append(record)
        return record

    # --- individual handlers -------------------------------------------------
    def _move_mouse_to(self, target: tuple[int, int]) -> None:
        target = humanize.aim_jitter(target, self.config.aim_error_px)
        if not self.live:
            return
        start = self._mouse.position
        path = humanize.mouse_path((int(start[0]), int(start[1])), target)
        total = humanize_duration(self.config)
        per_step = total / max(1, len(path))
        for point in path:
            self._mouse.position = point
            time.sleep(per_step)

    def _do_move(self, action: Action) -> None:
        if action.target is not None:
            self._move_mouse_to(action.target)

    def _do_click(self, action: Action) -> None:
        if action.target is not None:
            self._move_mouse_to(action.target)
        if self.live and Button is not None:
            self._mouse.click(Button.left, 1)

    def _do_key(self, action: Action) -> None:
        if not action.key:
            return
        if not self.live:
            return
        key = self._resolve_key(action.key)
        self._kb.press(key)
        time.sleep(max(0.03, action.duration_s))
        self._kb.release(key)

    def _do_say(self, action: Action) -> None:
        if not action.text or not self.live:
            return
        self._kb.type(action.text)

    def _do_wait(self, action: Action) -> None:
        time.sleep(max(0.0, action.duration_s))

    def _resolve_key(self, name: str):
        if Key is not None and hasattr(Key, name):
            return getattr(Key, name)
        return name
