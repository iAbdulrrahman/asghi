import uuid
from datetime import datetime, timezone, timedelta
from asghi.domain.passage import Passage
from asghi.domain.audio_recording import AudioRecording
from asghi.domain.enums import ContentStatus, Level


def test_release_claim_transitions_claimed_to_draft_only():
    """Defect 5 / Item 8: releaseClaim() must transition CLAIMED to DRAFT only,

    never inventing a CLAIMED -> VERIFIED transition even if the passage has
    verified audio recordings attached.
    """
    contributor_id = uuid.uuid4()
    p = Passage(
        passageId=uuid.uuid4(),
        text="نص تدريبي للتأكد من حالة الإفراج عن الحجز",
        level=Level.B1,
        topic="General",
        duration=timedelta(seconds=60),
        status=ContentStatus.DRAFT,
    )
    rec = AudioRecording(
        contentId=uuid.uuid4(),
        passageId=p.passageId,
        audioFile="/audio/test.mp3",
        duration=timedelta(seconds=60),
        status=ContentStatus.VERIFIED,
    )
    p.audioRecordings.append(rec)

    # Claim the passage
    p.status = ContentStatus.CLAIMED
    p.claimedBy = contributor_id
    p.claimedAt = datetime.now(timezone.utc)

    # Calling releaseClaim must set status to DRAFT, NOT VERIFIED
    p.releaseClaim()

    assert p.claimedBy is None
    assert p.claimedAt is None
    assert p.status == ContentStatus.DRAFT, f"Expected DRAFT but got {p.status}"
