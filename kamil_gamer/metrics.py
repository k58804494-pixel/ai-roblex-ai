"""Self-improvement metrics.

A running scoreboard the agent uses to find its own weaknesses: success rate,
deaths, time spent stuck, quest completion speed, action accuracy. The
orchestrator updates these as it plays; the dashboard/self-reflection step reads
them to decide what to improve.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Metrics:
    cycles: int = 0
    actions: int = 0
    successful_actions: int = 0
    missions_completed: int = 0
    missions_failed: int = 0
    deaths: int = 0
    recoveries: int = 0
    seconds_stuck: float = 0.0
    quest_completion_seconds: list[float] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return self.successful_actions / self.actions if self.actions else 0.0

    @property
    def mission_completion_rate(self) -> float:
        total = self.missions_completed + self.missions_failed
        return self.missions_completed / total if total else 0.0

    @property
    def avg_quest_seconds(self) -> float:
        xs = self.quest_completion_seconds
        return sum(xs) / len(xs) if xs else 0.0

    def record_action(self, success: bool) -> None:
        self.actions += 1
        if success:
            self.successful_actions += 1

    def weaknesses(self) -> list[str]:
        """Heuristically surface what the agent is worst at."""

        issues: list[str] = []
        if self.actions and self.success_rate < 0.5:
            issues.append("low action success rate")
        if self.recoveries and self.recoveries > max(1, self.cycles // 10):
            issues.append("gets stuck often")
        if self.deaths and self.deaths > self.missions_completed:
            issues.append("dies more than it completes")
        if self.mission_completion_rate < 0.5 and (
            self.missions_completed + self.missions_failed
        ):
            issues.append("low mission completion rate")
        return issues

    def render(self) -> str:
        return (
            f"success_rate={self.success_rate:.0%} "
            f"missions={self.missions_completed}✅/{self.missions_failed}❌ "
            f"deaths={self.deaths} recoveries={self.recoveries} "
            f"stuck={self.seconds_stuck:.0f}s"
        )
