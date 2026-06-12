"""Runtime configuration.

Configuration is layered: built-in defaults -> optional YAML file -> environment
variables. Nothing here requires an API key; the cloud vision model is only used
when ``openai_api_key`` resolves to a non-empty value.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:  # PyYAML is optional; config works without it.
    import yaml
except Exception:  # pragma: no cover - exercised only when PyYAML missing
    yaml = None


DEFAULT_CONFIG_PATHS = (
    Path("config.yaml"),
    Path.home() / ".config" / "kamil_gamer" / "config.yaml",
)


@dataclass
class VisionConfig:
    use_llm: bool = True  # use cloud LLM when an API key is available
    llm_model: str = "gpt-4o-mini"
    use_ocr: bool = True
    capture_monitor: int = 1  # mss monitor index; 1 = primary
    max_image_dim: int = 1280  # downscale before sending to the LLM


@dataclass
class ControlConfig:
    dry_run: bool = True  # when True, actions are logged, not executed
    min_reaction_ms: int = 120
    max_reaction_ms: int = 320
    aim_error_px: int = 6  # std-dev of gaussian aiming error
    move_min_duration_s: float = 0.12
    move_max_duration_s: float = 0.45


@dataclass
class LocalLLMConfig:
    """Local Ollama backend — no API key, runs on your machine."""

    enabled: bool = True
    host: str = "http://localhost:11434"
    vision_model: str = "llava"
    text_model: str = "llama3.2"
    timeout_s: float = 60.0


@dataclass
class YoloConfig:
    """Local YOLO object detection (ultralytics)."""

    enabled: bool = True
    weights: str = "yolov8n.pt"
    conf: float = 0.35


@dataclass
class MemoryConfig:
    root: Path = field(default_factory=lambda: Path.home() / ".kamil_gamer")


@dataclass
class AntiStuckConfig:
    stuck_seconds: float = 60.0
    progress_eps: float = 1.0  # min change considered "progress"


@dataclass
class Config:
    hotkey: str = "r"  # press to start/stop the agent loop
    loop_hz: float = 2.0  # how many perceive->act cycles per second
    game_name: str = "unknown_game"
    openai_api_key: Optional[str] = None

    vision: VisionConfig = field(default_factory=VisionConfig)
    control: ControlConfig = field(default_factory=ControlConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    anti_stuck: AntiStuckConfig = field(default_factory=AntiStuckConfig)
    local_llm: LocalLLMConfig = field(default_factory=LocalLLMConfig)
    yolo: YoloConfig = field(default_factory=YoloConfig)

    @property
    def llm_enabled(self) -> bool:
        return bool(self.vision.use_llm and self.openai_api_key)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        data: dict[str, Any] = {}
        candidates = [path] if path else list(DEFAULT_CONFIG_PATHS)
        for candidate in candidates:
            if candidate and candidate.exists() and yaml is not None:
                with open(candidate, "r", encoding="utf-8") as fh:
                    data = yaml.safe_load(fh) or {}
                break
        cfg = cls._from_dict(data)
        cfg._apply_env()
        return cfg

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Config":
        cfg = cls()
        for key in ("hotkey", "loop_hz", "game_name", "openai_api_key"):
            if key in data:
                setattr(cfg, key, data[key])
        if "vision" in data:
            cfg.vision = VisionConfig(**{**cfg.vision.__dict__, **data["vision"]})
        if "control" in data:
            cfg.control = ControlConfig(**{**cfg.control.__dict__, **data["control"]})
        if "anti_stuck" in data:
            cfg.anti_stuck = AntiStuckConfig(
                **{**cfg.anti_stuck.__dict__, **data["anti_stuck"]}
            )
        if "local_llm" in data:
            cfg.local_llm = LocalLLMConfig(
                **{**cfg.local_llm.__dict__, **data["local_llm"]}
            )
        if "yolo" in data:
            cfg.yolo = YoloConfig(**{**cfg.yolo.__dict__, **data["yolo"]})
        if "memory" in data and "root" in data["memory"]:
            cfg.memory = MemoryConfig(root=Path(data["memory"]["root"]))
        return cfg

    def _apply_env(self) -> None:
        env_key = os.environ.get("OPENAI_API_KEY")
        if env_key:
            self.openai_api_key = env_key
        if os.environ.get("KAMIL_GAMER_DRY_RUN") == "0":
            self.control.dry_run = False
        if os.environ.get("KAMIL_GAMER_GAME"):
            self.game_name = os.environ["KAMIL_GAMER_GAME"]
