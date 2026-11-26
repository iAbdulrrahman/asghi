# Asghi — Code Review Findings

Scope: `asghi/` (4,395 LOC), `mobile/lib/` (4,116 LOC of Dart), reviewed against a freshly seeded
scratch database. Every finding below was reproduced, not inferred — the evidence line quotes the
actual response or measurement.

**Verdict:** the architecture is sound and the suite is genuinely green (128 backend tests, 45 client
tests), but the boundary layer — the file that turns HTTP into domain calls — has four defects that
break requirements outright, and the workflow guards that the diagrams describe are enforced only in
the client, not on the server.

---

## P0 — Critical

### 1. Path traversal on the audio endpoint exposes the whole database
`asghi/api.py:1273-1284`

```python
path = os.path.join(UPLOAD_DIR, filename)      # filename straight from the URL
if os.path.exists(path):
    return FileResponse(path, media_type="audio/mpeg")
```

`filename` is a path segment, and on Windows a backslash survives URL decoding, so `..%5C..%5C` climbs
out of `uploads/audio/`. Any authenticated user — the seeded learner account is enough — can read any
file the API process can read.

**Evidence**

```
GET /api/audio/..%5C..%5Casghi.db   (Bearer learner token)
  -> 200  len=155648  head=b'SQLite format 3\x00'
```

That is the live database: every password hash, every user, every flag.

**Fix:** resolve and constrain — `target = (Path(UPLOAD_DIR) / filename).resolve()`; reject unless
`target.parent == Path(UPLOAD_DIR).resolve()` and `target.is_file()`. Also serve `audio/wav` for `.wav`
instead of a hardcoded `audio/mpeg`.

---

## P1 — Breaks a requirement or leaks protected data

### 2. Any learner can drive another learner's session
`asghi/api.py:830-900`

`/sessions/{id}/question`, `/answer` and `/finish` fetch from the module-level `active_sessions` dict by
session id and never compare the session's owner with the caller.

**Evidence** (learner A starts a session, learner B — a brand-new account — uses the id)

```
A: POST /api/learner/sessions            -> 200 {sessionId: 7f7ea5b7-…}
B: GET  /api/learner/sessions/7f7e…/question -> 200 {"done":false,"questionId":"58c9558f-…","promptText":"ما السبب ا…"}
```

Session ids are unguessable, so this is an IDOR rather than a walk-in, but it also means a leaked id
(shared screenshot, proxy log) hands over another learner's progress and lets the attacker finish their
session.

**Fix:** store `learnerProfileId` with the session and reject when it differs from
`current_user`'s profile (404, not 403, so ids stay unenumerable).

### 3. Audio can be submitted without claiming the passage
`asghi/api.py:469-540`

Sequence 1 and Req 4.2 require claim → record → submit. `submit_audio` checks only that the caller is a
contributor, never that an unexpired claim exists for that passage.

**Evidence** (passage `claimedBy` is `None`)

```
POST /api/contributor/submit-audio  (never claimed this passage)
  -> 200 {"message":"تم رفع التسجيل الصوتي بنجاح وهو قيد المراجعة", …}
```

**Fix:** inside the same transaction that attaches the recording, require
`active_claims.contributor_id = caller` and `claimed_at` within `CLAIM_TTL`, else `409`.

### 4. Correct answers are readable without logging in
`asghi/api.py` — `GET /api/passages` and `GET /api/passages/{id}/offline-package` carry no auth
dependency (confirmed by route-table introspection: 6 of 38 routes have none, and two of those return
content).

**Evidence** (no token at all)

```
GET /api/passages                                  -> 200  [1 passage]
GET /api/passages/{id}/offline-package             -> 200  questions: 3, correctAnswer exposed
```

The offline package was declared **out of scope** (Req 6.8) yet ships unauthenticated, which is how the
answers leak.

**Fix:** require a token on both; if the catalogue is intentionally public, strip `correctAnswer` and
`explanation` from the offline package and gate that endpoint.

### 5. Duration validation trusts the client for anything that is not a WAV
`asghi/moderation.py:66-90`, used at `asghi/api.py:495`

`extract_audio_duration` only parses RIFF/WAV (`wave.open`). For every other container it returns
`None`, and the caller falls back to the `durationSeconds` form field the client sent.

**Evidence**

```
2 KB fake mp3, durationSeconds=90  -> 200  (stored as a 90 s recording)
2 KB fake mp3, durationSeconds=3   -> 400  "مدة التسجيل قصيرة جداً"
```

The 3-second case proves the number being validated is the client's, not the file's. Requirement 19
(60–180 s) is therefore unenforced for MP3/M4A — the formats a phone actually records.

**Fix:** parse duration server-side for the accepted containers (ID3/MPEG frame headers, MP4 `mvhd`,
Ogg granule), and reject when the duration cannot be determined rather than defaulting to the claim.

### 6. The quorum rule exists twice, and the two versions disagree
`asghi/domain/reviewable_content.py:48-61` vs `asghi/repository.py:911-925`

The domain method says: verified if one specialist approved **or** three distinct reviewers approved.
The SQL says the same for approval but adds a rejection rule that the domain has no notion of
(`is_specialist or len(rejected) >= 2`). Only the SQL decides anything at runtime; `meetsThreshold()` is
called at `reviewer_profile.py:146` on the in-memory object, which the API path does not use.

Separately, `POST /api/reviewer/questions/{questionId}/review` publishes or rejects a question on a
single reviewer's word — no assignment row, no quorum, no author check — although `Question` is a
`ReviewableContent` in the class diagram.

**Impact:** the model in the report cannot explain the system's behaviour, and a question's lifecycle
differs from a recording's without that being a documented decision.

**Fix:** make the transaction call one shared rule (or move the rule into SQL only and delete the domain
method), and either route question review through quorum or write the exemption down as a requirement.

---

## P2 — Correctness and cost

### 7. The schema is re-created on every request
`asghi/repository.py:49-56` — `get_repository()` builds a new `Repository`, whose `__init__` runs
`_init_db()` (10 `CREATE TABLE IF NOT EXISTS` + 10 `CREATE INDEX IF NOT EXISTS`).

**Measured:** 3.5 ms per construction — more than the 2.6 ms median the catalogue endpoint takes to
answer. The API spends more time re-checking its schema than doing its job, on every single request.

**Fix:** initialise once at startup (already the case in `lifespan`) and have `get_repository()` return
a process-wide instance.

### 8. An unknown question id returns 500 instead of 4xx
`asghi/api.py:855-880` → `record_answer_tx` inserts a `question_responses` row whose FK fails.

**Evidence:** valid-but-unused UUID → `500`; malformed UUID → `422`. So a deleted question or a stale
client turns into a server error and a rollback.

**Fix:** look the question up first and return `404`, and reject answers for questions outside the
session's passage.

### 9. CORS is wide open with credentials
`asghi/api.py:101-107` — `allow_origins=["*"]` together with `allow_credentials=True`, which per the CORS
spec is invalid and makes Starlette echo any `Origin` back. Low impact today because auth rides in a
header, but it is the wrong default to demo.

### 10. Prohibited-term matching rejects legitimate Arabic
`asghi/moderation.py:41-45` — plain substring search over `PROHIBITED_TERMS`, which includes `"سب"`.

**Evidence:** `check_content_guidelines("ارتفعت النسبة في المئة")` → **False**; same for
`"كان ذلك بسبب الطقس"`. `"سب"` occurs inside `النسبة` and `بسبب`, so valid passages are refused.

**Fix:** match whole words (`\b`-delimited, as `check_fusha_compliance` already does) or use a normalised
token set.

### 11. Content-Type is always `audio/mpeg`
`asghi/api.py:1282` — a `.wav` is served as MPEG audio. Players sniff and cope, browsers and strict
clients may not. Derive it from the suffix or `mimetypes.guess_type`.

---

## P3 — Hygiene

| # | Where | Issue |
|---|---|---|
| 12 | `api.py:69-78` | Sweeper loop swallows every exception (`except Exception: pass`), so a permanently failing sweep is invisible — the claim TTL would silently stop working. Log it. |
| 13 | `repository.py:873` | `fail_injection` test hook inside the production verdict transaction. |
| 14 | `mobile/lib/providers/providers.dart:203` | `audioPlaybackProvider` builds a `JustAudioPlaybackService` but registers no `ref.onDispose`, so the underlying `AudioPlayer` is never released. |
| 15 | `security.py:29` | `SECRET_KEY` is computed at import and then never used — every call re-reads `get_secret_key()`. Dead constant that suggests a fixed key at runtime. |
| 16 | `repository.py:57-70` | `clear_all_tables` toggles `PRAGMA foreign_keys` inside a transaction, where SQLite ignores it; the flag does not do what it looks like it does. |

---

## What this review did not cover

- Exhaustive Dart screen logic: I checked service lifecycles, disposal and provider wiring, not every
  widget's state handling. `flutter analyze` and 45 widget tests are the current evidence there.
- Behaviour under concurrent load: only the claim race is covered by a test; the in-memory registries
  and `active_sessions` are shared mutable state across the threadpool and deserve a stress test.
- No fuzzing of the multipart upload path beyond the cases above.
