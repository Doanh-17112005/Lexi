"""Tests for Firebase ID-token verification modes."""

from unittest.mock import MagicMock

from app.core import firebase_auth


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
