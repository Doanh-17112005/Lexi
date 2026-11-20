"""Tests for T19-T22: Public guest trial pack and published course preview."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.user import User


@pytest.mark.asyncio
class TestGuestTrialRoutes:
    async def test_trial_pack_manifest_requires_no_auth_and_leaks_no_answers(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        before_users = (
            await db_session.execute(select(func.count(User.id)))
        ).scalar_one()

        res = await async_client.get("/api/v1/guest/trial-pack")
        assert res.status_code == 200
        payload = res.json()["data"]

        assert payload["manifest_version"] == "2026.1.0"
        assert payload["policy"]["requires_auth"] is False
        assert payload["policy"]["creates_user"] is False
        assert payload["policy"]["premium_included"] is False
        assert len(payload["vocabulary_items"]) == 6
        assert payload["grammar_theory"]["title"]
        assert len(payload["quiz_questions"]) == 4

        # Ensure raw answers are never leaked inside manifest
        serialized = res.text.lower()
        assert '"correct_answer"' not in serialized
        assert '"correct_option"' not in serialized
        assert '"is_correct"' not in serialized
        for q in payload["quiz_questions"]:
            assert len(q["answer_digest"]) == 64

        after_users = (
            await db_session.execute(select(func.count(User.id)))
        ).scalar_one()
        assert after_users == before_users

    async def test_trial_pack_grade_evaluates_correctly_without_creating_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        before_users = (
            await db_session.execute(select(func.count(User.id)))
        ).scalar_one()

        res = await async_client.post(
            "/api/v1/guest/trial-pack/grade",
            json={
                "answers": [
                    {"question_id": "gq-1", "selected_option": "commutes"},
                    {"question_id": "gq-2", "selected_option": "in"},
                    {"question_id": "gq-3", "selected_option": "confirm"},
                    {"question_id": "gq-4", "selected_option": "polite"},
                ]
            },
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["correct_count"] == 3
        assert data["total_questions"] == 4
        assert data["score_percentage"] == 75.0

        after_users = (
            await db_session.execute(select(func.count(User.id)))
        ).scalar_one()
        assert after_users == before_users

    async def test_public_courses_returns_only_published_non_sensitive_metadata(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        pub = Course(
            id=uuid.uuid4(),
            title="Published Guest Course",
            description="Public course",
            language="en",
            level="A1",
            is_published=True,
            total_lessons=3,
        )
        draft = Course(
            id=uuid.uuid4(),
            title="Secret Unpublished Draft",
            description="Private draft",
            language="en",
            level="B2",
            is_published=False,
            total_lessons=1,
        )
        db_session.add_all([pub, draft])
        await db_session.commit()

        res = await async_client.get("/api/v1/guest/courses?limit=20")
        assert res.status_code == 200
        titles = [c["title"] for c in res.json()["data"]]
        assert "Published Guest Course" in titles
        assert "Secret Unpublished Draft" not in titles
