from kamil_gamer.world import PlaceKind, WorldModel


def test_add_and_connect():
    w = WorldModel()
    w.add_place("Town", PlaceKind.TOWN)
    w.connect("Town", "Shop")
    assert "Shop" in w.places
    assert "Shop" in w.places["Town"].neighbors
    assert "Town" in w.places["Shop"].neighbors


def test_route_bfs():
    w = WorldModel()
    w.connect("Town", "Gate")
    w.connect("Gate", "Dungeon")
    assert w.route("Town", "Dungeon") == ["Town", "Gate", "Dungeon"]
    assert w.route("Town", "Nowhere") == []
    assert w.route("Town", "Town") == ["Town"]


def test_route_avoids_danger():
    w = WorldModel()
    w.connect("Town", "Trap")
    w.connect("Trap", "Exit")
    w.connect("Town", "Safe")
    w.connect("Safe", "Exit")
    w.mark_danger("Trap", 1.0)
    route = w.route("Town", "Exit", avoid_danger=1.0)
    assert "Trap" not in route
    assert route == ["Town", "Safe", "Exit"]


def test_serialization_roundtrip():
    w = WorldModel()
    w.add_place("Cave", PlaceKind.SECRET, position=(3.0, 4.0), notes="hidden")
    w.connect("Cave", "Town")
    data = w.to_dict()
    w2 = WorldModel.from_dict(data)
    assert w2.places["Cave"].kind == PlaceKind.SECRET
    assert w2.places["Cave"].position == (3.0, 4.0)
    assert "Town" in w2.places["Cave"].neighbors
