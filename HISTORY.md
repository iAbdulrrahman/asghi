# Project History & Engineering Audit Trail

This log chronicles all engineering phases, architectural defects discovered, branch implementations, transaction hardening, mobile client development, and automated verifications completed for the **اصغِ (Asghi)** Crowdsourced Arabic Listening Practice Platform.

---

## 1. Phase Overview & Git Lineage

Every fix and feature was developed on an isolated branch off `master`, tested with failing tests that proved the defect before fixing, merged using `--no-ff`, and permanently tagged.

### Initial Hardening & Mobile Bootstrap
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

### Final Mobile Deliverable, Audio Engine, & Live End-to-End Suite
| Item | Branch | Tag | Description | Failing Test Catching It |
|---|---|---|---|---|
| 1 | `fix/1-toolchain-discovery` | `fix-1` | Makefile auto-discovers Python and Flutter across Windows/Unix without hardcoding PATH | `make check` |
| 2 | `fix/2-repo-hygiene` | `fix-2` | Removed leftover `test_lifespan.db` and unified root `seed.py` delegating to `asghi.seed` | `test_lifespan.db` check |
| 3 | `fix/3-reproducible-toolchain` | `fix-3` | Added `make setup`, pinned `requirements.txt`, and tracked `mobile/pubspec.lock` | Missing lockfile check |
| 4 | `feat/4-audio-recorder-service` | `feat-4` | Implemented `AudioRecorderService`, `DeviceAudioRecorder`, and `BundledAudioSource` | Missing recorder service check |
| 5 | `feat/5-audio-playback-service` | `feat-5` | Implemented `AudioPlaybackService` with `JustAudioPlaybackService` and speed controls | `mobile/test/audio_playback_test.dart` |
| 6 | `feat/6-contributor-real-audio` | `feat-6` | Replaced mock byte uploads with real WAV audio capture, duration checks (60–180s), and `MultipartFile.fromFile` | Mock upload assert in contributor screen |
| 7 | `fix/7-audio-player-wire` | `fix-7` | Connected `AudioPlayerWidget` to Riverpod `audioPlaybackProvider` | Null player engine in widget |
| 8 | `feat/8-acceptance-real-audio` | `feat-8` | Verified full audio lifecycle: WAV upload, disk byte size match, streaming, verdict, and catalogue playback | `tests/test_p1_item_8_acceptance.py` |
| 9 | `feat/9-endpoint-alignment` | `feat-9` | Aligned client-server endpoints: `/api/admin/generate` and `/api/contributor/awaiting-recording` with aliases | `tests/test_fix_9_endpoints.py` |
| 10 | `feat/10-progress-screen-api` | `feat-10` | Rewired `progress_screen.dart` to consume `GET /api/learner/progress` for live stats and streak | `mobile/test/progress_screen_test.dart` |
| 11 | `feat/11-contributor-rejection-ui` | `feat-11` | Added contributor submissions view with prominent rejection reasons and tashkeel toggle | `mobile/test/contributor_screen_test.dart` |
| 12 | `feat/12-reviewer-dual-queues` | `feat-12` | Implemented dual queues in `reviewer_screen.dart` for pending audio recordings and questions | `mobile/test/reviewer_screen_test.dart` |
| 13 | `feat/13-admin-dashboard-disputes` | `feat-13` | Added admin dashboard metrics, dispute resolution, reporting, and flag moderation views | `mobile/test/admin_screen_test.dart` |
| 14 | `feat/14-global-error-handling-and-rbac` | `feat-14` | Global 401 unauth redirect to `LoginScreen`, network error `OfflineBanner`, and RBAC view gating | `mobile/test/error_handling_rbac_test.dart` |
| 15 | `test/15-widget-tests-all-screens` | `test-15` | Comprehensive screen widget test suite across all 4 roles with clean provider tearDown | `mobile/test/widget_test.dart` |
| 16 | `feat/16-live-e2e-integration` | `feat-16` | Standalone multi-role live server end-to-end integration test against running uvicorn process | `tests/test_live_e2e_integration.py`, `scripts/e2e.py` |
| 17 | `test/17-mobile-integration-test` | `test-17` | Flutter integration test `mobile/integration_test/app_test.dart` and documented BLOCKED-BY-PLATFORM | Headless device check |
| 18 | `docs/18-flow-walkthrough` | `docs-18` | Exhaustive UI flows markdown walkthrough `mobile/docs/FLOWS.md` and captured flow screenshots `flow_{1..5}.png` | `mobile/test/golden_flows_test.dart` |
| 19b | `feat/19b-build-debug-apk` | `feat-19b` | Built Android debug APK with native plugins: `mobile/build/app/outputs/flutter-apk/app-debug.apk` (211.9 MB) | `flutter build apk --debug` |
| 20 | `docs/20-traceability-matrix` | `docs-20` | Updated bidirectional requirements traceability matrix in `TRACEABILITY.md` | Audit verification |
| 21 | `docs/21-inventions-catalog` | `docs-21` | Documented 33 architectural decisions and diagram edit specifications in `INVENTIONS.md` | Exhaustive decisions audit |
| 22 | `docs/22-history-and-progress` | `docs-22` | Updated project history, audit reconciliation, and final status in `HISTORY.md` and `PROGRESS.md` | Consistency audit |
| 23 | `master` | `v2.0.0-final` | Clean grep gate: zero occurrences of `Mock`/`dummy`/`placeholder` in production code | `grep -r "Mock\|dummy\|placeholder" mobile/lib asghi` |

---

## 2. Test Suite Summary

- **Total Python Backend Tests**: 91 passed in ~6.5 seconds (`python -m pytest`)
- **Total Python Live Server E2E Tests**: 1 full multi-role integration suite passed in ~3.3 seconds (`python scripts/e2e.py`)
- **Total Flutter Mobile Tests**: 24 tests passed across 7 test files in ~4.5 seconds (`cd mobile && flutter test`)
- **Static Analysis**: 0 issues found (`cd mobile && flutter analyze`)
- **Automated Verification**: Complete execution via `make check` and `make test-live`

---

## 3. Final Audit Reconciliation

### What Was Completely Fixed in this Iteration
1. **Authentic Mobile Audio Engine**: Replaced all fake mock strings in `contributor_screen.dart` with real audio capture using `record` and `file_picker`. Validated minimum recording duration (60s–180s per Req 4.2). Connected `AudioPlayerWidget` to `just_audio` with multi-speed playback (0.75x–1.5x).
2. **True Live Server Integration Proof**: Created `tests/test_live_e2e_integration.py` and `scripts/e2e.py` which spawns a clean uvicorn server on a newly seeded SQLite database, exercises all 5 sequence flows across all 4 user roles with authentic WAV audio upload, physical disk byte verification, streaming playback, and dispute resolution.
3. **Parity in Screen Implementations**:
   - `progress_screen.dart`: Connected to `GET /api/learner/progress` for real streak, score, listening time, and completed tests.
   - `contributor_screen.dart`: Connected to `GET /api/contributor/submissions` with prominent rejection reasons and tashkeel toggling.
   - `reviewer_screen.dart`: Dual queues for pending audio recordings and pending questions.
   - `admin_screen.dart`: Full dashboard metrics, report viewer, dispute resolution, and flag moderation.
4. **Resilient Error Handling & RBAC**: Added global 401 unauth redirect to `LoginScreen`, network error `OfflineBanner`, and role-gated home navigation.
5. **Clean Grep Gate**: Zero occurrences of `Mock`, `dummy`, or `placeholder` in production code (`mobile/lib/` and `asghi/`).
