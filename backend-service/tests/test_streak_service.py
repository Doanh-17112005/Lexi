from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.progress import DailyActivity
from app.services import streak_service
from app.services.streak_service import get_or_create_daily_activity, update_user_streak


def _result(value=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


@pytest.mark.asyncio
async def test_update_user_streak_uses_utc_service_date(monkeypatch):
    fixed_today = date(2026, 6, 26)
    monkeypatch.setattr(streak_service, "_utc_today", lambda: fixed_today)
    monkeypatch.setattr(
        streak_service,
        "check_achievements_for_user",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(streak_service, "delete_cached", AsyncMock())

    db = MagicMock()
    db.execute = AsyncMock(side_effect=[_result(None), _result(None)])
    db.add = MagicMock()
    db.flush = AsyncMock()

    streak, increased, saved, achievements = await update_user_streak(
        db,
        uuid4(),
    )

    assert streak.last_activity_date == fixed_today
    assert streak.current_streak == 1
    assert increased is True
    assert saved is False
    assert achievements == []


@pytest.mark.asyncio
async def test_update_user_streak_reuses_pending_daily_activity(
    monkeypatch, db_session, test_user
):
    fixed_today = date(2026, 8, 30)
    monkeypatch.setattr(streak_service, "_utc_today", lambda: fixed_today)
    monkeypatch.setattr(
        streak_service,
        "check_achievements_for_user",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(streak_service, "delete_cached", AsyncMock())
    db_session.sync_session.autoflush = False
    pending_activity = DailyActivity(
        user_id=test_user.id,
        activity_date=fixed_today,
        vocabulary_reviewed=1,
    )
    db_session.add(pending_activity)

    await update_user_streak(db_session, test_user.id)

    activities = (
        await db_session.execute(
            select(DailyActivity).where(
                DailyActivity.user_id == test_user.id,
                DailyActivity.activity_date == fixed_today,
            )
        )
    ).scalars().all()
    assert activities == [pending_activity]
    assert activities[0].vocabulary_reviewed == 1


@pytest.mark.asyncio
async def test_get_or_create_daily_activity_recovers_from_concurrent_insert(
    monkeypatch, db_session, test_user
):
    from sqlalchemy.exc import IntegrityError

    fixed_today = date(2026, 9, 1)
    winner = DailyActivity(
        user_id=test_user.id,
        activity_date=fixed_today,
        xp_earned=15,
    )
    db_session.add(winner)
    await db_session.commit()

    # Simulate a stale snapshot on the first SELECT followed by a unique constraint
    # collision during nested flush, verifying recovery fetches the existing row.
    real_execute = db_session.execute
    calls = {"count": 0}

    async def raced_execute(stmt, *args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return _result(None)
        return await real_execute(stmt, *args, **kwargs)

    real_flush = db_session.flush

    async def raced_flush(*args, **kwargs):
        raise IntegrityError("INSERT", {}, Exception("idx_daily_activity_user_date"))

    monkeypatch.setattr(db_session, "execute", raced_execute)
    monkeypatch.setattr(db_session, "flush", raced_flush)

    recovered = await get_or_create_daily_activity(
        db_session, test_user.id, today=fixed_today
    )

    monkeypatch.setattr(db_session, "flush", real_flush)
    assert recovered.id == winner.id
    assert recovered.xp_earned == 15
