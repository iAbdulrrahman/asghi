"""QuestionAuthor interface.
Matches class-diagram.puml.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID

from asghi.domain.question import Question


class QuestionAuthor(ABC):
    @abstractmethod
    def authorQuestion(self, passageId: UUID, q: Question) -> Question:
        """Authors a question manually for a given passage."""
        raise NotImplementedError

    @abstractmethod
    def generateQuestions(self, passageId: UUID, count: int) -> list[Question]:
        """Generates questions via AI for a given passage."""
        raise NotImplementedError
