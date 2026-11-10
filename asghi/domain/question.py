"""Question class.
Matches class-diagram.puml and sequence diagram 3.
"""
from __future__ import annotations
from typing import Optional, List
from uuid import UUID

from asghi.domain.enums import ContentStatus, Difficulty, Origin, QuestionType
from asghi.domain.reviewable_content import ReviewableContent


class Question(ReviewableContent):
    def __init__(
        self,
        promptText: str,
        answers: List[str],
        correctAnswer: str,
        explanation: str,
        passageReference: str = "",
        difficulty: Difficulty = Difficulty.MEDIUM,
        type: QuestionType = QuestionType.MCQ,
        passageId: Optional[UUID] = None,
        authorId: Optional[UUID] = None,
        contentId: Optional[UUID] = None,
        status: ContentStatus = ContentStatus.PENDING_REVIEW,
        origin: Origin = Origin.HUMAN,
    ):
        super().__init__(
            contentId=contentId,
            authorId=authorId,
            status=status,
            origin=origin,
        )
        self.questionId: UUID = self.contentId
        self.type: QuestionType = type
        self.promptText: str = promptText
        self.answers: List[str] = answers
        self.correctAnswer: str = correctAnswer
        self.explanation: str = explanation
        self.passageReference: str = passageReference
        self.difficulty: Difficulty = difficulty
        self.passageId: Optional[UUID] = passageId

    def edit(
        self,
        prompt: str,
        answers: List[str],
        correctAnswer: str,
        explanation: str,
    ) -> None:
        """Edit question properties."""
        self.promptText = prompt
        self.answers = answers
        self.correctAnswer = correctAnswer
        self.explanation = explanation
