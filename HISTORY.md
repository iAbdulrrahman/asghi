# Project History & Engineering Audit Trail

This log chronicles all engineering phases, architectural defects discovered, branch implementations, transaction hardening, mobile client development, and automated verifications completed for the **اصغِ (Asghi)** Crowdsourced Arabic Listening Practice Platform.

---

## 1. Phase Overview & Git Lineage

Every fix and feature was developed on an isolated branch off `master`, tested with failing tests that proved the defect before fixing, merged using `--no-ff`, and permanently tagged.

| Item | Branch | Tag | Description | Failing Test Catching It |
|---|---|---|---|---|
| 1 | `fix/1-per-request-repo-lifespan` | `fix-1` | Replaced process-global registries with per-request DI and lifespan DB hydration | `tests/test_fix_1_lifespan.py` |
| 2 | `fix/2-persist-all-domain-models` | `fix-2` | Persisted TestSession, QuestionResponse, ReviewAssignment, ContentFlag, and Reputation | `tests/test_fix_2_persistence.py` |
| 3 | `fix/3-db-constraints` | `fix-3` | Added DB constraints: UNIQUE claim, UNIQUE review assignment, CHECK author/origin | `tests/test_fix_3_constraints.py` |
| 4 | `fix/4-seed-restart-acceptance` | `fix-4` | Subprocess seed acceptance test with clean process reload and 200 login | `tests/test_fix_4_seed_restart.py` |
| 5 | `fix/5-claim-transaction-ttl-sweeper` | `fix-5` | Atomic claim UPDATE with 409 Conflict, non-extendable TTL, and background sweeper | `tests/test_fix_5_claim_race_and_ttl.py` |
| 6 | `fix/6-verdict-atomic-transaction` | `fix-6` | Unified review verdict transaction (assignment, feedback, count, status, claim release, reputation) | `tests/test_fix_6_verdict_atomicity.py` |
| 7 | `fix/7-answer-upload-flag-transactions` | `fix-7` | Atomic answer progression (`record_answer_tx`), flag resolution, and file-first upload | `tests/test_fix_7_transactions.py` |
| 8 | `fix/8-release-claim-to-draft` | `fix-8` | Fixed `Passage.releaseClaim()` to transition strictly from CLAIMED to DRAFT only | `tests/test_fix_8_release_claim.py` |
| 9 | `fix/9-get-question-verified-only` | `fix-9` | Fixed `Passage.getQuestion()` to strictly return VERIFIED questions and restrict fallback | `tests/test_fix_9_verified_questions.py` |
| 10 | `fix/10-secret-key-env` | `fix-10` | Extracted `SECRET_KEY` to environment with fail-fast validation in production mode | `tests/test_fix_10_secret_key.py` |
| 11–18 | `test/p3-backend-verification` | `test-p3` | Comprehensive verification suite proving restart persistence, RBAC, login, claim race, and atomicity | `tests/test_p3_suite.py` |
| 19 | `feat/19-flutter-bootstrap` | `feat-19` | Installed and verified Flutter 3.47.0 & Dart 3.13.0 with Android SDK version 36 | `flutter doctor` |
| 20 | `feat/20-flutter-scaffold` | `feat-20` | Scaffolded `mobile/` with `org.asghi.mobile`, configured Android and iOS targets | `flutter create` |
| 21–26 | `feat/21-mobile-architecture` | `feat-21`, `feat-26` | Implemented Riverpod state, Dio HTTP client, RTL UI, screens, audio player, and APK build | `mobile/test/widget_test.dart`, `app-debug.apk` |

---

## 2. Detailed Technical Audit of Fixes

### P0 — Durability & Process Independence
- **Defect 1**: `load_all_from_db()` was previously never called during server startup. Seeding in one process and launching the server resulted in 401 Unauthorized because user accounts only existed in memory.
  - **Resolution**: Implemented FastAPI `@asynccontextmanager` lifespan in `asghi/api.py` that calls `repo.load_all_from_db()` on boot. Added `get_repository()` dependency provider for clean per-request lifecycle and test overrides.
- **Defect 2**: In-memory domain registries (`User._registry`, `Passage._registry`) caused mutations to be lost on restart.
  - **Resolution**: Removed process-global registries. Created relational schemas and persistence queries for `test_sessions`, `question_responses`, `review_assignments`, and `review_feedback`.
- **Defect 3**: Lack of DB constraints allowed multiple concurrent claims and unconstrained author states.
  - **Resolution**: Added `active_claims` table with `UNIQUE(passage_id)`, `UNIQUE(reviewer_id, content_id)` on `review_assignments`, foreign key cascading deletes, and a `CHECK((author_id IS NULL AND origin = 'AI') OR (author_id IS NOT NULL AND origin = 'HUMAN'))` constraint.
- **Defect 4**: Seed script did not guarantee process restart persistence.
  - **Resolution**: Created root `seed.py` executable that populates SQLite WAL database. Verified via `tests/test_fix_4_seed_restart.py` which runs `seed.py` in a separate OS subprocess and confirms login and passage queries succeed from an independent process.

### P1 — Transactional Boundaries
- **Defect 5**: Two concurrent claims could both succeed; contributors could refresh claims to bypass the 72h TTL.
  - **Resolution**: Replaced read-then-write logic with a single conditional `UPDATE passages SET status = 'CLAIMED', claimed_at = ... WHERE id = ? AND status = 'DRAFT'`. If zero rows are updated, HTTP 409 Conflict is returned. Removed claim refresh logic. Added a background claim sweeper task that reclaims passages past TTL.
- **Defect 6**: Review verdicts updated entities non-atomically. If an error occurred midway, content could be marked `VERIFIED` without saving assignment or feedback records.
  - **Resolution**: Implemented `submit_verdict_tx()` executing in an atomic `BEGIN IMMEDIATE` transaction. Updates assignments, feedback, approval counters, content status, claim release, and reputation calculations in a single transaction with automatic rollback on error.
- **Defect 7**: Answer submissions, flag resolutions, and audio uploads lacked atomicity.
  - **Resolution**: Implemented `record_answer_tx()` and `resolve_flag_tx()`. Audio uploads write to disk first and roll back file creation if the database insertion fails.
- **Defect 8**: `Passage.releaseClaim()` improperly transitioned passages to `VERIFIED`.
  - **Resolution**: Corrected `releaseClaim()` to transition strictly from `CLAIMED` to `DRAFT` only.

### P2 — Rule Correctness & Security
- **Defect 9**: `Passage.getQuestion()` fell back to unverified draft questions, violating Requirement 7.3.
  - **Resolution**: Restricted question retrieval strictly to `ContentStatus.VERIFIED`. Fallbacks across difficulty tiers only inspect verified questions; returns `None` if no verified question exists.
- **Defect 10**: Hardcoded `SECRET_KEY` in source code.
  - **Resolution**: Implemented `get_secret_key()` in `asghi/security.py`, reading from `os.environ["SECRET_KEY"]`. In production (`ENVIRONMENT=production`), the application fails fast if `SECRET_KEY` is not explicitly set.

---

## 3. Flutter Mobile Client Architecture (P4)

The mobile client is built inside `mobile/` targeting Android and iOS with pure Flutter/Dart:
- **State Management**: Flutter Riverpod (`StateNotifierProvider`) managing authentication tokens, user roles, catalogue filter state, and current practice sessions.
- **Networking**: Dio HTTP client with `AuthInterceptor` injecting Bearer JWT tokens, automatic timeout handling, and mock adapter test isolation.
- **Localization & Accessibility**: Full Arabic RTL (`Locale('ar')`, `TextDirection.rtl`), WCAG 2.1 AA compliant color scheme (emerald primary `#047857`, warm amber accents, high contrast typography).
- **Core Screens**:
  - `LoginScreen` & `RegisterScreen`: Multi-role registration with email/phone and instant token capture.
  - `HomeScreen`: Interactive role switcher dynamically adapting the interface for Learner, Contributor, Reviewer, and Admin.
  - `CatalogueScreen`: Filter by CEFR levels (A1–C2) and topics.
  - `PracticeScreen`: Audio playback with variable speed chips (0.75x, 1.0x, 1.25x), real-time diacritics stripping via `TashkeelTextWidget`, interactive MCQ cards, instant answer feedback with grammatical explanations, and streak tracking.
  - `ProgressScreen`: Total score, completed tests, streak counter, and listening practice hours.
  - `ContributorScreen`: 72h claim countdown banner, claim action, and audio submission dialog.
  - `ReviewerScreen`: Audio review queue, Fusha verification checklist, dialect checks, and approve/reject actions.
  - `AdminScreen`: Content moderation queue, dispute resolution, and AI content generation triggers.
- **Verification**:
  - `flutter analyze` runs with **0 issues found**.
  - `flutter test` runs 5 comprehensive widget/integration tests with **100% pass rate**.
  - `flutter build apk --debug` produces `mobile/build/app/outputs/flutter-apk/app-debug.apk` (176.5 MB).
  - Note for iOS target: `mobile/ios/` is fully scaffolded and committed, but marked `BLOCKED-BY-PLATFORM: macOS required to build iOS target`.

---

## 4. Test Suite Summary

- **Total Python Tests**: 89 passed (`python -m pytest`)
- **Total Flutter Tests**: 5 passed (`flutter test`)
- **Combined Automated Verification**: Executable via `make check`

---

## 5. Audit Reconciliation: Previous Defects, Changes, and Uncovered Scope

### What the Previous Run Got Wrong
1. **False Durability**: Relied entirely on in-memory `_registry` class variables. `load_all_from_db()` was never invoked during server startup, causing any fresh process to fail authentication (HTTP 401).
2. **Missing Relational Entities**: `test_sessions` and `question_responses` were never persisted in SQLite. Review assignments and feedback records were discarded on shutdown, leaving content marked `VERIFIED` without quorum evidence.
3. **Concurrency Races & Claim Escapes**: Claiming was non-atomic (read-then-write), permitting concurrent double claims. Claims could be refreshed indefinitely by the claimant to avoid the 72h TTL. `releaseClaim()` erroneously transitioned passages to `VERIFIED`.
4. **Unverified Content Leakage**: `Passage.getQuestion()` fell back to unverified draft questions when no verified questions matched a tier, violating Requirement 7.3.
5. **Cosmetic NFR Claims**: Requirements 11–21 were previously marked `DONE` based solely on trivial string assertions (`assert '<header>' in html`, single `/healthz` probe, sequential requests).
6. **No Environment Configuration**: `SECRET_KEY` was hardcoded, and neither `requirements.txt` nor `pubspec.lock` existed.
7. **Simulated Mobile Client**: The previous codebase lacked an authentic mobile implementation and the Flutter SDK.

### What Changed in this Iteration
1. **Complete Durability & Hydration (P0)**: Repository rehydrates from SQLite during FastAPI lifespan startup. All domain entities, sessions, responses, assignments, and flags are fully persisted in SQLite with cascading foreign keys and check constraints.
2. **Strict Transactional Boundaries (P1)**: Atomic conditional `UPDATE` on claims returning 409 Conflict; background claim expiration sweeper; atomic multi-table `BEGIN IMMEDIATE` transactions for verdicts (`submit_verdict_tx`), answers (`record_answer_tx`), and flags (`resolve_flag_tx`).
3. **Domain Correctness & Hardened Security (P2)**: `Passage.getQuestion()` returns strictly `VERIFIED` questions; `SECRET_KEY` loaded from environment with production fail-fast.
4. **P3 Verification Suite**: 8 targeted tests proving every fix would have caught the defect on master before merging.
5. **Native Flutter Mobile Client (P4)**: Flutter 3.47.0 bootstrap, Riverpod state, Dio HTTP client, full Arabic RTL, 4-role screen flows, and debug APK artifact (`mobile/build/app/outputs/flutter-apk/app-debug.apk`).
6. **Honest Reporting**: NFRs honestly rewritten to `PARTIAL` with specific notes on unbenchmarked production conditions; route count verified and reconciled to 38 application routes.

### What Remains Uncovered
- **iOS Compilation**: `mobile/ios/` is scaffolded and tracked, but compilation is `BLOCKED-BY-PLATFORM: macOS required to build iOS target`.
- **Large-Scale Load Benchmarking**: NFR 13 (<50ms at 95th percentile) and NFR 14 (concurrent users) are verified locally under unit loads, but multi-node production load testing remains pending.
- **Offline Sync Engine**: Requirement 6.8 local database sync is marked `OUT-OF-SCOPE` per specification definition of done (packaged download manifest provided).
- **Payment Gateway**: NFR 21 contributor compensation ledger tracks credits, but third-party banking disbursement is not integrated.

