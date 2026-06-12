from kamil_gamer.adapters import GameAdapter, RobloxAdapter, get_adapter
from kamil_gamer.metrics import Metrics
from kamil_gamer.safety import SafetyPolicy


def test_safety_blocks_cheats():
    policy = SafetyPolicy()
    assert not policy.check("use a wallhack").allowed
    assert not policy.check("bypass anti-cheat please").allowed
    assert not policy.check("harass that player").allowed


def test_safety_allows_normal():
    policy = SafetyPolicy()
    assert policy.check("collect 5 coins and find the key").allowed


def test_adapter_registry():
    assert isinstance(get_adapter("roblox"), RobloxAdapter)
    assert isinstance(get_adapter("unknown-game"), GameAdapter)
    assert get_adapter(None).name == "generic"


def test_roblox_recovery_is_jump():
    action = RobloxAdapter().recovery_hint()
    assert action.key == "space"


def test_metrics_rates_and_weaknesses():
    m = Metrics()
    for _ in range(8):
        m.record_action(success=False)
    for _ in range(2):
        m.record_action(success=True)
    assert m.success_rate == 0.2
    assert "low action success rate" in m.weaknesses()
    assert m.render()
