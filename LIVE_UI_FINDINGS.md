# Live UI findings — emulator walkthrough (Pixel_3a_API_33, API 33)

Tested by driving the real APK (`org.asghi.mobile`) on an emulator through `adb`
(tap/swipe/text/uiautomator/screencap/logcat), against a seeded backend on `127.0.0.1:8000`
with `adb reverse`. Users: `learner@`, `contributor@`, `reviewer@`, `admin@asghi.org`.

## Learner

| # | Sev | Finding | Evidence |
|---|-----|---------|----------|
| L1 | P0 | **Audio never plays.** The screen passes the stored filename straight to `just_audio`; no base URL is prepended. | `logcat`: `AudioPlayer: TYPE_SOURCE: java.io.FileNotFoundException: sample_fusha_01.mp3`; `practice_screen.dart:138` → `audioUrl: widget.passage.verifiedAudio?.audioFile ?? ''` |
| L2 | P0 | **Catalogue has no status filter.** Every passage is listed regardless of state. | `Passage.browse()` filters only level/topic/duration; library showed `VERIFIED, DRAFT, CLAIMED, PENDING_REVIEW, FLAGGED` |
| L3 | High | **Empty session reported as success.** Opening a passage with no verified questions jumps to "أحسنت! اكتملت الجلسة التدريبية — النقاط: 0". | DB session row `total_score=0`, started and finished 0.18 s apart |
| L4 | High | **Abandoned sessions never close.** Leaving mid-session leaves `finished_at = NULL` and the score stranded. | `test_sessions`: `(20, 17:26:24, None)` |
| L5 | Med | **"الاختبارات المكتملة" stays 0** after a finished 60-point session, while the completion badge unlocks. | progress screen vs `test_sessions` finished row |
| L6 | Med | **Duration is a constant, not measured.** A 5 s WAV displays `01:00` and is stored as `60.0` s. | imported `short5.wav`; `audio_recordings.duration_seconds = 60.0` |

Working: login, catalogue from API, session start, question + 4 options, scoring (MEDIUM = 20),
correct-answer feedback + explanation, next question, finish, progress totals (60 pts, 0.9 min),
streak, badge unlock, RTL rendering with the bundled font.

## Contributor

| # | Sev | Finding | Evidence |
|---|-----|---------|----------|
| C1 | P0 | **"تسجيلاتي وحالتها" is always empty.** Backend compares the recording's `authorId` (a user id) with `userRoleProfileId` (a profile id), so the filter never matches. Req 8 is unreachable. | `GET /api/contributor/submissions` → `[]` while `audio_recordings.author_id` = contributor's `user_id` |
| C2 | P0 | **Upload never advances the passage.** No `changeStatus(PENDING_REVIEW)` in `submit-audio`, so the passage stays `CLAIMED` and its own state contradicts the recording's. | `submit-audio` → `addAudio()` + `save_passage()` only; DB passage `CLAIMED` with recording `PENDING_REVIEW` |
| C3 | High | **Recording failure is silent and unhandled.** Tapping "بدء التسجيل" throws and the timer stays `00:00` with no message. | `Unhandled Exception: PlatformException(record, PCM reader failed to initialize., null, null)` |
| C4 | High | **Tab bar renders broken** (labels drawn over the header, row collapsed, white sliver). | screenshot: "تسجيلاتي وحالتها" overlapping the app bar |
| C5 | Med | **Server trusts the client's duration** — no validation that the uploaded file matches the declared 60–180 s. Req 19 unenforced end to end. | 5 s file accepted as 60 s |

Working: claim (72 h banner), record/import modal, tashkeel toggle, attribution choice,
real multipart upload (`MultipartFile.fromFile`), file written to `uploads/audio/<uuid>.wav`,
row created `PENDING_REVIEW`.

## Reviewer

| # | Sev | Finding | Evidence |
|---|-----|---------|----------|
| R1 | High | Same broken tab bar; review is presented with the same fabricated `60.0 ثانية`. | screenshot |
| R2 | Med | **Review outcome and passage state are disconnected.** After a positive decision the passage went `CLAIMED → DRAFT` (claim released), never `VERIFIED` / `PENDING_REVIEW`. | DB after approve: recording approved, passage `DRAFT` |

Working: pending-recording queue, player UI, criteria checkboxes (Fusha, dialect-free),
audio-quality rating, approve/reject, decision persisted (`is_approved`, `is_fusha`,
`dialect_free`, `audio_quality=5`).

## Admin

| # | Sev | Finding | Evidence |
|---|-----|---------|----------|
| A1 | P0 | **Flag resolution can never succeed from the app.** Client sends `RESOLVED_CONTENT_REMOVED` / `RESOLVED_NO_ACTION`; the enum is `PENDING/NO_ACTION/ACTION_TAKEN` → 422 every time. With `ACTION_TAKEN` the backend works and the passage becomes `FLAGGED`. | `resolve=422`; client `admin_screen.dart:459,467`; `enums.py:55` |
| A2 | High | **Dashboard numbers are wrong in the UI.** API: `verifiedPassages 1`, `pendingRecordings 2`, `totalFlags 1`. UI: "التسجيلات المعتمدة 0", "البلاغات المعلقة 0". | screenshot vs `GET /api/admin/dashboard` |
| A3 | High | **In-app refresh does not reload flags.** The list stayed empty until the app was force-stopped and relaunched. | flag existed, refresh → still "لا توجد بلاغات معلقة"; after restart it appeared |
| A4 | Med | **AI generation gives no feedback.** The passage is created (`origin=AI`) but the screen is unchanged; no toast, no navigation. Also saved as `PENDING_REVIEW` although the button says "حفظ كمسودة". | DB: new passage `الثقافة والعلوم`, origin `AI`, `PENDING_REVIEW` |
| A5 | Med | **Requirement IDs in user-facing copy**: heading reads "توليد محتوى جديد بالذكاء الاصطناعي (Req 3.1, 3.2)" — and bidi mangles it. | screenshot |
| A6 | Low | Flag card prints the raw enum: "بلاغ عن PASSAGE: …". | uiautomator dump |

Working: dashboard request, 3 tabs, flag list on fresh load, content approve/reject buttons,
`/api/admin/generate` (alias `generate-passage` also exists), report card.

## Environment notes (not product bugs)

- Only one backend can hold `127.0.0.1:8000`. A stale instance from an earlier run served the app
  while new servers silently failed to bind — check `netstat -ano | grep :8000` before testing.
- `mobile/build/.../app-debug.apk` can be older than `lib/`; the app then shows demo data that no
  longer exists in source. Rebuild before installing.
- Starting the emulator with `-no-audio` makes `AudioRecord` fail (C3's trigger); launch without it
  to test real capture.
