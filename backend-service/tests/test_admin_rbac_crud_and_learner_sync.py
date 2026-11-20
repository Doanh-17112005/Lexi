"""Admin RBAC, CRUD, cache invalidation, and Learner-sync regression tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import Achievement
from app.models.vocabulary import VocabularyItem


@pytest.mark.asyncio
class TestAdminRbacAndLearnerSync:
    """End-to-end verification of Admin guards, non-destructive edits, and cache sync."""

    async def test_unauthenticated_and_non_admin_blocked(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        protected_paths = [
            "/api/v1/admin/courses",
            "/api/v1/admin/vocabulary",
            "/api/v1/admin/grammar",
            "/api/v1/admin/achievements",
            "/api/v1/admin/users",
            "/api/v1/admin/analytics/dashboard/kpis",
            "/api/v1/admin/system-info",
        ]
        for path in protected_paths:
            unauth = await async_client.get(path)
            assert unauth.status_code == 401, f"Expected 401 for unauthenticated {path}"

            learner = await async_client.get(path, headers=auth_headers)
            assert learner.status_code == 403, f"Expected 403 for learner on {path}"

    async def test_course_unit_lesson_publish_gate_and_cache_invalidation(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        auth_headers: dict,
    ):
        # Warm learner courses cache before admin creates & publishes a course
        before = await async_client.get("/api/v1/courses", headers=auth_headers)
        assert before.status_code == 200
        initial_titles = {c["title"] for c in before.json()["data"]}

        course_res = await async_client.post(
            "/api/v1/admin/courses",
            headers=admin_headers,
            json={
                "title": "Admin Sync Course A2",
                "description": "Course created by admin",
                "language": "en",
                "level": "A2",
                "is_published": False,
            },
        )
        assert course_res.status_code == 200
        course_id = course_res.json()["data"]["id"]

        # Publishing empty course is blocked with 409
        blocked = await async_client.put(
            f"/api/v1/admin/courses/{course_id}",
            headers=admin_headers,
            json={"is_published": True},
        )
        assert blocked.status_code == 409

        unit_res = await async_client.post(
            "/api/v1/admin/units",
            headers=admin_headers,
            json={
                "course_id": course_id,
                "title": "Unit 1 Basics",
                "description": "Unit description",
                "order_index": 0,
            },
        )
        assert unit_res.status_code == 200
        unit_id = unit_res.json()["data"]["id"]

        lesson_res = await async_client.post(
            "/api/v1/admin/lessons",
            headers=admin_headers,
            json={
                "course_id": course_id,
                "unit_id": unit_id,
                "title": "Lesson 1 Sync",
                "description": "Practice",
                "order_index": 0,
                "lesson_type": "grammar",
                "skill": "grammar",
                "xp_reward": 20,
                "pass_threshold": 70,
            },
        )
        assert lesson_res.status_code == 200
        lesson_id = lesson_res.json()["data"]["id"]

        # Empty lesson exercises still blocks publish with 409
        empty_lesson_blocked = await async_client.put(
            f"/api/v1/admin/courses/{course_id}",
            headers=admin_headers,
            json={"is_published": True},
        )
        assert empty_lesson_blocked.status_code == 409

        # Populate exercises via /lessons/{id}/content (exact Admin Exercise Editor path)
        content_res = await async_client.put(
            f"/api/v1/admin/lessons/{lesson_id}/content",
            headers=admin_headers,
            json={
                "content": {
                    "exercises": [
                        {
                            "id": "q1",
                            "type": "multiple_choice",
                            "question": "Pick correct",
                            "options": ["is", "are"],
                            "correct_answer": "is",
                        }
                    ]
                }
            },
        )
        assert content_res.status_code == 200

        publish_res = await async_client.put(
            f"/api/v1/admin/courses/{course_id}",
            headers=admin_headers,
            json={"is_published": True},
        )
        assert publish_res.status_code == 200
        assert publish_res.json()["data"]["is_published"] is True

        # Learner immediately sees newly published course (courses cache invalidated)
        after = await async_client.get("/api/v1/courses", headers=auth_headers)
        assert after.status_code == 200
        after_titles = {c["title"] for c in after.json()["data"]}
        assert "Admin Sync Course A2" not in initial_titles
        assert "Admin Sync Course A2" in after_titles

    async def test_vocabulary_update_preserves_examples_enforces_qa_and_syncs_learner(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        db_session: AsyncSession,
    ):
        vocab = VocabularyItem(
            word="itinerary",
            definition="A planned route or journey",
            translation={"vi": "lịch trình cũ", "examples": ["We checked the travel itinerary."]},
            part_of_speech="noun",
            pronunciation="/aɪˈtɪnəreri/",
            difficulty_level="B2",
            tags={"tags": ["travel"], "topic": "travel", "source": "AI_GENERATED", "qa_status": "NEEDS_REVIEW"},
        )
        db_session.add(vocab)
        await db_session.commit()
        await db_session.refresh(vocab)

        # Warm learner vocab cache — NEEDS_REVIEW item must stay hidden from learner catalog
        warm = await async_client.get("/api/v1/vocabulary/items?tag=travel")
        assert warm.status_code == 200
        assert not any(item["word"] == "itinerary" for item in warm.json())

        # Attempt update without source_reference while requesting VERIFIED -> stays NEEDS_REVIEW, examples preserved
        update_res = await async_client.put(
            f"/api/v1/admin/vocabulary/{vocab.id}",
            headers=admin_headers,
            params={
                "translation": "hành trình chi tiết",
                "topics": "travel,business",
                "qa_status": "VERIFIED",
            },
        )
        assert update_res.status_code == 200
        data = update_res.json()["data"]
        assert data["translation"]["vi"] == "hành trình chi tiết"
        assert data["translation"]["examples"] == ["We checked the travel itinerary."]
        assert data["topics"] == ["travel", "business"]
        assert data["qa_status"] == "NEEDS_REVIEW"

        # Add source_reference -> now VERIFIED is accepted and filterable
        verify_res = await async_client.put(
            f"/api/v1/admin/vocabulary/{vocab.id}",
            headers=admin_headers,
            params={
                "qa_status": "VERIFIED",
                "source_reference": "Cambridge Dictionary B2",
            },
        )
        assert verify_res.status_code == 200
        assert verify_res.json()["data"]["qa_status"] == "VERIFIED"

        filtered = await async_client.get(
            "/api/v1/admin/vocabulary",
            headers=admin_headers,
            params={"topic": "business", "qa_status": "VERIFIED", "difficulty_level": "B2"},
        )
        assert filtered.status_code == 200
        assert any(item["id"] == str(vocab.id) for item in filtered.json()["data"])

        # Learner /vocabulary/items?tag=business sees updated translation without stale cache
        learner_items = await async_client.get("/api/v1/vocabulary/items?tag=business")
        assert learner_items.status_code == 200
        matched = [item for item in learner_items.json() if item["word"] == "itinerary"]
        assert len(matched) == 1
        assert matched[0]["translation"]["vi"] == "hành trình chi tiết"

    async def test_user_management_hides_secrets_and_achievements_kpis_respond(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_user,
        db_session: AsyncSession,
    ):
        ach = Achievement(
            name="Test First Badge",
            description="Complete 1 lesson",
            condition_type="lesson_complete",
            condition_value=1,
            xp_reward=10,
            category="lessons",
            slug="test_first_badge",
        )
        db_session.add(ach)
        await db_session.commit()

        users_res = await async_client.get("/api/v1/admin/users", headers=admin_headers)
        assert users_res.status_code == 200
        body = users_res.json()["data"]
        assert body["total"] >= 1
        for u in body["users"]:
            assert "hashed_password" not in u
            assert "password" not in u

        kpis_res = await async_client.get("/api/v1/admin/analytics/dashboard/kpis", headers=admin_headers)
        assert kpis_res.status_code == 200
        assert "kpis" in kpis_res.json()

        ach_res = await async_client.get("/api/v1/admin/achievements", headers=admin_headers)
        assert ach_res.status_code == 200
        assert any(item["slug"] == "test_first_badge" for item in ach_res.json()["data"])
