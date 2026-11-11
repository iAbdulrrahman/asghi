# اصغِ (Asghi) — منصة التدريب على الاستماع العربي الفصيح
### Crowdsourced Arabic Listening Practice Platform

A full-stack, crowdsourced Arabic listening practice system built from the domain model, sequence diagrams, and functional requirements specifications.

---

## 🚀 Quick Start Instructions

### 1. Requirements & Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Pip / virtualenv

### 2. Installation
Install project dependencies with:
```bash
make setup
# Or: pip install -r requirements.txt && cd mobile && flutter pub get
```

### 3. Configuration & Environment Variables
The application reads configuration from environment variables:
- `SECRET_KEY`: Cryptographic signing key for JWT tokens. In `ENVIRONMENT=production` mode, this variable is **required** and the application fails fast if unset. In development mode, a secure fallback is provided.
- `ENVIRONMENT`: Set to `production` or `development` (default: `development`).
- `ASGHI_DB_PATH`: Optional path to SQLite database (default: `asghi.db`).
- `ASGHI_SEED_PASSWORD`: Master password applied to all seeded accounts when initializing. When omitted in development, well-known defaults (`LearnerPass123!`, etc.) are used. In non-development environments, a security warning is emitted if defaults are used.

Example:
```bash
# Production mode with credential rotation
export ENVIRONMENT=production
export SECRET_KEY="your-strong-production-random-secret-key"
export ASGHI_SEED_PASSWORD="strong-production-seed-password-rotated"
```

### 4. Database Seeding & Credential Rotation
Seed the database with sample listening passages, tiered comprehension questions (Easy, Medium, Hard), and seed accounts across all four roles (Admin, Reviewers, Contributor, Learner):
```bash
python seed.py
# Root entry point delegating to asghi.seed
```
> 🔒 **Credential Rotation & Security Policy**:
> For public or production deployments, never deploy with default passwords. Set `ASGHI_SEED_PASSWORD` or pass custom `password_overrides` to `seed_database(password_overrides={...})` to rotate initial credentials. Seed accounts can also rotate their passwords via the authentication profile API.

### 5. Running the Application
Start the ASGI web server with Uvicorn:
```bash
python -m uvicorn asghi.api:app --host 0.0.0.0 --port 8000 --workers 1 --reload
```
> ⚠️ **Worker Concurrency Note**: Always run Uvicorn with `--workers 1`. The Asghi backend uses SQLite immediate transaction coordination and an in-process claim TTL sweeper designed for single-process durability. Multi-worker uvicorn processes would bypass single-process concurrency coordination.
Once booted:
- **Arabic-First Web UI**: Navigate to [http://localhost:8000/](http://localhost:8000/) in any desktop or mobile browser.
- **Interactive OpenAPI Documentation**: Available at [http://localhost:8000/docs](http://localhost:8000/docs).
- **Health Check Probe**: Accessible at [http://localhost:8000/healthz](http://localhost:8000/healthz).

---

## 🧪 Running the Test Suite
Run the entire comprehensive test suite with a single command:
```bash
python -m pytest
```
All 65 automated tests verify all 41 Functional Requirements, 5 Authoritative Sequence Flows, Domain Operations, Role-Gating, and Non-Functional Requirements (NFR 11–21).

---

## 📱 Mobile Client (Flutter) & Device Verification
- **Platforms**: Android + iOS (mobile/)
- **Package / Org**: org.asghi.mobile
- **Architecture**: Flutter 3.47 / Dart 3.13, Material 3, Riverpod state management, Dio HTTP networking, Secure Storage, Just Audio.
- **RTL & Localization**: Arabic native (Locale('ar')), right-to-left layout direction.
- **iOS Target Build Status**: BLOCKED-BY-PLATFORM: macOS required to build iOS target (iOS project scaffold generated and committed in mobile/ios/).
- **Android Target**: Built with Gradle via lutter build apk --release.

### 🤖 Running on Android Emulator & Device Check
To execute the live UI smoke test against the live Android emulator:
1. Start an Android emulator (API 33 recommended) **without** -no-audio so that audio services and playback engines initialize properly:
   `ash
   # Start Android emulator (do NOT use -no-audio flag)
   emulator -avd <avd_name> -no-snapshot-load
   # e.g.: %LOCALAPPDATA%\Android\Sdk\emulator\emulator.exe -avd Pixel_3a_API_33_x86_64 -no-snapshot-load
   `
   > ⚠️ **Important**: The emulator must **NOT** be launched with the -no-audio flag, as audio playback (Just Audio / OpenSL ES) and recording hardware services must be active for audio verification flows.

2. Run the automated device smoke test walkthrough:
   `ash
   make device-check
   `
   This script (scripts/ui_smoke.py):
   - Configures reverse port forwarding (db reverse tcp:8000 tcp:8000).
   - Seeds sample test data (seed.py).
   - Logs into all 4 roles on the device (Learner, Contributor, Reviewer, Admin).
   - Verifies key UI interactions and saves live screenshots to mobile/docs/live_{learner,contributor,reviewer,admin}.png.

3. Run public HTTPS verification (Cloudflare tunnel or custom domain):
   `ash
   ASGHI_PUBLIC_URL=https://invoicing.0xabdul.dev make public-check
   `
   This target:
   - Validates that ASGHI_PUBLIC_URL is set and reachable.
   - Configures the runtime server address in the mobile app over HTTPS.
   - Verifies that audio streams cleanly without cleartext violations or audio backend crashes.
   - Saves public verification evidence to mobile/docs/live_audio_https.png.

> 💡 **Headless CI / Emulator Flags Note**:
> - For headless or CI emulator runs where no host soundcard exists, the emulator can be run with the -no-audio flag (e.g. emulator -avd <name> -no-audio -no-window) so the Android emulator does not abort due to missing audio hardware devices, while mobile audio state and logic continue cleanly.

## 👥 Seed Accounts for Testing

| Role | Email / Identifier | Password | Arabic Level | Notes |
|---|---|---|---|---|
| **Learner** | `learner@asghi.org` / `+966500000001` | `LearnerPass123!` | B1 | Practice sessions, adaptive testing, progress tracking |
| **Contributor** | `contributor@asghi.org` | `ContributorPass123!` | C1 | Passage claiming (72h TTL), audio upload, tashkeel toggle |
| **Reviewer (Specialist)** | `reviewer@asghi.org` | `ReviewerPass123!` | C2 | Single specialist verification threshold, dialect inspection |
| **Reviewer (General)** | `reviewer2@asghi.org` | `ReviewerPass123!` | C1 | General review threshold (requires 3 distinct reviewers) |
| **Admin** | `admin@asghi.org` | `AdminPass123!` | C2 | Dispute resolution, content moderation flags, AI generation |

---

## 🏛 Architecture & Authority Order Compliance

1. **Domain Model (`class-diagram.puml`)**: Every entity, enum, and operation is modeled with exact signatures in `asghi/domain/`.
2. **Authoritative Sequences (`h_seq1` to `h_seq5`)**:
   - `h_seq1_claim_cycle`: Contributor claim cycle, 72h claim TTL, tashkeel toggle, audio submission with clock freeze.
   - `h_seq2_review_verdict`: Self-review prohibition, Fusha/dialect checks, threshold rules (1 specialist vs 3 general), dispute escalation.
   - `h_seq3_learner_session`: Test session lifecycle, audio playback speed, question adaptive difficulty progression, score updates.
   - `h_seq4_registration`: User registration, profile completion, multi-role profile instantiation.
   - `h_seq5_flagging`: Content flag lifecycle, admin moderation, and `FLAGGED` state transitions.
3. **Actor Use Case Role-Gating (`h_uc.puml`)**: Every API endpoint is protected with JWT Bearer tokens and role-gated per actor permissions.
4. **Scope Traceability**: Full matrix documented in `TRACEABILITY.md` and design decisions documented in `INVENTIONS.md`.
