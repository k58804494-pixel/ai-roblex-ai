"""The AI's "brain view": current goal, plan, confidence, and any blocker.

This is what the Control Room's thinking panel renders so you can *see* the
agent's reasoning. ``needs_clarification`` is the anti-confusion signal: when
confidence is too low the agent should pause and ask rather than loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ThinkingState:
    current_goal: str = ""
    subgoal: str = ""
    next_action: str = ""
    problem: str = ""
    confidence: float = 1.0  # 0..1
    clarify_threshold: float = 0.35

    def needs_clarification(self) -> bool:
        return self.confidence < self.clarify_threshold

    def render(self) -> str:
        pct = int(round(self.confidence * 100))
        lines = [
            f"Current Goal: {self.current_goal or '-'}",
            f"Subgoal: {self.subgoal or '-'}",
            f"Confidence: {pct}%",
        ]
        if self.problem:
            lines.append(f"Problem: {self.problem}")
        lines.append(f"Next action: {self.next_action or '-'}")
        if self.needs_clarification():
            lines.append("⚠ Low confidence — should ask the user.")
        return "\n".join(lines)

    def clarifying_question(self) -> Optional[str]:
        if not self.needs_clarification():
            return None
        if self.problem:
            return f"I'm unsure how to handle: {self.problem}. How should I proceed?"
        if self.current_goal:
            return f"I'm not confident about '{self.current_goal}'. Can you clarify?"
        return "I'm not sure what to do next. What should I focus on?"
