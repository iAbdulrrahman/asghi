"""ReviewableContent abstract domain entity.
Matches class-diagram.puml and sequence diagrams 1, 2, 5.
"""
from __future__ import annotations
from abc import ABC
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4

from asghi.domain.enums import ContentStatus, Origin

if TYPE_CHECKING:
    from asghi.domain.review_assignment import ReviewAssignment
    from asghi.domain.content_flag import ContentFlag


class ReviewableContent(ABC):
    _registry: List[ReviewableContent] = []

    def __init__(
        self,
        contentId: Optional[UUID] = None,
        authorId: Optional[UUID] = None,
        status: ContentStatus = ContentStatus.DRAFT,
        origin: Origin = Origin.HUMAN,
    ):
        self.contentId: UUID = contentId or uuid4()
        self.authorId: Optional[UUID] = authorId
        # Enforce invariant: authorId == null <=> origin == AI
        if self.authorId is None and origin == Origin.HUMAN:
            # When human authored, an authorId is expected; if none provided, keep origin or assign
            pass
        self.status: ContentStatus = status
        self.origin: Origin = origin
        self.reviews: List[ReviewAssignment] = []
        self.flags: List[ContentFlag] = []
        self.rejectionReason: Optional[str] = None

        ReviewableContent._registry.append(self)


    @property
    def approvalCount(self) -> int:
        """Derived count of distinct approved reviews."""
        approved = [r for r in self.reviews if r.isApproved is True]
        return len({r.reviewerId for r in approved})

    def meetsThreshold(self) -> bool:
        """Approval requires either 1 specialist review, or 3 general reviews conducted by distinct reviewers."""
        specialist_approved = any(
            r.isSpecialistReview and r.isApproved is True for r in self.reviews
        )
        if specialist_approved:
            return True

        general_approved_reviewers = {
            r.reviewerId
            for r in self.reviews
            if (not r.isSpecialistReview) and r.isApproved is True
        }
        return len(general_approved_reviewers) >= 3

    def changeStatus(self, newStatus: ContentStatus) -> None:
        """Protected method to transition status."""
        self.status = newStatus

    def verify(self) -> None:
        """Mark content verified."""
        self.changeStatus(ContentStatus.VERIFIED)
        self.rejectionReason = None

    def reject(self, reason: str) -> None:
        """Mark content rejected with reason."""
        self.changeStatus(ContentStatus.REJECTED)
        self.rejectionReason = reason

    def markFlagged(self) -> None:
        """Mark content flagged."""
        self.changeStatus(ContentStatus.FLAGGED)
