import numpy as np

from kamil_gamer.config import Config
from kamil_gamer.schemas import EntityKind, Scene
from kamil_gamer.vision.capture import Frame
from kamil_gamer.vision.local_vision import LocalLLM
from kamil_gamer.vision.pipeline import VisionPipeline
from kamil_gamer.vision.scene_json import parse_scene_json
from kamil_gamer.vision.yolo import detections_to_entities


# --- shared scene-JSON parser -------------------------------------------------
def test_parse_scene_json_valid():
    scene = parse_scene_json(
        '{"player_health_pct": 80, '
        '"entities": [{"kind": "enemy", "label": "zombie", "distance_m": 10}], '
        '"quests": [{"text": "Collect 5 apples", "progress": "2/5"}], '
        '"inventory": ["sword"], "notes": "ok"}'
    )
    assert scene is not None
    assert scene.player_health_pct == 80
    assert scene.entities[0].kind == EntityKind.ENEMY
    assert scene.entities[0].distance_m == 10
    assert scene.quests[0].progress == "2/5"
    assert scene.inventory == ["sword"]


def test_parse_scene_json_accepts_dict_and_bad_kind():
    scene = parse_scene_json({"entities": [{"kind": "dragon", "label": "x"}]})
    assert scene is not None
    assert scene.entities[0].kind == EntityKind.UNKNOWN


def test_parse_scene_json_malformed_returns_none():
    assert parse_scene_json("not json") is None
    assert parse_scene_json(None) is None
    assert parse_scene_json("[1, 2, 3]") is None


# --- YOLO mapping -------------------------------------------------------------
def test_detections_to_entities_maps_person_and_box():
    entities = detections_to_entities(
        [("person", 0.9, 10, 20, 40, 60), ("apple", 0.5, 0, 0, 5, 5)]
    )
    assert entities[0].kind == EntityKind.PLAYER
    assert entities[0].box is not None
    assert (entities[0].box.width, entities[0].box.height) == (30, 40)
    assert entities[1].kind == EntityKind.UNKNOWN
    assert entities[1].label == "apple"


# --- Local Ollama backend -----------------------------------------------------
def test_local_llm_unavailable_when_no_server():
    # Nothing is listening on this port in the test env.
    llm = LocalLLM(host="http://localhost:6", timeout_s=1.0)
    assert llm.available is False


def test_local_llm_understand_returns_none_when_unreachable():
    llm = LocalLLM(host="http://localhost:6", timeout_s=1.0)
    img = np.zeros((8, 8, 3), dtype=np.uint8)
    assert llm.understand(img) is None


def test_local_llm_post_body_extraction():
    llm = LocalLLM()
    # /api/chat shape
    assert llm._extract({"message": {"content": "hi"}}) == "hi"  # type: ignore[attr-defined]
    # /api/generate shape
    assert llm._extract({"response": "yo"}) == "yo"  # type: ignore[attr-defined]
    assert llm._extract({"nope": 1}) is None  # type: ignore[attr-defined]


# --- pipeline precedence + augmentation --------------------------------------
class _FakeYolo:
    available = True

    def detect(self, image):
        return detections_to_entities([("person", 0.8, 0, 0, 10, 10)])


def _ocr_only_config() -> Config:
    cfg = Config()
    cfg.vision.use_llm = False
    cfg.vision.use_ocr = False
    cfg.local_llm.enabled = False
    cfg.yolo.enabled = False
    return cfg


def test_pipeline_falls_back_to_no_perception():
    pipe = VisionPipeline(_ocr_only_config())
    frame = Frame(image=np.zeros((4, 4, 3), dtype=np.uint8))
    scene = pipe.perceive(frame)
    assert isinstance(scene, Scene)
    assert scene.notes == "no-perception"
    pipe.close()


def test_pipeline_merges_yolo_detections():
    pipe = VisionPipeline(_ocr_only_config())
    pipe.yolo = _FakeYolo()
    frame = Frame(image=np.zeros((4, 4, 3), dtype=np.uint8))
    scene = pipe.perceive(frame)
    assert any(e.kind == EntityKind.PLAYER for e in scene.entities)
    pipe.close()


def test_config_parses_local_llm_and_yolo():
    cfg = Config._from_dict(
        {
            "local_llm": {"enabled": False, "vision_model": "moondream"},
            "yolo": {"conf": 0.5},
        }
    )
    assert cfg.local_llm.enabled is False
    assert cfg.local_llm.vision_model == "moondream"
    assert cfg.yolo.conf == 0.5
