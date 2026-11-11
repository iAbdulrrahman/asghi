"""Passage class.
Matches class-diagram.puml and sequence diagrams 1, 2, 3.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any
from uuid import UUID

from asghi.domain.enums import ContentStatus, Difficulty, Level, Origin, AttributionType
from asghi.domain.reviewable_content import ReviewableContent
from asghi.domain.audio_recording import AudioRecording
from asghi.domain.question import Question


# Invention #3: 72 hours claim TTL per class diagram note
CLAIM_TTL = timedelta(hours=72)


class Passage(ReviewableContent):
    _registry: List[Passage] = []

    def __init__(
        self,
        text: str,
        level: Level,
        topic: str,
        duration: timedelta,
        passageId: Optional[UUID] = None,
        claimedBy: Optional[UUID] = None,
        claimedAt: Optional[datetime] = None,
        authorId: Optional[UUID] = None,
        status: ContentStatus = ContentStatus.DRAFT,
        origin: Optional[Origin] = None,
    ):
        super().__init__(
            contentId=passageId,
            authorId=authorId,
            status=status,
            origin=origin,
        )
        self.passageId: UUID = self.contentId
        self.text: str = text
        self.level: Level = level
        self.topic: str = topic
        self.duration: timedelta = duration
        self.claimedBy: Optional[UUID] = claimedBy
        self.claimedAt: Optional[datetime] = claimedAt
        self.audioRecordings: List[AudioRecording] = []
        self.questions: List[Question] = []

        Passage._registry.append(self)

    def isClaimExpired(self) -> bool:
        """Check whether the active claim has expired."""
        if self.claimedBy is None or self.claimedAt is None:
            return True
        now = datetime.now(timezone.utc)
        claimed_at = self.claimedAt
        if claimed_at.tzinfo is None:
            claimed_at = claimed_at.replace(tzinfo=timezone.utc)
        return (now - claimed_at) > CLAIM_TTL

    def claim(self, contributorId: UUID) -> bool:
        """Implements Sequence 1: claim cycle logic."""
        expired = self.isClaimExpired()

        # If claimed by someone else and not expired
        if self.claimedBy is not None and self.claimedBy != contributorId and not expired:
            return False

        # If already has a VERIFIED or PENDING_REVIEW recording
        has_active_recording = any(
            rec.status in (ContentStatus.VERIFIED, ContentStatus.PENDING_REVIEW)
            for rec in self.audioRecordings
        )
        if has_active_recording:
            return False

        # Free, or previous claim expired (or re-claiming own active claim)
        self.claimedBy = contributorId
        self.claimedAt = datetime.now(timezone.utc)
        self.changeStatus(ContentStatus.CLAIMED)
        return True

    def releaseClaim(self) -> None:
        """Release contributor claim on passage."""
        self.claimedBy = None
        self.claimedAt = None
        # If still in claimed status, revert to draft or verified
        if self.status == ContentStatus.CLAIMED:
            has_verified = any(r.status == ContentStatus.VERIFIED for r in self.audioRecordings)
            self.changeStatus(ContentStatus.VERIFIED if has_verified else ContentStatus.DRAFT)

    def addAudio(
        self,
        audioFile: Any,
        duration: Optional[timedelta] = None,
        attribution: AttributionType = AttributionType.SHOW_NAME,
        authorId: Optional[UUID] = None,
    ) -> AudioRecording:
        """Sequence 1 step 40: P -> AR : new(audioFile, duration, attribution)."""
        rec_duration = duration or self.duration
        rec_author = authorId or self.claimedBy or self.authorId
        recording = AudioRecording(
            audioFile=audioFile,
            duration=rec_duration,
            attribution=attribution,
            passageId=self.passageId,
            authorId=rec_author,
            status=ContentStatus.PENDING_REVIEW,
            origin=Origin.HUMAN if rec_author else Origin.AI,
        )
        self.audioRecordings.append(recording)
        # Sequence 1 step 43: claimedAt = null (clock stops, claim held until verdict)
        self.claimedAt = None
        return recording

    def addQuestion(self, question: Question) -> None:
        """Add a question to this passage."""
        question.passageId = self.passageId
        self.questions.append(question)

    def getQuestion(self, difficulty: Difficulty) -> Optional[Question]:
        """Sequence 3 step 32-34: fetch question matching target difficulty."""
        matching = [q for q in self.questions if q.difficulty == difficulty and q.status == ContentStatus.VERIFIED]
        if matching:
            return matching[0]
        # Fallback to any verified question
        verified = [q for q in self.questions if q.status == ContentStatus.VERIFIED]
        if verified:
            return verified[0]
        # If no verified yet, return any matching
        unverified_match = [q for q in self.questions if q.difficulty == difficulty]
        if unverified_match:
            return unverified_match[0]
        return self.questions[0] if self.questions else None

    @classmethod
    def browse(
        cls,
        level: Optional[Level] = None,
        topic: Optional[str] = None,
        maxDuration: Optional[timedelta] = None,
    ) -> List[Passage]:
        """Static query method to browse passages."""
        results = []
        for p in cls._registry:
            if level and p.level != level:
                continue
            if topic and topic.strip() and topic.lower() not in p.topic.lower():
                continue
            if maxDuration and p.duration > maxDuration:
                continue
            results.append(p)
        return results

    @classmethod
    def awaitingRecording(cls) -> List[Passage]:
        """Passages that need recording: no verified/pending recording and not actively claimed."""
        results = []
        for p in cls._registry:
            has_valid_rec = any(
                r.status in (ContentStatus.VERIFIED, ContentStatus.PENDING_REVIEW)
                for r in p.audioRecordings
            )
            is_active_claim = (p.claimedBy is not None) and (not p.isClaimExpired())
            if not has_valid_rec and not is_active_claim:
                results.append(p)
        return results
