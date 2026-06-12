"""Local object detection via YOLO (ultralytics) — no API key, runs offline.

Augments the scene with bounding boxes for detected objects. Optional: if
``ultralytics`` isn't installed (or weights can't load) the detector is simply
unavailable and the pipeline carries on with OCR/LLM perception.

Note: the default pretrained weights detect **COCO** objects (person, car, ...),
which only loosely map to game entities. For game-specific detection (coins,
zombies, chests) train a small custom YOLO model and point ``weights`` at it —
the rest of the pipeline is unchanged. See docs/TRAINING.md.
"""

from __future__ import annotations

import numpy as np

from ..schemas import BoundingBox, Entity, EntityKind

try:
    from ultralytics import YOLO  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    YOLO = None

# COCO labels that map to a meaningful game entity kind; everything else is
# recorded as UNKNOWN but keeps its detected label.
_KIND_BY_LABEL = {
    "person": EntityKind.PLAYER,
}


def detections_to_entities(
    detections: list[tuple[str, float, int, int, int, int]],
) -> list[Entity]:
    """Pure mapping from (label, conf, x1, y1, x2, y2) tuples to ``Entity``s."""

    entities: list[Entity] = []
    for label, conf, x1, y1, x2, y2 in detections:
        kind = _KIND_BY_LABEL.get(label.lower(), EntityKind.UNKNOWN)
        entities.append(
            Entity(
                kind=kind,
                label=label,
                confidence=float(conf),
                box=BoundingBox(
                    x=int(x1),
                    y=int(y1),
                    width=int(x2 - x1),
                    height=int(y2 - y1),
                ),
            )
        )
    return entities


class YoloDetector:
    def __init__(self, weights: str = "yolov8n.pt", conf: float = 0.35) -> None:
        self.conf = conf
        self._model = None
        if YOLO is not None:
            try:
                self._model = YOLO(weights)
            except Exception:
                self._model = None

    @property
    def available(self) -> bool:
        return self._model is not None

    def detect(self, image: np.ndarray) -> list[Entity]:
        if self._model is None:
            return []
        try:
            results = self._model.predict(image, conf=self.conf, verbose=False)
        except Exception:
            return []
        detections: list[tuple[str, float, int, int, int, int]] = []
        for result in results:
            names = getattr(result, "names", {}) or {}
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                cls_id = int(box.cls[0])
                label = names.get(cls_id, str(cls_id))
                conf = float(box.conf[0])
                x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
                detections.append((label, conf, x1, y1, x2, y2))
        return detections_to_entities(detections)
