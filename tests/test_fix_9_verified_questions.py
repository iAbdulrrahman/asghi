import uuid
from datetime import timedelta
from asghi.domain.passage import Passage
from asghi.domain.question import Question
from asghi.domain.enums import ContentStatus, Difficulty, Level


def test_unverified_question_never_served():
    """Defect 4 / Item 9 / Req 7.3: Passage.getQuestion() must return VERIFIED questions only.

    Tier fallback must stay strictly inside VERIFIED.
    If no VERIFIED questions exist, it must return None, never falling back
    to DRAFT or PENDING_REVIEW questions.
    """
    p = Passage(
        passageId=uuid.uuid4(),
        text="نص اختباري للتأكد من عدم تقديم أي سؤال غير معتمد",
        level=Level.B1,
        topic="General",
        duration=timedelta(seconds=45),
        status=ContentStatus.VERIFIED,
    )

    # Add questions with DRAFT and PENDING_REVIEW status matching the requested difficulty
    draft_q = Question(
        contentId=uuid.uuid4(),
        passageId=p.passageId,
        promptText="ما هي الفكرة الأساسية؟ (مسودة)",
        answers=["أ", "ب", "ج", "د"],
        correctAnswer="أ",
        explanation="شرح",
        difficulty=Difficulty.MEDIUM,
        status=ContentStatus.DRAFT,
    )
    pending_q = Question(
        contentId=uuid.uuid4(),
        passageId=p.passageId,
        promptText="ما هو الهدف؟ (قيد المراجعة)",
        answers=["أ", "ب", "ج", "د"],
        correctAnswer="ب",
        explanation="شرح",
        difficulty=Difficulty.MEDIUM,
        status=ContentStatus.PENDING_REVIEW,
    )
    p.addQuestion(draft_q)
    p.addQuestion(pending_q)

    # On master, getQuestion returns draft_q or pending_q because it falls back to unverified
    served_q = p.getQuestion(Difficulty.MEDIUM)
    assert served_q is None, f"Expected None for unverified questions, but got {served_q}"

    # Now add a VERIFIED question with a DIFFERENT difficulty (e.g. EASY)
    verified_easy = Question(
        contentId=uuid.uuid4(),
        passageId=p.passageId,
        promptText="سؤال معتمد بدرجة سهلة",
        answers=["1", "2", "3", "4"],
        correctAnswer="3",
        explanation="شرح",
        difficulty=Difficulty.EASY,
        status=ContentStatus.VERIFIED,
    )
    p.addQuestion(verified_easy)

    # When requesting MEDIUM, fallback must return the VERIFIED question, NOT the unverified MEDIUM questions!
    fallback_q = p.getQuestion(Difficulty.MEDIUM)
    assert fallback_q is not None
    assert fallback_q.questionId == verified_easy.questionId
    assert fallback_q.status == ContentStatus.VERIFIED
