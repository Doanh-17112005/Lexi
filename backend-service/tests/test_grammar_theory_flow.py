"""Tests for T10-T12: Grammar theory -> practice contract, sanitization, and theory-viewed tracking."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import GrammarItem
from app.models.course import Course, Lesson, Unit
from app.models.progress import UserProgress
from app.models.user import User


@pytest.mark.asyncio
class TestGrammarTheoryPracticeContract:
    async def _seed_grammar_lesson(
        self,
        db_session: AsyncSession,
        *,
        lesson_type: str = "grammar",
        content: dict | None = None,
    ) -> tuple[Course, Lesson]:
        course = Course(
            id=uuid.uuid4(),
            title="Grammar Course",
            description="Grammar course",
            language="en",
            level="A1",
            is_published=True,
        )
        db_session.add(course)
        await db_session.flush()

        unit = Unit(
            id=uuid.uuid4(),
            course_id=course.id,
            title="Unit 1",
            order_index=1,
        )
        db_session.add(unit)
        await db_session.flush()

        lesson = Lesson(
            id=uuid.uuid4(),
            course_id=course.id,
            unit_id=unit.id,
            title="Present Simple",
            description="Present simple rules",
            lesson_type=lesson_type,
            order_index=1,
            xp_reward=25,
            pass_threshold=80,
            estimated_minutes=10,
            content=content,
        )
        db_session.add(lesson)
        await db_session.commit()
        return course, lesson

    async def test_grammar_lesson_returns_sanitized_linked_theory_and_tracks_view(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        grammar_item = GrammarItem(
            id=uuid.uuid4(),
            title="Present Simple Tense",
            level="A1",
            topic="tenses",
            summary="Routine actions and general facts.",
            content="Add -s/-es for third-person singular subjects.",
            examples=[
                {
                    "sentence": "She walks to school.",
                    "translation": "Cô ấy đi bộ đến trường.",
                    "correct_answer": "LEAKED",
                    "answer": "LEAKED",
                }
            ],
            is_active=True,
        )
        db_session.add(grammar_item)
        await db_session.flush()

        _, lesson = await self._seed_grammar_lesson(
            db_session,
            lesson_type="grammar",
            content={
                "grammar_item_id": str(grammar_item.id),
                "grammar_points": ["Subject + V(s/es)"],
                "exercises": [
                    {
                        "id": "ex-g1",
                        "type": "multiple_choice",
                        "question": "She ___ to school.",
                        "options": ["walk", "walks"],
                        "correct_answer": "walks",
                    }
                ],
            },
        )

        initial_xp = test_user.total_xp or 0

        res = await async_client.get(
            f"/api/v1/learning/lessons/{lesson.id}/content",
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["theory_viewed"] is False
        theory = data["grammar_theory"]
        assert theory is not None
        assert theory["grammar_item_id"] == str(grammar_item.id)
        assert theory["title"] == "Present Simple Tense"
        assert theory["linked_exercise_ids"] == ["ex-g1"]
        assert theory["examples"][0]["sentence"] == "She walks to school."
        assert "correct_answer" not in theory["examples"][0]
        assert "answer" not in theory["examples"][0]

        # Mark theory viewed — should NOT complete lesson or award XP
        view_res = await async_client.post(
            f"/api/v1/learning/lessons/{lesson.id}/theory-viewed",
            headers=auth_headers,
        )
        assert view_res.status_code == 200
        assert view_res.json()["data"]["theory_viewed"] is True

        # Idempotent repeat view
        view_res_2 = await async_client.post(
            f"/api/v1/learning/lessons/{lesson.id}/theory-viewed",
            headers=auth_headers,
        )
        assert view_res_2.status_code == 200

        await db_session.refresh(test_user)
        assert (test_user.total_xp or 0) == initial_xp

        prog = (
            await db_session.execute(
                select(UserProgress).where(
                    UserProgress.user_id == test_user.id,
                    UserProgress.lesson_id == lesson.id,
                )
            )
        ).scalar_one()
        assert prog.status == "in_progress"

        # Content now reflects theory_viewed == True
        res_after = await async_client.get(
            f"/api/v1/learning/lessons/{lesson.id}/content",
            headers=auth_headers,
        )
        assert res_after.status_code == 200
        assert res_after.json()["data"]["theory_viewed"] is True

    async def test_grammar_lesson_without_theory_returns_409(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        _, lesson = await self._seed_grammar_lesson(
            db_session,
            lesson_type="grammar",
            content={
                "exercises": [
                    {
                        "id": "ex-1",
                        "type": "multiple_choice",
                        "question": "Pick one",
                        "options": ["a", "b"],
                        "correct_answer": "a",
                    }
                ]
            },
        )
        res = await async_client.get(
            f"/api/v1/learning/lessons/{lesson.id}/content",
            headers=auth_headers,
        )
        assert res.status_code == 409

    async def test_non_grammar_lesson_keeps_theory_null(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        _, lesson = await self._seed_grammar_lesson(
            db_session,
            lesson_type="lesson",
            content={
                "exercises": [
                    {
                        "id": "ex-1",
                        "type": "multiple_choice",
                        "question": "Hello?",
                        "options": ["Hi", "Bye"],
                        "correct_answer": "Hi",
                    }
                ]
            },
        )
        res = await async_client.get(
            f"/api/v1/learning/lessons/{lesson.id}/content",
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["grammar_theory"] is None
        assert data["theory_viewed"] is False
