"""Tests for T07–T08 shared roadmap unlock policy and route enforcement."""

from types import SimpleNamespace
import uuid

import pytest
from httpx import AsyncClient

from app.services.roadmap_unlock_policy import evaluate_course_unlocks


def _lesson(order_index: int, *, exercises: int = 2, prerequisites=None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        order_index=order_index,
        exercise_count=exercises,
        prerequisites=prerequisites or [],
    )


def _unit(order_index: int, lessons):
    return SimpleNamespace(
        id=uuid.uuid4(),
        order_index=order_index,
        lessons=lessons,
    )


class TestRoadmapUnlockPolicyUnit:
    def test_empty_course_and_non_playable_lessons_do_not_dead_end(self):
        assert evaluate_course_unlocks([], set()) == {}

        draft_l1 = _lesson(1, exercises=0)
        real_l2 = _lesson(2, exercises=3)
        unit1 = _unit(1, [draft_l1, real_l2])

        decisions = evaluate_course_unlocks([unit1], set(), playable_only=True)
        assert set(decisions.keys()) == {real_l2.id}
        assert decisions[real_l2.id].is_locked is False

    def test_previous_lesson_previous_unit_and_explicit_prerequisites(self):
        u1_l1 = _lesson(1)
        u1_l2 = _lesson(2)
        u2_l1 = _lesson(1)
        u2_l2 = _lesson(2, prerequisites=[u1_l1.id])
        units = [_unit(1, [u1_l1, u1_l2]), _unit(2, [u2_l1, u2_l2])]

        # Initial state: only u1_l1 unlocked
        d0 = evaluate_course_unlocks(units, set())
        assert d0[u1_l1.id].is_locked is False
        assert d0[u1_l2.id].is_locked is True
        assert d0[u2_l1.id].is_locked is True
        assert d0[u2_l2.id].is_locked is True

        # Complete u1_l1 -> u1_l2 unlocks, u2_l1 still locked by unit 1
        d1 = evaluate_course_unlocks(units, {u1_l1.id})
        assert d1[u1_l1.id].is_locked is False  # replay allowed
        assert d1[u1_l2.id].is_locked is False
        assert d1[u2_l1.id].is_locked is True

        # Complete u1_l2 -> u2_l1 unlocks, u2_l2 waits for u2_l1
        d2 = evaluate_course_unlocks(units, {u1_l1.id, u1_l2.id})
        assert d2[u2_l1.id].is_locked is False
        assert d2[u2_l2.id].is_locked is True

        # Complete u2_l1 -> u2_l2 unlocks
        d3 = evaluate_course_unlocks(units, {u1_l1.id, u1_l2.id, u2_l1.id})
        assert d3[u2_l2.id].is_locked is False


class TestRoadmapUnlockGateRoutes:
    @pytest.mark.asyncio
    async def test_roadmap_course_detail_and_start_lesson_enforce_same_policy(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session,
        test_user,
    ):
        from app.models.course import Course, Lesson, Unit
        from app.models.progress import UserCourseProgress, UserProgress

        course = Course(
            title="T08 Unlock Gate Course",
            description="Unlock gate integration test",
            language="en",
            level="A1",
            total_lessons=3,
            is_published=True,
        )
        db_session.add(course)
        await db_session.flush()

        unit1 = Unit(
            course_id=course.id,
            title="Unit 1",
            description="Unit 1",
            order_index=1,
            total_lessons=2,
        )
        unit2 = Unit(
            course_id=course.id,
            title="Unit 2",
            description="Unit 2",
            order_index=2,
            total_lessons=1,
        )
        db_session.add_all([unit1, unit2])
        await db_session.flush()

        ex = [{"id": "q1", "type": "multiple_choice", "question": "Q", "correct_answer": "A"}]
        l1 = Lesson(
            course_id=course.id,
            unit_id=unit1.id,
            title="Lesson 1",
            description="L1",
            order_index=1,
            content={"exercises": ex},
        )
        l2 = Lesson(
            course_id=course.id,
            unit_id=unit1.id,
            title="Lesson 2",
            description="L2",
            order_index=2,
            content={"exercises": ex},
        )
        l3 = Lesson(
            course_id=course.id,
            unit_id=unit2.id,
            title="Lesson 3 (Unit 2)",
            description="L3",
            order_index=1,
            content={"exercises": ex},
        )
        db_session.add_all([l1, l2, l3])
        await db_session.flush()

        db_session.add(
            UserCourseProgress(
                user_id=test_user.id,
                course_id=course.id,
                progress_percentage=0.0,
                lessons_completed=0,
            )
        )
        await db_session.commit()

        # 1. Roadmap and Course Detail agree: l1 unlocked, l2 & l3 locked
        roadmap_res = await async_client.get(
            f"/api/v1/learning/courses/{course.id}/roadmap",
            headers=auth_headers,
        )
        assert roadmap_res.status_code == 200
        rm_units = roadmap_res.json()["data"]["units"]
        rm_locks = {
            les["lesson_id"]: les["is_locked"]
            for u in rm_units
            for les in u["lessons"]
        }
        assert rm_locks == {str(l1.id): False, str(l2.id): True, str(l3.id): True}

        detail_res = await async_client.get(
            f"/api/v1/courses/{course.id}",
            headers=auth_headers,
        )
        assert detail_res.status_code == 200
        dt_locks = {
            les["id"]: les["is_locked"]
            for u in detail_res.json()["data"]["units"]
            for les in u["lessons"]
        }
        assert dt_locks == rm_locks

        # 2. Direct start_lesson on locked l2 & l3 is rejected with 403
        start_l2_locked = await async_client.post(
            f"/api/v1/learning/lessons/{l2.id}/start",
            headers=auth_headers,
        )
        assert start_l2_locked.status_code == 403

        start_l3_locked = await async_client.post(
            f"/api/v1/learning/lessons/{l3.id}/start",
            headers=auth_headers,
        )
        assert start_l3_locked.status_code == 403

        # 3. Complete l1 -> l2 unlocks (l3 stays locked until l2 completes)
        db_session.add(
            UserProgress(
                user_id=test_user.id,
                course_id=course.id,
                lesson_id=l1.id,
                status="completed",
                score=100,
                attempts=1,
            )
        )
        await db_session.commit()

        start_l2_unlocked = await async_client.post(
            f"/api/v1/learning/lessons/{l2.id}/start",
            headers=auth_headers,
        )
        assert start_l2_unlocked.status_code == 200

        # Replay of completed l1 still allowed
        replay_l1 = await async_client.post(
            f"/api/v1/learning/lessons/{l1.id}/start",
            headers=auth_headers,
        )
        assert replay_l1.status_code == 200
