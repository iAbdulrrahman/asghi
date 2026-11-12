import logging
from typing import Optional, Dict
logger = logging.getLogger(__name__)
"""Database and domain seed script for اصغِ (Asghi).
Seeds sample passages, questions across all difficulties, and users for all 4 roles.
"""
import os
from datetime import timedelta
from uuid import uuid4

from asghi.domain.enums import (
    UserRole,
    Difficulty,
    Level,
    Origin,
    AttributionType,
    QuestionType,
    ContentStatus,
)
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.domain.question import Question
from asghi.domain.audio_recording import AudioRecording
from asghi.repository import Repository

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "audio")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def write_sample_audio(path: str, seconds: int = 90, rate: int = 16000) -> None:
    """Write a real, decodable mono WAV so seeded passages are actually playable.

    A placeholder tone is enough for the demo: the point is that the file is valid
    audio (ExoPlayer/just_audio can decode it), not that it sounds like a person.
    """
    import math
    import struct
    import wave

    frames = bytearray()
    for n in range(rate * seconds):
        # soft 440 Hz tone at ~9% amplitude, faded in/out over the first and last second
        envelope = 1.0
        if n < rate:
            envelope = n / rate
        elif n > rate * (seconds - 1):
            envelope = max(0.0, (rate * seconds - n) / rate)
        frames += struct.pack("<h", int(3000 * envelope * math.sin(2 * math.pi * 440 * n / rate)))

    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))


def seed_database(db_path: str = "asghi.db", password_overrides: Optional[Dict[str, str]] = None):
    repo = Repository(db_path=db_path)

    # Resolve passwords with env var and per-role overrides
    env_default_pass = os.environ.get("ASGHI_SEED_PASSWORD")
    current_env = os.environ.get("ENVIRONMENT", "development").lower()

    if not env_default_pass and not password_overrides and current_env != "development":
        logger.warning(
            "SECURITY WARNING: Seeding default credentials into non-development environment (%s)! "
            "Please configure ASGHI_SEED_PASSWORD or rotate credentials immediately.",
            current_env,
        )

    def resolve_password(identifier: str, role_name: str, default_pass: str) -> str:
        if password_overrides:
            if identifier in password_overrides:
                return password_overrides[identifier]
            if role_name in password_overrides:
                return password_overrides[role_name]
        if env_default_pass:
            return env_default_pass
        return default_pass

    admin_pass = resolve_password("admin@asghi.org", "admin", "AdminPass123!")
    reviewer_pass = resolve_password("reviewer@asghi.org", "reviewer", "ReviewerPass123!")
    reviewer2_pass = resolve_password("reviewer2@asghi.org", "reviewer", "ReviewerPass123!")
    contributor_pass = resolve_password("contributor@asghi.org", "contributor", "ContributorPass123!")
    learner_pass = resolve_password("learner@asghi.org", "learner", "LearnerPass123!")

    # Clear current registries
    User._registry.clear()
    Passage._registry.clear()

    # 1. Create a real sample recording so playback actually works
    sample_audio_filename = "sample_fusha_01.wav"
    sample_audio_path = os.path.join(UPLOAD_DIR, sample_audio_filename)
    if not os.path.exists(sample_audio_path):
        write_sample_audio(sample_audio_path, seconds=90)

    # 2. Seed Users for all 4 roles
    # Admin
    admin_user = User(
        email="admin@asghi.org",
        displayName="مدير المنصة",
        arabicLevel=Level.C2,
    )
    admin_user.register("admin@asghi.org", admin_pass)
    admin_user.completeProfile("مدير المنصة", Level.C2, UserRole.ADMIN)

    # Reviewer (Specialist)
    reviewer_user = User(
        email="reviewer@asghi.org",
        displayName="أستاذ فصيح (مراجع متخصص)",
        arabicLevel=Level.C2,
    )
    reviewer_user.register("reviewer@asghi.org", reviewer_pass)
    reviewer_user.completeProfile("أستاذ فصيح", Level.C2, UserRole.REVIEWER)
    # Grant specialist status
    for prof in reviewer_user.userProfiles:
        if hasattr(prof, "isSpecialist"):
            prof.isSpecialist = True

    # Reviewer (General)
    general_rev_user = User(
        email="reviewer2@asghi.org",
        displayName="مراجع لغوي عام",
        arabicLevel=Level.C1,
    )
    general_rev_user.register("reviewer2@asghi.org", reviewer2_pass)
    general_rev_user.completeProfile("مراجع لغوي عام", Level.C1, UserRole.REVIEWER)

    # Contributor
    contributor_user = User(
        email="contributor@asghi.org",
        displayName="القارئ المتطوع",
        arabicLevel=Level.C1,
    )
    contributor_user.register("contributor@asghi.org", contributor_pass)
    contributor_user.completeProfile("القارئ المتطوع", Level.C1, UserRole.CONTRIBUTOR)

    # Learner
    learner_user = User(
        email="learner@asghi.org",
        phoneNo="+966500000001",
        displayName="سعيد المتعلم",
        arabicLevel=Level.B1,
    )
    learner_user.register("learner@asghi.org", learner_pass)
    learner_user.completeProfile("سعيد المتعلم", Level.B1, UserRole.LEARNER)

    # 3. Seed Passages
    # Passage 1: Fully Verified with audio and questions across all 3 difficulties
    p1 = Passage(
        text=(
            "تَمْتَازُ اللُّغَةُ العَرَبِيَّةُ بِبَلَاغَتِهَا وَتَنَوُّعِ أَسَالِيبِهَا. "
            "وَقَدْ حَظِيَتْ بِمَكَانَةٍ رَفِيعَةٍ عَبْرَ العُصُورِ، لِأَنَّهَا لُغَةُ القُرْآنِ الكَرِيمِ "
            "وَوِعَاءُ العُلُومِ وَالآدَابِ الإِسْلَامِيَّةِ. يُسَاعِدُ الِاسْتِمَاعُ المُنْتَظِمُ "
            "عَلَى اكْتِسَابِ الفَصَاحَةِ وَتَرْسِيخِ النُّطْقِ السَّلِيمِ."
        ),
        level=Level.B1,
        topic="اللغة والثقافة",
        duration=timedelta(seconds=90),
        status=ContentStatus.VERIFIED,
        origin=Origin.HUMAN,
        authorId=admin_user.userId,
    )
    # Verified audio
    p1_rec = AudioRecording(
        audioFile=sample_audio_filename,
        duration=timedelta(seconds=90),
        attribution=AttributionType.SHOW_NAME,
        passageId=p1.passageId,
        authorId=contributor_user.userId,
        status=ContentStatus.VERIFIED,
        origin=Origin.HUMAN,
    )
    p1.audioRecordings.append(p1_rec)

    # Questions: EASY, MEDIUM, HARD
    q_easy = Question(
        promptText="بماذا تمتاز اللغة العربية وفقاً للنص؟",
        answers=["بالبلاغة وتنوع الأساليب", "بقلة مفرداتها", "بصعوبة فهمها", "بانحسار استعمالها"],
        correctAnswer="بالبلاغة وتنوع الأساليب",
        explanation="ذكر النص في بدايته: تمتاز اللغة العربية ببلاغتها وتنوع أساليبها.",
        passageReference="السطر الأول",
        difficulty=Difficulty.EASY,
        type=QuestionType.MCQ,
        passageId=p1.passageId,
        authorId=admin_user.userId,
        status=ContentStatus.VERIFIED,
        origin=Origin.HUMAN,
    )
    q_med = Question(
        promptText="ما السبب الرئيس للمكانة الرفيعة التي حظيت بها اللغة العربية عبر العصور؟",
        answers=["لأنها لغة القرآن الكريم ووعاء العلوم", "لأنها سهلة الحفظ فقط", "بسبب قلة قواعدها", "لاقتصارها على الشعر"],
        correctAnswer="لأنها لغة القرآن الكريم ووعاء العلوم",
        explanation="أوضح النص أن مكانتها الرفيعة تعود إلى كونها لغة القرآن الكريم ووعاء العلوم والآداب.",
        passageReference="السطر الثاني",
        difficulty=Difficulty.MEDIUM,
        type=QuestionType.MCQ,
        passageId=p1.passageId,
        authorId=admin_user.userId,
        status=ContentStatus.VERIFIED,
        origin=Origin.HUMAN,
    )
    q_hard = Question(
        promptText="ما هي النتيجة المترتبة على الاستماع المنتظم للفصحى بحسب النص؟",
        answers=["اكتساب الفصاحة وترسيخ النطق السليم", "نسيان القواعد القديمة", "تراجع الفهم السمعي", "التحول نحو اللهجات"],
        correctAnswer="اكتساب الفصاحة وترسيخ النطق السليم",
        explanation="اختتم النص بأن الاستماع المنتظم يساعد على اكتساب الفصاحة وترسيخ النطق السليم.",
        passageReference="السطر الثالث",
        difficulty=Difficulty.HARD,
        type=QuestionType.MCQ,
        passageId=p1.passageId,
        authorId=admin_user.userId,
        status=ContentStatus.VERIFIED,
        origin=Origin.HUMAN,
    )
    p1.addQuestion(q_easy)
    p1.addQuestion(q_med)
    p1.addQuestion(q_hard)

    # Passage 2: Awaiting recording (for contributors to claim)
    p2 = Passage(
        text=(
            "بَيْتُ الحِكْمَةِ فِي بَغْدَادَ كَانَ صَرْحًا عِلْمِيًّا شَامِخًا، "
            "شَهِدَ حَرَكَةَ تَرْجَمَةٍ كُبْرَى مِنَ اليُونَانِيَّةِ وَالفَارِسِيَّةِ إِلَى العَرَبِيَّةِ. "
            "أَسْهَمَ هَذَا المَرْكَزُ فِي حِفْظِ التُّرَاثِ الإِنْسَانِيِّ وَتَطْوِيرِ الرِّيَاضِيَّاتِ وَالفَلَكِ."
        ),
        level=Level.B2,
        topic="التاريخ والحضارة",
        duration=timedelta(seconds=110),
        status=ContentStatus.DRAFT,
        origin=Origin.HUMAN,
        authorId=admin_user.userId,
    )

    # Passage 3: Has a pending recording (for reviewers to verify)
    p3 = Passage(
        text=(
            "الغِذَاءُ الصِّحِّيُّ هُوَ الرَّكِيزَةُ الأَسَاسِيَّةُ لِبِنَاءِ جِسْمٍ سَلِيمٍ وَعَقْلٍ نَشِيطٍ. "
            "يُوصِي الأَطِبَّاءُ بِتَنَاوُلِ الخُضْرَاوَاتِ وَالفَوَاكِهِ الطَّازَجَةِ، "
            "وَالتَّقْلِيلِ مِنَ السُّكَّرِيَّاتِ وَالدُّهُونِ الضَّارَّةِ."
        ),
        level=Level.A2,
        topic="الصحة والعلوم",
        duration=timedelta(seconds=80),
        status=ContentStatus.CLAIMED,
        origin=Origin.HUMAN,
        authorId=admin_user.userId,
    )
    p3_rec = AudioRecording(
        audioFile=sample_audio_filename,
        duration=timedelta(seconds=80),
        attribution=AttributionType.SHOW_NAME,
        passageId=p3.passageId,
        authorId=contributor_user.userId,
        status=ContentStatus.PENDING_REVIEW,
        origin=Origin.HUMAN,
    )
    p3.audioRecordings.append(p3_rec)

    # Save all to SQLite
    repo.sync_all_to_db()
    print("Seed completed successfully:")
    print(f"- {len(User._registry)} users created (Admin, Reviewers, Contributor, Learner)")
    print(f"- {len(Passage._registry)} passages created (Verified, Awaiting Recording, Pending Review)")


if __name__ == "__main__":
    seed_database()


seed = seed_database
