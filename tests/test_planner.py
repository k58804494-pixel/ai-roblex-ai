import time

from kamil_gamer.planning import Planner
from kamil_gamer.schemas import (
    ActionType,
    BoundingBox,
    Entity,
    EntityKind,
    Quest,
    Scene,
)


def make_scene(**kwargs):
    return Scene(timestamp=time.time(), **kwargs)


def test_low_health_retreats():
    planner = Planner()
    action = planner.plan(make_scene(player_health_pct=10.0))
    assert action.type == ActionType.KEY
    assert action.key == "s"


def test_engages_nearest_enemy_with_box():
    planner = Planner()
    enemy = Entity(
        kind=EntityKind.ENEMY,
        label="zombie",
        distance_m=5.0,
        box=BoundingBox(x=100, y=100, width=40, height=40),
    )
    action = planner.plan(make_scene(player_health_pct=90.0, entities=[enemy]))
    assert action.type == ActionType.CLICK
    assert action.target == (120, 120)


def test_moves_toward_objective():
    planner = Planner()
    npc = Entity(
        kind=EntityKind.NPC,
        label="elder",
        box=BoundingBox(x=200, y=50, width=20, height=20),
    )
    action = planner.plan(make_scene(player_health_pct=90.0, entities=[npc]))
    assert action.type == ActionType.MOVE
    assert action.target == (210, 60)


def test_pursues_quest_when_no_targets():
    planner = Planner()
    action = planner.plan(
        make_scene(player_health_pct=90.0, quests=[Quest(text="Collect 5 apples")])
    )
    assert action.type == ActionType.KEY
    assert action.key == "w"


def test_explores_when_nothing_visible():
    planner = Planner()
    action = planner.plan(make_scene(player_health_pct=90.0))
    assert action.type == ActionType.KEY
    assert action.key in {"w", "a", "d"}
