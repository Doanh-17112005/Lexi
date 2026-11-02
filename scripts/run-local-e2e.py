"""Repeatable local LexiLingo E2E smoke test.

The script creates one local-only test account and intentionally leaves it in
the confirmed local database. It never prints credentials, JWTs, verification
tokens, or provider keys.
"""

from __future__ import annotations

import json
import secrets
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend-service"
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.security import create_verification_token

BACKEND = "http://127.0.0.1:8000"
AI = "http://127.0.0.1:8001"


class E2EFailure(RuntimeError):
    pass


def request_json(
    method: str,
    url: str,
    *,
    body: dict[str, Any] | None = None,
    token: str | None = None,
    expected: int | tuple[int, ...] = 200,
    timeout: float = 20.0,
) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    allowed = (expected,) if isinstance(expected, int) else expected
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            if response.status not in allowed:
                raise E2EFailure(f"{method} {url} returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise E2EFailure(
            f"{method} {url} returned HTTP {exc.code}: {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise E2EFailure(f"{method} {url} could not connect: {exc.reason}") from exc

    if not payload:
        return {}
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise E2EFailure(f"{method} {url} returned a non-object JSON response")
    return parsed


def require(condition: bool, message: str) -> None:
    if not condition:
        raise E2EFailure(message)


def check_cors(base_url: str, path: str) -> None:
    origins = (
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )
    for origin in origins:
        req = urllib.request.Request(
            f"{base_url}{path}",
            method="OPTIONS",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            allowed = response.headers.get("Access-Control-Allow-Origin")
            require(allowed == origin, f"CORS rejected {origin} at {base_url}")


def main() -> int:
    suffix = f"{int(time.time())}_{secrets.token_hex(3)}"
    email = f"local-e2e-{suffix}@example.com"
    username = f"local_e2e_{suffix}"
    password = f"Aa1!{secrets.token_urlsafe(24)}"

    registered = request_json(
        "POST",
        f"{BACKEND}/api/v1/auth/register",
        body={
            "email": email,
            "username": username,
            "password": password,
            "display_name": "Local E2E User",
        },
        expected=201,
    )
    user_id = str(registered.get("id") or "")
    require(bool(user_id), "Registration did not return a user id")
    print("register=pass")

    verification_token = create_verification_token(
        {"sub": user_id, "email": email, "purpose": "email_verify"},
        expires_minutes=10,
    )
    verified = request_json(
        "POST",
        f"{BACKEND}/api/v1/auth/verify-email",
        body={"token": verification_token},
    )
    require(verified.get("verified") is True, "Local email verification failed")
    print("verify_email=pass")

    logged_in = request_json(
        "POST",
        f"{BACKEND}/api/v1/auth/login",
        body={"email": email, "password": password},
    )
    access_token = str(logged_in.get("access_token") or "")
    require(bool(access_token), "Login did not return an access token")
    print("login=pass")

    catalog = request_json(
        "GET", f"{BACKEND}/api/v1/courses?page=1&page_size=20", token=access_token
    )
    courses = catalog.get("data") or []
    course = next(
        (item for item in courses if item.get("title") == "A1 - English Foundations"),
        None,
    )
    require(isinstance(course, dict), "Published A1 CEFR course was not listed")
    course_id = str(course["id"])

    request_json(
        "POST",
        f"{BACKEND}/api/v1/courses/{course_id}/enroll",
        body={},
        token=access_token,
    )
    detail = request_json(
        "GET", f"{BACKEND}/api/v1/courses/{course_id}", token=access_token
    ).get("data") or {}
    units = detail.get("units") or []
    require(bool(units and units[0].get("lessons")), "A1 course has no lesson")
    lesson_id = str(units[0]["lessons"][0]["id"])
    print("course_select_enroll=pass")

    started = request_json(
        "POST",
        f"{BACKEND}/api/v1/learning/lessons/{lesson_id}/start",
        body={},
        token=access_token,
    ).get("data") or {}
    attempt_id = str(started.get("attempt_id") or "")
    require(bool(attempt_id), "Lesson start did not return an attempt id")

    content = request_json(
        "GET",
        f"{BACKEND}/api/v1/learning/lessons/{lesson_id}/content",
        token=access_token,
    ).get("data") or {}
    exercises = content.get("exercises") or []
    require(len(exercises) == 2, "Seeded A1 lesson does not contain two exercises")
    known_answers = {"a1_ex_1": "goes", "a1_ex_2": "have"}
    earned_on_answers = 0
    for exercise in exercises:
        exercise_id = str(exercise.get("id") or "")
        require(exercise_id in known_answers, f"Unexpected A1 exercise: {exercise_id}")
        answer = request_json(
            "POST",
            f"{BACKEND}/api/v1/learning/attempts/{attempt_id}/answer",
            body={
                "question_id": exercise_id,
                "question_type": exercise.get("type"),
                "user_answer": known_answers[exercise_id],
                "time_spent_ms": 1500,
                "hint_used": False,
            },
            token=access_token,
        ).get("data") or {}
        require(answer.get("is_correct") is True, f"Correct answer failed: {exercise_id}")
        earned_on_answers += int(answer.get("xp_earned") or 0)

    completed = request_json(
        "POST",
        f"{BACKEND}/api/v1/learning/attempts/{attempt_id}/complete",
        body={},
        token=access_token,
    ).get("data") or {}
    require(completed.get("passed") is True, "Completed lesson was not passed")
    require(int(completed.get("total_xp_earned") or 0) > 0, "No XP was awarded")
    require(earned_on_answers > 0, "Answers awarded no XP")
    print("lesson_xp=pass")

    summary = request_json(
        "GET", f"{BACKEND}/api/v1/progress/me", token=access_token
    ).get("data") or {}
    course_progress = request_json(
        "GET",
        f"{BACKEND}/api/v1/progress/courses/{course_id}",
        token=access_token,
    ).get("data") or {}
    require(
        int((summary.get("summary") or {}).get("lessons_completed") or 0) >= 1,
        "Progress lost lesson",
    )
    require(
        float((course_progress.get("course") or {}).get("progress_percentage") or 0) > 0,
        "Course progress is zero",
    )
    print("progress_persist=pass")

    session = request_json(
        "POST",
        f"{AI}/api/v1/lexi/sessions",
        body={"user_id": user_id},
        token=access_token,
    )
    session_id = str(session.get("session_id") or "")
    require(bool(session_id), "AI Chat session was not persisted")

    chat = request_json(
        "POST",
        f"{AI}/api/v1/lexi/chat",
        body={
            "user_id": user_id,
            "session_id": session_id,
            "message": "Hello, I want to practise a simple A1 greeting.",
            "input_type": "text",
            "enable_tts": False,
            "learner_level": "A1",
            "native_language": "vi",
        },
        token=access_token,
        timeout=45,
    )
    require(bool(str(chat.get("lexi_response") or "").strip()), "AI Chat returned empty text")
    print("ai_chat_fallback=pass")

    check_cors(BACKEND, "/api/v1/courses")
    check_cors(AI, "/health")
    print("cors=pass")
    print("e2e=pass")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except E2EFailure as exc:
        print(f"e2e=fail: {exc}", file=sys.stderr)
        raise SystemExit(1)
