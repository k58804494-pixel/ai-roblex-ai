"""Mission board: turn goals into trackable missions with subgoals and a queue.

Every command from the player can become a mission with subgoals and a status:

    🟢 not_started  🟡 in_progress  🔴 stuck  ✅ completed

The board also acts as a simple task queue: ``next_actionable()`` returns the
mission the agent should work on right now.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class MissionStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    STUCK = "stuck"
    COMPLETED = "completed"

    @property
    def emoji(self) -> str:
        return {
            MissionStatus.NOT_STARTED: "🟢",
            MissionStatus.IN_PROGRESS: "🟡",
            MissionStatus.STUCK: "🔴",
            MissionStatus.COMPLETED: "✅",
        }[self]


@dataclass
class Subgoal:
    text: str
    done: bool = False


@dataclass
class Mission:
    goal: str
    subgoals: list[Subgoal] = field(default_factory=list)
    status: MissionStatus = MissionStatus.NOT_STARTED
    created_at: float = field(default_factory=time.time)

    def add_subgoal(self, text: str) -> Subgoal:
        sg = Subgoal(text=text)
        self.subgoals.append(sg)
        return sg

    def progress(self) -> tuple[int, int]:
        done = sum(1 for s in self.subgoals if s.done)
        return done, len(self.subgoals)

    def complete_next_subgoal(self) -> Optional[Subgoal]:
        for sg in self.subgoals:
            if not sg.done:
                sg.done = True
                if all(s.done for s in self.subgoals):
                    self.status = MissionStatus.COMPLETED
                else:
                    self.status = MissionStatus.IN_PROGRESS
                return sg
        self.status = MissionStatus.COMPLETED
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "status": self.status.value,
            "subgoals": [{"text": s.text, "done": s.done} for s in self.subgoals],
            "created_at": self.created_at,
        }


class MissionBoard:
    def __init__(self) -> None:
        self.missions: list[Mission] = []

    def add(self, goal: str, subgoals: Optional[list[str]] = None) -> Mission:
        mission = Mission(goal=goal)
        for sg in subgoals or []:
            mission.add_subgoal(sg)
        self.missions.append(mission)
        return mission

    def next_actionable(self) -> Optional[Mission]:
        # Prefer in-progress, then not-started; never completed.
        for status in (MissionStatus.IN_PROGRESS, MissionStatus.NOT_STARTED,
                       MissionStatus.STUCK):
            for mission in self.missions:
                if mission.status == status:
                    return mission
        return None

    def active(self) -> list[Mission]:
        return [m for m in self.missions if m.status != MissionStatus.COMPLETED]

    def render(self) -> str:
        if not self.missions:
            return "(no missions)"
        lines = []
        for m in self.missions:
            done, total = m.progress()
            lines.append(f"{m.status.emoji} {m.goal} [{done}/{total}]")
            for sg in m.subgoals:
                lines.append(f"    {'[x]' if sg.done else '[ ]'} {sg.text}")
        return "\n".join(lines)
