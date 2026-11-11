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
python -m pip install fastapi uvicorn pydantic PyJWT python-multipart pytest httpx
```

### 3. Configuration & Environment Variables
The application reads configuration from environment variables:
- `SECRET_KEY`: Cryptographic signing key for JWT tokens. In `ENVIRONMENT=production` mode, this variable is **required** and the application fails fast if unset. In development mode, a secure fallback is provided.
- `ENVIRONMENT`: Set to `production` or `development` (default: `development`).
- `ASGHI_DB_PATH`: Optional path to SQLite database (default: `asghi.db`).

Example:
```bash
# Production mode
export ENVIRONMENT=production
export SECRET_KEY="your-strong-production-random-secret-key"
```

### 4. Database Seeding
Seed the database with sample listening passages, tiered comprehension questions (Easy, Medium, Hard), and seed accounts across all four roles (Admin, Reviewers, Contributor, Learner):
```bash
python seed.py
# Root entry point delegating to asghi.seed
```

### 5. Running the Application
Start the ASGI web server with Uvicorn:
```bash
python -m uvicorn asghi.api:app --host 0.0.0.0 --port 8000 --reload
```
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

## 📱 Mobile Client (Flutter)
- **Platforms**: Android + iOS (mobile/)
- **Package / Org**: org.asghi.mobile
- **Architecture**: Flutter 3.47 / Dart 3.13, Material 3, Riverpod state management, Dio HTTP networking, Secure Storage, Just Audio.
- **RTL & Localization**: Arabic native (Locale('ar')), right-to-left layout direction.
- **iOS Target Build Status**: BLOCKED-BY-PLATFORM: macOS required to build iOS target (iOS project scaffold generated and committed in mobile/ios/).
- **Android Target**: Built with Gradle via lutter build apk --debug.

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
