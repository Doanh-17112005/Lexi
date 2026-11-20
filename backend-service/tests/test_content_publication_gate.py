"""Tests enforcing content publication gating between PUBLISHED/VERIFIED,
NEEDS_REVIEW/DRAFT, and CONFLICT/BLOCKED across Learner & Admin endpoints."""

from __future__ import annotations

from datetime import date
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.progress import ProgressCRUD
from app.models.course import Course, Lesson, Unit
from app.models.progress import LessonAttempt, LessonCompletion, UserCourseProgress
from app.models.user import User
from app.models.vocabulary import DifficultyLevel, PartOfSpeech, VocabularyItem
from app.services.content_publication_policy import (
    PUBLICATION_DRAFT,
    PUBLICATION_PUBLISHED,
    PUBLICATION_QUARANTINED,
    classify_lesson_publication,
    classify_vocabulary_publication,
)


def test_publication_classifier_separates_published_draft_and_quarantined() -> None:
    assert classify_vocabulary_publication(None) == PUBLICATION_PUBLISHED
    assert (
        classify_vocabulary_publication(
            {"qa_status": "VERIFIED", "audit_status": "CONFIRMED_SOURCE", "topic": ["daily"]}
        )
        == PUBLICATION_PUBLISHED
    )
    assert (
        classify_vocabulary_publication(
            {"qa_status": "NEEDS_REVIEW", "audit_status": "CONFIRMED_SOURCE", "topic": ["daily"]}
        )
        == PUBLICATION_DRAFT
    )
    assert (
        classify_vocabulary_publication(
            {"qa_status": "NEEDS_REVIEW", "audit_status": "CONFLICT", "topic": ["travel"]}
        )
        == PUBLICATION_QUARANTINED
    )
    assert (
        classify_vocabulary_publication(
            {"qa_status": "NEEDS_REVIEW", "audit_status": "BLOCKED", "topic": ["science"]}
        )
        == PUBLICATION_QUARANTINED
    )

    legacy_lesson = Lesson(id=uuid.uuid4(), title="Legacy", content={"exercises": []})
    draft_lesson = Lesson(
        id=uuid.uuid4(),
        title="Draft Grammar",
        content={"metadata": {"qa_status": "NEEDS_REVIEW", "is_published": False}},
    )
    quarantined_lesson = Lesson(
        id=uuid.uuid4(),
        title="Conflict Grammar",
        content={"metadata": {"audit_status": "CONFLICT"}},
    )
    verified_lesson = Lesson(
        id=uuid.uuid4(),
        title="Verified Grammar",
        content={"metadata": {"qa_status": "VERIFIED", "is_published": True}},
    )
    assert classify_lesson_publication(legacy_lesson) == PUBLICATION_PUBLISHED
    assert classify_lesson_publication(verified_lesson) == PUBLICATION_PUBLISHED
    assert classify_lesson_publication(draft_lesson) == PUBLICATION_DRAFT
    assert classify_lesson_publication(quarantined_lesson) == PUBLICATION_QUARANTINED


@pytest.mark.asyncio
async def test_learner_vocabulary_hides_draft_conflict_and_blocked_while_admin_sees_all(
    async_client: AsyncClient,
    admin_headers: dict,
    db_session: AsyncSession,
) -> None:
    published_word = VocabularyItem(
        id=uuid.uuid4(),
        word="clarity",
        definition="The quality of being clear and easy to understand.",
        translation={"vi": "sự rõ ràng"},
        part_of_speech=PartOfSpeech.NOUN,
        difficulty_level=DifficultyLevel.B2,
        tags={
            "source": "SOURCE_VERIFIED",
            "source_reference": "Oxford B2",
            "qa_status": "VERIFIED",
            "audit_status": "CONFIRMED_SOURCE",
            "topic": ["general"],
        },
    )
    draft_word = VocabularyItem(
        id=uuid.uuid4(),
        word="draft_confirmed",
        definition="Confirmed source item still awaiting editorial verification.",
        translation={"vi": "nháp đã đối chứng"},
        part_of_speech=PartOfSpeech.NOUN,
        difficulty_level=DifficultyLevel.B2,
        tags={
            "source": "AI_GENERATED",
            "source_reference": None,
            "qa_status": "NEEDS_REVIEW",
            "audit_status": "CONFIRMED_SOURCE",
            "topic": ["general"],
        },
    )
    conflict_word = VocabularyItem(
        id=uuid.uuid4(),
        word="airport_conflict",
        definition="Place where planes land with CEFR level conflict.",
        translation={"vi": "sân bay"},
        part_of_speech=PartOfSpeech.NOUN,
        difficulty_level=DifficultyLevel.A2,
        tags={
            "source": "AI_GENERATED",
            "source_reference": None,
            "qa_status": "NEEDS_REVIEW",
            "audit_status": "CONFLICT",
            "topic": ["general"],
        },
    )
    blocked_word = VocabularyItem(
        id=uuid.uuid4(),
        word="rationale_blocked",
        definition="Underlying reason lacking direct CEFR badge.",
        translation={"vi": "cơ sở lý luận"},
        part_of_speech=PartOfSpeech.NOUN,
        difficulty_level=DifficultyLevel.C1,
        tags={
            "source": "AI_GENERATED",
            "source_reference": None,
            "qa_status": "NEEDS_REVIEW",
            "audit_status": "BLOCKED",
            "topic": ["general"],
        },
    )
    db_session.add_all([published_word, draft_word, conflict_word, blocked_word])
    await db_session.commit()

    # Learner catalog & Word-of-Day ONLY serve PUBLISHED items
    learner_list = await async_client.get("/api/v1/vocabulary/items?tag=general&limit=50")
    assert learner_list.status_code == 200
    assert [row["word"] for row in learner_list.json()] == ["clarity"]

    learner_search = await async_client.get("/api/v1/vocabulary/items?search=conflict")
    assert learner_search.status_code == 200
    assert learner_search.json() == []

    for hidden_id in (draft_word.id, conflict_word.id, blocked_word.id):
        detail = await async_client.get(f"/api/v1/vocabulary/items/{hidden_id}")
        assert detail.status_code == 404

    wod = await async_client.get("/api/v1/vocabulary/word-of-day")
    assert wod.status_code == 200
    assert wod.json()["word"] == "clarity"

    # Admin sees all states + publication_state + audit_status, and cannot verify CONFLICT without resolution
    admin_list = await async_client.get("/api/v1/admin/vocabulary?limit=50", headers=admin_headers)
    assert admin_list.status_code == 200
    by_word = {row["word"]: row for row in admin_list.json()["data"]}
    assert by_word["clarity"]["publication_state"] == PUBLICATION_PUBLISHED
    assert by_word["draft_confirmed"]["publication_state"] == PUBLICATION_DRAFT
    assert by_word["airport_conflict"]["publication_state"] == PUBLICATION_QUARANTINED
    assert by_word["rationale_blocked"]["publication_state"] == PUBLICATION_QUARANTINED

    attempt_verify_conflict = await async_client.put(
        f"/api/v1/admin/vocabulary/{conflict_word.id}",
        headers=admin_headers,
        params={"qa_status": "VERIFIED", "source_reference": "Cambridge A2"},
    )
    assert attempt_verify_conflict.status_code == 200
    assert attempt_verify_conflict.json()["data"]["qa_status"] == "NEEDS_REVIEW"
    assert attempt_verify_conflict.json()["data"]["publication_state"] == PUBLICATION_QUARANTINED


@pytest.mark.asyncio
async def test_learner_course_detail_and_roadmap_hide_draft_lessons(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict,
) -> None:
    course = Course(
        id=uuid.uuid4(),
        title="B1 Publication Gate Test",
        language="en",
        level="B1",
        total_lessons=1,
        is_published=True,
    )
    db_session.add(course)
    await db_session.flush()

    unit1 = Unit(id=uuid.uuid4(), course_id=course.id, title="Unit 1 Live", order_index=1)
    unit2 = Unit(id=uuid.uuid4(), course_id=course.id, title="Unit 2 Draft", order_index=2)
    db_session.add_all([unit1, unit2])
    await db_session.flush()

    live_lesson = Lesson(
        id=uuid.uuid4(),
        course_id=course.id,
        unit_id=unit1.id,
        title="Lesson 1 Published",
        order_index=1,
        lesson_type="lesson",
        content={
            "metadata": {"qa_status": "VERIFIED", "is_published": True},
            "exercises": [{"id": "e1", "type": "multiple_choice", "question": "Q", "correct_answer": "A"}],
        },
    )
    draft_grammar_lesson = Lesson(
        id=uuid.uuid4(),
        course_id=course.id,
        unit_id=unit2.id,
        title="Grammar Draft Needs Review",
        order_index=1,
        lesson_type="grammar",
        content={
            "metadata": {"qa_status": "NEEDS_REVIEW", "is_published": False, "publication_state": "DRAFT"},
            "grammar_points": ["Present Perfect"],
            "exercises": [{"id": "g1", "type": "multiple_choice", "question": "Q2", "correct_answer": "B"}],
        },
    )
    db_session.add_all([live_lesson, draft_grammar_lesson])
    await db_session.commit()

    detail = await async_client.get(f"/api/v1/courses/{course.id}", headers=auth_headers)
    assert detail.status_code == 200
    detail_data = detail.json()["data"]
    assert detail_data["total_lessons"] == 1
    assert len(detail_data["units"]) == 1
    assert [item["id"] for item in detail_data["units"][0]["lessons"]] == [str(live_lesson.id)]

    await async_client.post(f"/api/v1/courses/{course.id}/enroll", headers=auth_headers)
    roadmap = await async_client.get(f"/api/v1/learning/courses/{course.id}/roadmap", headers=auth_headers)
    assert roadmap.status_code == 200
    rm_data = roadmap.json()["data"]
    assert rm_data["total_lessons"] == 1
    assert len(rm_data["units"]) == 1

    # Direct access to unpublished NEEDS_REVIEW grammar lesson is denied cleanly
    for method, url in (
        ("POST", f"/api/v1/learning/lessons/{draft_grammar_lesson.id}/start"),
        ("GET", f"/api/v1/learning/lessons/{draft_grammar_lesson.id}/content"),
        ("GET", f"/api/v1/learning/lessons/{draft_grammar_lesson.id}/context"),
        ("POST", f"/api/v1/learning/lessons/{draft_grammar_lesson.id}/theory-viewed"),
    ):
        resp = await async_client.request(method, url, headers=auth_headers)
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_draft_attempt_cannot_submit_answer_complete_or_dilute_progress(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict,
    test_user: User,
) -> None:
    course = Course(
        id=uuid.uuid4(),
        title="A1 Gate With Legacy Lesson",
        language="en",
        level="A1",
        total_lessons=1,
        is_published=True,
    )
    db_session.add(course)
    await db_session.flush()

    unit1 = Unit(id=uuid.uuid4(), course_id=course.id, title="Unit 1 Legacy", order_index=1)
    unit2 = Unit(id=uuid.uuid4(), course_id=course.id, title="Unit 2 Grammar Draft", order_index=2)
    db_session.add_all([unit1, unit2])
    await db_session.flush()

    # Legacy Lesson 1 has NO metadata block — must stay visible and completable
    legacy_lesson = Lesson(
        id=uuid.uuid4(),
        course_id=course.id,
        unit_id=unit1.id,
        title="Legacy Lesson 1",
        order_index=1,
        lesson_type="lesson",
        xp_reward=15,
        pass_threshold=70.0,
        content={
            "exercises": [
                {
                    "id": "ex1",
                    "type": "multiple_choice",
                    "question": "Hello?",
                    "correct_answer": "Hi",
                }
            ]
        },
    )
    draft_lesson = Lesson(
        id=uuid.uuid4(),
        course_id=course.id,
        unit_id=unit2.id,
        title="Draft Grammar Unit 2",
        order_index=1,
        lesson_type="grammar",
        xp_reward=25,
        pass_threshold=80.0,
        content={
            "metadata": {"qa_status": "NEEDS_REVIEW", "is_published": False, "publication_state": "DRAFT"},
            "exercises": [
                {
                    "id": "g1",
                    "type": "multiple_choice",
                    "question": "I ___ a student.",
                    "correct_answer": "am",
                }
            ],
        },
    )
    db_session.add_all([legacy_lesson, draft_lesson])
    await db_session.flush()

    # Enroll + pass only the legacy Lesson 1
    db_session.add(
        UserCourseProgress(
            id=uuid.uuid4(),
            user_id=test_user.id,
            course_id=course.id,
            progress_percentage=0.0,
            lessons_completed=0,
        )
    )
    db_session.add(
        LessonCompletion(
            id=uuid.uuid4(),
            user_id=test_user.id,
            lesson_id=legacy_lesson.id,
            best_score=100,
            is_passed=True,
        )
    )

    # Even if an orphaned/crafted LessonAttempt exists for a draft lesson, submit & complete are forbidden
    stale_draft_attempt = LessonAttempt(
        id=uuid.uuid4(),
        user_id=test_user.id,
        lesson_id=draft_lesson.id,
        score=100.0,
        xp_earned=25,
    )
    db_session.add(stale_draft_attempt)
    await db_session.commit()

    # Course progress must be 100% (1/1 published), NOT diluted by draft_lesson
    pct = await ProgressCRUD.calculate_course_progress(db_session, str(test_user.id), str(course.id))
    assert pct == 100.0

    unit_breakdown = await ProgressCRUD.get_course_progress_detail(
        db_session, str(test_user.id), str(course.id)
    )
    assert unit_breakdown is not None
    assert unit_breakdown["course"]["total_lessons"] == 1
    assert len(unit_breakdown["units_progress"]) == 1
    assert unit_breakdown["units_progress"][0]["unit_title"] == "Unit 1 Legacy"

    ans_resp = await async_client.post(
        f"/api/v1/learning/attempts/{stale_draft_attempt.id}/answer",
        headers=auth_headers,
        json={
            "question_id": "g1",
            "question_type": "multiple_choice",
            "user_answer": "am",
            "time_spent_ms": 1200,
        },
    )
    assert ans_resp.status_code == 403

    complete_resp = await async_client.post(
        f"/api/v1/learning/attempts/{stale_draft_attempt.id}/complete",
        headers=auth_headers,
    )
    assert complete_resp.status_code == 403


@pytest.mark.asyncio
async def test_vocabulary_collection_pagination_legacy_and_stale_wod_cache_gate(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict,
) -> None:
    legacy_vocab = VocabularyItem(
        id=uuid.uuid4(),
        word="legacyword",
        definition="Legacy untagged vocabulary item.",
        translation={"vi": "từ cũ"},
        part_of_speech=PartOfSpeech.NOUN,
        difficulty_level=DifficultyLevel.A1,
        tags=None,
    )
    draft_vocab = VocabularyItem(
        id=uuid.uuid4(),
        word="draftword",
        definition="Draft vocabulary waiting review.",
        translation={"vi": "từ nháp"},
        part_of_speech=PartOfSpeech.NOUN,
        difficulty_level=DifficultyLevel.A2,
        tags={"qa_status": "NEEDS_REVIEW", "audit_status": "CONFIRMED_SOURCE"},
    )
    quarantined_vocab = VocabularyItem(
        id=uuid.uuid4(),
        word="quarantinedword",
        definition="Conflicting level item.",
        translation={"vi": "từ cách ly"},
        part_of_speech=PartOfSpeech.NOUN,
        difficulty_level=DifficultyLevel.B1,
        tags={"qa_status": "NEEDS_REVIEW", "audit_status": "CONFLICT"},
    )
    db_session.add_all([legacy_vocab, draft_vocab, quarantined_vocab])
    await db_session.commit()

    # Legacy untagged word remains discoverable via pagination while drafts/quarantined are filtered out
    page1 = await async_client.get("/api/v1/vocabulary/items?limit=10&offset=0")
    assert page1.status_code == 200
    assert [row["word"] for row in page1.json()] == ["legacyword"]

    # Adding unpublished draft or quarantined item directly to collection fails with 404
    for hidden_id in (draft_vocab.id, quarantined_vocab.id):
        add_resp = await async_client.post(
            "/api/v1/vocabulary/collection",
            headers=auth_headers,
            params={"vocabulary_id": str(hidden_id)},
        )
        assert add_resp.status_code == 404

    bulk_resp = await async_client.post(
        "/api/v1/vocabulary/collection/bulk",
        headers=auth_headers,
        json={"vocabulary_ids": [str(legacy_vocab.id), str(draft_vocab.id), str(quarantined_vocab.id)]},
    )
    assert bulk_resp.status_code == 200
    assert [row["vocabulary_id"] for row in bulk_resp.json()] == [str(legacy_vocab.id)]

    # Even if Redis returned a stale cached draft item for word-of-day, route rejects it & picks legacyword
    stale_wod_payload = {
        "id": str(draft_vocab.id),
        "word": "draftword",
        "definition": draft_vocab.definition,
        "translation": {"vi": "từ nháp"},
        "part_of_speech": "noun",
        "difficulty_level": "A2",
        "tags": ["needs_review", "confirmed_source"],
    }
    with (
        patch("app.routes.vocabulary.get_cached", new=AsyncMock(return_value=stale_wod_payload)),
        patch("app.routes.vocabulary.set_cached", new=AsyncMock()),
    ):
        wod_resp = await async_client.get(f"/api/v1/vocabulary/word-of-day?today={date.today()}")
    assert wod_resp.status_code == 200
    assert wod_resp.json()["word"] == "legacyword"
