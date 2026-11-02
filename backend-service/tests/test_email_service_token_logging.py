import logging
from urllib.parse import quote

import pytest

from app.core.config import settings
from app.services.email_service import EmailService


def _captured_messages(caplog: pytest.LogCaptureFixture) -> str:
    return "\n".join(record.getMessage() for record in caplog.records)


@pytest.mark.asyncio
async def test_missing_smtp_does_not_log_password_reset_token_or_url(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = "reset-canary/?&=not-a-secret"
    monkeypatch.setattr(settings, "SMTP_HOST", None)

    with caplog.at_level(logging.WARNING, logger="app.services.email_service"):
        sent = await EmailService.send_password_reset_email(
            to_email="learner@example.com",
            reset_token=token,
            display_name="Learner",
        )

    logged = _captured_messages(caplog)
    assert sent is False
    assert token not in logged
    assert quote(token, safe="") not in logged
    assert "?token=" not in logged
    assert settings.effective_password_reset_url_base not in logged


@pytest.mark.asyncio
async def test_missing_smtp_does_not_log_verification_token_or_url(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = "verify-canary/?&=not-a-secret"
    monkeypatch.setattr(settings, "SMTP_HOST", None)

    with caplog.at_level(logging.WARNING, logger="app.services.email_service"):
        sent = await EmailService.send_verification_email(
            to_email="learner@example.com",
            token=token,
            display_name="Learner",
        )

    logged = _captured_messages(caplog)
    assert sent is False
    assert token not in logged
    assert quote(token, safe="") not in logged
    assert "?token=" not in logged
    assert settings.effective_email_verification_url_base not in logged
