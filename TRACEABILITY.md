# TRACEABILITY MATRIX

## (a) Requirement -> Implementation Mapping

| Req ID | status | implemented by (file :: symbol or METHOD /path) | test that proves it |
|---|---|---|---|
| 1 | DONE | `asghi/domain/user.py::User` | `tests/test_domain.py::test_user_roles_and_registration` |
| 1.1 | DONE | `asghi/domain/enums.py::UserRole`, `asghi/domain/user.py::User.addRole` | `tests/test_domain.py::test_user_roles_and_registration` |
| 1.2 | DONE | `asghi/domain/user.py::User.register`, `POST /api/auth/register`, `POST /api/auth/login`, `mobile/lib/screens/auth/login_screen.dart`, `register_screen.dart` | `tests/test_auth_api.py::test_register_and_login_email_or_phone`, `tests/test_fix_4_seed_restart.py`, `tests/test_live_e2e_integration.py`, `mobile/test/register_screen_test.dart`, `scripts/ui_smoke.py` (live device login across 4 roles) |
| 1.3 | DONE | `asghi/domain/user.py::User.completeProfile`, `POST /api/users/profile`, `mobile/lib/screens/auth/register_screen.dart` | `tests/test_auth_api.py::test_complete_profile`, `tests/test_live_e2e_integration.py` |
| 2 | DONE | `asghi/domain/passage.py::Passage`, `GET /api/passages` (verified-only filter with verified audio) | `tests/test_fix_2_catalogue_filter.py::test_catalogue_filters_unverified_passages`, `tests/test_passage_api.py::test_catalogue_maintenance` |
| 2.1 | DONE | `asghi/domain/passage.py::Passage`, `asghi/domain/audio_recording.py::AudioRecording`, `asghi/domain/question.py::Question` | `tests/test_domain.py::test_passage_structure` |
| 2.2 | DONE | `asghi/domain/enums.py::Origin`, `asghi/domain/reviewable_content.py::ReviewableContent.origin`, `asghi/repository.py` | `tests/test_domain.py::test_passage_origin_tagging`, `tests/test_fix_3_constraints.py::test_check_author_id_origin_equivalence` |
| 2.3 | DONE | `asghi/domain/passage.py::Passage.level`, `topic`, `duration` | `tests/test_domain.py::test_passage_metadata` |
| 3 | DONE | `asghi/domain/ai_engine.py::AIEngine`, `POST /api/admin/generate` | `tests/test_ai_and_review.py::test_ai_generation_and_human_review` |
| 3.1 | DONE | `asghi/domain/ai_engine.py::AIEngine.generatePassageText`, `generateQuestions`, `mobile/lib/screens/admin/admin_screen.dart` | `tests/test_fix_11_admin_generation_feedback.py`, `tests/test_ai_and_review.py::test_ai_content_generator`, `mobile/test/admin_screen_test.dart` |
| 3.2 | DONE | `asghi/domain/ai_engine.py::AIEngine.generateQuestions` | `tests/test_ai_and_review.py::test_ai_question_generation_difficulties` |
| 3.3 | DONE | `asghi/domain/enums.py::ContentStatus.PENDING_REVIEW`, `asghi/domain/ai_engine.py::AIEngine` | `tests/test_ai_and_review.py::test_ai_content_requires_human_review` |
| 4 | DONE | `asghi/domain/contributor_profile.py::ContributorProfile`, `POST /api/contributor/claim` | `tests/test_contributor_api.py::test_contributor_recording_cycle` |
| 4.1 | DONE | `asghi/domain/passage.py::Passage.awaitingRecording`, `GET /api/contributor/awaiting-recording`, `POST /api/contributor/claim`, `mobile/lib/screens/contributor/contributor_screen.dart` | `tests/test_contributor_api.py::test_browse_and_claim_passages`, `tests/test_fix_5_claim_race_and_ttl.py`, `tests/test_live_e2e_integration.py`, `mobile/test/contributor_screen_test.dart`, `scripts/ui_smoke.py` |
| 4.2 | DONE | `asghi/domain/contributor_profile.py::ContributorProfile.recordOrUploadAudio`, `POST /api/contributor/submit-audio` (advances passage to `PENDING_REVIEW`), `mobile/lib/core/audio_recorder_service.dart`, `mobile/lib/screens/contributor/contributor_screen.dart` | `tests/test_fix_4_submit_audio_advances_passage.py`, `tests/test_contributor_api.py::test_upload_audio_recording`, `tests/test_p1_item_8_acceptance.py`, `tests/test_live_e2e_integration.py`, `mobile/test/contributor_screen_test.dart` |
| 4.3 | DONE | `asghi/domain/contributor_profile.py::ContributorProfile.toggleTashkeel`, `GET /api/passages/{id}/text`, `mobile/lib/widgets/tashkeel_text_widget.dart` | `tests/test_contributor_api.py::test_passage_display_and_tashkeel_toggle`, `mobile/test/widget_test.dart::TashkeelTextWidget toggles diacritics stripping correctly` |
| 4.4 | DONE | `asghi/domain/enums.py::AttributionType`, `asghi/domain/audio_recording.py::AudioRecording.attribution`, `mobile/lib/screens/contributor/contributor_screen.dart` | `tests/test_contributor_api.py::test_attribution_choice`, `tests/test_p1_item_8_acceptance.py` |
| 5 | DONE | `asghi/domain/reviewer_profile.py::ReviewerProfile`, `POST /api/reviewer/decision`, `asghi/repository.py::submit_verdict_tx`, `mobile/lib/screens/reviewer/reviewer_screen.dart` | `tests/test_fix_8_reviewer_verdict_passage_status.py`, `tests/test_review_api.py::test_reviewer_verification_flow`, `tests/test_fix_6_verdict_atomicity.py`, `tests/test_live_e2e_integration.py`, `mobile/test/reviewer_screen_test.dart` |
| 5.1 | DONE | `asghi/domain/reviewer_profile.py::ReviewerProfile.getAudioFile`, `createFeedback`, `submitDecision`, `mobile/lib/core/audio_playback_service.dart`, `mobile/lib/widgets/audio_player_widget.dart`, `mobile/lib/screens/reviewer/reviewer_screen.dart` | `tests/test_review_api.py::test_reviewer_evaluation`, `tests/test_p1_item_8_acceptance.py`, `tests/test_live_e2e_integration.py`, `mobile/test/reviewer_screen_test.dart` |
| 5.2 | DONE | `asghi/domain/reviewable_content.py::ReviewableContent.meetsThreshold` | `tests/test_review_api.py::test_specialist_vs_general_reviewers_threshold`, `tests/test_live_e2e_integration.py` |
| 5.3 | DONE | `asghi/domain/reviewer_profile.py::ReviewerProfile.assignReview`, `POST /api/reviewer/assignments` | `tests/test_review_api.py::test_prevent_author_self_review` |
| 5.4 | DONE | `asghi/domain/admin_profile.py::AdminProfile.resolveDispute`, `POST /api/admin/disputes/{contentId}/resolve`, `mobile/lib/screens/admin/admin_screen.dart` | `tests/test_fix_5_admin_flag_resolution.py`, `tests/test_review_api.py::test_dispute_resolution_policy`, `tests/test_live_e2e_integration.py`, `mobile/test/admin_screen_test.dart` |
| 5.5 | DONE | `asghi/domain/review_feedback.py::ReviewFeedback.isFusha`, `dialectFree`, `mobile/lib/screens/reviewer/reviewer_screen.dart` | `tests/test_review_api.py::test_fusha_and_dialect_free_verification`, `tests/test_live_e2e_integration.py` |
| 6 | DONE | `asghi/domain/learner_profile.py::LearnerProfile`, `asghi/domain/test_session.py::TestSession`, `mobile/lib/screens/learner/practice_screen.dart` | `tests/test_learner_api.py::test_learner_full_practice_session`, `tests/test_live_e2e_integration.py`, `scripts/ui_smoke.py` |
| 6.1 | DONE | `asghi/domain/passage.py::Passage.browse`, `GET /api/learner/browse`, `POST /api/learner/play`, ready `audioUrl` (`/api/audio/<file>`), `mobile/lib/core/audio_playback_service.dart`, `mobile/lib/widgets/audio_player_widget.dart` | `tests/test_fix_1_audio_url_and_playback.py`, `tests/test_learner_api.py::test_browse_and_play_verified_audio`, `mobile/test/audio_playback_test.dart`, `tests/test_live_e2e_integration.py` |
| 6.2 | DONE | `asghi/domain/learner_profile.py::LearnerProfile.startSession`, `POST /api/learner/sessions` (validates non-empty questions), `mobile/lib/screens/learner/practice_screen.dart` | `tests/test_fix_12_empty_session_validation.py`, `tests/test_learner_api.py::test_start_and_run_listening_test`, `tests/test_live_e2e_integration.py` |
| 6.3 | DONE | `asghi/domain/passage.py::Passage.getQuestion`, `asghi/domain/enums.py::Difficulty`, `mobile/lib/screens/learner/practice_screen.dart` | `tests/test_domain.py::test_passage_difficulty_tiers`, `tests/test_live_e2e_integration.py` |
| 6.4 | DONE | `asghi/domain/test_session.py::TestSession.adaptDifficulty`, `mobile/lib/screens/learner/practice_screen.dart` | `tests/test_learner_api.py::test_adaptive_difficulty_progression`, `tests/test_live_e2e_integration.py` |
| 6.5 | DONE | `asghi/domain/question_response.py::QuestionResponse.evaluate`, `asghi/domain/test_session.py::TestSession.submitAnswer`, `asghi/repository.py::record_answer_tx` | `tests/test_learner_api.py::test_score_responses_and_explanations`, `tests/test_fix_7_transactions.py`, `tests/test_live_e2e_integration.py` |
| 6.6 | DONE | `asghi/domain/learner_progress.py::LearnerProgress.update`, `GET /api/learner/progress`, `mobile/lib/screens/learner/progress_screen.dart` | `tests/test_fix_14_learner_progress_completed.py`, `tests/test_learner_api.py::test_learner_progress_tracking`, `mobile/test/progress_screen_test.dart`, `tests/test_live_e2e_integration.py` |
| 6.7 | DONE | `asghi/domain/learner_profile.py::LearnerProfile.flagContent`, `POST /api/learner/flag`, `asghi/repository.py::resolve_flag_tx`, `mobile/lib/screens/admin/admin_screen.dart` | `tests/test_fix_10_admin_flags_refresh.py`, `tests/test_flagging_api.py::test_flag_problematic_content`, `tests/test_fix_7_transactions.py`, `tests/test_live_e2e_integration.py`, `mobile/test/admin_screen_test.dart` |
| 6.8 | OUT-OF-SCOPE | Offline local database sync marked OUT-OF-SCOPE per specification definition of done; API offline package manifest provided at `GET /api/passages/{id}/offline-package` | `tests/test_learner_api.py::test_offline_package_endpoint` |
| 7 | DONE | `asghi/domain/question_author.py::QuestionAuthor`, `POST /api/questions` | `tests/test_question_authoring.py::test_question_authoring_all_roles` |
| 7.1 | DONE | `ContributorProfile.authorQuestion`, `ReviewerProfile.authorQuestion`, `AdminProfile.authorQuestion` | `tests/test_question_authoring.py::test_author_question_roles` |
| 7.2 | DONE | `AIEngine.generateQuestions`, `QuestionAuthor.generateQuestions` | `tests/test_question_authoring.py::test_balanced_difficulty_generation` |
| 7.3 | DONE | `asghi/domain/passage.py::Passage.getQuestion`, `POST /api/reviewer/questions/{id}/review`, `mobile/lib/screens/reviewer/reviewer_screen.dart` | `tests/test_fix_9_verified_questions.py::test_unverified_question_never_served`, `mobile/test/reviewer_screen_test.dart` |
| 8 | DONE | `asghi/domain/reviewable_content.py::ReviewableContent.reject`, `GET /api/contributor/submissions` (author matching by user ID), `mobile/lib/screens/contributor/contributor_screen.dart` | `tests/test_fix_3_contributor_submissions_author.py`, `tests/test_contributor_api.py::test_rejection_explanation_visible_to_contributor`, `mobile/test/contributor_screen_test.dart` |
| 9 | DONE | `asghi/domain/test_session.py::TestSession.submitAnswer`, `asghi/domain/question.py::Question.explanation`, `mobile/lib/screens/learner/practice_screen.dart` | `tests/test_learner_api.py::test_actionable_feedback_on_wrong_answer`, `tests/test_live_e2e_integration.py` |
| 10 | DONE | `asghi/domain/admin_profile.py::AdminProfile`, `/api/admin/*`, `mobile/lib/screens/admin/admin_screen.dart` | `tests/test_admin_api.py::test_admin_governance_and_moderation`, `tests/test_live_e2e_integration.py` |
| 10.1 | DONE | `asghi/domain/reputation.py::Reputation`, `GET /api/users/{id}/reputation` | `tests/test_admin_api.py::test_contributor_and_reviewer_reputation` |
| 10.2 | DONE | `asghi/domain/admin_profile.py::AdminProfile`, `GET /api/admin/dashboard`, `GET /api/admin/report`, `mobile/lib/screens/admin/admin_screen.dart` | `tests/test_fix_9_admin_dashboard_metrics.py`, `tests/test_admin_api.py::test_admin_dashboard_and_reporting`, `tests/test_live_e2e_integration.py`, `mobile/test/admin_screen_test.dart` |
| 11 | DONE | Native Flutter Mobile Client (`mobile/lib/main.dart`, `mobile/lib/screens/*`, `mobile/docs/FLOWS.md`, `mobile/docs/live_learner.png`, `mobile/docs/live_contributor.png`, `mobile/docs/live_reviewer.png`, `mobile/docs/live_admin.png`, `mobile/docs/flow_{1..5}.png`) & responsive viewport in `asghi/static/index.html` | `scripts/ui_smoke.py` (live run on Android emulator `emulator-5554` via `make device-check`), `tests/test_fix_18_ui_smoke_and_target.py`, `mobile/test/widget_test.dart`, `mobile/test/golden_flows_test.dart`, `tests/test_live_e2e_integration.py`, `tests/test_nfr.py::test_nfr11_mobile_responsive_contract` |
| 12 | PARTIAL | Size validation enforces 25 MB ceiling in `validate_audio_metadata`; full 25 MB streaming load unbenchmarked | `tests/test_nfr.py::test_nfr12_audio_upload_25mb_contract` |
| 13 | PARTIAL | Single endpoint responds in <50ms locally; 95th percentile under concurrent load unbenchmarked | `tests/test_nfr.py::test_nfr13_screen_load_performance` |
| 14 | PARTIAL | Non-blocking async endpoints proven in unit suite; high-concurrency production benchmarking pending | `tests/test_nfr.py::test_nfr14_concurrent_capacity` |
| 15 | PARTIAL | Health probe verified at `/healthz`; long-term 99.5% monthly uptime SLA monitoring pending | `tests/test_nfr.py::test_nfr15_uptime_and_healthz` |
| 16 | PARTIAL | User privacy attributes and email storage tested; formal GDPR/copyright legal audit pending | `tests/test_nfr.py::test_nfr16_privacy_and_copyright` |
| 16.1 | PARTIAL | Security response headers (HSTS, nosniff, DENY) verified in tests; production reverse-proxy TLS termination pending | `tests/test_nfr.py::test_nfr16_1_security_headers` |
| 16.2 | DONE | Anonymous voice recording attribution option and pseudonymized logs | `tests/test_nfr.py::test_nfr16_2_voice_privacy` |
| 16.3 | DONE | Mandatory passage origin attribution (`Origin.AI` / `Origin.HUMAN`) enforced by domain and SQL CHECK | `tests/test_nfr.py::test_nfr16_3_origin_attribution`, `tests/test_fix_3_constraints.py` |
| 17 | PARTIAL | RTL layout and semantic structure verified; assistive technology and screen reader usability study pending | `tests/test_nfr.py::test_nfr17_accessibility_and_usability` |
| 17.1 | PARTIAL | High contrast ratios and semantic HTML verified; full automated WCAG 2.1 AA audit suite pending | `mobile/test/widget_test.dart::Login screen renders input fields and submit button`, `tests/test_nfr.py::test_nfr17_1_wcag_aa` |
| 17.2 | PARTIAL | Onboarding flow launches first session; formal first-time learner UX usability testing pending | `tests/test_nfr.py::test_nfr17_2_first_time_learner` |
| 18 | PARTIAL | Fusha and content heuristics verified on sample strings; full dialect NLP dictionary integration pending | `tests/test_nfr.py::test_nfr18_fusha_and_content_guidelines` |
| 18.1 | DONE | Strict Fusha verification rules in reviewer feedback and automated checker reject dialectal keywords | `tests/test_nfr.py::test_nfr18_1_fusha_verification` |
| 18.2 | DONE | Content moderation filter actively blocks vulgar and non-halal keywords | `tests/test_nfr.py::test_nfr18_2_halal_content_filter` |
| 19 | DONE | Audio recordings validated and tagged for 1–3 minutes (60–180s) with pure-Python RIFF/WAVE header duration enforcement | `tests/test_fix_15_audio_duration_validation.py`, `tests/test_nfr.py::test_nfr19_audio_duration_rules`, `tests/test_live_e2e_integration.py` |
| 20 | DONE | Arabic-first interface with full RTL layout, bundled `Noto Naskh Arabic` font (`mobile/lib/main.dart` with `Locale('ar')`, `mobile/assets/fonts/NotoNaskhArabic.ttf`), authentic Arabic enum translation layer (`mobile/lib/core/arabic_display.dart`), and proven live device walkthroughs (`mobile/docs/live_learner.png`, `mobile/docs/live_contributor.png`, `mobile/docs/live_reviewer.png`, `mobile/docs/live_admin.png`) | `mobile/test/arabic_enum_mapping_test.dart`, `mobile/test/clean_ui_copy_test.dart`, `mobile/test/font_and_theme_test.dart`, `mobile/test/golden_flows_test.dart`, `scripts/ui_smoke.py`, `tests/test_nfr.py::test_nfr20_arabic_rtl_ui` |
| 21 | PARTIAL | Contributor compensation ledger and credit calculation tested; automated banking/payout integration pending | `tests/test_nfr.py::test_nfr21_compensation_model` |

## (b) Implementation -> Requirement Mapping

| Implementation Artifact (Module / Entity / Endpoint) | Served Requirement IDs |
|---|---|
| `asghi/domain/enums.py` | Req 1.1, 2.2, 2.3, 4.4, 5.2, 6.3, 10.1, 16.3 |
| `asghi/domain/user.py::User` | Req 1, 1.1, 1.2, 1.3, 10.2 |
| `asghi/domain/user_role_profile.py::UserRoleProfile` | Req 1, 1.1 |
| `asghi/domain/learner_profile.py::LearnerProfile` | Req 6, 6.1, 6.2, 6.7, 17.2 |
| `asghi/domain/learner_progress.py::LearnerProgress` | Req 6.6 |
| `asghi/domain/reputation.py::Reputation` | Req 10.1, 21 |
| `asghi/domain/contributor_profile.py::ContributorProfile` | Req 4, 4.1, 4.2, 4.3, 4.4, 7.1, 8, 21 |
| `asghi/domain/reviewer_profile.py::ReviewerProfile` | Req 5, 5.1, 5.2, 5.3, 5.5, 7.1, 7.3 |
| `asghi/domain/review_assignment.py::ReviewAssignment` | Req 5, 5.1, 5.2, 5.3, 5.4 |
| `asghi/domain/review_feedback.py::ReviewFeedback` | Req 5.1, 5.5, 8, 18.1 |
| `asghi/domain/admin_profile.py::AdminProfile` | Req 5.4, 6.7, 7.1, 10, 10.2 |
| `asghi/domain/content_flag.py::ContentFlag` | Req 6.7, 10, 18.2 |
| `asghi/domain/passage.py::Passage` | Req 2, 2.1, 2.2, 2.3, 4.1, 4.3, 6.1, 6.3, 19 |
| `asghi/domain/reviewable_content.py::ReviewableContent` | Req 2.2, 3.3, 5.2, 5.4, 6.7, 7.3, 8 |
| `asghi/domain/audio_recording.py::AudioRecording` | Req 2.1, 4.2, 4.4, 5.1, 5.5, 12, 16.2, 19 |
| `asghi/domain/question_author.py::QuestionAuthor` | Req 7, 7.1, 7.2 |
| `asghi/domain/question.py::Question` | Req 2.1, 6.3, 6.5, 7.1, 7.2, 9 |
| `asghi/domain/question_response.py::QuestionResponse` | Req 6.5, 9 |
| `asghi/domain/test_session.py::TestSession` | Req 6.2, 6.4, 6.5, 6.6, 9, 17.2 |
| `asghi/domain/ai_engine.py::AIEngine` | Req 3, 3.1, 3.2, 3.3, 7.2, 16.3 |
| `asghi/moderation.py` | Req 18.1, 18.2, 19 |
| `asghi/security.py` | Req 1.2, 14, 16.1 |
| `asghi/repository.py` | Req 1, 2, 4, 5, 6, 7, 10, 14 |
| `POST /api/auth/register` | Req 1.2 |
| `POST /api/auth/login` | Req 1.2 |
| `POST /api/users/profile` | Req 1.3 |
| `GET /api/passages` | Req 2, 2.1, 2.3, 6.1 |
| `GET /api/contributor/awaiting-recording` | Req 4.1 |
| `POST /api/contributor/claim` | Req 4.1 |
| `POST /api/contributor/submit-audio` | Req 4.2, 4.4, 12, 19 |
| `GET /api/contributor/submissions` | Req 8 |
| `GET /api/reviewer/pending-recordings` | Req 5.1 |
| `GET /api/reviewer/pending-questions` | Req 7.3 |
| `POST /api/reviewer/assignments` | Req 5.1, 5.3 |
| `POST /api/reviewer/decision` | Req 5.1, 5.2, 5.5, 8 |
| `POST /api/reviewer/questions/{id}/review` | Req 7.3 |
| `POST /api/learner/sessions` | Req 6.2 |
| `GET /api/learner/sessions/{id}/question` | Req 6.3 |
| `POST /api/learner/sessions/{id}/answer` | Req 6.4, 6.5, 9 |
| `POST /api/learner/sessions/{id}/finish` | Req 6.6 |
| `GET /api/learner/progress` | Req 6.6 |
| `POST /api/learner/flag` | Req 6.7 |
| `GET /api/passages/{id}/offline-package` | Req 6.8 |
| `POST /api/questions` | Req 7.1, 7.3 |
| `POST /api/admin/generate` | Req 3.1, 3.2, 7.2, 10.2 |
| `POST /api/admin/disputes/{contentId}/resolve` | Req 5.4, 10.2 |
| `POST /api/admin/flags/{flagId}/resolve` | Req 6.7, 10.2 |
| `GET /api/admin/flags` | Req 6.7, 10.2 |
| `GET /api/admin/dashboard` | Req 10.2 |
| `GET /api/admin/report` | Req 10.2 |
| `GET /healthz` | Req 15 |
| `GET /api/audio/{filename}` | Req 5.1, 6.1 |
| `GET /` (Arabic-first Web UI) | Req 11, 13, 17.1, 17.2, 20 |
| `mobile/lib/main.dart` | Req 11, 20 |
| `mobile/lib/core/theme.dart` | Req 11, 17.1, 20 |
| `mobile/lib/core/arabic_display.dart` | Req 17, 20 |
| `mobile/lib/core/api_client.dart` | Req 1.2, 11 |
| `mobile/lib/core/audio_recorder_service.dart` | Req 4.2, 11 |
| `mobile/lib/core/audio_playback_service.dart` | Req 5.1, 6.1, 11 |
| `mobile/lib/screens/auth/login_screen.dart` | Req 1.2, 11, 17.1 |
| `mobile/lib/screens/auth/register_screen.dart` | Req 1.2, 1.3, 11 |
| `mobile/lib/screens/home_screen.dart` | Req 1.1, 11, 20 |
| `mobile/lib/screens/learner/catalogue_screen.dart` | Req 2, 6.1, 11 |
| `mobile/lib/screens/learner/practice_screen.dart` | Req 6.1, 6.2, 6.3, 6.4, 6.5, 9, 11 |
| `mobile/lib/screens/learner/progress_screen.dart` | Req 6.6, 11 |
| `mobile/lib/screens/contributor/contributor_screen.dart` | Req 4.1, 4.2, 4.3, 4.4, 8, 11 |
| `mobile/lib/screens/reviewer/reviewer_screen.dart` | Req 5.1, 5.2, 5.5, 7.3, 11, 18.1 |
| `mobile/lib/screens/admin/admin_screen.dart` | Req 3.1, 5.4, 6.7, 10.2, 11 |
| `mobile/lib/widgets/audio_player_widget.dart` | Req 5.1, 6.1, 11 |
| `mobile/lib/widgets/tashkeel_text_widget.dart` | Req 4.3, 11, 20 |
| `mobile/docs/FLOWS.md` | Req 11, 20 |
| `scripts/ui_smoke.py` | Req 1.2, 4.1, 5.1, 6.1, 10.2, 11, 20 |
| `tests/test_live_e2e_integration.py` | Req 1.2, 1.3, 4.1, 4.2, 5.1, 5.2, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 7.1, 10.2, 11, 12, 19, 20 |
