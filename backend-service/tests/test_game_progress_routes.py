"""Tests for durable, immutable per-question game progress."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.routes.games import get_game_session_progress, save_game_answer
from app.schemas.games import GameAnswerProgressRequest


def _session_and_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    session = MagicMock()
    session.id = uuid.uuid4()
    session.user_id = user.id
    session.game_type = "grammar_quiz"
    session.cefr_level = "B1"
    session.completed_at = None
    session.xp_awarded = False
    session.started_at = datetime.now(timezone.utc)
    session.created_at = session.started_at
    session.session_data = {
        "expected_items": [
            {
                "id": "q1",
                "answer": "has",
                "xp_value": 15,
                "explanation": {
                    "summary": "Use has with she.",
                    "rule": "Present perfect: has + past participle.",
                    "example": "She has finished.",
                    "option_explanations": {},
                },
            }
        ],
        "submitted_answers": {},
        "content_snapshot": {"game": "grammar_quiz"},
    }
    return session, user


@pytest.mark.asyncio
async def test_answer_is_saved_once_and_returns_feedback():
    session, user = _session_and_user()
    db = MagicMock()
    db.commit = AsyncMock()

    with patch(
        "app.routes.games.get_game_session_for_update",
        new_callable=AsyncMock,
        return_value=session,
    ):
        response = await save_game_answer(
            session_id=session.id,
            item_id="q1",
            body=GameAnswerProgressRequest(answer="has"),
            db=db,
            current_user=user,
        )

    assert response.is_correct is True
    assert response.correct_answer == "has"
    assert response.explanation["example"] == "She has finished."
    assert session.session_data["submitted_answers"] == {"q1": "has"}
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_same_answer_retry_is_idempotent_without_second_write():
    session, user = _session_and_user()
    session.session_data["submitted_answers"] = {"q1": "has"}
    db = MagicMock()
    db.commit = AsyncMock()

    with patch(
        "app.routes.games.get_game_session_for_update",
        new_callable=AsyncMock,
        return_value=session,
    ):
        response = await save_game_answer(
            session_id=session.id,
            item_id="q1",
            body=GameAnswerProgressRequest(answer="has"),
            db=db,
            current_user=user,
        )

    assert response.already_submitted is True
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_finalized_answer_cannot_be_changed():
    session, user = _session_and_user()
    session.session_data["submitted_answers"] = {"q1": "have"}

    with patch(
        "app.routes.games.get_game_session_for_update",
        new_callable=AsyncMock,
        return_value=session,
    ):
        with pytest.raises(HTTPException) as exc:
            await save_game_answer(
                session_id=session.id,
                item_id="q1",
                body=GameAnswerProgressRequest(answer="has"),
                db=MagicMock(),
                current_user=user,
            )

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_progress_returns_content_and_finalized_answers():
    session, user = _session_and_user()
    session.session_data["submitted_answers"] = {"q1": "have"}

    with patch(
        "app.routes.games.get_game_session_for_update",
        new_callable=AsyncMock,
        return_value=session,
    ):
        response = await get_game_session_progress(
            session_id=session.id,
            db=MagicMock(),
            current_user=user,
        )

    assert response.status == "in_progress"
    assert response.content == {"game": "grammar_quiz"}
    assert len(response.answers) == 1
    assert response.answers[0].is_correct is False


@pytest.mark.asyncio
async def test_expired_progress_is_reported_and_cannot_accept_answers():
    session, user = _session_and_user()
    session.started_at = datetime.now(timezone.utc) - timedelta(hours=3)

    with patch(
        "app.routes.games.get_game_session_for_update",
        new_callable=AsyncMock,
        return_value=session,
    ):
        progress = await get_game_session_progress(
            session_id=session.id,
            db=MagicMock(),
            current_user=user,
        )
        with pytest.raises(HTTPException) as exc:
            await save_game_answer(
                session_id=session.id,
                item_id="q1",
                body=GameAnswerProgressRequest(answer="has"),
                db=MagicMock(),
                current_user=user,
            )

    assert progress.status == "expired"
    assert exc.value.status_code == 410
