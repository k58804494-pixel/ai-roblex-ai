"""Vision pipeline: capture -> scene understanding -> Scene.

The pipeline always produces a ``Scene``. It picks the best available
*understander* in this order, falling through on failure so the agent always
perceives *something*:

1. **Cloud LLM** (`LLMVision`) — only when an ``OPENAI_API_KEY`` is set.
2. **Local Ollama** (`LocalLLM`) — free, no key, when a server is reachable.
3. **OCR heuristics** — Tesseract + light regex parsing.

Regardless of which understander runs, **YOLO** object detections (if available)
are merged in to give the planner clickable bounding boxes.
"""

from __future__ import annotations

import re
import time
from typing import Optional

from ..config import Config
from ..schemas import Quest, Scene
from .capture import Frame, ScreenCapture
from .llm_vision import LLMVision
from .local_vision import LocalLLM
from .ocr import OCR
from .yolo import YoloDetector

_HEALTH_RE = re.compile(r"(?:hp|health)\D{0,3}(\d{1,3})\s*%?", re.IGNORECASE)
_QUEST_RE = re.compile(r"(collect|defeat|find|reach|talk to|kill)\b.*", re.IGNORECASE)
_PROGRESS_RE = re.compile(r"\b(\d+)\s*/\s*(\d+)\b")


class VisionPipeline:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.capture = ScreenCapture(monitor=config.vision.capture_monitor)
        self.ocr = OCR() if config.vision.use_ocr else None

        self.llm: Optional[LLMVision] = None
        if config.llm_enabled:
            self.llm = LLMVision(
                api_key=config.openai_api_key,
                model=config.vision.llm_model,
                max_dim=config.vision.max_image_dim,
            )

        self.local_llm: Optional[LocalLLM] = None
        if config.local_llm.enabled:
            self.local_llm = LocalLLM(
                host=config.local_llm.host,
                vision_model=config.local_llm.vision_model,
                text_model=config.local_llm.text_model,
                max_dim=config.vision.max_image_dim,
                timeout_s=config.local_llm.timeout_s,
            )

        self.yolo: Optional[YoloDetector] = None
        if config.yolo.enabled:
            self.yolo = YoloDetector(
                weights=config.yolo.weights, conf=config.yolo.conf
            )

    def perceive(self, frame: Optional[Frame] = None) -> Scene:
        if frame is None:
            frame = self.capture.grab()

        scene = self._understand(frame)
        if scene is None:
            scene = self._ocr_scene(frame)

        self._augment(scene, frame)
        return scene

    def _understand(self, frame: Frame) -> Optional[Scene]:
        if self.llm is not None and self.llm.available:
            scene = self.llm.understand(frame.image)
            if scene is not None:
                if not scene.notes:
                    scene.notes = "cloud-llm"
                return scene
        if self.local_llm is not None and self.local_llm.available:
            scene = self.local_llm.understand(frame.image)
            if scene is not None:
                if not scene.notes:
                    scene.notes = "local-llm"
                return scene
        return None

    def _augment(self, scene: Scene, frame: Frame) -> None:
        """Merge YOLO detections and OCR text into ``scene`` in place."""

        if self.yolo is not None and self.yolo.available:
            detected = self.yolo.detect(frame.image)
            if detected:
                # Keep semantic entities; append detections that add boxes.
                scene.entities.extend(detected)
        if self.ocr is not None and self.ocr.available and not scene.raw_text:
            scene.raw_text = self.ocr.read_text(frame.image)

    def _ocr_scene(self, frame: Frame) -> Scene:
        text = ""
        lines: list[str] = []
        if self.ocr is not None and self.ocr.available:
            lines = self.ocr.read_lines(frame.image)
            text = "\n".join(lines)

        health = None
        quests: list[Quest] = []
        for line in lines:
            m = _HEALTH_RE.search(line)
            if m and health is None:
                try:
                    health = max(0.0, min(100.0, float(m.group(1))))
                except ValueError:
                    pass
            if _QUEST_RE.search(line):
                pm = _PROGRESS_RE.search(line)
                quests.append(
                    Quest(text=line, progress=pm.group(0) if pm else None)
                )

        return Scene(
            timestamp=time.time(),
            player_health_pct=health,
            quests=quests,
            raw_text=text,
            notes="ocr-fallback" if text else "no-perception",
        )

    def close(self) -> None:
        self.capture.close()
