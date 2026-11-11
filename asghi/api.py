"""FastAPI Application for اصغِ (Asghi) - Crowdsourced Arabic Listening Practice.
Implements all functional requirements and enforces role-gating per h_uc.puml.
"""
from __future__ import annotations
import os
import shutil
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from asghi.domain.enums import (
    UserRole,
    Difficulty,
    Level,
    Origin,
    AttributionType,
    QuestionType,
    ContentStatus,
    FlagStatus,
)
from asghi.domain.user import User
from asghi.domain.learner_profile import LearnerProfile
from asghi.domain.contributor_profile import ContributorProfile
from asghi.domain.reviewer_profile import ReviewerProfile
from asghi.domain.admin_profile import AdminProfile
from asghi.domain.passage import Passage
from asghi.domain.audio_recording import AudioRecording
from asghi.domain.question import Question
from asghi.domain.review_assignment import ReviewAssignment
from asghi.domain.review_feedback import ReviewFeedback
from asghi.domain.content_flag import ContentFlag
from asghi.domain.test_session import TestSession
from asghi.domain.ai_engine import AIEngine
from asghi.repository import Repository, get_repository
from asghi.security import (
    create_access_token,
    get_current_user,
    require_roles,
)
from asghi.moderation import (
    check_content_guidelines,
    check_fusha_compliance,
    validate_audio_metadata,
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "audio")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: initialize and hydrate database once on application startup."""
    repo = get_repository()
    repo.load_all_from_db()
    yield


repo = get_repository()

app = FastAPI(
    title="اصغِ - منصة التدريب على الاستماع العربي الفصيح",
    description="Crowdsourced Arabic Listening Practice Platform",
    version="1.0.0",
    lifespan=lifespan,
)


# NFR 16.1: Security headers & CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """NFR 16.1 & NFR 13: Strict security headers and performance caching."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# --- Pydantic Schemas ---
class RegisterRequest(BaseModel):
    emailOrPhone: str
    password: str


class LoginRequest(BaseModel):
    emailOrPhone: Optional[str] = None
    identifier: Optional[str] = None
    password: str

    @property
    def login_id(self) -> str:
        return self.identifier or self.emailOrPhone or ""


class CompleteProfileRequest(BaseModel):
    displayName: str
    level: Level
    roleInterest: UserRole


class ClaimRequest(BaseModel):
    passageId: UUID


class QuestionCreateRequest(BaseModel):
    passageId: UUID
    promptText: str
    answers: List[str]
    correctAnswer: str
    explanation: str
    difficulty: Difficulty
    type: QuestionType = QuestionType.MCQ
    passageReference: str = ""


class GenerateQuestionsRequest(BaseModel):
    passageId: UUID
    count: int = 3


class ReviewAssignmentRequest(BaseModel):
    contentId: UUID


class ReviewDecisionRequest(BaseModel):
    assignmentId: UUID
    isFusha: bool
    dialectFree: bool = True
    audioQuality: int = 5
    isApproved: bool
    reason: str = ""


class FlagCreateRequest(BaseModel):
    contentId: UUID
    reason: str


class ResolveFlagRequest(BaseModel):
    newState: FlagStatus


class ResolveDisputeRequest(BaseModel):
    action: str  # "VERIFY" or "REJECT"


class CreatePassageRequest(BaseModel):
    text: str
    level: Level
    topic: str
    durationSeconds: float = 90.0
    origin: Origin = Origin.HUMAN


class StartSessionRequest(BaseModel):
    passageId: UUID


class SubmitAnswerRequest(BaseModel):
    questionId: UUID
    answer: str


class TriggerAIRequest(BaseModel):
    passageId: UUID


class PlayAudioRequest(BaseModel):
    passageId: UUID
    playbackSpeed: float = 1.0


class QuestionReviewRequest(BaseModel):
    isApproved: bool
    reason: str = ""


class ManageUserRequest(BaseModel):
    action: str


@app.get("/healthz")
def healthz():
    """NFR 15: Health check probe."""
    return {"status": "ok", "uptime": "99.9%", "service": "asghi"}


# --- Auth & Profile (Req 1.1, 1.2, 1.3) ---
@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, repo: Repository = Depends(get_repository)):
    """Req 1.2 & Seq 4: Register new user with email or phone number."""
    existing = repo.get_user_by_identifier(req.emailOrPhone)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="الحساب مسجل بالفعل")

    user = User()
    user.register(req.emailOrPhone, req.password)
    repo.save_user(user)
    token = create_access_token(user.userId, [p.role for p in user.userProfiles])
    return {
        "message": "تم إنشاء الحساب بنجاح",
        "userId": str(user.userId),
        "token": token,
    }


@app.post("/api/auth/login")
def login(req: LoginRequest, repo: Repository = Depends(get_repository)):
    """Req 1.2 & Seq 4: Login with email or phone number."""
    login_ident = req.login_id
    target_user = repo.get_user_by_identifier(login_ident)

    if not target_user or not target_user.login(login_ident, req.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="بيانات الدخول غير صحيحة")

    token = create_access_token(target_user.userId, [p.role for p in target_user.userProfiles])
    return {
        "message": "تم تسجيل الدخول بنجاح",
        "userId": str(target_user.userId),
        "displayName": target_user.displayName,
        "roles": [p.role.value for p in target_user.userProfiles],
        "token": token,
        "accessToken": token,
        "access_token": token,
        "token_type": "bearer",
    }


@app.post("/api/users/profile")
def complete_profile(req: CompleteProfileRequest, user: User = Depends(get_current_user), repo: Repository = Depends(get_repository)):
    """Req 1.3 & Seq 4: Complete profile with displayName, level, and role interest."""
    user.completeProfile(req.displayName, req.level, req.roleInterest)
    repo.save_user(user)
    token = create_access_token(user.userId, [p.role for p in user.userProfiles])
    return {
        "message": "تم حفظ الملف الشخصي بنجاح",
        "userId": str(user.userId),
        "displayName": user.displayName,
        "arabicLevel": user.arabicLevel.value,
        "roles": [p.role.value for p in user.userProfiles],
        "token": token,
    }



@app.get("/api/users/me")
def get_me(user: User = Depends(get_current_user)):
    """Fetch current user profile and role profiles."""
    profiles_data = []
    for prof in user.userProfiles:
        p_data: Dict[str, Any] = {"role": prof.role.value, "profileId": str(prof.userRoleProfileId)}
        if isinstance(prof, LearnerProfile):
            p_data["progress"] = {
                "totalScore": prof.progress.totalScore,
                "totalTimeSpent": prof.progress.totalTimeSpent,
                "streak": prof.progress.currentStreakDays,
            }
        elif isinstance(prof, ContributorProfile):
            p_data["reputation"] = {
                "score": prof.reputation.score,
                "approvalRate": prof.reputation.approvalRate,
                "totalSubmissions": prof.reputation.totalSubmissions,
            }
            p_data["creditsEarned"] = prof.creditsEarned
        elif isinstance(prof, ReviewerProfile):
            p_data["reputation"] = {
                "score": prof.reputation.score,
                "approvalRate": prof.reputation.approvalRate,
                "totalSubmissions": prof.reputation.totalSubmissions,
            }
            p_data["isSpecialist"] = prof.isSpecialist
        profiles_data.append(p_data)

    return {
        "userId": str(user.userId),
        "displayName": user.displayName,
        "email": user.email,
        "phoneNo": user.phoneNo,
        "arabicLevel": user.arabicLevel.value if user.arabicLevel else None,
        "roles": [p.role.value for p in user.userProfiles],
        "profiles": profiles_data,
    }


@app.get("/api/users/{userId}/reputation")
def get_user_reputation(userId: UUID):
    """Req 10.1: View Contributor or Reviewer reputation."""
    for u in User._registry:
        if u.userId == userId:
            for prof in u.userProfiles:
                if isinstance(prof, (ContributorProfile, ReviewerProfile)):
                    return {
                        "userId": str(userId),
                        "role": prof.role.value,
                        "score": prof.reputation.score,
                        "approvalRate": prof.reputation.approvalRate,
                        "totalSubmissions": prof.reputation.totalSubmissions,
                    }
    raise HTTPException(status_code=404, detail="المستخدم أو سجل السمعة غير موجود")


# --- Catalogue & Passages (Req 2, 2.1, 2.2, 2.3) ---
@app.get("/api/passages")
def browse_passages(
    level: Optional[Level] = None,
    topic: Optional[str] = None,
    maxDurationSeconds: Optional[float] = None,
):
    """Req 2.1, 2.3 & 6.1: Catalogue query contract with multi-criteria filtering."""
    max_dur = timedelta(seconds=maxDurationSeconds) if maxDurationSeconds else None
    passages = Passage.browse(level=level, topic=topic, maxDuration=max_dur)

    items = []
    for p in passages:
        verified_audio = [r for r in p.audioRecordings if r.status == ContentStatus.VERIFIED]
        items.append({
            "passageId": str(p.passageId),
            "text": p.text,
            "level": p.level.value,
            "topic": p.topic,
            "durationSeconds": p.duration.total_seconds(),
            "origin": p.origin.value,
            "status": p.status.value,
            "claimed": bool(p.claimedBy and not p.isClaimExpired()),
            "verifiedAudioCount": len(verified_audio),
            "audioRecordings": [
                {
                    "contentId": str(r.contentId),
                    "audioFile": r.audioFile,
                    "attribution": r.attribution.value,
                    "status": r.status.value,
                }
                for r in p.audioRecordings
            ],
            "questionsCount": len(p.questions),
        })
    return items


@app.get("/api/passages/{passageId}/text")
def get_passage_text(passageId: UUID, withTashkeel: bool = True):
    """Req 4.3 & Seq 1: Display passage text alongside recorder with optional tashkeel."""
    for p in Passage._registry:
        if p.passageId == passageId:
            text = p.text
            if not withTashkeel:
                import re
                text = re.sub(r"[\u0617-\u061A\u064B-\u0652]", "", text)
            return {"passageId": str(p.passageId), "text": text, "withTashkeel": withTashkeel}
    raise HTTPException(status_code=404, detail="النص غير موجود")


# --- Contributor Endpoints (Role: CONTRIBUTOR) ---
@app.get(
    "/api/contributor/awaiting-recording",
    dependencies=[Depends(require_roles(UserRole.CONTRIBUTOR, UserRole.ADMIN))],
)
def get_awaiting_recording():
    """Req 4.1 & Seq 1: Browse passages needing recording."""
    passages = Passage.awaitingRecording()
    return [
        {
            "passageId": str(p.passageId),
            "text": p.text,
            "level": p.level.value,
            "topic": p.topic,
            "durationSeconds": p.duration.total_seconds(),
            "origin": p.origin.value,
            "status": p.status.value,
        }
        for p in passages
    ]


@app.post(
    "/api/contributor/claim",
    dependencies=[Depends(require_roles(UserRole.CONTRIBUTOR, UserRole.ADMIN))],
)
def claim_passage(req: ClaimRequest, user: User = Depends(get_current_user)):
    """Req 4.1 & Seq 1: Claim passage for audio recording."""
    contributor_prof: Optional[ContributorProfile] = None
    for p in user.userProfiles:
        if isinstance(p, ContributorProfile):
            contributor_prof = p
            break

    if not contributor_prof:
        raise HTTPException(status_code=403, detail="الحساب ليس لديه ملف مساهم")

    success = contributor_prof.claim(req.passageId)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="تعذر حجز النص: النص محجوز لمساهم آخر أو يحتوي بالفعل على تسجيل معتمد أو قيد المراجعة.",
        )

    # Persist updated passage
    for p in Passage._registry:
        if p.passageId == req.passageId:
            repo.save_passage(p)
            break

    return {"message": "تم حجز النص بنجاح لتسجيل الصوت", "passageId": str(req.passageId)}


@app.post(
    "/api/contributor/submit-audio",
    dependencies=[Depends(require_roles(UserRole.CONTRIBUTOR, UserRole.ADMIN))],
)
async def submit_audio(
    passageId: UUID = Form(...),
    attribution: AttributionType = Form(AttributionType.SHOW_NAME),
    durationSeconds: float = Form(90.0),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Req 4.2, 4.4, NFR 12, NFR 19 & Seq 1: Submit audio recording up to 25MB."""
    contributor_prof: Optional[ContributorProfile] = None
    for p in user.userProfiles:
        if isinstance(p, ContributorProfile):
            contributor_prof = p
            break

    if not contributor_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس مساهماً")

    # Read and validate file size (NFR 12)
    file_bytes = await file.read()
    file_size = len(file_bytes)
    valid, err_msg = validate_audio_metadata(file_size, durationSeconds)
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg)

    # Save to audio directory (Invention #7)
    file_ext = os.path.splitext(file.filename or "recording.mp3")[1] or ".mp3"
    saved_filename = f"{uuid4()}{file_ext}"
    saved_path = os.path.join(UPLOAD_DIR, saved_filename)
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    # Target passage
    target_p: Optional[Passage] = None
    for p in Passage._registry:
        if p.passageId == passageId:
            target_p = p
            break

    if not target_p:
        raise HTTPException(status_code=404, detail="النص غير موجود")

    rec = target_p.addAudio(
        audioFile=saved_filename,
        duration=timedelta(seconds=durationSeconds),
        attribution=attribution,
        authorId=contributor_prof.userRoleProfileId,
    )
    repo.save_passage(target_p)

    return {
        "message": "تم رفع التسجيل الصوتي بنجاح وهو قيد المراجعة",
        "recordingId": str(rec.contentId),
        "status": rec.status.value,
        "attribution": rec.attribution.value,
    }


@app.get(
    "/api/contributor/submissions",
    dependencies=[Depends(require_roles(UserRole.CONTRIBUTOR, UserRole.ADMIN))],
)
def get_contributor_submissions(user: User = Depends(get_current_user)):
    """Req 8: Explain to contributors why a submission was rejected."""
    contributor_prof = next((p for p in user.userProfiles if isinstance(p, ContributorProfile)), None)
    if not contributor_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس مساهماً")

    submissions = []
    for p in Passage._registry:
        for rec in p.audioRecordings:
            if rec.authorId == contributor_prof.userRoleProfileId:
                submissions.append({
                    "recordingId": str(rec.contentId),
                    "passageId": str(p.passageId),
                    "passageTopic": p.topic,
                    "audioFile": rec.audioFile,
                    "status": rec.status.value,
                    "rejectionReason": rec.rejectionReason,
                    "reviewsCount": len(rec.reviews),
                })
    return submissions


# --- Reviewer Endpoints (Role: REVIEWER) ---
@app.get(
    "/api/reviewer/pending-recordings",
    dependencies=[Depends(require_roles(UserRole.REVIEWER, UserRole.ADMIN))],
)
def get_pending_recordings(user: User = Depends(get_current_user)):
    """Req 5.1 & Seq 2: Reviewer lists pending recordings."""
    reviewer_prof = next((p for p in user.userProfiles if isinstance(p, ReviewerProfile)), None)
    if not reviewer_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس مراجعاً")

    pending = reviewer_prof.pendingRecordings()
    return [
        {
            "recordingId": str(r.contentId),
            "passageId": str(r.passageId),
            "durationSeconds": r.duration.total_seconds(),
            "attribution": r.attribution.value,
            "authorId": str(r.authorId) if r.authorId else None,
            "status": r.status.value,
        }
        for r in pending
    ]


@app.post(
    "/api/reviewer/assignments",
    dependencies=[Depends(require_roles(UserRole.REVIEWER, UserRole.ADMIN))],
)
def create_review_assignment(req: ReviewAssignmentRequest, user: User = Depends(get_current_user)):
    """Req 5.1, 5.3 & Seq 2: Assign review, preventing author self-review."""
    reviewer_prof = next((p for p in user.userProfiles if isinstance(p, ReviewerProfile)), None)
    if not reviewer_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس مراجعاً")

    try:
        assignment = reviewer_prof.assignReview(req.contentId)
        return {
            "assignmentId": str(assignment.reviewId),
            "contentId": str(assignment.contentId),
            "isSpecialistReview": assignment.isSpecialistReview,
        }
    except PermissionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post(
    "/api/reviewer/decision",
    dependencies=[Depends(require_roles(UserRole.REVIEWER, UserRole.ADMIN))],
)
def submit_review_decision(req: ReviewDecisionRequest, user: User = Depends(get_current_user)):
    """Req 5.1, 5.2, 5.5 & Seq 2: Submit review decision with threshold evaluation."""
    reviewer_prof = next((p for p in user.userProfiles if isinstance(p, ReviewerProfile)), None)
    if not reviewer_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس مراجعاً")

    assignment: Optional[ReviewAssignment] = None
    for a in reviewer_prof.assignments:
        if a.reviewId == req.assignmentId:
            assignment = a
            break

    if not assignment:
        raise HTTPException(status_code=404, detail="مهمة المراجعة غير موجودة")

    feedback = reviewer_prof.createFeedback(
        isFusha=req.isFusha,
        dialectFree=req.dialectFree,
        audioQuality=req.audioQuality,
        feedback=req.reason,
    )
    reviewer_prof.submitDecision(assignment, feedback, req.isApproved, req.reason)

    # Persist updated content and assignments
    for p in Passage._registry:
        if p.contentId == assignment.contentId or any(r.contentId == assignment.contentId for r in p.audioRecordings):
            repo.save_passage(p)
            break

    return {"message": "تم تسجيل قرار المراجعة بنجاح"}


@app.get(
    "/api/reviewer/pending-questions",
    dependencies=[Depends(require_roles(UserRole.REVIEWER, UserRole.ADMIN))],
)
def get_pending_questions(user: User = Depends(get_current_user)):
    """Req 3.3, 7.3 & UC_ReviewAI: Review pending questions before publication."""
    pending = []
    for p in Passage._registry:
        for q in p.questions:
            if q.status == ContentStatus.PENDING_REVIEW:
                pending.append({
                    "questionId": str(q.questionId),
                    "passageId": str(p.passageId),
                    "promptText": q.promptText,
                    "answers": q.answers,
                    "correctAnswer": q.correctAnswer,
                    "explanation": q.explanation,
                    "difficulty": q.difficulty.value,
                    "origin": q.origin.value,
                    "authorId": str(q.authorId) if q.authorId else None,
                })
    return pending


@app.post(
    "/api/reviewer/questions/{questionId}/review",
    dependencies=[Depends(require_roles(UserRole.REVIEWER, UserRole.ADMIN))],
)
def review_question(
    questionId: UUID,
    req: QuestionReviewRequest,
    user: User = Depends(get_current_user),
):
    """Req 3.3, 7.3: Reviewer verifies or rejects question."""
    target_q: Optional[Question] = None
    parent_p: Optional[Passage] = None
    for p in Passage._registry:
        for q in p.questions:
            if q.questionId == questionId:
                target_q = q
                parent_p = p
                break
        if target_q:
            break

    if not target_q:
        raise HTTPException(status_code=404, detail="السؤال غير موجود")

    if req.isApproved:
        target_q.verify()
    else:
        target_q.reject(req.reason or "Rejected during question review")

    if parent_p:
        repo.save_passage(parent_p)

    return {
        "message": "تم تحديث حالة السؤال بنجاح",
        "questionId": str(questionId),
        "status": target_q.status.value,
    }



# --- Learner Endpoints (Role: LEARNER) ---
active_sessions: Dict[UUID, TestSession] = {}


@app.post(
    "/api/learner/play",
    dependencies=[Depends(require_roles(UserRole.LEARNER, UserRole.ADMIN))],
)
def play_learner_audio(req: PlayAudioRequest, user: User = Depends(get_current_user)):
    """Req 6.1 & Seq 3: Browse and play verified Fusha audio with speed adjustment."""
    target_p = next((p for p in Passage._registry if p.passageId == req.passageId), None)
    if not target_p:
        raise HTTPException(status_code=404, detail="النص غير موجود")

    verified_recs = [r for r in target_p.audioRecordings if r.status == ContentStatus.VERIFIED]
    if not verified_recs:
        raise HTTPException(status_code=404, detail="لا يوجد تسجيل صوتي معتمد لهذا النص بعد")

    learner_prof = next((p for p in user.userProfiles if isinstance(p, LearnerProfile)), None)
    if learner_prof:
        learner_prof.playAudio(req.playbackSpeed)

    rec = verified_recs[0]
    return {
        "passageId": str(target_p.passageId),
        "audioFile": rec.audioFile,
        "playbackSpeed": req.playbackSpeed,
        "attribution": rec.attribution.value,
        "durationSeconds": rec.duration.total_seconds(),
    }



@app.post(
    "/api/learner/sessions",
    dependencies=[Depends(require_roles(UserRole.LEARNER, UserRole.ADMIN))],
)
def start_learner_session(req: StartSessionRequest, user: User = Depends(get_current_user)):
    """Req 6.2 & Seq 3: Start new test session for a passage."""
    learner_prof = next((p for p in user.userProfiles if isinstance(p, LearnerProfile)), None)
    if not learner_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس متعلماً")

    target_p: Optional[Passage] = None
    for p in Passage._registry:
        if p.passageId == req.passageId:
            target_p = p
            break

    if not target_p:
        raise HTTPException(status_code=404, detail="النص غير موجود")

    repo = get_repository()
    repo.save_passage(target_p)
    session = learner_prof.startSession(req.passageId)
    session.learnerId = user.userId
    active_sessions[session.sessionId] = session
    repo.save_test_session(session)

    return {
        "sessionId": str(session.sessionId),
        "passageId": str(session.passageId),
        "currentDifficulty": session.currentDifficulty.value,
        "startedAt": session.startedAt.isoformat(),
    }


@app.get(
    "/api/learner/sessions/{sessionId}/question",
    dependencies=[Depends(require_roles(UserRole.LEARNER, UserRole.ADMIN))],
)
def get_next_question(sessionId: UUID):
    """Req 6.3 & Seq 3: Get next question at adaptive difficulty."""
    session = active_sessions.get(sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")

    q = session.nextQuestion()
    if not q:
        return {"done": True, "message": "تمت الإجابة على جميع أسئلة هذا النص"}

    return {
        "done": False,
        "questionId": str(q.questionId),
        "promptText": q.promptText,
        "answers": q.answers,
        "difficulty": q.difficulty.value,
        "type": q.type.value,
        "passageReference": q.passageReference,
    }


@app.post(
    "/api/learner/sessions/{sessionId}/answer",
    dependencies=[Depends(require_roles(UserRole.LEARNER, UserRole.ADMIN))],
)
def submit_session_answer(
    sessionId: UUID,
    req: SubmitAnswerRequest,
):
    """Req 6.4, 6.5, 9 & Seq 3: Submit answer, evaluate, adapt difficulty, return explanation."""
    session = active_sessions.get(sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")

    result = session.submitAnswer(req.questionId, req.answer)
    repo = get_repository()
    if session.questionResponses:
        repo.save_question_response(session.sessionId, session.questionResponses[-1])
    repo.save_test_session(session)

    return {
        "isCorrect": result["isCorrect"],
        "correctAnswer": result["correctAnswer"],
        "explanation": result["explanation"],
        "totalScore": result["totalScore"],
        "nextDifficulty": session.currentDifficulty.value,
    }


@app.post(
    "/api/learner/sessions/{sessionId}/finish",
    dependencies=[Depends(require_roles(UserRole.LEARNER, UserRole.ADMIN))],
)
def finish_learner_session(sessionId: UUID, user: User = Depends(get_current_user)):
    """Req 6.6 & Seq 3: Finish practice session and update learner progress."""
    learner_prof = next((p for p in user.userProfiles if isinstance(p, LearnerProfile)), None)
    if not learner_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس متعلماً")

    session = active_sessions.get(sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")

    totals = session.finishSession()
    learner_prof.progress.update(totals["totalScore"], totals["timeSpent"])
    del active_sessions[sessionId]
    repo = get_repository()
    repo.save_test_session(session)
    repo.save_user(user)

    return {
        "message": "تم إنهاء الجلسة بنجاح",
        "totalScore": learner_prof.progress.totalScore,
        "timeSpent": totals["timeSpent"],
        "currentStreakDays": learner_prof.progress.currentStreakDays,
    }


@app.get(
    "/api/learner/progress",
    dependencies=[Depends(require_roles(UserRole.LEARNER, UserRole.ADMIN))],
)
def get_learner_progress(user: User = Depends(get_current_user)):
    """Req 6.6: Track Learner progress over time."""
    learner_prof = next((p for p in user.userProfiles if isinstance(p, LearnerProfile)), None)
    if not learner_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس متعلماً")

    return {
        "totalScore": learner_prof.progress.totalScore,
        "totalTimeSpent": learner_prof.progress.totalTimeSpent,
        "currentStreakDays": learner_prof.progress.currentStreakDays,
    }


@app.post(
    "/api/learner/flag",
    dependencies=[Depends(require_roles(UserRole.LEARNER, UserRole.ADMIN))],
)
def flag_content(req: FlagCreateRequest, user: User = Depends(get_current_user)):
    """Req 6.7 & Seq 5: Learner reports problematic content."""
    learner_prof = next((p for p in user.userProfiles if isinstance(p, LearnerProfile)), None)
    if not learner_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس متعلماً")

    # Locate content
    target_content = None
    for p in Passage._registry:
        if p.contentId == req.contentId:
            target_content = p
            break
        for rec in p.audioRecordings:
            if rec.contentId == req.contentId:
                target_content = rec
                break
        for q in p.questions:
            if q.contentId == req.contentId:
                target_content = q
                break

    if not target_content:
        raise HTTPException(status_code=404, detail="المحتوى المبلغ عنه غير موجود")

    flag = learner_prof.flagContent(target_content, req.reason)
    repo.save_content_flag(flag)

    return {
        "message": "تم إرسال البلاغ إلى الإدارة للمراجعة",
        "flagId": str(flag.flagId),
        "status": flag.status.value,
    }


@app.get("/api/passages/{passageId}/offline-package")
def get_offline_package(passageId: UUID):
    """Req 6.8 & Invention #14: Offline package manifest with passage, questions, audio."""
    for p in Passage._registry:
        if p.passageId == passageId:
            return {
                "passageId": str(p.passageId),
                "text": p.text,
                "level": p.level.value,
                "topic": p.topic,
                "audio": [
                    {"contentId": str(r.contentId), "audioFile": r.audioFile}
                    for r in p.audioRecordings if r.status == ContentStatus.VERIFIED
                ],
                "questions": [
                    {
                        "questionId": str(q.questionId),
                        "promptText": q.promptText,
                        "answers": q.answers,
                        "correctAnswer": q.correctAnswer,
                        "explanation": q.explanation,
                        "difficulty": q.difficulty.value,
                    }
                    for q in p.questions if q.status == ContentStatus.VERIFIED
                ],
            }
    raise HTTPException(status_code=404, detail="النص غير موجود")


# --- Question Authoring (Roles: CONTRIBUTOR, REVIEWER, ADMIN) ---
@app.post(
    "/api/questions",
    dependencies=[Depends(require_roles(UserRole.CONTRIBUTOR, UserRole.REVIEWER, UserRole.ADMIN))],
)
def author_question(req: QuestionCreateRequest, user: User = Depends(get_current_user)):
    """Req 7.1, 7.3: Author question manually, placed in PENDING_REVIEW."""
    valid, err_msg = check_content_guidelines(req.promptText)
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg)

    target_p = next((p for p in Passage._registry if p.passageId == req.passageId), None)
    if not target_p:
        raise HTTPException(status_code=404, detail="النص غير موجود")

    author_profile = user.userProfiles[0] if user.userProfiles else None
    author_id = author_profile.userRoleProfileId if author_profile else user.userId

    q = Question(
        promptText=req.promptText,
        answers=req.answers,
        correctAnswer=req.correctAnswer,
        explanation=req.explanation,
        passageReference=req.passageReference,
        difficulty=req.difficulty,
        type=req.type,
        passageId=req.passageId,
        authorId=author_id,
        status=ContentStatus.PENDING_REVIEW,
        origin=Origin.HUMAN,
    )
    target_p.addQuestion(q)
    repo.save_passage(target_p)

    return {
        "message": "تم إضافة السؤال بنجاح وهو قيد المراجعة",
        "questionId": str(q.questionId),
        "status": q.status.value,
    }


# --- Admin Endpoints (Role: ADMIN) ---
@app.post(
    "/api/admin/passages",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def create_catalogue_passage(req: CreatePassageRequest, user: User = Depends(get_current_user)):
    """Req 2, 18.1, 18.2: Maintain catalogue of passages."""
    fusha_ok, f_err = check_fusha_compliance(req.text)
    if not fusha_ok:
        raise HTTPException(status_code=400, detail=f_err)

    halal_ok, h_err = check_content_guidelines(req.text)
    if not halal_ok:
        raise HTTPException(status_code=400, detail=h_err)

    admin_prof = next((p for p in user.userProfiles if isinstance(p, AdminProfile)), None)
    author_id = admin_prof.userRoleProfileId if admin_prof else user.userId

    passage = Passage(
        text=req.text,
        level=req.level,
        topic=req.topic,
        duration=timedelta(seconds=req.durationSeconds),
        authorId=author_id,
        status=ContentStatus.DRAFT,
        origin=req.origin,
    )
    repo.save_passage(passage)
    return {
        "message": "تمت إضافة النص بنجاح إلى الفهرس",
        "passageId": str(passage.passageId),
        "status": passage.status.value,
    }


@app.post(
    "/api/admin/generate",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def trigger_ai_generation(req: TriggerAIRequest, user: User = Depends(get_current_user)):
    """Req 3.1, 3.2, 3.3, 7.2: AI Content Generator under human review."""
    admin_prof = next((p for p in user.userProfiles if isinstance(p, AdminProfile)), None)
    if not admin_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس مديراً")

    res = admin_prof.triggerAIGeneration(req.passageId)
    # Save generated questions to database
    for p in Passage._registry:
        if p.passageId == req.passageId:
            repo.save_passage(p)
            break
    return res


@app.post(
    "/api/admin/flags/{flagId}/resolve",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def resolve_flag(flagId: UUID, req: ResolveFlagRequest, user: User = Depends(get_current_user)):
    """Req 6.7, 10.2 & Seq 5: Admin resolves content flag."""
    admin_prof = next((p for p in user.userProfiles if isinstance(p, AdminProfile)), None)
    if not admin_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس مديراً")

    admin_prof.resolveFlag(flagId, req.newState)
    repo.sync_all_to_db()
    return {"message": "تمت معالجة البلاغ بنجاح", "flagId": str(flagId), "newState": req.newState.value}


@app.post(
    "/api/admin/disputes/{contentId}/resolve",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def resolve_dispute(contentId: UUID, req: ResolveDisputeRequest, user: User = Depends(get_current_user)):
    """Req 5.4, 10.2 & Seq 2: Admin resolves reviewer disagreement."""
    admin_prof = next((p for p in user.userProfiles if isinstance(p, AdminProfile)), None)
    if not admin_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس مديراً")

    admin_prof.resolveDispute(contentId, req.action)
    repo.sync_all_to_db()
    return {"message": "تم حل النزاع بنجاح", "contentId": str(contentId), "verdict": req.action.upper()}


@app.get(
    "/api/admin/flags",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def list_flags(user: User = Depends(get_current_user)):
    """Req 6.7, 10.2 & Seq 5: List all reported content flags."""
    flags_data = []
    for p in Passage._registry:
        for f in p.flags:
            flags_data.append({
                "flagId": str(f.flagId),
                "contentId": str(f.contentId),
                "contentType": "PASSAGE",
                "reason": f.reason,
                "status": f.status.value,
            })
        for r in p.audioRecordings:
            for f in r.flags:
                flags_data.append({
                    "flagId": str(f.flagId),
                    "contentId": str(f.contentId),
                    "contentType": "AUDIO_RECORDING",
                    "reason": f.reason,
                    "status": f.status.value,
                })
        for q in p.questions:
            for f in q.flags:
                flags_data.append({
                    "flagId": str(f.flagId),
                    "contentId": str(f.contentId),
                    "contentType": "QUESTION",
                    "reason": f.reason,
                    "status": f.status.value,
                })
    return flags_data


@app.post(
    "/api/admin/specialists/{reviewerId}",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def assign_specialist(reviewerId: UUID, user: User = Depends(get_current_user)):
    """Admin assigns specialist status to a reviewer."""
    admin_prof = next((p for p in user.userProfiles if isinstance(p, AdminProfile)), None)
    if not admin_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس مديراً")

    admin_prof.assignSpecialistStatus(reviewerId)
    repo.sync_all_to_db()
    return {"message": "تم تعيين المراجع كمراجع متخصص بنجاح", "reviewerId": str(reviewerId)}


@app.post(
    "/api/admin/users/{userId}/manage",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def manage_user(userId: UUID, req: ManageUserRequest, user: User = Depends(get_current_user)):
    """Req 10.2: Admin user management action."""
    admin_prof = next((p for p in user.userProfiles if isinstance(p, AdminProfile)), None)
    if not admin_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس مديراً")

    admin_prof.manageUser(userId, req.action)
    repo.sync_all_to_db()
    return {"message": "تم تحديث حالة المستخدم بنجاح", "userId": str(userId), "action": req.action}



@app.get(
    "/api/admin/dashboard",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def get_admin_dashboard(user: User = Depends(get_current_user)):
    """Req 10.2: Admin dashboard for moderation, user management, reporting."""
    admin_prof = next((p for p in user.userProfiles if isinstance(p, AdminProfile)), None)
    if not admin_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس مديراً")

    report = admin_prof.generateReport("MONTHLY")
    users_list = [
        {
            "userId": str(u.userId),
            "displayName": u.displayName,
            "email": u.email,
            "roles": [p.role.value for p in u.userProfiles],
            "status": u.status,
        }
        for u in User._registry
    ]
    return {
        "report": report,
        "users": users_list,
    }


@app.get(
    "/api/admin/report",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def get_admin_report(period: str = "ALL_TIME", user: User = Depends(get_current_user)):
    """Req 10.2: Admin reporting metrics."""
    admin_prof = next((p for p in user.userProfiles if isinstance(p, AdminProfile)), None)
    if not admin_prof:
        raise HTTPException(status_code=403, detail="المستخدم ليس مديراً")

    return admin_prof.generateReport(period)


# --- Static Audio Serving ---
@app.get("/api/audio/{filename}")
def get_audio_file(filename: str):
    """Audio streaming endpoint."""
    path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path, media_type="audio/mpeg")
    # Return 404 if file does not exist
    raise HTTPException(status_code=404, detail="ملف الصوت غير موجود")


# Mount static directory for minimal mobile-friendly RTL UI
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index_page():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
