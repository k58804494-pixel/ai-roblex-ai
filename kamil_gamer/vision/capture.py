"""Screen capture.

Uses ``mss`` when available (fast, cross-platform). Falls back to a solid-colour
placeholder frame so the pipeline and tests run on headless machines without a
display server.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    import mss  # type: ignore
except Exception:  # pragma: no cover - depends on host
    mss = None


@dataclass
class Frame:
    """A captured frame as an RGB numpy array plus its screen offset."""

    image: np.ndarray  # shape (H, W, 3), dtype uint8, RGB
    left: int = 0
    top: int = 0

    @property
    def width(self) -> int:
        return int(self.image.shape[1])

    @property
    def height(self) -> int:
        return int(self.image.shape[0])


class ScreenCapture:
    def __init__(self, monitor: int = 1) -> None:
        self.monitor = monitor
        self._sct = mss.mss() if mss is not None else None

    @property
    def available(self) -> bool:
        return self._sct is not None

    def grab(self) -> Frame:
        if self._sct is None:
            # Headless fallback: a blank 1280x720 frame.
            return Frame(image=np.zeros((720, 1280, 3), dtype=np.uint8))
        monitors = self._sct.monitors
        idx = self.monitor if self.monitor < len(monitors) else 0
        mon = monitors[idx]
        raw = self._sct.grab(mon)
        # mss returns BGRA; convert to RGB.
        arr = np.array(raw, dtype=np.uint8)[:, :, :3][:, :, ::-1]
        return Frame(image=np.ascontiguousarray(arr), left=mon["left"], top=mon["top"])

    def close(self) -> None:
        if self._sct is not None:
            self._sct.close()
