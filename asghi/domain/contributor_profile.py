"""ContributorProfile class.
Matches class-diagram.puml and sequence diagram 1.
"""
from __future__ import annotations
from typing import Optional, List, Any
from uuid import UUID

from asghi.domain.enums import UserRole, AttributionType
from asghi.domain.user_role_profile import UserRoleProfile
from asghi.domain.reputation import Reputation
from asghi.domain.passage import Passage
from asghi.domain.question import Question
from asghi.domain.question_author import QuestionAuthor
from asghi.domain.ai_engine import AIEngine


class ContributorProfile(UserRoleProfile, QuestionAuthor):
    def __init__(
        self,
        userRoleProfileId: Optional[UUID] = None,
        reputation: Optional[Reputation] = None,
    ):
        super().__init__(role=UserRole.CONTRIBUTOR, userRoleProfileId=userRoleProfileId)
        self.reputation: Reputation = reputation or Reputation()
        self.showTashkeel: bool = True
        self.creditsEarned: int = 0

    def claim(self, passageId: UUID) -> bool:
        """Sequence 1 step 10-27: Contributor claims passage for recording."""
        for p in Passage._registry:
            if p.passageId == passageId:
                return p.claim(self.userRoleProfileId)
        return False

    def recordOrUploadAudio(
        self,
        passageId: UUID,
        audioFile: Any,
        attribution: AttributionType = AttributionType.SHOW_NAME,
    ) -> None:
        """Sequence 1 step 36-46: Contributor uploads/records audio for claimed passage."""
        for p in Passage._registry:
            if p.passageId == passageId:
                p.addAudio(
                    audioFile=audioFile,
                    attribution=attribution,
                    authorId=self.userRoleProfileId,
                )
                break

    def toggleTashkeel(self) -> None:
        """Sequence 1 step 31-33 & Req 4.3: Toggle diacritic visibility."""
        self.showTashkeel = not self.showTashkeel

    def authorQuestion(self, passageId: UUID, q: Question) -> Question:
        """QuestionAuthor implementation: manual question authoring."""
        q.passageId = passageId
        q.authorId = self.userRoleProfileId
        for p in Passage._registry:
            if p.passageId == passageId:
                p.addQuestion(q)
                break
        return q

    def generateQuestions(self, passageId: UUID, count: int) -> List[Question]:
        """QuestionAuthor implementation: trigger AI generator."""
        engine = AIEngine()
        return engine.generateQuestions(passageId, count)
