"""Tests for T23-T29: 6-Skill Placement Test (Start, Answer, Submit, Rubric, Deduplication)."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.course import Course
from app.models.proficiency import UserProficiencyProfile, UserSkillScore
from app.models.user import User


@pytest.mark.asyncio
class TestSixSkillPlacementTest:
    async def test_full_six_skill_lifecycle_with_rubric_and_dedup(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        # Seed a published course at B1/B2 so recommendations return real courses
        db_session.add(
            Course(
                id=uuid.uuid4(),
                title="B2 Academic Mastery",
                description="Targeted B2 skills",
                language="en",
                level="B2",
                is_published=True,
                total_lessons=12,
            )
        )
        await db_session.commit()

        # 1. Start attempt
        start_res = await async_client.post(
            "/api/v1/proficiency/placement-test/start",
            headers=auth_headers,
        )
        assert start_res.status_code == 200
        start_data = start_res.json()
        attempt_id = start_data["attempt_id"]
        assert set(start_data["skills"]) == {
            "listening",
            "speaking",
            "reading",
            "writing",
            "grammar",
            "vocabulary",
        }
        assert len(start_data["questions"]) == 10
        assert "not an official cefr" in start_data["disclaimer"].lower()

        # No answer keys leaked in start payload
        lowered = start_res.text.lower()
        assert '"correct"' not in lowered
        assert '"rubric_keywords"' not in lowered

        # 2. Save partial answer draft & verify reload persistence + cross-user isolation
        save_res = await async_client.put(
            f"/api/v1/proficiency/placement-test/{attempt_id}/answer",
            headers=auth_headers,
            json={"task_id": "p6-vocab-1", "selected_option": 0},
        )
        assert save_res.status_code == 200
        assert save_res.json()["answered_count"] == 1

        reload_res = await async_client.get(
            f"/api/v1/proficiency/placement-test/{attempt_id}",
            headers=auth_headers,
        )
        assert reload_res.status_code == 200
        assert reload_res.json()["status"] == "in_progress"
        assert "p6-vocab-1" in reload_res.json()["saved_answers"]

        # Cross-user access denied
        other_user = User(
            id=uuid.uuid4(),
            email="other-placement@example.com",
            username="other_placement",
            hashed_password=get_password_hash("StrongPass123!"),
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        other_headers = {
            "Authorization": f"Bearer {create_access_token({'sub': str(other_user.id)})}"
        }
        cross_res = await async_client.get(
            f"/api/v1/proficiency/placement-test/{attempt_id}",
            headers=other_headers,
        )
        assert cross_res.status_code == 404

        # 3. Submit all remaining answers (high score + real speaking/writing rubric text)
        answers = [
            {"task_id": "p6-vocab-2", "selected_option": 0},
            {"task_id": "p6-grammar-1", "selected_option": 0},
            {"task_id": "p6-grammar-2", "selected_option": 0},
            {"task_id": "p6-reading-1", "selected_option": 0},
            {"task_id": "p6-reading-2", "selected_option": 0},
            {"task_id": "p6-listening-1", "selected_option": 0},
            {"task_id": "p6-listening-2", "selected_option": 0},
            {
                "task_id": "p6-speaking-1",
                "text_response": (
                    "Every morning I listen to English podcasts and read news aloud. "
                    "I practice speaking for twenty minutes daily because it helps improve my fluency."
                ),
            },
            {
                "task_id": "p6-writing-1",
                "text_response": (
                    "My main English goal for the next three months is to improve my writing and speaking fluency. "
                    "I will study vocabulary every morning and read articles because regular practice builds confidence. "
                    "Therefore, I plan to write one short summary each week."
                ),
            },
        ]

        idem_key = "submit-once-key-1"
        sub_res = await async_client.post(
            f"/api/v1/proficiency/placement-test/{attempt_id}/submit",
            headers=auth_headers,
            json={
                "answers": answers,
                "time_taken_seconds": 180,
                "idempotency_key": idem_key,
            },
        )
        assert sub_res.status_code == 200
        result = sub_res.json()
        assert result["idempotent_replay"] is False
        assert result["objective_correct"] if "objective_correct" in result else result["correct_count"] == 8
        assert set(result["skill_scores"].keys()) == set(start_data["skills"])
        assert result["skill_scores"]["speaking"] > 50
        assert result["skill_scores"]["writing"] > 50
        assert len(result["recommendations"]) == 2
        assert "not an official cefr" in result["disclaimer"].lower()

        rubric_details = {
            d["task_id"]: d for d in result["details"]
        }
        assert rubric_details["p6-speaking-1"]["scoring_mode"] == "deterministic_rubric"
        assert rubric_details["p6-speaking-1"]["ai_graded"] is False
        assert rubric_details["p6-writing-1"]["scoring_mode"] == "deterministic_rubric"
        assert rubric_details["p6-writing-1"]["ai_graded"] is False

        # Verify persistent DB state for all 6 UserSkillScore rows
        prof = (
            await db_session.execute(
                select(UserProficiencyProfile).where(
                    UserProficiencyProfile.user_id == test_user.id
                )
            )
        ).scalar_one()
        skill_rows = (
            await db_session.execute(
                select(UserSkillScore).where(UserSkillScore.profile_id == prof.id)
            )
        ).scalars().all()
        assert len(skill_rows) == 6

        # 4. Idempotent retry returns cached result; different/missing key gets 409 Conflict
        replay_res = await async_client.post(
            f"/api/v1/proficiency/placement-test/{attempt_id}/submit",
            headers=auth_headers,
            json={"answers": [], "idempotency_key": idem_key},
        )
        assert replay_res.status_code == 200
        assert replay_res.json()["idempotent_replay"] is True

        dup_res = await async_client.post(
            f"/api/v1/proficiency/placement-test/{attempt_id}/submit",
            headers=auth_headers,
            json={"answers": [], "idempotency_key": "other-key"},
        )
        assert dup_res.status_code == 409
