"""AdminProfile class.
Matches class-diagram.puml and sequence diagrams 2 and 5.
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from uuid import UUID

from asghi.domain.enums import UserRole, FlagStatus, ContentStatus
from asghi.domain.user_role_profile import UserRoleProfile
from asghi.domain.passage import Passage
from asghi.domain.question import Question
from asghi.domain.question_author import QuestionAuthor
from asghi.domain.ai_engine import AIEngine
from asghi.domain.reviewable_content import ReviewableContent
from asghi.domain.content_flag import ContentFlag


class AdminProfile(UserRoleProfile, QuestionAuthor):
    def __init__(
        self,
        userRoleProfileId: Optional[UUID] = None,
    ):
        super().__init__(role=UserRole.ADMIN, userRoleProfileId=userRoleProfileId)

    def assignSpecialistStatus(self, reviewerId: UUID) -> None:
        """Assign specialist reviewer status."""
        from asghi.domain.user import User
        for u in User._registry:
            for prof in u.userProfiles:
                if prof.userRoleProfileId == reviewerId and prof.role == UserRole.REVIEWER:
                    prof.isSpecialist = True  # type: ignore

    def resolveDispute(self, contentId: UUID, action: str) -> None:
        """Sequence 2 steps 58-61: resolve reviewer dispute by verifying or rejecting."""
        content: Optional[ReviewableContent] = None
        parent_passage: Optional[Passage] = None
        for p in Passage._registry:
            if p.contentId == contentId:
                content = p
                parent_passage = p
                break
            for rec in p.audioRecordings:
                if rec.contentId == contentId:
                    content = rec
                    parent_passage = p
                    break
            for q in p.questions:
                if q.contentId == contentId:
                    content = q
                    parent_passage = p
                    break

        if not content:
            return

        if action.upper() == "VERIFY":
            content.verify()
        else:
            content.reject(f"Admin dispute resolution: {action}")

        if parent_passage:
            parent_passage.releaseClaim()

    def resolveFlag(self, flagId: UUID, newState: FlagStatus) -> None:
        """Sequence 5 steps 21-36: resolve content flag."""
        target_flag: Optional[ContentFlag] = None
        target_content: Optional[ReviewableContent] = None

        for p in Passage._registry:
            for f in p.flags:
                if f.flagId == flagId:
                    target_flag = f
                    target_content = p
                    break
            if target_flag:
                break
            for rec in p.audioRecordings:
                for f in rec.flags:
                    if f.flagId == flagId:
                        target_flag = f
                        target_content = rec
                        break
                if target_flag:
                    break
            if target_flag:
                break
            for q in p.questions:
                for f in q.flags:
                    if f.flagId == flagId:
                        target_flag = f
                        target_content = q
                        break
                if target_flag:
                    break
            if target_flag:
                break

        if target_flag:
            target_flag.resolve(newState)
            if newState == FlagStatus.ACTION_TAKEN and target_content:
                target_content.markFlagged()

    def manageUser(self, userId: UUID, action: str) -> None:
        """Manage user status (e.g. suspend, activate, reset)."""
        from asghi.domain.user import User
        for u in User._registry:
            if u.userId == userId:
                u.status = action
                break

    def triggerAIGeneration(self, passageId: UUID) -> Dict[str, Any]:
        """Requirements 3.1 & 3.2: trigger AI generation for passage and questions."""
        engine = AIEngine()
        text = engine.generatePassageText(passageId)
        questions = engine.generateQuestions(passageId, 3)
        return {
            "passageId": passageId,
            "text": text,
            "questionsCount": len(questions),
        }

    def generateReport(self, period: str) -> Dict[str, Any]:
        """Invention #11: generate admin reporting summary."""
        from asghi.domain.user import User
        total_users = len(User._registry)
        total_passages = len(Passage._registry)
        verified_passages = sum(1 for p in Passage._registry if p.status == ContentStatus.VERIFIED)
        pending_recordings = sum(
            1 for p in Passage._registry
            for r in p.audioRecordings
            if r.status == ContentStatus.PENDING_REVIEW
        )
        total_flags = sum(
            len(p.flags) + sum(len(r.flags) for r in p.audioRecordings) + sum(len(q.flags) for q in p.questions)
            for p in Passage._registry
        )

        return {
            "period": period,
            "totalUsers": total_users,
            "totalPassages": total_passages,
            "verifiedPassages": verified_passages,
            "pendingRecordings": pending_recordings,
            "totalFlags": total_flags,
            "disputesCount": 0,
        }

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
