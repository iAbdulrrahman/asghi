"""LearnerProfile class.
Matches class-diagram.puml and sequence diagrams 3 and 5.
"""
from __future__ import annotations
from typing import Optional
from uuid import UUID

from asghi.domain.enums import UserRole
from asghi.domain.user_role_profile import UserRoleProfile
from asghi.domain.learner_progress import LearnerProgress
from asghi.domain.test_session import TestSession
from asghi.domain.reviewable_content import ReviewableContent
from asghi.domain.content_flag import ContentFlag


class LearnerProfile(UserRoleProfile):
    def __init__(
        self,
        userRoleProfileId: Optional[UUID] = None,
        progress: Optional[LearnerProgress] = None,
    ):
        super().__init__(role=UserRole.LEARNER, userRoleProfileId=userRoleProfileId)
        self.progress: LearnerProgress = progress or LearnerProgress()
        self.currentSession: Optional[TestSession] = None

    def startSession(self, passageId: UUID) -> TestSession:
        """Sequence 3 step 12-16: start new test session for passage."""
        session = TestSession(passageId=passageId)
        self.currentSession = session
        return session

    def fetchPassage(self, passageId: UUID) -> None:
        """Sequence 3 step 19-23: fetch passage text and audio through current session."""
        if self.currentSession:
            self.currentSession.fetchPassage(passageId)

    def playAudio(self, playbackSpeed: float) -> None:
        """Sequence 3 step 25-28: play audio at specified speed."""
        if self.currentSession:
            self.currentSession.playAudio(playbackSpeed)

    def submitAnswer(self, questionId: UUID, answer: str) -> bool:
        """Sequence 3 step 39-56: submit answer and evaluate."""
        if not self.currentSession:
            return False
        res = self.currentSession.submitAnswer(questionId, answer)
        return bool(res.get("isCorrect", False))

    def finishSession(self) -> None:
        """Sequence 3 step 59-69: finish session and update progress."""
        if not self.currentSession:
            return
        totals = self.currentSession.finishSession()
        self.progress.update(
            totalScore=totals.get("totalScore", 0),
            timeSpent=totals.get("timeSpent", 0),
        )
        self.currentSession = None

    def flagContent(self, content: ReviewableContent, reason: str) -> ContentFlag:
        """Sequence 5 step 12-18: report problematic content."""
        flag = ContentFlag(
            contentId=content.contentId,
            reason=reason,
            reporterId=self.userRoleProfileId,
        )
        content.flags.append(flag)
        return flag
