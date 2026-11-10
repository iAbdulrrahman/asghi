"""TestSession class.
Matches class-diagram.puml and sequence diagram 3.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from asghi.domain.enums import Difficulty
from asghi.domain.passage import Passage
from asghi.domain.question import Question
from asghi.domain.question_response import QuestionResponse


# Invention #5: Scoring rules
POINTS_BY_DIFFICULTY = {
    Difficulty.EASY: 10,
    Difficulty.MEDIUM: 20,
    Difficulty.HARD: 30,
}


class TestSession:
    def __init__(
        self,
        passageId: UUID,
        learnerId: Optional[UUID] = None,
        sessionId: Optional[UUID] = None,
        startedAt: Optional[datetime] = None,
        currentDifficulty: Difficulty = Difficulty.MEDIUM,
    ):
        self.sessionId: UUID = sessionId or uuid4()
        self.passageId: UUID = passageId
        self.learnerId: Optional[UUID] = learnerId
        self.startedAt: datetime = startedAt or datetime.now(timezone.utc)
        self.finishedAt: Optional[datetime] = None
        self.questionResponses: List[QuestionResponse] = []
        self.totalScore: int = 0
        self.currentDifficulty: Difficulty = currentDifficulty
        self._currentPassage: Optional[Passage] = None
        self.lastPlaybackSpeed: float = 1.0
        self.answeredQuestionIds: List[UUID] = []

    def fetchPassage(self, passageId: UUID) -> Optional[Passage]:
        """Sequence 3 step 20-22: fetch passage text and audio."""
        for p in Passage._registry:
            if p.passageId == passageId:
                self._currentPassage = p
                return p
        return None

    def playAudio(self, playbackSpeed: float) -> None:
        """Sequence 3 step 26-27: play audio with speed adjustment."""
        self.lastPlaybackSpeed = playbackSpeed

    def nextQuestion(self) -> Optional[Question]:
        """Sequence 3 step 31-33: fetch next question from passage at current difficulty."""
        if self._currentPassage is None:
            self.fetchPassage(self.passageId)
        if not self._currentPassage:
            return None

        # Filter out questions already answered in this session
        unanswered = [
            q for q in self._currentPassage.questions
            if q.questionId not in self.answeredQuestionIds
        ]
        if not unanswered:
            return None

        # Prefer current difficulty
        matching = [q for q in unanswered if q.difficulty == self.currentDifficulty]
        if matching:
            return matching[0]
        return unanswered[0]

    def adaptDifficulty(self, isCorrect: boolean) -> None:  # Note: signature uses bool / boolean
        """Sequence 3 step 53 & Invention #4: Adaptive difficulty progression."""
        ladder = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]
        idx = ladder.index(self.currentDifficulty)
        if isCorrect:
            if idx < len(ladder) - 1:
                self.currentDifficulty = ladder[idx + 1]
        else:
            if idx > 0:
                self.currentDifficulty = ladder[idx - 1]

    def submitAnswer(self, questionId: UUID, answer: str) -> Dict[str, Any]:
        """Sequence 3 steps 41-55: submit and evaluate answer, adapt difficulty on error."""
        if self._currentPassage is None:
            self.fetchPassage(self.passageId)

        target_q: Optional[Question] = None
        if self._currentPassage:
            for q in self._currentPassage.questions:
                if q.questionId == questionId:
                    target_q = q
                    break

        qr = QuestionResponse(
            questionId=questionId,
            submittedAnswer=answer,
            question=target_q,
        )
        is_correct = qr.evaluate()
        self.questionResponses.append(qr)
        self.answeredQuestionIds.append(questionId)

        if is_correct:
            points = POINTS_BY_DIFFICULTY.get(
                target_q.difficulty if target_q else self.currentDifficulty, 10
            )
            self.totalScore += points
            self.adaptDifficulty(True)
            return {
                "isCorrect": True,
                "scoreAdded": points,
                "totalScore": self.totalScore,
                "explanation": target_q.explanation if target_q else "",
                "correctAnswer": target_q.correctAnswer if target_q else "",
            }
        else:
            self.adaptDifficulty(False)
            return {
                "isCorrect": False,
                "scoreAdded": 0,
                "totalScore": self.totalScore,
                "explanation": target_q.explanation if target_q else "",
                "correctAnswer": target_q.correctAnswer if target_q else "",
            }

    def finishSession(self) -> Dict[str, int]:
        """Sequence 3 step 61-63: finish session and return totals."""
        self.finishedAt = datetime.now(timezone.utc)
        started = self.startedAt
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        time_spent_seconds = max(1, int((self.finishedAt - started).total_seconds()))
        return {
            "totalScore": self.totalScore,
            "timeSpent": time_spent_seconds,
        }
