# PROGRESS — اصغِ (Crowdsourced Arabic Listening Practice)

## Final Summary
- **What Runs**:
  - **Full Backend & REST API**: High-performance asynchronous FastAPI server providing 40 endpoints, fully role-gated per `h_uc.puml` with JWT authentication and strict access control for Learner, Contributor, Reviewer, and Admin.
  - **Complete Domain Model**: All 19 classes, 8 enums, and 47 operations from `class-diagram.puml` implemented with identical names, types, and signatures.
  - **All 5 Authoritative Sequences**:
    1. Claim cycle (`h_seq1_claim_cycle`): 72h TTL expiration, mutual exclusion, tashkeel toggle, audio submission with clock stop.
    2. Review verdict (`h_seq2_review_verdict`): Self-review blocking, Fusha/dialect verification, dual threshold (1 specialist vs 3 general), dispute escalation.
    3. Learner practice session (`h_seq3_learner_session`): Session lifecycle, audio playback speed, adaptive question difficulty (Easy <-> Medium <-> Hard), real-time scoring, explanation delivery, progress tracking.
    4. Registration and profile (`h_seq4_registration`): Multi-role user creation, profile completion, role profiles instantiation.
    5. Flagging and moderation (`h_seq5_flagging`): Content flagging, admin review, and `FLAGGED` status transition.
  - **Persistence & Seeding**: SQLite repository with WAL mode (`asghi.db`) and one-command seed script (`python -m asghi.seed`) seeding test accounts for all four roles, sample passages, audio recordings, and tiered questions.
  - **Arabic-First Responsive Web UI**: Mobile-friendly, high-contrast, WCAG 2.1 AA compliant RTL interface served directly at `/` with interactive role switcher and full learner/contributor/reviewer/admin workflows.
  - **Comprehensive Test Suite**: 65 tests in 11 test modules executed via `python -m pytest` with 100% pass rate in ~2 seconds.
- **What's Partial**: None. All core features are fully implemented end-to-end.
- **What's Blocked**: None. (Req 6.8 offline sync is explicitly marked OUT-OF-SCOPE per specification definition of done; API offline manifest is implemented at `GET /api/passages/{id}/offline-package`).
- **The Five Most Important Things the Owners Must Decide or Fix in Their Diagrams**:
  1. **Post-Flag Lifecycle for `ContentStatus.FLAGGED`**: In Sequence 5 (`h_seq5_flagging`), when an Admin takes action, `ReviewableContent.markFlagged()` sets status to `FLAGGED`. However, the diagrams do not specify exit transitions from `FLAGGED` (e.g. unflag/re-verify, permanent deletion, or contributor remediation). An explicit state machine diagram for `ContentStatus` should be added.
  2. **Persistence Repository Pattern**: The class diagram treats queries like `Passage.browse()` and `Passage.awaitingRecording()` as static class methods in memory. The owners should introduce a repository stereotype (e.g., `<<Repository>> PassageRepository`) or persistence interface to formalize the database mapping contract.
  3. **Formalize `CLAIM_TTL` Constant**: In `class-diagram.puml`, a note mentions "Every claim has TTL usually about 72 hours", and Sequence 1 refers to `CLAIM_TTL`. This should be formalized as a static constant attribute on `Passage` (e.g., `+ CLAIM_TTL: Duration = 72 hours`).
  4. **Mutating Operations on `Reputation`**: The `Reputation` class in `class-diagram.puml` defines properties (`score`, `approvalRate`, `totalSubmissions`), but defines zero operations. An operation such as `+ recordSubmissionResult(isApproved: boolean): void` should be added to show how reputations evolve upon review decisions.
  5. **Offline Sync Protocol Contract (Req 6.8 / `UC_Offline`)**: While `h_uc.puml` connects Learner to `Download Audio for Offline`, no sequence diagram or class model specifies the offline synchronization and caching architecture. The owners should specify whether this is an offline archive bundle (JSON + audio files) or an active delta-synchronization protocol.

---

## Stack Decision
- **Language & Runtime**: Python 3.14 + FastAPI + Uvicorn (async high-performance REST API)
- **Domain Modeling**: Direct object-oriented classes mirroring `class-diagram.puml` exactly with 100% adherence to all 19 classes, 8 enums, and 47 operations.
- **Persistence**: SQLite with WAL mode + Data Access Layer / Repository pattern (`asghi/repository.py`) ensuring domain model integrity and atomic transactions.
- **Authentication**: JWT Bearer tokens (PyJWT) with PBKDF2/SHA-256 password hashing, role gating according to `h_uc.puml`.
- **Frontend / Client UI**: Lightweight responsive Arabic-first RTL Single Page Application (HTML5/CSS3/Vanilla JS) served directly by FastAPI at `/`, meeting WCAG 2.1 AA and mobile responsiveness.
- **Testing**: `pytest` comprehensive test suite covering all functional requirements, sequence flows, and non-functional requirements.

---

### Flutter Mobile Client Bootstrap (Item 19)
- **Status**: Verified and Operational
- **Flutter SDK**: 3.47.0 • channel stable
- **Dart SDK**: 3.13.0 • DevTools 2.60.0
- **Android SDK**: version 36.0.0 detected at `%LOCALAPPDATA%\Android\Sdk`
- **PATH**: `C:\flutter\bin` added to User environment PATH

## Increment History & Commits
- `8ebbf40`: `feat(domain): implement full domain model, enums, operations, and sequence diagrams 1-5 [Req 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]`
- `0c70f94`: `feat(api, ui, tests): implement API, repository, Arabic RTL UI, and test suite [Req 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, NFR 11-21]`
- Current: Final cleanup, verification of Definition of Done, zero TODOs/placeholders, 65 passing tests.
