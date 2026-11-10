"""QuestionResponse class.
Matches class-diagram.puml and sequence diagram 3.
"""
from __future__ import annotations
from typing import Optional
from uuid import UUID, uuid4

from asghi.domain.question import Question


class QuestionResponse:
    def __init__(
        self,
        questionId: UUID,
        submittedAnswer: str,
        question: Optional[Question] = None,
        responseId: Optional[UUID] = None,
    ):
        self.responseId: UUID = responseId or uuid4()
        self.questionId: UUID = questionId
        self.submittedAnswer: str = submittedAnswer
        self.question: Optional[Question] = question
        self.isCorrect: bool = False

    def evaluate(self) -> bool:
        """Evaluate submitted answer against the question's correct answer."""
        if self.question is None:
            return False
        # Normalize whitespace and case
        submitted = (self.submittedAnswer or "").strip().lower()
        expected = (self.question.correctAnswer or "").strip().lower()
        self.isCorrect = (submitted == expected)
        return self.isCorrect
