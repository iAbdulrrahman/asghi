"""ReviewerProfile class.
Matches class-diagram.puml and sequence diagram 2.
"""
from __future__ import annotations
from typing import Optional, List, Any
from uuid import UUID

from asghi.domain.enums import UserRole, ContentStatus
from asghi.domain.user_role_profile import UserRoleProfile
from asghi.domain.reputation import Reputation
from asghi.domain.review_assignment import ReviewAssignment
from asghi.domain.review_feedback import ReviewFeedback
from asghi.domain.audio_recording import AudioRecording
from asghi.domain.passage import Passage
from asghi.domain.question import Question
from asghi.domain.question_author import QuestionAuthor
from asghi.domain.ai_engine import AIEngine
from asghi.domain.reviewable_content import ReviewableContent


class ReviewerProfile(UserRoleProfile, QuestionAuthor):
    def __init__(
        self,
        userRoleProfileId: Optional[UUID] = None,
        isSpecialist: bool = False,
        reputation: Optional[Reputation] = None,
    ):
        super().__init__(role=UserRole.REVIEWER, userRoleProfileId=userRoleProfileId)
        self.isSpecialist: bool = isSpecialist
        self.reputation: Reputation = reputation or Reputation()
        self.assignments: List[ReviewAssignment] = []

    def pendingRecordings(self) -> List[AudioRecording]:
        """Sequence 2 & Req 5.1: List pending audio recordings across passages."""
        pending: List[AudioRecording] = []
        for p in Passage._registry:
            for rec in p.audioRecordings:
                if rec.status == ContentStatus.PENDING_REVIEW:
                    pending.append(rec)
        return pending

    def assignReview(self, contentId: UUID) -> ReviewAssignment:
        """Sequence 2 steps 15-24: Assign review, preventing author self-review."""
        # Find content
        content: Optional[ReviewableContent] = None
        for p in Passage._registry:
            if p.contentId == contentId:
                content = p
                break
            for rec in p.audioRecordings:
                if rec.contentId == contentId:
                    content = rec
                    break
            for q in p.questions:
                if q.contentId == contentId:
                    content = q
                    break

        if content and content.authorId == self.userRoleProfileId:
            raise PermissionError("Reviewer cannot review their own submission (Sequence 2 break / Req 5.3)")

        assignment = ReviewAssignment(
            reviewerId=self.userRoleProfileId,
            contentId=contentId,
            isSpecialistReview=self.isSpecialist,
        )
        self.assignments.append(assignment)
        if content:
            content.reviews.append(assignment)
        return assignment

    def getAudioFile(self, assignment: ReviewAssignment) -> Any:
        """Sequence 2 step 26-29: fetch audio file for assignment."""
        for p in Passage._registry:
            for rec in p.audioRecordings:
                if rec.contentId == assignment.contentId:
                    return rec.audioFile
        return None

    def createFeedback(
        self,
        isFusha: bool,
        dialectFree: bool = True,
        audioQuality: int = 5,
        feedback: str = "",
    ) -> ReviewFeedback:
        """Sequence 2 step 31-35: create review feedback object."""
        return ReviewFeedback(
            isFusha=isFusha,
            dialectFree=dialectFree,
            audioQuality=audioQuality,
            feedback=feedback,
        )

    def submitDecision(
        self,
        assignment: ReviewAssignment,
        feedback: ReviewFeedback,
        isApproved: bool,
        reason: str = "",
    ) -> None:
        """Sequence 2 step 37-78: submit decision and apply verification threshold / release claim."""
        # Criteria check: if not Fusha or dialect present, approval must be false (Seq 2 step 37)
        effective_approval = isApproved
        if (not feedback.isFusha) or (feedback.dialectFree is False):
            effective_approval = False
            if not reason:
                reason = "Rejected: recording must be in Fusha and dialect-free (Req 5.5)"

        assignment.recordDecision(feedback, effective_approval, reason)

        # Locate content and passage
        content: Optional[ReviewableContent] = None
        parent_passage: Optional[Passage] = None
        for p in Passage._registry:
            if p.contentId == assignment.contentId:
                content = p
                parent_passage = p
                break
            for rec in p.audioRecordings:
                if rec.contentId == assignment.contentId:
                    content = rec
                    parent_passage = p
                    break
            for q in p.questions:
                if q.contentId == assignment.contentId:
                    content = q
                    parent_passage = p
                    break

        if not content:
            return

        # Check threshold
        if content.meetsThreshold():
            content.verify()
            if parent_passage:
                parent_passage.releaseClaim()
        else:
            # Check for reviewer disagreement
            verdicts = [r.isApproved for r in content.reviews if r.isApproved is not None]
            has_approved = True in verdicts
            has_rejected = False in verdicts
            if has_approved and has_rejected:
                # Escalated to Admin dispute per Sequence 2 step 56-57
                pass
            elif not effective_approval and (assignment.isSpecialistReview or len([v for v in verdicts if v is False]) >= 2):
                content.reject(reason)
                if parent_passage:
                    parent_passage.releaseClaim()

        # Update reviewer reputation
        self.reputation.recordSubmissionResult(True)

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
