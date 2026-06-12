"""OCR text extraction.

Wraps Tesseract via ``pytesseract`` when available. Designed to degrade
gracefully: if Tesseract is not installed, ``read_text`` returns an empty string
rather than raising, so the rest of the pipeline keeps working.
"""

from __future__ import annotations

import numpy as np

try:
    import pytesseract  # type: ignore
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover - depends on host
    pytesseract = None
    Image = None


class OCR:
    def __init__(self) -> None:
        self._available = pytesseract is not None and Image is not None
        if self._available:
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def read_text(self, image: np.ndarray) -> str:
        if not self._available:
            return ""
        try:
            pil = Image.fromarray(image)
            return pytesseract.image_to_string(pil).strip()
        except Exception:
            return ""

    def read_lines(self, image: np.ndarray) -> list[str]:
        text = self.read_text(image)
        return [line.strip() for line in text.splitlines() if line.strip()]
