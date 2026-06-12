"""Safety & boundaries.

The agent should refuse instructions that involve cheating/exploits, harassment,
or anything that puts the user's account at risk. This is a lightweight,
explainable gate over incoming chat commands (and could also wrap planned
actions). It is intentionally conservative and easy to audit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Phrases that indicate cheating, exploits, harassment, or account risk.
_BLOCKLIST = [
    r"\baim\s*bot\b",
    r"\bwall\s*hack\b",
    r"\bspeed\s*hack\b",
    r"\bexploit\b",
    r"\bduplicat(e|ion)\s+glitch\b",
    r"\binject(or|ion)?\b",
    r"\bcheat\s*engine\b",
    r"\bbypass\s+(anti[- ]?cheat|ban|detection)\b",
    r"\bevade\s+(detection|anti[- ]?cheat)\b",
    r"\bddos\b",
    r"\bharass\b",
    r"\bbully\b",
    r"\bscam\b",
    r"\bsteal\s+(account|password|credentials)\b",
    r"\bphish\b",
    r"\bdox\b",
    r"\bgrief\b",
]

_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _BLOCKLIST]


@dataclass
class SafetyVerdict:
    allowed: bool
    reason: str = ""
    matched: str = ""


class SafetyPolicy:
    def check(self, text: str) -> SafetyVerdict:
        for pat in _PATTERNS:
            m = pat.search(text or "")
            if m:
                return SafetyVerdict(
                    allowed=False,
                    matched=m.group(0),
                    reason=(
                        f"I can't help with that ('{m.group(0)}'). I won't cheat, "
                        "exploit, harass, or do anything that risks your account "
                        "or breaks game rules."
                    ),
                )
        return SafetyVerdict(allowed=True)
