"""Chat router: a command + conversation hybrid.

Turns each player message into one of:

* a **command** (``/goal ...``, ``/reset``, ``/focus ...``, ``/follow me``,
  ``/status``),
* a **mission** (natural-language imperatives like "collect 5 gems"),
* a **preference** ("I like stealth") -> remembered for later, or
* a **conversation** turn (questions / chit-chat) -> a teammate-style reply.

The router is deliberately rule-based and dependency-free so it is easy to test
and reason about; an LLM responder can be layered on top later.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Protocol, runtime_checkable

from ..memory import GameMemory
from ..safety import SafetyPolicy
from .missions import MissionBoard

_CHAT_SYSTEM = (
    "You are Kamil AI Gamer, a friendly game-playing teammate. Reply in one or "
    "two short, natural sentences. Never help with cheating or exploits."
)


@runtime_checkable
class TextLLM(Protocol):
    """Anything that can answer text (e.g. the local Ollama ``LocalLLM``)."""

    @property
    def available(self) -> bool: ...

    def chat(self, prompt: str, system: Optional[str] = None) -> Optional[str]: ...


_IMPERATIVE = re.compile(
    r"^\s*(collect|find|finish|complete|reach|go|explore|kill|defeat|build|open|"
    r"get|grab|gather|deliver|escort|follow|craft|trade|talk to)\b",
    re.IGNORECASE,
)
_PREFERENCE = re.compile(
    r"\bi\s+(?:like|prefer|enjoy|want)\b\s+(.+?)\s*(?:playstyle|style|game[- ]?play)?\.?$",
    re.IGNORECASE,
)
_QUESTION = re.compile(
    r"^\s*(what|why|how|where|when|who|do|are|is|can|should|could|would)\b",
    re.IGNORECASE,
)
_COUNT = re.compile(r"\b(\d+)\b")


class TurnKind(str, Enum):
    COMMAND = "command"
    MISSION = "mission"
    PREFERENCE = "preference"
    CONVERSATION = "conversation"
    REFUSED = "refused"


@dataclass
class ChatTurn:
    kind: TurnKind
    reply: str
    mission_goal: Optional[str] = None


class ChatRouter:
    def __init__(
        self,
        board: MissionBoard,
        memory: Optional[GameMemory] = None,
        safety: Optional[SafetyPolicy] = None,
        llm: Optional[TextLLM] = None,
    ) -> None:
        self.board = board
        self.memory = memory
        self.safety = safety or SafetyPolicy()
        self.llm = llm

    def handle(self, text: str) -> ChatTurn:
        text = (text or "").strip()
        if not text:
            return ChatTurn(TurnKind.CONVERSATION, "I'm here. What should I do?")

        verdict = self.safety.check(text)
        if not verdict.allowed:
            return ChatTurn(TurnKind.REFUSED, verdict.reason)

        if text.startswith("/"):
            return self._command(text)

        pref = _PREFERENCE.search(text)
        if pref:
            value = pref.group(1).strip()
            if self.memory is not None:
                prefs = self.memory.recall("player_preferences", [])
                if value not in prefs:
                    prefs.append(value)
                self.memory.remember("player_preferences", prefs)
            return ChatTurn(
                TurnKind.PREFERENCE, f"Got it — I'll remember you prefer {value}."
            )

        if _IMPERATIVE.match(text):
            return self._mission(text)

        if _QUESTION.match(text) or text.endswith("?"):
            return ChatTurn(TurnKind.CONVERSATION, self._answer(text))

        # Default: treat as a soft goal.
        return self._mission(text)

    # --- commands ------------------------------------------------------------
    def _command(self, text: str) -> ChatTurn:
        parts = text[1:].split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "goal" and arg:
            return self._mission(arg)
        if cmd == "reset":
            self.board.missions.clear()
            return ChatTurn(TurnKind.COMMAND, "Cleared all missions.")
        if cmd == "focus" and arg:
            if self.memory is not None:
                self.memory.remember("focus", arg)
            return ChatTurn(TurnKind.COMMAND, f"Focusing on {arg}.")
        if cmd == "follow":
            self.board.add("Follow the player", ["Stay near the player"])
            return ChatTurn(TurnKind.COMMAND, "Following you.", "Follow the player")
        if cmd == "status":
            return ChatTurn(TurnKind.COMMAND, self.board.render())
        return ChatTurn(TurnKind.COMMAND, f"Unknown command: /{cmd}")

    # --- missions ------------------------------------------------------------
    def _mission(self, goal: str) -> ChatTurn:
        self.board.add(goal, self._decompose(goal))
        if self.memory is not None:
            self.memory.log_event("mission_added", {"goal": goal})
        return ChatTurn(
            TurnKind.MISSION,
            f"New mission: {goal}\n{self.board.render()}",
            mission_goal=goal,
        )

    @staticmethod
    def _decompose(goal: str) -> list[str]:
        """Naive goal decomposition into ordered subgoals."""

        subs: list[str] = []
        m = _COUNT.search(goal)
        target = m.group(1) if m else None
        lower = goal.lower()
        if any(v in lower for v in ("collect", "gather", "get", "grab", "find")):
            subs.append("Locate the target(s)")
            subs.append(f"Acquire {target or 'the'} item(s)")
        elif any(v in lower for v in ("kill", "defeat")):
            subs.append("Find the enemy")
            subs.append("Defeat it safely")
        elif any(v in lower for v in ("reach", "go", "finish", "complete")):
            subs.append("Find the route")
            subs.append("Travel there")
        else:
            subs.append("Plan an approach")
            subs.append("Execute it")
        subs.append("Report when done")
        return subs

    # --- conversation --------------------------------------------------------
    def _answer(self, text: str) -> str:
        llm_reply = self._llm_answer(text)
        if llm_reply:
            return llm_reply
        lower = text.lower()
        if "what are you doing" in lower or "what're you doing" in lower:
            m = self.board.next_actionable()
            return f"Working on: {m.goal}" if m else "Waiting for a goal."
        if "map" in lower:
            return "I'm building a map as I explore; ask /status for missions."
        if "stuck" in lower:
            return "If I stop making progress I switch to recovery and ask you."
        return "Tell me a goal (e.g. 'collect 5 coins') or ask /status."

    def _llm_answer(self, text: str) -> Optional[str]:
        """Use a local LLM for a natural reply when one is available."""

        if self.llm is None:
            return None
        try:
            if not self.llm.available:
                return None
            reply = self.llm.chat(text, system=_CHAT_SYSTEM)
        except Exception:
            return None
        return reply.strip() if reply else None
