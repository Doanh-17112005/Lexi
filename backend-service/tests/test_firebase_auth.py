"""Tests for Firebase ID-token verification modes."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core import firebase_auth
from app.models.user import User


def test_public_cert_verification_without_service_account(monkeypatch):
    project_id = "lexilingo-test"
    claims = {
        "sub": "firebase-user",
        "iss": f"https://securetoken.google.com/{project_id}",
        "aud": project_id,
        "email": "user@example.com",
    }
    verify_token = MagicMock(return_value=claims)

    monkeypatch.setattr(firebase_auth.settings, "FIREBASE_PROJECT_ID", project_id)
    monkeypatch.setattr(firebase_auth.settings, "FIREBASE_CREDENTIALS_FILE", None)
    monkeypatch.setattr(firebase_auth.settings, "FIREBASE_CREDENTIALS_JSON", None)
    monkeypatch.setattr(firebase_auth.google_id_token, "verify_token", verify_token)

    assert firebase_auth.verify_firebase_token("firebase-token") == claims
    assert verify_token.call_args.kwargs["audience"] == project_id
    assert (
        verify_token.call_args.kwargs["certs_url"]
        == firebase_auth.FIREBASE_CERTS_URL
    )


def test_public_cert_verification_rejects_wrong_issuer(monkeypatch):
    monkeypatch.setattr(firebase_auth.settings, "FIREBASE_PROJECT_ID", "expected")
    monkeypatch.setattr(firebase_auth.settings, "FIREBASE_CREDENTIALS_FILE", None)
    monkeypatch.setattr(firebase_auth.settings, "FIREBASE_CREDENTIALS_JSON", None)
    monkeypatch.setattr(
        firebase_auth.google_id_token,
        "verify_token",
        lambda *_args, **_kwargs: {"sub": "user", "iss": "wrong-issuer"},
    )

    assert firebase_auth.verify_firebase_token("firebase-token") is None


def test_admin_sdk_is_used_when_credentials_are_configured(monkeypatch):
    claims = {"sub": "firebase-user"}
    initialize = MagicMock()
    verify_id_token = MagicMock(return_value=claims)

    monkeypatch.setattr(firebase_auth.settings, "FIREBASE_CREDENTIALS_FILE", "key.json")
    monkeypatch.setattr(firebase_auth.settings, "FIREBASE_CREDENTIALS_JSON", None)
    monkeypatch.setattr(firebase_auth, "_init_firebase_app", initialize)
    monkeypatch.setattr(firebase_auth.firebase_auth, "verify_id_token", verify_id_token)

    assert firebase_auth.verify_firebase_token("firebase-token") == claims
    initialize.assert_called_once_with()
    verify_id_token.assert_called_once_with("firebase-token")


@pytest.mark.asyncio
async def test_facebook_claim_links_facebook_provider(monkeypatch):
    user = User(
        email="facebook@example.com",
        username="facebook-user",
        hashed_password="not-used",
        provider=["local"],
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db = AsyncMock()
    db.execute.return_value = result
    monkeypatch.setattr(
        type(firebase_auth.settings),
        "get_admin_role_for_email",
        lambda _settings, _email: None,
    )

    linked = await firebase_auth.get_or_create_user_from_claims(
        db,
        {
            "email": user.email,
            "email_verified": True,
            "firebase": {"sign_in_provider": "facebook.com"},
        },
    )

    assert linked is user
    assert user.provider == ["local", "facebook"]
    assert "google" not in user.provider


@pytest.mark.asyncio
@pytest.mark.parametrize("email_verified", [False, None])
async def test_firebase_claim_rejects_unverified_email(email_verified):
    db = AsyncMock()

    with pytest.raises(ValueError, match="not verified"):
        await firebase_auth.get_or_create_user_from_claims(
            db,
            {
                "email": "unverified@example.com",
                "email_verified": email_verified,
                "firebase": {"sign_in_provider": "facebook.com"},
            },
        )

    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_firebase_claim_rejects_unsupported_provider():
    db = AsyncMock()

    with pytest.raises(ValueError, match="Unsupported"):
        await firebase_auth.get_or_create_user_from_claims(
            db,
            {
                "email": "password@example.com",
                "email_verified": True,
                "firebase": {"sign_in_provider": "password"},
            },
        )

    db.execute.assert_not_awaited()
