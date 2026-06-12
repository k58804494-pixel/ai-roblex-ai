"""Vision pipeline: capture -> (LLM understanding | OCR heuristics) -> Scene.

The pipeline always produces a ``Scene``. When a cloud LLM is configured it does
the heavy lifting of scene understanding; otherwise the pipeline falls back to
OCR plus light heuristics so the agent still has *some* structured perception.
"""

from __future__ import annotations

import re
import time
from typing import Optional

from ..config import Config
from ..schemas import Quest, Scene
from .capture import Frame, ScreenCapture
from .llm_vision import LLMVision
from .ocr import OCR

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

    def perceive(self, frame: Optional[Frame] = None) -> Scene:
        if frame is None:
            frame = self.capture.grab()

        if self.llm is not None and self.llm.available:
            scene = self.llm.understand(frame.image)
            if scene is not None:
                if self.ocr is not None and self.ocr.available and not scene.raw_text:
                    scene.raw_text = self.ocr.read_text(frame.image)
                return scene

        return self._ocr_scene(frame)

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
