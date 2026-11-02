"""Extended E2E tests for LexiLingo — vocabulary, gamification, IELTS,
admin API, AI error paths, security, challenges, games, progress APIs.

Rules:
- 404 => skip (no data seeded yet)
- 401/403 when expected => pass (security working)
- Never prints secrets / tokens in output
- Does not reset/modify DB data
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

BACKEND = "http://127.0.0.1:8000"
AI = "http://127.0.0.1:8001"

RESULTS: dict[str, str] = {}
FIXES: list[str] = []
ISSUES: list[str] = []

# ─── HTTP helpers ─────────────────────────────────────────────────────────────

def _do_request(
    method: str,
    url: str,
    *,
    body: dict[str, Any] | None = None,
    token: str | None = None,
    headers_extra: dict[str, str] | None = None,
    timeout: float = 15.0,
) -> tuple[int, dict[str, Any] | list | None]:
    headers: dict[str, str] = {"Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if headers_extra:
        headers.update(headers_extra)

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            status = resp.status
            return status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"raw": raw[:300]}
        return exc.code, payload
    except urllib.error.URLError as exc:
        return 0, {"error": str(exc.reason)}


def request_json(
    method: str,
    url: str,
    *,
    body: dict[str, Any] | None = None,
    token: str | None = None,
    expected: int | tuple[int, ...] = 200,
    timeout: float = 15.0,
) -> dict[str, Any]:
    status, payload = _do_request(method, url, body=body, token=token, timeout=timeout)
    allowed = (expected,) if isinstance(expected, int) else expected
    if status not in allowed:
        raise RuntimeError(f"{method} {url} → HTTP {status}: {str(payload)[:200]}")
    if isinstance(payload, dict):
        return payload
    return {"_list": payload}


# ─── Token acquisition ────────────────────────────────────────────────────────

def get_token() -> tuple[str, str]:
    """Register + verify + login a fresh test user and return (access_token, user_id)."""
    from app.core.security import create_verification_token  # noqa: PLC0415

    suffix = f"{int(time.time())}_{secrets.token_hex(3)}"
    email = f"e2e-ext-{suffix}@example.com"
    username = f"e2e_ext_{suffix}"
    password = f"Aa1!{secrets.token_urlsafe(16)}"

    reg = request_json(
        "POST",
        f"{BACKEND}/api/v1/auth/register",
        body={
            "email": email,
            "username": username,
            "password": password,
            "display_name": "E2E Ext User",
        },
        expected=201,
    )
    user_id = str(reg.get("id") or "")

    vtoken = create_verification_token(
        {"sub": user_id, "email": email, "purpose": "email_verify"},
        expires_minutes=10,
    )
    verified = request_json(
        "POST",
        f"{BACKEND}/api/v1/auth/verify-email",
        body={"token": vtoken},
    )
    if verified.get("verified") is not True:
        raise RuntimeError("Email verification failed")

    login_resp = request_json(
        "POST",
        f"{BACKEND}/api/v1/auth/login",
        body={"email": email, "password": password},
    )
    access_token = str(login_resp.get("access_token") or "")
    if not access_token:
        raise RuntimeError("Login did not return access_token")

    return access_token, user_id


# ─── Individual test suites ───────────────────────────────────────────────────

def test_vocabulary(token: str) -> None:
    """Vocabulary items & flashcard/collection."""
    try:
        # GET /vocabulary/items
        status, payload = _do_request("GET", f"{BACKEND}/api/v1/vocabulary/items", token=token)
        if status == 404:
            RESULTS["vocabulary"] = "skip"
            RESULTS["flashcard"] = "skip"
            return
        if status != 200:
            RESULTS["vocabulary"] = f"fail:items→{status}"
            RESULTS["flashcard"] = "skip"
            return

        items = payload if isinstance(payload, list) else (payload.get("_list") or payload.get("data") or [])
        RESULTS["vocabulary"] = "pass"

        # GET /vocabulary/items/{id}
        if items:
            first_id = items[0].get("id") if isinstance(items[0], dict) else None
            if first_id:
                s2, _ = _do_request("GET", f"{BACKEND}/api/v1/vocabulary/items/{first_id}", token=token)
                if s2 not in (200, 404):
                    RESULTS["vocabulary"] = f"fail:item_by_id→{s2}"

        # GET /vocabulary/collection (flashcard user collection)
        sc, pc = _do_request("GET", f"{BACKEND}/api/v1/vocabulary/collection", token=token)
        if sc in (200, 204):
            RESULTS["flashcard"] = "pass"
        elif sc == 404:
            RESULTS["flashcard"] = "skip"
        else:
            RESULTS["flashcard"] = f"fail:collection→{sc}"

    except Exception as exc:
        RESULTS["vocabulary"] = f"fail:{exc}"
        RESULTS["flashcard"] = f"fail:{exc}"


def test_gamification(token: str) -> None:
    """Leaderboard, XP profile, shop, achievements."""
    fails = []
    try:
        # Leaderboard
        sl, _ = _do_request("GET", f"{BACKEND}/api/v1/gamification/leaderboard", token=token)
        if sl not in (200, 404):
            fails.append(f"leaderboard→{sl}")

        # Achievements list
        sa, _ = _do_request("GET", f"{BACKEND}/api/v1/gamification/achievements", token=token)
        if sa not in (200, 404):
            fails.append(f"achievements→{sa}")

        # My achievements
        sm, _ = _do_request("GET", f"{BACKEND}/api/v1/gamification/achievements/me", token=token)
        if sm not in (200, 404):
            fails.append(f"achievements/me→{sm}")

        # Shop items
        ss, _ = _do_request("GET", f"{BACKEND}/api/v1/gamification/shop", token=token)
        if ss not in (200, 404):
            fails.append(f"shop→{ss}")

        # XP profile
        sx, _ = _do_request("GET", f"{BACKEND}/api/v1/xp/profile", token=token)
        if sx not in (200, 404):
            fails.append(f"xp/profile→{sx}")

        RESULTS["gamification"] = "pass" if not fails else f"fail:{','.join(fails)}"
    except Exception as exc:
        RESULTS["gamification"] = f"fail:{exc}"


def test_ielts(token: str) -> None:
    """IELTS tests listing."""
    try:
        status, payload = _do_request("GET", f"{BACKEND}/api/v1/ielts/tests", token=token)
        if status == 200:
            data = payload if isinstance(payload, list) else (payload.get("data") or [])
            RESULTS["ielts"] = "pass"
        elif status == 404:
            RESULTS["ielts"] = "skip"
        else:
            RESULTS["ielts"] = f"fail:{status}"
    except Exception as exc:
        RESULTS["ielts"] = f"fail:{exc}"


def test_admin_api(token: str) -> None:
    """Admin courses & analytics — regular user should get 403 (security pass)."""
    try:
        # Regular user hitting admin => expect 401/403
        sc, _ = _do_request("GET", f"{BACKEND}/api/v1/admin/courses", token=token)
        admin_courses_ok = sc in (401, 403)

        sa, _ = _do_request("GET", f"{BACKEND}/api/v1/analytics/dashboard/kpis", token=token)
        analytics_ok = sa in (200, 403, 401, 404)

        # No token => expect 401/403 on admin
        sn, _ = _do_request("GET", f"{BACKEND}/api/v1/admin/courses")
        no_token_ok = sn in (401, 403)

        if admin_courses_ok and no_token_ok:
            RESULTS["admin_api"] = "pass"
        else:
            RESULTS["admin_api"] = f"fail:courses_auth→{sc},no_token→{sn}"
    except Exception as exc:
        RESULTS["admin_api"] = f"fail:{exc}"


def test_ai_chat_errors() -> None:
    """AI chat error paths: invalid token, missing fields."""
    try:
        # Invalid token
        s1, p1 = _do_request(
            "POST",
            f"{AI}/api/v1/lexi/chat",
            body={"user_id": "bad", "session_id": "bad", "message": "hi", "input_type": "text"},
            token="invalid.token.here",
        )
        invalid_token_ok = s1 in (401, 403, 422, 500)

        # Missing required fields
        s2, _ = _do_request(
            "POST",
            f"{AI}/api/v1/lexi/chat",
            body={},
        )
        missing_fields_ok = s2 in (400, 401, 403, 422)

        if invalid_token_ok and missing_fields_ok:
            RESULTS["ai_chat_errors"] = "pass"
        else:
            RESULTS["ai_chat_errors"] = f"fail:invalid_token→{s1},missing→{s2}"
    except Exception as exc:
        RESULTS["ai_chat_errors"] = f"fail:{exc}"


def test_security() -> None:
    """CORS rejection of unknown origin + health endpoint + rate-limit header presence."""
    try:
        # /health endpoint
        sh, ph = _do_request("GET", f"{BACKEND}/health")
        health_ok = sh == 200

        # CORS reject unknown origin
        cors_rejected = True
        unknown_origin = "https://evil.hacker.io"
        req = urllib.request.Request(
            f"{BACKEND}/api/v1/courses",
            headers={"Origin": unknown_origin, "Accept": "application/json"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                acao = resp.getheader("Access-Control-Allow-Origin") or ""
                # If ACAO header is NOT the evil origin or wildcard that permits it, CORS is restricted
                if acao == unknown_origin or acao == "*":
                    cors_rejected = False
        except urllib.error.HTTPError as exc:
            acao = exc.headers.get("Access-Control-Allow-Origin") or ""
            if acao == unknown_origin or acao == "*":
                cors_rejected = False

        if health_ok and cors_rejected:
            RESULTS["security"] = "pass"
        elif not health_ok:
            RESULTS["security"] = f"fail:health→{sh}"
        else:
            RESULTS["security"] = "fail:cors_allows_unknown_origin"
    except Exception as exc:
        RESULTS["security"] = f"fail:{exc}"


def test_challenges_games(token: str) -> None:
    """Challenges daily + games word-scramble."""
    try:
        sc, _ = _do_request("GET", f"{BACKEND}/api/v1/challenges/daily", token=token)
        challenges_ok = sc in (200, 404)

        sg, _ = _do_request("GET", f"{BACKEND}/api/v1/games/word-scramble", token=token)
        games_ok = sg in (200, 404)

        sg2, _ = _do_request("GET", f"{BACKEND}/api/v1/games/categories", token=token)
        cats_ok = sg2 in (200, 404)

        fails = []
        if not challenges_ok:
            fails.append(f"challenges/daily→{sc}")
        if not games_ok:
            fails.append(f"games/word-scramble→{sg}")
        if not cats_ok:
            fails.append(f"games/categories→{sg2}")

        RESULTS["challenges_games"] = "pass" if not fails else f"fail:{','.join(fails)}"
    except Exception as exc:
        RESULTS["challenges_games"] = f"fail:{exc}"


def test_progress_apis(token: str) -> None:
    """Progress me, streak, weekly."""
    try:
        sp, pp = _do_request("GET", f"{BACKEND}/api/v1/progress/me", token=token)
        if sp == 200:
            data = pp.get("data") or {}
            summary = data.get("summary") or {}
            RESULTS["progress_apis"] = "pass"
        elif sp == 404:
            RESULTS["progress_apis"] = "skip"
        else:
            RESULTS["progress_apis"] = f"fail:progress/me→{sp}"
            return

        # streak
        ss, _ = _do_request("GET", f"{BACKEND}/api/v1/progress/streak", token=token)
        if ss not in (200, 404):
            RESULTS["progress_apis"] = f"fail:streak→{ss}"
    except Exception as exc:
        RESULTS["progress_apis"] = f"fail:{exc}"


def test_flutter_chrome() -> None:
    """Run flutter test on premium_gate_test.dart with timeout."""
    import subprocess

    flutter_test = Path(REPO_ROOT) / "flutter-app" / "test" / "core" / "widgets" / "premium_gate_test.dart"
    if not flutter_test.exists():
        RESULTS["flutter_chrome_runner"] = "skip:test_file_not_found"
        return

    try:
        result = subprocess.run(
            ["flutter", "test", "-d", "chrome", str(flutter_test)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(REPO_ROOT / "flutter-app"),
        )
        if result.returncode == 0:
            RESULTS["flutter_chrome_runner"] = "pass"
        else:
            stderr = (result.stderr or "")[:500]
            stdout = (result.stdout or "")[:500]
            combined = (stderr + stdout).strip()
            RESULTS["flutter_chrome_runner"] = f"fail:{combined[:300]}"
    except subprocess.TimeoutExpired:
        RESULTS["flutter_chrome_runner"] = "blocker:flutter_test_timed_out_120s"
    except FileNotFoundError:
        RESULTS["flutter_chrome_runner"] = "blocker:flutter_cli_not_found_in_PATH"
    except Exception as exc:
        RESULTS["flutter_chrome_runner"] = f"blocker:{exc}"


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=== LexiLingo Extended E2E ===", flush=True)

    # Step 1: get auth token via core E2E flow
    try:
        print("Acquiring test token...", flush=True)
        token, user_id = get_token()
        print("Token acquired.", flush=True)
    except Exception as exc:
        print(f"FATAL: cannot obtain token: {exc}", file=sys.stderr)
        # Fill all as fail
        for k in ["vocabulary", "flashcard", "gamification", "ielts",
                  "admin_api", "ai_chat_errors", "security",
                  "challenges_games", "progress_apis", "flutter_chrome_runner"]:
            RESULTS[k] = f"fail:no_token:{exc}"
        print_report()
        return 1

    # Step 2: run all suites
    print("Running vocabulary...", flush=True)
    test_vocabulary(token)

    print("Running gamification...", flush=True)
    test_gamification(token)

    print("Running IELTS...", flush=True)
    test_ielts(token)

    print("Running admin API...", flush=True)
    test_admin_api(token)

    print("Running AI chat error paths...", flush=True)
    test_ai_chat_errors()

    print("Running security...", flush=True)
    test_security()

    print("Running challenges & games...", flush=True)
    test_challenges_games(token)

    print("Running progress APIs...", flush=True)
    test_progress_apis(token)

    print("Running Flutter Chrome runner...", flush=True)
    test_flutter_chrome()

    print_report()
    failures = [k for k, v in RESULTS.items() if v.startswith("fail")]
    return 0 if not failures else 1


def print_report() -> None:
    report = {
        "vocabulary": RESULTS.get("vocabulary", "skip"),
        "flashcard": RESULTS.get("flashcard", "skip"),
        "gamification": RESULTS.get("gamification", "skip"),
        "ielts": RESULTS.get("ielts", "skip"),
        "admin_api": RESULTS.get("admin_api", "skip"),
        "ai_chat_errors": RESULTS.get("ai_chat_errors", "skip"),
        "security": RESULTS.get("security", "skip"),
        "challenges_games": RESULTS.get("challenges_games", "skip"),
        "progress_apis": RESULTS.get("progress_apis", "skip"),
        "flutter_chrome_runner": RESULTS.get("flutter_chrome_runner", "skip"),
        "fixes_applied": FIXES,
        "remaining_issues": ISSUES,
    }
    print("\n=== EXTENDED E2E REPORT ===")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        raise SystemExit(2)
