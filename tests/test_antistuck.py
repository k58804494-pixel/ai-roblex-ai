import time

from kamil_gamer.agents.antistuck import AntiStuck
from kamil_gamer.config import AntiStuckConfig
from kamil_gamer.schemas import Quest, Scene


def scene_with(progress: str | None):
    return Scene(timestamp=time.time(), quests=[Quest(text="q", progress=progress)])


def test_not_stuck_when_progress_changes():
    anti = AntiStuck(AntiStuckConfig(stuck_seconds=10.0))
    t0 = 1000.0
    anti.observe(scene_with("1/5"), now=t0)
    anti.observe(scene_with("2/5"), now=t0 + 8)
    assert not anti.is_stuck(now=t0 + 12)  # progress reset the timer at t0+8


def test_stuck_when_no_change():
    anti = AntiStuck(AntiStuckConfig(stuck_seconds=10.0))
    t0 = 2000.0
    anti.observe(scene_with("1/5"), now=t0)
    anti.observe(scene_with("1/5"), now=t0 + 5)
    assert anti.is_stuck(now=t0 + 11)


def test_recovery_cycles_strategies():
    anti = AntiStuck(AntiStuckConfig(stuck_seconds=1.0))
    first = anti.recovery_action()
    second = anti.recovery_action()
    assert first.describe() != second.describe()


def test_reset():
    anti = AntiStuck(AntiStuckConfig(stuck_seconds=5.0))
    anti.observe(scene_with("1/5"), now=100.0)
    anti.reset()
    assert not anti.is_stuck(now=101.0)
