"""ContentFlag class.
Matches class-diagram.puml and sequence diagram 5.
"""
from __future__ import annotations
from typing import Optional
from uuid import UUID, uuid4

from asghi.domain.enums import FlagStatus


class ContentFlag:
    def __init__(
        self,
        contentId: UUID,
        reason: str,
        reporterId: Optional[UUID] = None,
        flagId: Optional[UUID] = None,
        status: FlagStatus = FlagStatus.PENDING,
    ):
        self.flagId: UUID = flagId or uuid4()
        self.contentId: UUID = contentId
        self.reporterId: Optional[UUID] = reporterId
        self.reason: str = reason
        self.status: FlagStatus = status

    def resolve(self, newState: FlagStatus) -> None:
        """Resolve content flag status."""
        self.status = newState
