import time

from kamil_gamer.schemas import (
    Action,
    ActionType,
    BoundingBox,
    Entity,
    EntityKind,
    Quest,
    Scene,
)


def test_bounding_box_center():
    box = BoundingBox(x=10, y=20, width=100, height=40)
    assert box.center == (60, 40)


def test_scene_nearest_enemy():
    scene = Scene(
        timestamp=time.time(),
        entities=[
            Entity(kind=EntityKind.ENEMY, label="zombie", distance_m=10.0),
            Entity(kind=EntityKind.ENEMY, label="skeleton", distance_m=3.0),
            Entity(kind=EntityKind.NPC, label="trader", distance_m=1.0),
        ],
    )
    assert len(scene.enemies()) == 2
    nearest = scene.nearest_enemy()
    assert nearest is not None and nearest.label == "skeleton"


def test_scene_no_enemy():
    scene = Scene(timestamp=time.time())
    assert scene.nearest_enemy() is None


def test_action_describe():
    a = Action(type=ActionType.CLICK, target=(5, 6), reason="engage")
    assert "click" in a.describe() and "engage" in a.describe()


def test_quest_optional_progress():
    q = Quest(text="Collect 5 apples", progress="2/5")
    assert q.progress == "2/5"
