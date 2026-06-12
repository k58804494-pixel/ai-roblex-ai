import time

from kamil_gamer.adapters.base import KeyBindings
from kamil_gamer.schemas import (
    ActionType,
    BoundingBox,
    Entity,
    EntityKind,
    Scene,
)
from kamil_gamer.skills import builtin_library


def test_library_lists_skills():
    lib = builtin_library()
    assert {"parkour", "combat", "explore", "trade"} <= set(lib.names())


def test_combat_applicable_only_with_enemy():
    lib = builtin_library()
    combat = lib.get("combat")
    assert combat is not None
    no_enemy = Scene(timestamp=time.time())
    with_enemy = Scene(
        timestamp=time.time(),
        entities=[Entity(kind=EntityKind.ENEMY, distance_m=2.0)],
    )
    assert not combat.applicable(no_enemy)
    assert combat.applicable(with_enemy)


def test_combat_step_targets_enemy_box():
    lib = builtin_library()
    combat = lib.get("combat")
    scene = Scene(
        timestamp=time.time(),
        entities=[
            Entity(
                kind=EntityKind.ENEMY,
                distance_m=2.0,
                box=BoundingBox(x=0, y=0, width=20, height=20),
            )
        ],
    )
    action = combat.step(scene, KeyBindings())
    assert action.type == ActionType.CLICK
    assert action.target == (10, 10)


def test_applicable_filters():
    lib = builtin_library()
    scene = Scene(timestamp=time.time())
    names = {s.name for s in lib.applicable(scene)}
    assert "combat" not in names
    assert "explore" in names
