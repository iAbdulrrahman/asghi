"""LearnerProgress class.
Matches class-diagram.puml and sequence diagram 3.
"""
from __future__ import annotations


class LearnerProgress:
    def __init__(
        self,
        totalScore: int = 0,
        totalTimeSpent: int = 0,
        currentStreakDays: int = 1,
    ):
        self.totalScore: int = totalScore
        self.totalTimeSpent: int = totalTimeSpent
        self.currentStreakDays: int = currentStreakDays

    def update(self, totalScore: int, timeSpent: int) -> None:
        """Sequence 3 step 65: update progress totals from finished session."""
        self.totalScore += totalScore
        self.totalTimeSpent += timeSpent
