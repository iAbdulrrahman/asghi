# PROGRESS — اصغِ (Crowdsourced Arabic Listening Practice)

## Final Summary
- **What Runs**:
  - **Full Backend & REST API**: High-performance asynchronous FastAPI server providing 38 application routes, fully role-gated per `h_uc.puml` with JWT authentication and strict access control for Learner, Contributor, Reviewer, and Admin.
  - **Complete Domain Model**: All 19 classes, 8 enums, and 47 operations from `class-diagram.puml` implemented with identical names, types, and signatures.
  - **All 5 Authoritative Sequences**:
    1. Claim cycle (`h_seq1_claim_cycle`): 72h TTL expiration, mutual exclusion with 409 Conflict, non-extendable claims, tashkeel toggle, audio submission with clock stop.
    2. Review verdict (`h_seq2_review_verdict`): Self-review blocking, Fusha/dialect verification, dual threshold (1 specialist vs 3 general), dispute escalation, atomic transaction (`submit_verdict_tx`).
    3. Learner practice session (`h_seq3_learner_session`): Session lifecycle, audio playback speed, adaptive question difficulty (Easy <-> Medium <-> Hard), real-time scoring, explanation delivery, progress tracking, atomic answer recording (`record_answer_tx`).
    4. Registration and profile (`h_seq4_registration`): Multi-role user creation, profile completion, role profiles instantiation, persistent rehydration across server restarts.
    5. Flagging and moderation (`h_seq5_flagging`): Content flagging, admin review, atomic flag resolution (`resolve_flag_tx`), and `FLAGGED` status transition.
  - **Persistence & Seeding**: SQLite repository with WAL mode (`asghi.db`), full foreign key cascades, unique claim constraints, and single documented root seed entry point (`python seed.py`, delegating to `asghi.seed`) seeding test accounts for all four roles, sample passages, audio recordings, and tiered questions.
  - **Native Flutter Mobile App (Android + iOS targets)**: Pure Flutter mobile client located in `mobile/` with Riverpod state management, Dio HTTP client, Arabic RTL layout, bundled `Noto Naskh Arabic` typography, WCAG 2.1 AA theme, responsive audio player widget with 0.75x/1.0x/1.25x/1.5x playback speeds, real-time diacritics stripping (`TashkeelTextWidget`), and complete screens for all four roles.
  - **Android Debug APK Built**: Successfully compiled to `mobile/build/app/outputs/flutter-apk/app-debug.apk`.
  - **Live Android Device Execution**: Executed live integration test (`mobile/integration_test/app_test.dart`) on Android emulator (`emulator-5554`, API 33) accelerated by WHPX, interacting with live FastAPI backend via `adb reverse tcp:8000 tcp:8000`, with physical framebuffer capture saved to `mobile/docs/device_flow_1.png` (1.3 MB).
  - **Comprehensive Test Suite**:
    - **92 Python backend tests + 1 live multi-role integration suite** passing with 100% pass rate (`make test-backend`, `make test-live`).
    - **26 Flutter mobile tests across 8 test files** passing with 100% pass rate (`cd mobile && flutter test`).
    - Clean static analysis: `cd mobile && flutter analyze` reports **No issues found**.
    - Fully hermetic verification: `make check` executes through dedicated `.venv` and succeeds even with global pytest stripped from PATH.

- **What's Partial**:
  - **NFR 12 (Audio Payload Limit)**: Size validation strictly enforces 25 MB ceiling in `validate_audio_metadata`; full 25 MB sustained streaming under concurrent load unbenchmarked.
  - **NFR 13 (Screen Load Performance)**: Single endpoint responds in <50ms locally; 95th percentile under concurrent load unbenchmarked.
  - **NFR 14 (Concurrent Capacity)**: Non-blocking asynchronous FastAPI endpoints proven in unit suite; high-concurrency production load benchmarking pending.
  - **NFR 15 (Uptime SLA & Health Monitoring)**: Health probe verified at `/healthz`; long-term 99.5% monthly uptime SLA monitoring pending production telemetry.
  - **NFR 16 (Privacy & Copyright)**: User privacy attributes and email storage tested; formal GDPR/copyright legal audit pending.
  - **NFR 16.1 (Security Headers)**: Security response headers (HSTS, nosniff, DENY) verified in tests; production reverse-proxy TLS termination pending.
  - **NFR 17 (Accessibility & Usability)**: RTL layout and semantic structure verified; assistive technology and screen reader usability study pending.
  - **NFR 17.1 (WCAG 2.1 AA Compliance)**: High contrast ratios and semantic HTML verified; full automated WCAG 2.1 AA audit suite pending.
  - **NFR 17.2 (First-time Learner UX)**: Onboarding flow launches first session; formal first-time learner UX usability testing pending.
  - **NFR 18 (Fusha & Content Guidelines)**: Fusha and content heuristics verified on sample strings; full dialect NLP dictionary integration pending.
  - **NFR 21 (Compensation Model)**: Contributor compensation ledger and credit calculation tested; automated banking/payout integration pending.
  - **Mobile iOS Target**: Fully scaffolded in `mobile/ios/`; physical iOS device compilation requires macOS / Xcode.

- **What's Blocked**:
  - `mobile/ios/`: `BLOCKED-BY-PLATFORM: macOS required to build iOS target`. Flutter iOS target is fully scaffolded and committed, but compilation requires Xcode on macOS.
  - Requirement 6.8: Offline local database sync is marked `OUT-OF-SCOPE` per specification definition of done (manifest endpoint implemented at `GET /api/passages/{id}/offline-package` with offline package download).

- **Mobile Testing Levels Verified**:
  1. **Live Android Device Run**: Automated runner `scripts/run_mobile_device.py` spawns a fresh database, boots FastAPI on port 8000, establishes `adb reverse tcp:8000 tcp:8000`, executes `mobile/integration_test/app_test.dart` on Android emulator `emulator-5554` (API 33), and captures the live screen to `mobile/docs/device_flow_1.png`.
  2. **Golden Visual Regression**: 5/5 golden flow renders (`mobile/docs/flow_1.png` to `flow_5.png`) regenerated with bundled `Noto Naskh Arabic` font, confirming authentic Arabic ligatures and diacritics.
  3. **Role-Gated Widget Testing**: 26 unit and widget tests covering Contributor, Reviewer, Learner, Admin, Auth, Error Handling, and Font/Theme rendering.
  4. **Live Server Integration**: `scripts/e2e.py` exercises all five domain flows against a running backend process.

- **Hermetic `make check` Verification**:
  ```
  .venv/Scripts/python.exe seed.py -> Seed completed successfully (5 users, 3 passages)
  .venv/Scripts/python.exe scripts/e2e.py -> All 5 flows passed against live server
  .venv/Scripts/python.exe -m pytest -> 92 passed, 1 warning in 15.42s
  .venv/Scripts/python.exe -m pytest tests/test_fix_4_seed_restart.py -> 1 passed
  cd mobile && flutter analyze -> No issues found! (ran in 13.4s)
  cd mobile && flutter test -> All tests passed! (26/26 tests passed in ~5.0s)
  HERMETIC MAKE CHECK PASSED WITH STRIPPED PATH (global pytest: None)
  ```

- **The Five Most Important Things the Owners Must Decide or Fix in Their Diagrams**:
  1. **Post-Flag Lifecycle for `ContentStatus.FLAGGED`**: In Sequence 5 (`h_seq5_flagging`), when an Admin takes action, `ReviewableContent.markFlagged()` sets status to `FLAGGED`. However, the diagrams do not specify exit transitions from `FLAGGED` (e.g. unflag/re-verify, permanent deletion, or contributor remediation). An explicit state machine diagram for `ContentStatus` should be added.
  2. **Persistence Repository Pattern**: The class diagram treats queries like `Passage.browse()` and `Passage.awaitingRecording()` as static class methods in memory. The owners should introduce a repository stereotype (e.g., `<<Repository>> PassageRepository`) or persistence interface to formalize the database mapping contract.
  3. **Formalize `CLAIM_TTL` Constant**: In `class-diagram.puml`, a note mentions "Every claim has TTL usually about 72 hours", and Sequence 1 refers to `CLAIM_TTL`. This should be formalized as a static constant attribute on `Passage` (e.g., `+ CLAIM_TTL: Duration = 72 hours`).
  4. **Mutating Operations on `Reputation`**: The `Reputation` class in `class-diagram.puml` defines properties (`score`, `approvalRate`, `totalSubmissions`), but defines zero operations. An operation such as `+ recordSubmissionResult(isApproved: boolean): void` should be added to show how reputations evolve upon review decisions.
  5. **Offline Sync Protocol Contract (Req 6.8 / `UC_Offline`)**: While `h_uc.puml` connects Learner to `Download Audio for Offline`, no sequence diagram or class model specifies the offline synchronization and caching architecture. The owners should specify whether this is an offline archive bundle (JSON + audio files) or an active delta-synchronization protocol.

---

## Stack Decisions
- **Backend & REST API**: Python 3.14 + FastAPI + Uvicorn + Pydantic v2.
- **Domain Modeling**: Direct object-oriented classes mirroring `class-diagram.puml` exactly with 100% adherence to all 19 classes, 8 enums, and 47 operations.
- **Persistence**: SQLite with WAL mode + repository pattern (`asghi/repository.py`), strict constraints (`active_claims`, `UNIQUE(reviewer_id, content_id)`, `CHECK(author_id IS NULL <=> origin = 'AI')`), and atomic transactions (`submit_verdict_tx`, `record_answer_tx`, `resolve_flag_tx`).
- **Authentication**: JWT Bearer tokens (PyJWT) with PBKDF2/SHA-256 password hashing, configurable `SECRET_KEY` from environment with production fail-fast check.
- **Mobile Client**: Flutter 3.47.0 / Dart 3.13.0, Flutter Riverpod 3.0, Dio HTTP client with JWT interceptors, bundled `Noto Naskh Arabic` typography, and WCAG 2.1 AA accessible color palette.
- **Hermetic Toolchain**: GNU Make with isolated `.venv` environment, auto-discovered Flutter SDK, and pinned dependency tracking.
- **Testing**: `pytest` for backend unit, integration, concurrency, and durability tests; `flutter test` for mobile widget and golden tests; `integration_test` for live device test; unified `make check`.

---

## Deliverables & Run Instructions

### 1. Unified Automated Verification
Run all automated checks in one command (hermetic via `.venv`):
```bash
make check
```
Or run individual verification steps:
- Setup environment: `make setup`
- Seed database: `make seed`
- Run backend pytest suite: `make test-backend`
- Run live server integration: `make test-live`
- Analyze and test mobile app: `make test-mobile`
- Run live Android device integration: `python scripts/run_mobile_device.py`

### 2. Starting the Backend Server
```bash
.venv/Scripts/python.exe -m uvicorn asghi.api:app --reload --host 127.0.0.1 --port 8000
```
- Interactive API documentation: `http://127.0.0.1:8000/docs`
- Health check probe: `http://127.0.0.1:8000/healthz`
- Responsive Arabic Web UI: `http://127.0.0.1:8000/`

### 3. Running the Mobile App
```bash
cd mobile
flutter run
```
To run integration test on Android device/emulator:
```bash
python scripts/run_mobile_device.py
```
To build debug APK:
```bash
cd mobile
flutter build apk --debug
# Output: mobile/build/app/outputs/flutter-apk/app-debug.apk
```
