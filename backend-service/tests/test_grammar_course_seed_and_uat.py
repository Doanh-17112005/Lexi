"""QA, Idempotency, Answer-Security, Roadmap-Gate & UX Journey Tests for A1-C2 Grammar Seed."""

from __future__ import annotations

import uuid
from collections import Counter

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cefr_vocabulary_data import (
    CEFR_LEVELS,
    PROVENANCE_AI_GENERATED,
    QA_STATUS_NEEDS_REVIEW,
)
from app.core.grammar_course_data import (
    GRAMMAR_DIFFICULTY_TIERS,
    GRAMMAR_UNITS_AND_LESSONS,
    validate_grammar_course_catalog,
)
from app.models.content import GrammarItem, QuestionItem
from app.models.course import Course, Lesson, Unit
from app.models.user import User
from scripts.seed_grammar_courses import upsert_grammar_and_courses


def test_grammar_catalog_structure_cefr_balance_tiers_and_provenance() -> None:
    validate_grammar_course_catalog()

    assert len(GRAMMAR_UNITS_AND_LESSONS) == 6
    lessons = [
        lesson for unit in GRAMMAR_UNITS_AND_LESSONS for lesson in unit["lessons"]
    ]
    assert len(lessons) == 12

    level_counts = Counter(unit["level"] for unit in GRAMMAR_UNITS_AND_LESSONS)
    assert level_counts == Counter({lvl: 1 for lvl in CEFR_LEVELS})

    total_exercises = sum(len(lesson["exercises"]) for lesson in lessons)
    total_qb = sum(len(lesson["question_bank"]) for lesson in lessons)
    assert total_exercises == 72
    assert total_qb == 36

    tier_counts = Counter(
        ex["difficulty_tier"] for lesson in lessons for ex in lesson["exercises"]
    )
    assert tier_counts == Counter({tier: 24 for tier in GRAMMAR_DIFFICULTY_TIERS})


@pytest.mark.asyncio
class TestGrammarSeedIdempotencyAndUAT:
    async def test_idempotent_upsert_preserves_existing_lesson1_and_prevents_duplicates(
        self,
        db_session: AsyncSession,
    ) -> None:
        # Simulate live local DB shape: 6 published CEFR courses each with 1 Unit & 1 Lesson.
        existing_lesson1_ids: list[uuid.UUID] = []
        for level in CEFR_LEVELS:
            course = Course(
                id=uuid.uuid4(),
                title=f"{level} - Custom Existing Course",
                description="Existing course",
                language="en",
                level=level,
                total_lessons=1,
                total_xp=50,
                is_published=True,
            )
            db_session.add(course)
            await db_session.flush()
            unit = Unit(
                id=uuid.uuid4(),
                course_id=course.id,
                title=f"Unit 1: {level} Core Skills",
                order_index=1,
                total_lessons=1,
            )
            db_session.add(unit)
            await db_session.flush()
            l1 = Lesson(
                id=uuid.uuid4(),
                course_id=course.id,
                unit_id=unit.id,
                title=f"Lesson 1: {level} Mastery Challenge",
                order_index=1,
                xp_reward=50,
                lesson_type="lesson",
                content={
                    "exercises": [
                        {
                            "id": f"pre-{level}",
                            "type": "multiple_choice",
                            "ui_type": "multiple_choice",
                            "question": f"Existing {level} Q?",
                            "options": ["yes", "no"],
                            "correct_answer": "yes",
                            "explanation": "Preserved.",
                        }
                    ]
                },
            )
            db_session.add(l1)
            existing_lesson1_ids.append(l1.id)
        await db_session.commit()

        # Run 1
        stats_1 = await upsert_grammar_and_courses(db_session, ensure_base_courses=True)
        await db_session.commit()
        assert stats_1["courses"] == {"created": 0, "updated": 6, "unchanged": 0}
        assert stats_1["units"] == {"created": 6, "updated": 0, "unchanged": 0}
        assert stats_1["grammar_items"] == {"created": 12, "updated": 0, "unchanged": 0}
        assert stats_1["lessons"] == {"created": 12, "updated": 0, "unchanged": 0}
        assert stats_1["question_bank"] == {"created": 36, "updated": 0, "unchanged": 0}

        # Run 2 — strictly idempotent
        stats_2 = await upsert_grammar_and_courses(db_session, ensure_base_courses=True)
        await db_session.commit()
        assert stats_2["courses"] == {"created": 0, "updated": 0, "unchanged": 6}
        assert stats_2["units"] == {"created": 0, "updated": 0, "unchanged": 6}
        assert stats_2["grammar_items"] == {"created": 0, "updated": 0, "unchanged": 12}
        assert stats_2["lessons"] == {"created": 0, "updated": 0, "unchanged": 12}
        assert stats_2["question_bank"] == {"created": 0, "updated": 0, "unchanged": 36}

        # Existing Lesson 1 rows preserved untouched; DB holds 3 lessons/course (1 published + 2 draft grammar),
        # while Course.total_lessons reports only the 1 published lesson until draft grammar lessons are approved.
        for l1_id in existing_lesson1_ids:
            row = await db_session.scalar(select(Lesson).where(Lesson.id == l1_id))
            assert row is not None
            assert row.order_index == 1

        courses = (await db_session.execute(select(Course))).scalars().all()
        assert len(courses) == 6
        for c in courses:
            assert c.total_lessons == 1
            cnt = await db_session.scalar(
                select(func.count(Lesson.id)).where(Lesson.course_id == c.id)
            )
            assert cnt == 3

        assert await db_session.scalar(select(func.count(GrammarItem.id))) == 12
        assert await db_session.scalar(select(func.count(QuestionItem.id))) == 36

        grammar_rows = (await db_session.execute(select(GrammarItem))).scalars().all()
        for g_row in grammar_rows:
            assert g_row.is_active is False
            tags = set(g_row.tags or [])
            assert f"provenance:{PROVENANCE_AI_GENERATED.lower()}" in tags
            assert f"qa_status:{QA_STATUS_NEEDS_REVIEW.lower()}" in tags
            assert "qa_status:verified" not in tags

        qb_rows = (await db_session.execute(select(QuestionItem))).scalars().all()
        for q_row in qb_rows:
            assert q_row.is_active is False
            tags = set(q_row.tags or [])
            assert f"provenance:{PROVENANCE_AI_GENERATED.lower()}" in tags
            assert f"qa_status:{QA_STATUS_NEEDS_REVIEW.lower()}" in tags
            assert "qa_status:verified" not in tags

    async def test_no_answer_leak_roadmap_unlock_theory_practice_and_reload(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ) -> None:
        # Seed empty isolated test DB with full A1-C2 base + grammar lessons
        stats = await upsert_grammar_and_courses(db_session, ensure_base_courses=True)
        await db_session.commit()
        assert stats["courses"]["created"] == 6
        assert stats["lessons"]["created"] == 18

        # Pick A1 course — before editorial approval, learner roadmap hides NEEDS_REVIEW grammar drafts
        a1_course = await db_session.scalar(
            select(Course).where(Course.level == "A1")
        )
        assert a1_course is not None
        a1_course_id = a1_course.id

        enroll_res = await async_client.post(
            f"/api/v1/courses/{a1_course_id}/enroll",
            headers=auth_headers,
        )
        assert enroll_res.status_code in (200, 201)

        draft_roadmap = await async_client.get(
            f"/api/v1/learning/courses/{a1_course_id}/roadmap",
            headers=auth_headers,
        )
        assert draft_roadmap.status_code == 200
        assert len(draft_roadmap.json()["data"]["units"]) == 1

        # Verify provenance metadata stored in Grammar Lesson DB stays AI_GENERATED + NEEDS_REVIEW (DRAFT)
        draft_grammar_lessons = (
            await db_session.execute(
                select(Lesson).where(
                    Lesson.course_id == a1_course_id,
                    Lesson.lesson_type == "grammar",
                )
            )
        ).scalars().all()
        assert len(draft_grammar_lessons) == 2
        for g_lesson in draft_grammar_lessons:
            assert g_lesson.content["metadata"]["provenance_type"] == PROVENANCE_AI_GENERATED
            assert g_lesson.content["metadata"]["qa_status"] == QA_STATUS_NEEDS_REVIEW
            assert g_lesson.content["metadata"]["is_published"] is False
            blocked_start = await async_client.post(
                f"/api/v1/learning/lessons/{g_lesson.id}/start",
                headers=auth_headers,
            )
            assert blocked_start.status_code == 403

        # Simulate editorial approval inside isolated lexilingo_test only to test full unlocked UAT flow
        for g_item in (
            await db_session.execute(select(GrammarItem).where(GrammarItem.level == "A1"))
        ).scalars().all():
            g_item.is_active = True
        for g_lesson in draft_grammar_lessons:
            content_copy = dict(g_lesson.content)
            meta_copy = dict(content_copy["metadata"])
            meta_copy["qa_status"] = "VERIFIED"
            meta_copy["publication_state"] = "PUBLISHED"
            meta_copy["is_published"] = True
            meta_copy["source_reference"] = "lexilingo_test_editorial_fixture"
            content_copy["metadata"] = meta_copy
            g_lesson.content = content_copy
        await db_session.commit()

        roadmap_1 = await async_client.get(
            f"/api/v1/learning/courses/{a1_course_id}/roadmap",
            headers=auth_headers,
        )
        assert roadmap_1.status_code == 200
        units_1 = roadmap_1.json()["data"]["units"]
        assert len(units_1) == 2
        lesson1_id = units_1[0]["lessons"][0]["lesson_id"]
        grammar1_id = units_1[1]["lessons"][0]["lesson_id"]
        grammar2_id = units_1[1]["lessons"][1]["lesson_id"]

        assert units_1[0]["lessons"][0]["is_locked"] is False
        assert units_1[1]["lessons"][0]["is_locked"] is True
        assert units_1[1]["lessons"][1]["is_locked"] is True

        # Locked grammar lesson cannot be started directly
        locked_res = await async_client.post(
            f"/api/v1/learning/lessons/{grammar1_id}/start",
            headers=auth_headers,
        )
        assert locked_res.status_code == 403

        # Verify NO ANSWER LEAK on /content and /context BEFORE answering
        for lid in (lesson1_id, grammar1_id, grammar2_id):
            content_res = await async_client.get(
                f"/api/v1/learning/lessons/{lid}/content",
                headers=auth_headers,
            )
            assert content_res.status_code == 200
            payload = content_res.json()["data"]
            for ex in payload["exercises"]:
                assert ex.get("correct_answer") is None
                assert ex.get("explanation") is None
                for opt in ex.get("options") or []:
                    assert opt.get("is_correct") is None

            ctx_res = await async_client.get(
                f"/api/v1/learning/lessons/{lid}/context",
                headers=auth_headers,
            )
            assert ctx_res.status_code == 200
            ctx_raw = str(ctx_res.json()["data"])
            assert "correct_answer" not in ctx_raw
            assert "is_correct" not in ctx_raw

        # Step 1: Complete Lesson 1 to unlock Unit 2 -> Grammar Lesson 1
        start_1 = await async_client.post(
            f"/api/v1/learning/lessons/{lesson1_id}/start",
            headers=auth_headers,
        )
        assert start_1.status_code == 200
        att_1 = start_1.json()["data"]["attempt_id"]
        for qid, qtype, ans in [
            ("a1_ex_1", "multiple_choice", "goes"),
            ("a1_ex_2", "fill_blank", "have"),
        ]:
            a_res = await async_client.post(
                f"/api/v1/learning/attempts/{att_1}/answer",
                headers=auth_headers,
                json={
                    "question_id": qid,
                    "question_type": qtype,
                    "user_answer": ans,
                    "time_spent_ms": 1000,
                },
            )
            assert a_res.status_code == 200
            assert a_res.json()["data"]["is_correct"] is True

        comp_1 = await async_client.post(
            f"/api/v1/learning/attempts/{att_1}/complete",
            headers=auth_headers,
        )
        assert comp_1.status_code == 200
        assert comp_1.json()["data"]["passed"] is True
        assert comp_1.json()["data"]["next_lesson_unlocked"] == grammar1_id

        # Step 2: Open Grammar Lesson 1 -> View Theory (0 XP) -> Practice -> Wrong + Right -> Complete
        xp_before_theory = (await db_session.scalar(select(User.total_xp).where(User.id == test_user.id))) or 0
        g_content = await async_client.get(
            f"/api/v1/learning/lessons/{grammar1_id}/content",
            headers=auth_headers,
        )
        assert g_content.status_code == 200
        g_data = g_content.json()["data"]
        assert g_data["theory_viewed"] is False
        assert g_data["grammar_theory"] is not None
        assert g_data["grammar_theory"]["title"] == "Verb 'To Be' & Present Simple Habits"
        assert len(g_data["grammar_theory"]["linked_exercise_ids"]) == 6

        tv = await async_client.post(
            f"/api/v1/learning/lessons/{grammar1_id}/theory-viewed",
            headers=auth_headers,
        )
        assert tv.status_code == 200
        assert tv.json()["data"]["theory_viewed"] is True

        xp_after_theory = (await db_session.scalar(select(User.total_xp).where(User.id == test_user.id))) or 0
        assert xp_after_theory == xp_before_theory

        start_g1 = await async_client.post(
            f"/api/v1/learning/lessons/{grammar1_id}/start",
            headers=auth_headers,
        )
        assert start_g1.status_code == 200
        att_g1 = start_g1.json()["data"]["attempt_id"]

        # Submit 1 intentional wrong answer + 5 right answers (score = 83% >= 70% pass_threshold)
        wrong_res = await async_client.post(
            f"/api/v1/learning/attempts/{att_g1}/answer",
            headers=auth_headers,
            json={
                "question_id": "a1_g1_ex1",
                "question_type": "multiple_choice",
                "user_answer": "is",
                "time_spent_ms": 1500,
            },
        )
        assert wrong_res.status_code == 200
        w_data = wrong_res.json()["data"]
        assert w_data["is_correct"] is False
        assert w_data["correct_answer"] == "are"
        assert "My parents" in w_data["explanation"]

        for qid, qtype, ans in [
            ("a1_g1_ex2", "true_false", "False"),
            ("a1_g1_ex3", "fill_blank", "studies"),
            ("a1_g1_ex4", "fill_blank", "don't"),
            ("a1_g1_ex5", "fill_blank", "She doesn't like spicy food."),
            ("a1_g1_ex6", "fill_blank", "do"),
        ]:
            ok_res = await async_client.post(
                f"/api/v1/learning/attempts/{att_g1}/answer",
                headers=auth_headers,
                json={
                    "question_id": qid,
                    "question_type": qtype,
                    "user_answer": ans,
                    "time_spent_ms": 1200,
                },
            )
            assert ok_res.status_code == 200
            ok_data = ok_res.json()["data"]
            assert ok_data["is_correct"] is True
            assert ok_data["correct_answer"] == ans
            assert ok_data["explanation"]

        comp_g1 = await async_client.post(
            f"/api/v1/learning/attempts/{att_g1}/complete",
            headers=auth_headers,
        )
        assert comp_g1.status_code == 200
        c_g1_data = comp_g1.json()["data"]
        assert c_g1_data["passed"] is True
        assert c_g1_data["total_xp_earned"] > 0
        assert c_g1_data["next_lesson_unlocked"] == grammar2_id

        xp_after_g1 = (await db_session.scalar(select(User.total_xp).where(User.id == test_user.id))) or 0
        assert xp_after_g1 > xp_after_theory

        # Duplicate completion must be rejected and NOT duplicate XP
        dup_g1 = await async_client.post(
            f"/api/v1/learning/attempts/{att_g1}/complete",
            headers=auth_headers,
        )
        assert dup_g1.status_code == 400
        xp_after_dup = (await db_session.scalar(select(User.total_xp).where(User.id == test_user.id))) or 0
        assert xp_after_dup == xp_after_g1

        # Simulate reload: verify roadmap unlock, course %, and theory_viewed persistence
        db_session.expire_all()
        roadmap_after = await async_client.get(
            f"/api/v1/learning/courses/{a1_course_id}/roadmap",
            headers=auth_headers,
        )
        assert roadmap_after.status_code == 200
        units_after = roadmap_after.json()["data"]["units"]
        assert units_after[1]["lessons"][0]["is_completed"] is True
        assert units_after[1]["lessons"][1]["is_locked"] is False

        course_detail = await async_client.get(
            f"/api/v1/courses/{a1_course_id}",
            headers=auth_headers,
        )
        assert course_detail.status_code == 200
        assert course_detail.json()["data"]["user_progress"] == pytest.approx(2 / 3 * 100, abs=0.2)

        g1_reload = await async_client.get(
            f"/api/v1/learning/lessons/{grammar1_id}/content",
            headers=auth_headers,
        )
        assert g1_reload.status_code == 200
        assert g1_reload.json()["data"]["theory_viewed"] is True

        # Grammar Lesson 2 is now startable
        start_g2 = await async_client.post(
            f"/api/v1/learning/lessons/{grammar2_id}/start",
            headers=auth_headers,
        )
        assert start_g2.status_code == 200
