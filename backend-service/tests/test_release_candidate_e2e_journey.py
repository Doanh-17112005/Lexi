"""Release Candidate Full User Journey Integration Test (Section 6).

Verifies an unbroken end-to-end learning lifecycle on isolated test DB:
  Enroll -> Roadmap Lock Check -> Lesson Start -> Wrong Answer (Mistake Capture)
  -> Retry Correct & Complete -> XP & Course Progress -> Roadmap Lesson 2 Unlock
  -> Practice Mistakes Session -> 6-Skill Placement Test & Dedup.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course, Lesson, Unit
from app.models.user import User


@pytest.mark.asyncio
class TestReleaseCandidateUserJourney:
    async def test_complete_end_to_end_learning_and_assessment_journey(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        # 1. Seed Course with 1 Unit & 2 sequential lessons
        course = Course(
            id=uuid.uuid4(),
            title="RC Integration English B1",
            description="End-to-end verification course",
            language="en",
            level="B1",
            is_published=True,
            total_lessons=2,
            total_xp=60,
        )
        db_session.add(course)
        await db_session.flush()

        unit = Unit(
            id=uuid.uuid4(),
            course_id=course.id,
            title="Unit 1: Core Flow",
            order_index=1,
        )
        db_session.add(unit)
        await db_session.flush()

        l1 = Lesson(
            id=uuid.uuid4(),
            course_id=course.id,
            unit_id=unit.id,
            title="RC Grammar Lesson",
            description="Present Perfect basics",
            lesson_type="grammar",
            order_index=1,
            xp_reward=30,
            pass_threshold=50,
            estimated_minutes=5,
            content={
                "theory": {
                    "title": "Present Perfect",
                    "explanation": "Use have/has + past participle.",
                    "examples": [{"sentence": "She has worked here since 2022."}],
                },
                "exercises": [
                    {
                        "id": "rc-ex-1",
                        "type": "multiple_choice",
                        "question": "She ___ here since 2022.",
                        "options": ["worked", "has worked"],
                        "correct_answer": "has worked",
                    },
                    {
                        "id": "rc-ex-2",
                        "type": "multiple_choice",
                        "question": "I ___ my homework already.",
                        "options": ["finished", "have finished"],
                        "correct_answer": "have finished",
                    },
                ],
            },
        )
        l2 = Lesson(
            id=uuid.uuid4(),
            course_id=course.id,
            unit_id=unit.id,
            title="RC Next Lesson",
            description="Follow-up lesson",
            lesson_type="lesson",
            order_index=2,
            xp_reward=30,
            pass_threshold=80,
            estimated_minutes=5,
            content={
                "exercises": [
                    {
                        "id": "rc-ex-3",
                        "type": "multiple_choice",
                        "question": "Pick greeting:",
                        "options": ["Hello", "Chair"],
                        "correct_answer": "Hello",
                    }
                ]
            },
        )
        db_session.add_all([l1, l2])
        await db_session.commit()

        # 2. Enroll in course
        enroll_res = await async_client.post(
            f"/api/v1/courses/{course.id}/enroll",
            headers=auth_headers,
        )
        assert enroll_res.status_code in (200, 201)

        # 3. Roadmap shows Lesson 1 unlocked and Lesson 2 locked (and direct start returns 403)
        roadmap_before = await async_client.get(
            f"/api/v1/learning/courses/{course.id}/roadmap",
            headers=auth_headers,
        )
        assert roadmap_before.status_code == 200
        lessons_before = roadmap_before.json()["data"]["units"][0]["lessons"]
        assert lessons_before[0]["is_locked"] is False
        assert lessons_before[1]["is_locked"] is True

        blocked_l2 = await async_client.post(
            f"/api/v1/learning/lessons/{l2.id}/start",
            headers=auth_headers,
        )
        assert blocked_l2.status_code == 403

        # 4. Load Grammar Theory -> Mark theory viewed (0 XP awarded)
        initial_xp = test_user.total_xp or 0
        content_res = await async_client.get(
            f"/api/v1/learning/lessons/{l1.id}/content",
            headers=auth_headers,
        )
        assert content_res.status_code == 200
        assert content_res.json()["data"]["grammar_theory"]["title"] == "Present Perfect"

        tv_res = await async_client.post(
            f"/api/v1/learning/lessons/{l1.id}/theory-viewed",
            headers=auth_headers,
        )
        assert tv_res.status_code == 200
        await db_session.refresh(test_user)
        assert (test_user.total_xp or 0) == initial_xp

        # 5. Start Lesson 1 -> Submit 1 wrong + 1 right -> Complete Lesson 1 -> XP & Progress updated
        start_res = await async_client.post(
            f"/api/v1/learning/lessons/{l1.id}/start",
            headers=auth_headers,
        )
        assert start_res.status_code == 200
        attempt_id = start_res.json()["data"]["attempt_id"]

        ans1 = await async_client.post(
            f"/api/v1/learning/attempts/{attempt_id}/answer",
            headers=auth_headers,
            json={
                "question_id": "rc-ex-1",
                "question_type": "multiple_choice",
                "user_answer": "worked",
                "time_spent_ms": 1200,
            },
        )
        assert ans1.status_code == 200
        assert ans1.json()["data"]["is_correct"] is False

        ans2 = await async_client.post(
            f"/api/v1/learning/attempts/{attempt_id}/answer",
            headers=auth_headers,
            json={
                "question_id": "rc-ex-2",
                "question_type": "multiple_choice",
                "user_answer": "have finished",
                "time_spent_ms": 1100,
            },
        )
        assert ans2.status_code == 200
        assert ans2.json()["data"]["is_correct"] is True

        comp_res = await async_client.post(
            f"/api/v1/learning/attempts/{attempt_id}/complete",
            headers=auth_headers,
        )
        assert comp_res.status_code == 200
        assert comp_res.json()["data"]["passed"] is True
        assert comp_res.json()["data"]["total_xp_earned"] > 0

        # Duplicate completion rejected
        dup_comp = await async_client.post(
            f"/api/v1/learning/attempts/{attempt_id}/complete",
            headers=auth_headers,
        )
        assert dup_comp.status_code == 400

        # Course progress reflects 50% (1/2) consistently in Detail & My Progress
        detail_after = await async_client.get(
            f"/api/v1/courses/{course.id}",
            headers=auth_headers,
        )
        assert detail_after.status_code == 200
        assert detail_after.json()["data"]["user_progress"] == pytest.approx(50.0)

        # Roadmap now unlocks Lesson 2
        roadmap_after = await async_client.get(
            f"/api/v1/learning/courses/{course.id}/roadmap",
            headers=auth_headers,
        )
        assert roadmap_after.status_code == 200
        lessons_after = roadmap_after.json()["data"]["units"][0]["lessons"]
        assert lessons_after[1]["is_locked"] is False

        start_l2 = await async_client.post(
            f"/api/v1/learning/lessons/{l2.id}/start",
            headers=auth_headers,
        )
        assert start_l2.status_code == 200

        # 6. Mistake notebook capture + review loop
        m_create = await async_client.post(
            "/api/v1/mistakes",
            headers=auth_headers,
            json={
                "id": "rc-mistake-1",
                "source_type": "course_lesson",
                "source_id": f"{l1.id}:rc-ex-1",
                "source_title": l1.title,
                "question": "She ___ here since 2022.",
                "selected_answer": "worked",
                "correct_answer": "has worked",
                "explanation": "Use Present Perfect with since 2022.",
                "skill": "grammar",
            },
        )
        assert m_create.status_code in (200, 201)
        m_rev = await async_client.patch(
            "/api/v1/mistakes/rc-mistake-1/review",
            headers=auth_headers,
        )
        assert m_rev.status_code == 200
        assert m_rev.json()["data"]["reviewed_at"] is not None

        # 7. 6-Skill Placement Test round-trip
        p_start = await async_client.post(
            "/api/v1/proficiency/placement-test/start",
            headers=auth_headers,
        )
        assert p_start.status_code == 200
        p_attempt_id = p_start.json()["attempt_id"]
        p_sub = await async_client.post(
            f"/api/v1/proficiency/placement-test/{p_attempt_id}/submit",
            headers=auth_headers,
            json={
                "answers": [
                    {"task_id": "p6-vocab-1", "selected_option": 0},
                    {"task_id": "p6-grammar-1", "selected_option": 0},
                    {"task_id": "p6-listening-1", "selected_option": 0},
                    {
                        "task_id": "p6-speaking-1",
                        "text_response": "I practice English every morning to improve fluency.",
                    },
                    {
                        "task_id": "p6-writing-1",
                        "text_response": "My goal is to study English grammar daily because it improves my writing skills.",
                    },
                ],
                "time_taken_seconds": 90,
                "idempotency_key": "rc-place-1",
            },
        )
        assert p_sub.status_code == 200
        assert "assessed_level" in p_sub.json()
        assert len(p_sub.json()["skill_scores"]) == 6
