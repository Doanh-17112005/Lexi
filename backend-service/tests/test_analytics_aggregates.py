"""Database-independent regression tests for analytics response aggregation."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.routes.analytics import (
    _retention_rate,
    get_content_performance,
    get_retention_cohorts,
    get_vocabulary_effectiveness,
)


def _result(rows: list[SimpleNamespace]) -> MagicMock:
    result = MagicMock()
    result.fetchall.return_value = rows
    return result


@pytest.mark.asyncio
async def test_content_performance_returns_real_attempt_aggregates():
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            _result([
                SimpleNamespace(
                    id="course-1",
                    title="Travel",
                    enrollments=4,
                    completions=3,
                    avg_score=82.5,
                    avg_time_minutes=12.25,
                )
            ]),
            _result([
                SimpleNamespace(
                    id="lesson-1",
                    title="At the airport",
                    attempts=5,
                    completions=4,
                    avg_score=78.4,
                )
            ]),
        ]
    )

    response = await get_content_performance(admin=SimpleNamespace(), db=db)

    assert response["courses"][0] == {
        "course_id": "course-1",
        "course_title": "Travel",
        "enrollments": 4,
        "completions": 3,
        "completion_rate": 75.0,
        "avg_score": 82.5,
        "avg_time_minutes": 12.25,
    }
    assert response["lessons"][0]["attempts"] == 5
    assert response["lessons"][0]["completions"] == 4
    assert response["lessons"][0]["avg_score"] == 78.4


@pytest.mark.asyncio
async def test_vocabulary_effectiveness_includes_per_word_review_average():
    db = MagicMock()
    db.scalar = AsyncMock(side_effect=[100, 20, 5, 7.25])
    db.execute = AsyncMock(
        return_value=_result([
            SimpleNamespace(word="ephemeral", total=10, mastered=2, avg_reviews=9.5)
        ])
    )

    response = await get_vocabulary_effectiveness(admin=SimpleNamespace(), db=db)

    assert response["avg_mastery_rate"] == 25.0
    assert response["avg_reviews_to_master"] == 7.25
    assert response["hardest_words"] == [
        {"word": "ephemeral", "mastery_rate": 20.0, "avg_reviews": 9.5}
    ]


def test_retention_rate_excludes_users_not_old_enough_for_horizon():
    signup_dates = {
        "old-retained": date(2026, 1, 1),
        "old-lost": date(2026, 1, 1),
        "too-new": date(2026, 1, 30),
    }
    activities = {
        "old-retained": {date(2026, 1, 8)},
        "too-new": {date(2026, 2, 6)},
    }

    rate = _retention_rate(
        set(signup_dates), signup_dates, activities, 7, date(2026, 2, 2)
    )

    assert rate == 50.0


@pytest.mark.asyncio
async def test_retention_cohorts_use_signup_and_activity_rows():
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            _result([
                SimpleNamespace(id="u1", created_at=SimpleNamespace(date=lambda: date.today())),
            ]),
            _result([]),
        ]
    )

    response = await get_retention_cohorts(admin=SimpleNamespace(), db=db)

    assert len(response["cohorts"]) == 12
    assert sum(cohort["users"] for cohort in response["cohorts"]) == 1
    assert db.execute.await_count == 2
