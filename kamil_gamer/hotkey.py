"""Global hotkey to toggle the agent on/off.

Press the configured key (default ``r``) to start the loop in a background
thread; press it again to stop. Uses ``pynput`` for a global listener; if that
is unavailable (e.g. headless), :class:`HotkeyRunner` still exposes ``start`` and
``stop`` so the agent can be driven programmatically.
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

from .agents import Orchestrator
from .config import Config

try:
    from pynput import keyboard  # type: ignore
except Exception:  # pragma: no cover - depends on host
    keyboard = None

logger = logging.getLogger("kamil_gamer")


class HotkeyRunner:
    def __init__(self, config: Config, orchestrator: Optional[Orchestrator] = None):
        self.config = config
        self.orchestrator = orchestrator or Orchestrator(config)
        self._thread: Optional[threading.Thread] = None
        self._listener = None

    def toggle(self) -> None:
        if self.orchestrator.running:
            self.stop()
        else:
            self.start()

    def start(self) -> None:
        if self.orchestrator.running:
            return
        logger.info("Agent START (game=%s)", self.config.game_name)
        self._thread = threading.Thread(
            target=self.orchestrator.run, name="kamil-agent", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        if not self.orchestrator.running:
            return
        logger.info("Agent STOP")
        self.orchestrator.stop()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def listen(self) -> None:
        """Block and listen for the toggle hotkey until interrupted."""

        if keyboard is None:
            raise RuntimeError(
                "pynput is not available; drive HotkeyRunner.start/stop directly."
            )
        target = self.config.hotkey.lower()
        logger.info("Press '%s' to start/stop. Ctrl-C to quit.", target)

        def on_press(key) -> None:
            try:
                char = getattr(key, "char", None)
            except Exception:
                char = None
            if char and char.lower() == target:
                self.toggle()

        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.start()
        try:
            self._listener.join()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
            self.orchestrator.close()
