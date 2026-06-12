from kamil_gamer.memory import GameMemory


def test_facts_roundtrip(tmp_path):
    mem = GameMemory(tmp_path, "Test Game")
    mem.remember("boss_weakness", "fire")
    mem.remember("level", 12)
    assert mem.recall("boss_weakness") == "fire"
    assert mem.recall("level") == 12
    assert mem.recall("missing", default="x") == "x"
    assert mem.all_facts()["level"] == 12
    mem.close()


def test_facts_persist_across_instances(tmp_path):
    mem = GameMemory(tmp_path, "Persisted")
    mem.remember("k", {"a": 1})
    mem.close()
    mem2 = GameMemory(tmp_path, "Persisted")
    assert mem2.recall("k") == {"a": 1}
    mem2.close()


def test_events_logged(tmp_path):
    mem = GameMemory(tmp_path, "g")
    mem.log_event("action", {"action": "move"})
    mem.log_event("recovery", {"action": "jump"})
    events = mem.recent_events()
    assert events[0]["kind"] == "recovery"
    assert events[1]["payload"]["action"] == "move"
    mem.close()


def test_goals(tmp_path):
    mem = GameMemory(tmp_path, "g")
    mem.set_goal("Collect 5 apples", status="active", progress="2/5")
    mem.set_goal("Collect 5 apples", status="active", progress="5/5")
    goals = mem.goals()
    assert len(goals) == 1
    assert goals[0]["progress"] == "5/5"
    mem.close()


def test_game_name_slugified_into_filename(tmp_path):
    mem = GameMemory(tmp_path, "Tower Defense / Sim!")
    assert mem.path.suffix == ".db"
    assert " " not in mem.path.name
    mem.close()
