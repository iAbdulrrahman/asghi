"""Reputation class.
Matches class-diagram.puml and Invention #6.
"""
from __future__ import annotations


class Reputation:
    def __init__(
        self,
        score: int = 100,
        approvalRate: float = 1.0,
        totalSubmissions: int = 0,
    ):
        self.score: int = score
        self.approvalRate: float = approvalRate
        self.totalSubmissions: int = totalSubmissions
        self.approvedCount: int = 0
        self.rejectedCount: int = 0

    def recordSubmissionResult(self, isApproved: bool) -> None:
        """Invention #6: Record submission outcome and recalculate reputation."""
        self.totalSubmissions += 1
        if isApproved:
            self.approvedCount += 1
            self.score += 10
        else:
            self.rejectedCount += 1
            self.score = max(0, self.score - 5)

        if self.totalSubmissions > 0:
            self.approvalRate = round(self.approvedCount / self.totalSubmissions, 2)
