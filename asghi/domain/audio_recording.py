"""AudioRecording class.
Matches class-diagram.puml and sequence diagram 1.
"""
from __future__ import annotations
from datetime import timedelta
from typing import Optional, Any
from uuid import UUID

from asghi.domain.enums import AttributionType, ContentStatus, Origin
from asghi.domain.reviewable_content import ReviewableContent


class AudioRecording(ReviewableContent):
    def __init__(
        self,
        audioFile: Any,
        duration: timedelta,
        attribution: AttributionType = AttributionType.SHOW_NAME,
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
        self.audioFile: Any = audioFile
        self.duration: timedelta = duration
        self.attribution: AttributionType = attribution
        self.passageId: Optional[UUID] = passageId
