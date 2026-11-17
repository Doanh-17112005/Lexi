# Flutter App

> Web-first learner application. Native platform folders are retained for possible future work, but the current build, QA, and deployment target is Flutter Web.

[![Flutter](https://img.shields.io/badge/Flutter-3.24.0-02569B?logo=flutter)](https://flutter.dev)
[![Dart](https://img.shields.io/badge/Dart-3.8.1-0175C2?logo=dart)](https://dart.dev)

---

## Features

### 🎓 Learning
- **AI Chat Tutor** — Practice with Gemini-powered AI
- **Structured Courses** — Multi-level curriculum (A1→C2)
- **Lessons & Exercises** — Interactive learning activities
- **Learning Sessions** — Timed practice with XP rewards

### 📚 Vocabulary
- **Personal Library** — Save and organize words
- **Word of the Day** — Daily vocabulary notifications
- **Smart Search** — Find words quickly
- **Review System** — Track learning progress

### 📈 Progress & Gamification
- **XP & Levels** — Earn experience points
- **Streaks** — Maintain daily learning habits
- **Achievements** — Unlock badges and milestones
- **Statistics** — Track learning analytics

### 🔐 Authentication
- **Google Sign-In** — Quick OAuth login
- **Email/Password** — Traditional authentication
- **Firebase Integration** — Secure user management

### 🔔 Engagement
- **Push Notifications** — Learning reminders
- **Daily Goals** — Set and track targets
- **Resilient browser state** — User-scoped local-first state for supported flows; server data remains authoritative

---

## Architecture

Clean Architecture với 3 layers:

```
lib/
├── core/                     # Shared infrastructure
│   ├── di/                  # Dependency Injection (GetIt)
│   ├── network/             # API clients
│   ├── services/            # Shared services
│   └── theme/               # App theming
│
└── features/                 # Feature modules
    ├── auth/                # Authentication
    ├── chat/                # AI Chat
    ├── course/              # Courses & Lessons
    ├── learning/            # Learning Sessions
    ├── vocabulary/          # Vocabulary Management
    ├── progress/            # Progress Tracking
    ├── notifications/       # Push Notifications
    └── home/                # Dashboard
```

Each feature follows:
```
feature/
├── domain/          # Business logic (entities, use cases)
├── data/            # Data layer (models, repositories)
└── presentation/    # UI layer (pages, providers)
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Flutter 3.24 |
| Language | Dart 3.8 |
| State | Provider |
| DI | GetIt |
| Client persistence | SharedPreferences/browser storage adapters; feature-scoped local-first caches |
| Auth | Firebase Auth |
| AI | Google Generative AI |

---

## Data Flow

```
UI (Widgets)
    ↓
Provider (State)
    ↓
Use Case (Business Logic)
    ↓
Repository (Data Access)
    ↓
Data Source
├── Remote → Backend API / AI Service
└── Local  → user-scoped browser storage (supported features only)
```

---

## API Integration

```dart
// Public client configuration
API_BASE_URL=https://api.lexilingo.me/api/v1
AI_SERVICE_URL=https://api.lexilingo.me/api/v1
```

For local development, update `assets/env/dev_config`. Provider API keys stay in
the backend/AI service environment, not in Flutter web assets.

The app connects to:
- **Backend Service** (port 8000) — User, courses, progress
- **AI Service** (port 8001) — Chat, analytics

## Vercel Production Deploy Checklist

Use this checklist to prevent Google OAuth and env drift in production/preview deploys.

1. `flutter-app/.env.production` is the single source of production config.
2. `flutter-app/web/index.html` `google-signin-client_id` matches `GOOGLE_SERVER_CLIENT_ID` in `.env.production`.
3. `flutter-app/lib/firebase_options.dart` points to the same Firebase project used by production OAuth credentials.
4. Firebase Console -> Authentication -> Settings -> Authorized domains contains:
    - production domain (for example your custom domain)
    - Vercel preview domain pattern being used for testing
5. Deploy with the Flutter Vercel script (prebuilt flow):

```bash
bash scripts/deploy-flutter-vercel.sh
```

This script enforces `.env.production` usage for release build, validates Google client ID sync, and deploys using `vercel deploy --prebuilt --prod`.

---

## Active platform

| Platform | Support status |
|----------|----------------|
| Web | Active build/test/deployment target; modern Chrome-compatible browsers |
| iOS / Android / desktop | Source scaffolding only; not claimed as tested in the current scope |

---

## Related Services

- **Backend Service** — REST API at port 8000
- **AI Service** — AI chat at port 8001

---

## License

MIT License
