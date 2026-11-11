"""Test suite for domain model and 5 authoritative sequence diagrams.
"""
from datetime import timedelta
import pytest
from uuid import uuid4

from asghi.domain import (
    UserRole,
    Difficulty,
    Level,
    Origin,
    AttributionType,
    QuestionType,
    ContentStatus,
    FlagStatus,
    User,
    LearnerProfile,
    ContributorProfile,
    ReviewerProfile,
    AdminProfile,
    Passage,
    Question,
    ReviewFeedback,
    AIEngine,
)


@pytest.fixture(autouse=True)
def reset_registries():
    User._registry.clear()
    Passage._registry.clear()
    yield
    User._registry.clear()
    Passage._registry.clear()


def test_sequence_4_registration_and_roles():
    """Sequence 4: User Registration and Role Granting."""
    user = User()
    user.register("learner@asghi.org", "Pass1234")
    assert user.email == "learner@asghi.org"
    assert user.login("learner@asghi.org", "Pass1234") is True
    assert user.login("learner@asghi.org", "WrongPass") is False

    user.completeProfile("أحمد المتعلم", Level.B1, UserRole.LEARNER)
    assert user.displayName == "أحمد المتعلم"
    assert user.arabicLevel == Level.B1
    assert len(user.userProfiles) == 1
    assert isinstance(user.userProfiles[0], LearnerProfile)

    # Test adding other roles
    cp = user.addRole(UserRole.CONTRIBUTOR)
    assert isinstance(cp, ContributorProfile)
    rp = user.addRole(UserRole.REVIEWER)
    assert isinstance(rp, ReviewerProfile)
    ap = user.addRole(UserRole.ADMIN)
    assert isinstance(ap, AdminProfile)
    assert len(user.userProfiles) == 4


def test_sequence_1_claim_cycle():
    """Sequence 1: Claim and recording submission."""
    passage = Passage(
        text="نَصٌّ تَجْرِيبِيٌّ لِاخْتِبَارِ الِاسْتِمَاعِ بِالفُصْحَى.",
        level=Level.B2,
        topic="الثقافة",
        duration=timedelta(seconds=90),
    )
    contributor = ContributorProfile()

    # Opt: reading passage first and toggle tashkeel
    assert contributor.showTashkeel is True
    contributor.toggleTashkeel()
    assert contributor.showTashkeel is False
    contributor.toggleTashkeel()
    assert contributor.showTashkeel is True

    # 1. Claim passage
    accepted = contributor.claim(passage.passageId)
    assert accepted is True
    assert passage.status == ContentStatus.CLAIMED
    assert passage.claimedBy == contributor.userRoleProfileId
    assert passage.claimedAt is not None

    # 2. Another contributor cannot claim actively claimed passage
    contributor2 = ContributorProfile()
    assert contributor2.claim(passage.passageId) is False

    # 3. Contributor uploads audio recording
    contributor.recordOrUploadAudio(
        passageId=passage.passageId,
        audioFile="audio_sample_01.mp3",
        attribution=AttributionType.SHOW_NAME,
    )
    assert len(passage.audioRecordings) == 1
    rec = passage.audioRecordings[0]
    assert rec.status == ContentStatus.PENDING_REVIEW
    assert rec.attribution == AttributionType.SHOW_NAME
    # Step 43: claimedAt is set to null, clock stops
    assert passage.claimedAt is None


def test_sequence_2_review_verdict_specialist():
    """Sequence 2: Review and verification by specialist reviewer."""
    passage = Passage(
        text="نص فصيح للمراجعة.",
        level=Level.A2,
        topic="العلوم",
        duration=timedelta(seconds=120),
    )
    contributor = ContributorProfile()
    contributor.claim(passage.passageId)
    contributor.recordOrUploadAudio(passage.passageId, "recording.mp3")
    rec = passage.audioRecordings[0]

    # Reviewer cannot review own submission (break branch)
    author_reviewer = ReviewerProfile(userRoleProfileId=rec.authorId)
    with pytest.raises(PermissionError):
        author_reviewer.assignReview(rec.contentId)

    # Specialist reviewer
    specialist = ReviewerProfile(isSpecialist=True)
    assignment = specialist.assignReview(rec.contentId)
    assert assignment.isSpecialistReview is True

    audio_file = specialist.getAudioFile(assignment)
    assert audio_file == "recording.mp3"

    feedback = specialist.createFeedback(isFusha=True, dialectFree=True, audioQuality=5)
    specialist.submitDecision(assignment, feedback, isApproved=True, reason="ممتاز وفصيح")

    # Threshold reached: 1 specialist approval
    assert rec.status == ContentStatus.VERIFIED
    # Claim released
    assert passage.claimedBy is None


def test_sequence_2_review_general_threshold_and_dispute():
    """Sequence 2: Review with 3 general reviewers vs dispute escalation."""
    passage = Passage(
        text="نص لاختبار المراجعين العامين.",
        level=Level.C1,
        topic="الأدب",
        duration=timedelta(seconds=110),
    )
    contributor = ContributorProfile()
    contributor.claim(passage.passageId)
    contributor.recordOrUploadAudio(passage.passageId, "general_test.mp3")
    rec = passage.audioRecordings[0]

    # Reviewer 1 approves
    rev1 = ReviewerProfile(isSpecialist=False)
    as1 = rev1.assignReview(rec.contentId)
    fb1 = rev1.createFeedback(isFusha=True, dialectFree=True, audioQuality=4)
    rev1.submitDecision(as1, fb1, isApproved=True)
    assert rec.status == ContentStatus.PENDING_REVIEW  # Needs 3

    # Reviewer 2 approves
    rev2 = ReviewerProfile(isSpecialist=False)
    as2 = rev2.assignReview(rec.contentId)
    fb2 = rev2.createFeedback(isFusha=True, dialectFree=True, audioQuality=4)
    rev2.submitDecision(as2, fb2, isApproved=True)
    assert rec.status == ContentStatus.PENDING_REVIEW  # Needs 3

    # Reviewer 3 approves -> 3 distinct general reviewers reach threshold
    rev3 = ReviewerProfile(isSpecialist=False)
    as3 = rev3.assignReview(rec.contentId)
    fb3 = rev3.createFeedback(isFusha=True, dialectFree=True, audioQuality=5)
    rev3.submitDecision(as3, fb3, isApproved=True)
    assert rec.status == ContentStatus.VERIFIED

    # Test dispute escalation to Admin
    passage2 = Passage(
        text="نص متنازع عليه.",
        level=Level.B1,
        topic="التاريخ",
        duration=timedelta(seconds=80),
    )
    contributor.claim(passage2.passageId)
    contributor.recordOrUploadAudio(passage2.passageId, "dispute.mp3")
    rec2 = passage2.audioRecordings[0]

    r_approve = ReviewerProfile(isSpecialist=False)
    as_app = r_approve.assignReview(rec2.contentId)
    r_approve.submitDecision(as_app, r_approve.createFeedback(True, True), True)

    r_reject = ReviewerProfile(isSpecialist=False)
    as_rej = r_reject.assignReview(rec2.contentId)
    r_reject.submitDecision(as_rej, r_reject.createFeedback(False, False), False, "لهجة عامية")

    # Conflict -> Admin resolves dispute
    admin = AdminProfile()
    admin.resolveDispute(rec2.contentId, "VERIFY")
    assert rec2.status == ContentStatus.VERIFIED


def test_sequence_3_learner_session():
    """Sequence 3: Learner practice session, audio playback, answer submission, difficulty adaptation."""
    passage = Passage(
        text="نص للاستماع والممارسة.",
        level=Level.A1,
        topic="التعارف",
        duration=timedelta(seconds=60),
        status=ContentStatus.VERIFIED,
    )
    # Add verified questions across difficulties
    q_easy = Question(
        promptText="سؤال سهل",
        answers=["نعم", "لا"],
        correctAnswer="نعم",
        explanation="التوضيح للسهل",
        difficulty=Difficulty.EASY,
        status=ContentStatus.VERIFIED,
    )
    q_medium = Question(
        promptText="سؤال متوسط",
        answers=["أ", "ب", "ج"],
        correctAnswer="أ",
        explanation="التوضيح للمتوسط",
        difficulty=Difficulty.MEDIUM,
        status=ContentStatus.VERIFIED,
    )
    q_hard = Question(
        promptText="سؤال صعب",
        answers=["1", "2", "3", "4"],
        correctAnswer="1",
        explanation="التوضيح للصعب",
        difficulty=Difficulty.HARD,
        status=ContentStatus.VERIFIED,
    )
    passage.addQuestion(q_easy)
    passage.addQuestion(q_medium)
    passage.addQuestion(q_hard)

    learner = LearnerProfile()
    session = learner.startSession(passage.passageId)
    assert learner.currentSession == session

    learner.fetchPassage(passage.passageId)
    learner.playAudio(1.25)
    assert session.lastPlaybackSpeed == 1.25

    # Question 1 (starts at MEDIUM)
    q1 = session.nextQuestion()
    assert q1 is not None
    assert q1.difficulty == Difficulty.MEDIUM

    # Submit correct answer
    is_correct = learner.submitAnswer(q1.questionId, "أ")
    assert is_correct is True
    assert session.totalScore == 20
    assert session.currentDifficulty == Difficulty.HARD  # Adapted up to HARD

    # Question 2 (at HARD)
    q2 = session.nextQuestion()
    assert q2 is not None
    assert q2.difficulty == Difficulty.HARD

    # Submit incorrect answer
    is_correct_wrong = learner.submitAnswer(q2.questionId, "4")
    assert is_correct_wrong is False
    assert session.currentDifficulty == Difficulty.MEDIUM  # Adapted down to MEDIUM

    # Finish session
    learner.finishSession()
    assert learner.currentSession is None
    assert learner.progress.totalScore == 20
    assert learner.progress.totalTimeSpent > 0


def test_sequence_5_flagging():
    """Sequence 5: Content Flagging and Moderation."""
    passage = Passage(
        text="محتوى مشكوك فيه.",
        level=Level.B1,
        topic="عام",
        duration=timedelta(seconds=70),
    )
    learner = LearnerProfile()
    flag = learner.flagContent(passage, "صوت غير واضح وكلمات غير مفهومة")
    assert flag.status == FlagStatus.PENDING
    assert len(passage.flags) == 1

    admin = AdminProfile()
    # Resolve flag with ACTION_TAKEN -> content status becomes FLAGGED
    admin.resolveFlag(flag.flagId, FlagStatus.ACTION_TAKEN)
    assert flag.status == FlagStatus.ACTION_TAKEN
    assert passage.status == ContentStatus.FLAGGED


def test_ai_engine_generation():
    """Requirements 3.1, 3.2, 3.3, 7.2: AI Content Generation."""
    passage = Passage(
        text="",
        level=Level.B2,
        topic="التكنولوجيا",
        duration=timedelta(seconds=100),
    )
    engine = AIEngine()
    text = engine.generatePassageText(passage.passageId)
    assert len(text) > 0
    assert passage.origin == Origin.AI
    assert passage.status == ContentStatus.DRAFT

    questions = engine.generateQuestions(passage.passageId, 3)
    assert len(questions) == 3
    difficulties = {q.difficulty for q in questions}
    assert Difficulty.EASY in difficulties
    assert Difficulty.MEDIUM in difficulties
    assert Difficulty.HARD in difficulties
    for q in questions:
        assert q.origin == Origin.AI
        assert q.status == ContentStatus.DRAFT
        assert q.authorId is None  # Invariant: authorId == null <=> origin == AI
