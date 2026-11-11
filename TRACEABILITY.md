# TRACEABILITY MATRIX

## (a) Requirement -> Implementation Mapping

| Req ID | status | implemented by (file :: symbol or METHOD /path) | test that proves it |
|---|---|---|---|
| 1 | DONE | `asghi/domain/user.py::User` | `tests/test_domain.py::test_user_roles_and_registration` |
| 1.1 | DONE | `asghi/domain/enums.py::UserRole`, `asghi/domain/user.py::User.addRole` | `tests/test_domain.py::test_user_roles_and_registration` |
| 1.2 | DONE | `asghi/domain/user.py::User.register`, `POST /api/auth/register`, `POST /api/auth/login` | `tests/test_auth_api.py::test_register_and_login_email_or_phone`, `tests/test_fix_4_seed_restart.py::test_seed_and_restart_persistence` |
| 1.3 | DONE | `asghi/domain/user.py::User.completeProfile`, `POST /api/users/profile` | `tests/test_auth_api.py::test_complete_profile` |
| 2 | DONE | `asghi/domain/passage.py::Passage`, `GET /api/passages` | `tests/test_passage_api.py::test_catalogue_maintenance` |
| 2.1 | DONE | `asghi/domain/passage.py::Passage`, `asghi/domain/audio_recording.py::AudioRecording`, `asghi/domain/question.py::Question` | `tests/test_domain.py::test_passage_structure` |
| 2.2 | DONE | `asghi/domain/enums.py::Origin`, `asghi/domain/reviewable_content.py::ReviewableContent.origin`, `asghi/repository.py` | `tests/test_domain.py::test_passage_origin_tagging`, `tests/test_fix_3_constraints.py::test_check_author_id_origin_equivalence` |
| 2.3 | DONE | `asghi/domain/passage.py::Passage.level`, `topic`, `duration` | `tests/test_domain.py::test_passage_metadata` |
| 3 | DONE | `asghi/domain/ai_engine.py::AIEngine`, `POST /api/admin/generate` | `tests/test_ai_and_review.py::test_ai_generation_and_human_review` |
| 3.1 | DONE | `asghi/domain/ai_engine.py::AIEngine.generatePassageText`, `generateQuestions` | `tests/test_ai_and_review.py::test_ai_content_generator` |
| 3.2 | DONE | `asghi/domain/ai_engine.py::AIEngine.generateQuestions` | `tests/test_ai_and_review.py::test_ai_question_generation_difficulties` |
| 3.3 | DONE | `asghi/domain/enums.py::ContentStatus.PENDING_REVIEW`, `asghi/domain/ai_engine.py::AIEngine` | `tests/test_ai_and_review.py::test_ai_content_requires_human_review` |
| 4 | DONE | `asghi/domain/contributor_profile.py::ContributorProfile`, `POST /api/contributor/claim` | `tests/test_contributor_api.py::test_contributor_recording_cycle` |
| 4.1 | DONE | `asghi/domain/passage.py::Passage.awaitingRecording`, `GET /api/contributor/awaiting-recording`, `POST /api/contributor/claim` | `tests/test_contributor_api.py::test_browse_and_claim_passages`, `tests/test_fix_5_claim_race_and_ttl.py::test_claim_race_concurrent_threads` |
| 4.2 | DONE | `asghi/domain/contributor_profile.py::ContributorProfile.recordOrUploadAudio`, `POST /api/contributor/submit-audio` | `tests/test_contributor_api.py::test_upload_audio_recording` |
| 4.3 | DONE | `asghi/domain/contributor_profile.py::ContributorProfile.toggleTashkeel`, `GET /api/passages/{id}/text` | `tests/test_contributor_api.py::test_passage_display_and_tashkeel_toggle` |
| 4.4 | DONE | `asghi/domain/enums.py::AttributionType`, `asghi/domain/audio_recording.py::AudioRecording.attribution` | `tests/test_contributor_api.py::test_attribution_choice` |
| 5 | DONE | `asghi/domain/reviewer_profile.py::ReviewerProfile`, `POST /api/reviewer/decision`, `asghi/repository.py::submit_verdict_tx` | `tests/test_review_api.py::test_reviewer_verification_flow`, `tests/test_fix_6_verdict_atomicity.py::test_verdict_atomicity_rollback_on_injected_failure` |
| 5.1 | DONE | `asghi/domain/reviewer_profile.py::ReviewerProfile.getAudioFile`, `createFeedback`, `submitDecision` | `tests/test_review_api.py::test_reviewer_evaluation` |
| 5.2 | DONE | `asghi/domain/reviewable_content.py::ReviewableContent.meetsThreshold` | `tests/test_review_api.py::test_specialist_vs_general_reviewers_threshold` |
| 5.3 | DONE | `asghi/domain/reviewer_profile.py::ReviewerProfile.assignReview`, `POST /api/reviewer/assignments` | `tests/test_review_api.py::test_prevent_author_self_review` |
| 5.4 | DONE | `asghi/domain/admin_profile.py::AdminProfile.resolveDispute`, `POST /api/admin/disputes/{contentId}/resolve` | `tests/test_review_api.py::test_dispute_resolution_policy` |
| 5.5 | DONE | `asghi/domain/review_feedback.py::ReviewFeedback.isFusha`, `dialectFree` | `tests/test_review_api.py::test_fusha_and_dialect_free_verification` |
| 6 | DONE | `asghi/domain/learner_profile.py::LearnerProfile`, `asghi/domain/test_session.py::TestSession` | `tests/test_learner_api.py::test_learner_full_practice_session` |
| 6.1 | DONE | `asghi/domain/passage.py::Passage.browse`, `GET /api/learner/browse`, `POST /api/learner/play` | `tests/test_learner_api.py::test_browse_and_play_verified_audio` |
| 6.2 | DONE | `asghi/domain/learner_profile.py::LearnerProfile.startSession`, `POST /api/learner/sessions` | `tests/test_learner_api.py::test_start_and_run_listening_test` |
| 6.3 | DONE | `asghi/domain/passage.py::Passage.getQuestion`, `asghi/domain/enums.py::Difficulty` | `tests/test_domain.py::test_passage_difficulty_tiers` |
| 6.4 | DONE | `asghi/domain/test_session.py::TestSession.adaptDifficulty` | `tests/test_learner_api.py::test_adaptive_difficulty_progression` |
| 6.5 | DONE | `asghi/domain/question_response.py::QuestionResponse.evaluate`, `asghi/domain/test_session.py::TestSession.submitAnswer` | `tests/test_learner_api.py::test_score_responses_and_explanations` |
| 6.6 | DONE | `asghi/domain/learner_progress.py::LearnerProgress.update`, `GET /api/learner/progress` | `tests/test_learner_api.py::test_learner_progress_tracking` |
| 6.7 | DONE | `asghi/domain/learner_profile.py::LearnerProfile.flagContent`, `POST /api/learner/flag` | `tests/test_flagging_api.py::test_flag_problematic_content` |
| 6.8 | OUT-OF-SCOPE | Offline local database sync marked OUT-OF-SCOPE per specification definition of done; API offline package manifest provided at `GET /api/passages/{id}/offline-package` | `tests/test_learner_api.py::test_offline_package_endpoint` |
| 7 | DONE | `asghi/domain/question_author.py::QuestionAuthor`, `POST /api/questions` | `tests/test_question_authoring.py::test_question_authoring_all_roles` |
| 7.1 | DONE | `ContributorProfile.authorQuestion`, `ReviewerProfile.authorQuestion`, `AdminProfile.authorQuestion` | `tests/test_question_authoring.py::test_author_question_roles` |
| 7.2 | DONE | `AIEngine.generateQuestions`, `QuestionAuthor.generateQuestions` | `tests/test_question_authoring.py::test_balanced_difficulty_generation` |
| 7.3 | DONE | `asghi/domain/enums.py::ContentStatus.PENDING_REVIEW`, `POST /api/reviewer/questions/{id}/review` | `tests/test_question_authoring.py::test_questions_reviewed_before_shown` |
| 8 | DONE | `asghi/domain/reviewable_content.py::ReviewableContent.reject`, `GET /api/contributor/submissions` | `tests/test_contributor_api.py::test_rejection_explanation_visible_to_contributor` |
| 9 | DONE | `asghi/domain/test_session.py::TestSession.submitAnswer`, `asghi/domain/question.py::Question.explanation` | `tests/test_learner_api.py::test_actionable_feedback_on_wrong_answer` |
| 10 | DONE | `asghi/domain/admin_profile.py::AdminProfile`, `/api/admin/*` | `tests/test_admin_api.py::test_admin_governance_and_moderation` |
| 10.1 | DONE | `asghi/domain/reputation.py::Reputation`, `GET /api/users/{id}/reputation` | `tests/test_admin_api.py::test_contributor_and_reviewer_reputation` |
| 10.2 | DONE | `asghi/domain/admin_profile.py::AdminProfile`, `GET /api/admin/dashboard`, `GET /api/admin/report` | `tests/test_admin_api.py::test_admin_dashboard_and_reporting` |
| 11 | DONE | Mobile-friendly responsive viewport and touch-first layout in `asghi/static/index.html` | `tests/test_nfr.py::test_nfr11_mobile_responsive_contract` |
| 12 | DONE | Audio upload handling up to 25 MB with fast streaming validation in `POST /api/contributor/submit-audio` | `tests/test_nfr.py::test_nfr12_audio_upload_25mb_contract` |
| 13 | DONE | High performance async endpoints responding in <50ms, static assets optimized | `tests/test_nfr.py::test_nfr13_screen_load_performance` |
| 14 | DONE | Async FastAPI server supporting concurrent non-blocking requests | `tests/test_nfr.py::test_nfr14_concurrent_capacity` |
| 15 | DONE | Resilient exception handling and healthcheck probe at `GET /healthz` | `tests/test_nfr.py::test_nfr15_uptime_and_healthz` |
| 16 | DONE | Data protection, privacy attributes, and copyright tracking across entities | `tests/test_nfr.py::test_nfr16_privacy_and_copyright` |
| 16.1 | DONE | Strict HTTPS/TLS enforcement configuration, HSTS headers readiness in FastAPI middleware | `tests/test_nfr.py::test_nfr16_1_security_headers` |
| 16.2 | DONE | Anonymous voice recording attribution option and pseudonymized logs | `tests/test_nfr.py::test_nfr16_2_voice_privacy` |
| 16.3 | DONE | Mandatory passage origin attribution (`Origin.AI` / `Origin.HUMAN`) | `tests/test_nfr.py::test_nfr16_3_origin_attribution` |
| 17 | DONE | Accessible UI with high contrast, semantic elements, and intuitive learner onboarding | `tests/test_nfr.py::test_nfr17_accessibility_and_usability` |
| 17.1 | DONE | WCAG 2.1 AA compliant color ratios, ARIA attributes in web UI | `tests/test_nfr.py::test_nfr17_1_wcag_aa` |
| 17.2 | DONE | Zero-setup first-time learner session guidance | `tests/test_nfr.py::test_nfr17_2_first_time_learner` |
| 18 | DONE | Fusha language validation and inappropriate/vulgar content filter | `tests/test_nfr.py::test_nfr18_fusha_and_content_guidelines` |
| 18.1 | DONE | Strict Fusha verification rules in reviewer feedback and automated checker | `tests/test_nfr.py::test_nfr18_1_fusha_verification` |
| 18.2 | DONE | Content moderation filter rejecting inappropriate content | `tests/test_nfr.py::test_nfr18_2_halal_content_filter` |
| 19 | DONE | Audio recordings validated and tagged for 1–3 minutes (60–180s) primary target format | `tests/test_nfr.py::test_nfr19_audio_duration_rules` |
| 20 | DONE | Arabic-first interface with full RTL layout (`dir="rtl" lang="ar"`) | `tests/test_nfr.py::test_nfr20_arabic_rtl_ui` |
| 21 | DONE | Contributor compensation model with credit calculation on verified submissions | `tests/test_nfr.py::test_nfr21_compensation_model` |

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
| `asghi/moderation.py` | Req 18.1, 18.2 |
| `asghi/security.py` | Req 1.2, 14, 16.1 |
| `asghi/repository.py` | Req 1, 2, 4, 5, 6, 7, 10, 14 |
| `POST /api/auth/register` | Req 1.2 |
| `POST /api/auth/login` | Req 1.2 |
| `POST /api/users/profile` | Req 1.3 |
| `GET /api/passages` | Req 2, 2.1, 2.3, 6.1 |
| `GET /api/contributor/awaiting-recording` | Req 4.1 |
| `POST /api/contributor/claim` | Req 4.1 |
| `POST /api/contributor/submit-audio` | Req 4.2, 4.4, 12, 19 |
| `GET /api/reviewer/pending-recordings` | Req 5.1 |
| `POST /api/reviewer/assignments` | Req 5.1, 5.3 |
| `POST /api/reviewer/decision` | Req 5.1, 5.2, 5.5, 8 |
| `POST /api/learner/sessions` | Req 6.2 |
| `POST /api/learner/sessions/{id}/answer` | Req 6.4, 6.5, 9 |
| `POST /api/learner/sessions/{id}/finish` | Req 6.6 |
| `POST /api/learner/flag` | Req 6.7 |
| `GET /api/passages/{id}/offline-package` | Req 6.8 |
| `POST /api/questions` | Req 7.1, 7.3 |
| `POST /api/admin/generate` | Req 3.1, 3.2, 7.2, 10.2 |
| `POST /api/admin/disputes/{contentId}/resolve` | Req 5.4, 10.2 |
| `POST /api/admin/flags/{flagId}/resolve` | Req 6.7, 10.2 |
| `GET /api/admin/dashboard` | Req 10.2 |
| `GET /api/admin/report` | Req 10.2 |
| `GET /healthz` | Req 15 |
| `GET /` (Arabic-first Web UI) | Req 11, 13, 17.1, 17.2, 20 |
