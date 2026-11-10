"""ReviewAssignment class.
Matches class-diagram.puml and sequence diagram 2.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from asghi.domain.review_feedback import ReviewFeedback


class ReviewAssignment:
    def __init__(
        self,
        reviewerId: UUID,
        contentId: UUID,
        isSpecialistReview: bool = False,
        reviewId: Optional[UUID] = None,
        createdAt: Optional[datetime] = None,
    ):
        self.reviewId: UUID = reviewId or uuid4()
        self.reviewerId: UUID = reviewerId
        self.contentId: UUID = contentId
        self.createdAt: datetime = createdAt or datetime.now(timezone.utc)
        self.isSpecialistReview: bool = isSpecialistReview
        self.isApproved: Optional[bool] = None
        self.reason: Optional[str] = None
        self.feedback: Optional[ReviewFeedback] = None

    def recordDecision(
        self,
        feedback: ReviewFeedback,
        isApproved: bool,
        reason: str,
    ) -> None:
        """Records reviewer decision and feedback."""
        self.feedback = feedback
        self.isApproved = isApproved
        self.reason = reason
