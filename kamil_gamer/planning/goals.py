"""Layered goals: short / medium / long-term.

A tiny stack abstraction the planner uses to keep "walk to NPC" (short) under
"finish quest" (medium) under "become strongest player" (long). The orchestrator
persists these to memory so progress survives across sessions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Horizon(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


@dataclass
class Goal:
    text: str
    horizon: Horizon
    done: bool = False


@dataclass
class GoalStack:
    goals: list[Goal] = field(default_factory=list)

    def add(self, text: str, horizon: Horizon) -> Goal:
        goal = Goal(text=text, horizon=horizon)
        self.goals.append(goal)
        return goal

    def current(self, horizon: Horizon) -> Goal | None:
        for goal in self.goals:
            if goal.horizon == horizon and not goal.done:
                return goal
        return None

    def complete(self, goal: Goal) -> None:
        goal.done = True

    def active(self) -> list[Goal]:
        return [g for g in self.goals if not g.done]
