import time

from kamil_gamer.agents import Orchestrator
from kamil_gamer.config import Config
from kamil_gamer.control import Controller
from kamil_gamer.memory import GameMemory
from kamil_gamer.planning import Planner
from kamil_gamer.schemas import ActionType, Quest, Scene


class StubVision:
    """A vision pipeline that returns a fixed scene without touching the screen."""

    def __init__(self, scene: Scene):
        self._scene = scene

    def perceive(self, frame=None):
        return self._scene

    @property
    def capture(self):
        class _Cap:
            def grab(self):
                class _F:
                    width = 1280
                    height = 720

                return _F()

        return _Cap()

    def close(self):
        pass


def build_orchestrator(tmp_path, scene):
    config = Config()
    config.memory.root = tmp_path
    config.control.dry_run = True
    config.control.min_reaction_ms = 0
    config.control.max_reaction_ms = 1
    return Orchestrator(
        config,
        vision=StubVision(scene),
        planner=Planner(),
        controller=Controller(config.control),
        memory=GameMemory(tmp_path, "test"),
    )


def test_step_records_action_in_dry_run(tmp_path):
    scene = Scene(timestamp=time.time(), player_health_pct=90.0)
    orch = build_orchestrator(tmp_path, scene)
    action = orch.step()
    assert orch.stats.cycles == 1
    assert action.type in {ActionType.KEY, ActionType.MOVE, ActionType.CLICK}
    assert len(orch.controller.log) == 1
    orch.close()


def test_run_max_cycles(tmp_path):
    scene = Scene(timestamp=time.time(), player_health_pct=90.0)
    orch = build_orchestrator(tmp_path, scene)
    orch.config.loop_hz = 100.0
    stats = orch.run(max_cycles=3)
    assert stats.cycles == 3
    orch.close()


def test_quest_progress_persisted_to_memory(tmp_path):
    scene = Scene(
        timestamp=time.time(),
        player_health_pct=80.0,
        quests=[Quest(text="Collect 5 apples", progress="2/5")],
    )
    orch = build_orchestrator(tmp_path, scene)
    orch.step()
    goals = orch.memory.goals()
    assert any(g["progress"] == "2/5" for g in goals)
    orch.close()
