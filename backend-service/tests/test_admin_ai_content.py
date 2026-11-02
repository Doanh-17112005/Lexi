"""Security and contract tests for the Admin AI Content Studio."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.routing import APIRoute

from app.core.dependencies import get_current_admin
from app.models.content_agent import LessonVocabularyItem
from app.routes import admin_ai_content
from app.services.ai_content_studio import (
    AIContentConfigurationError,
    AIContentProviderError,
    AIContentStudioService,
)


def _valid_payload() -> dict:
    vocabulary = [
        {
            "word": f"word-{index}",
            "pronunciation": f"/word{index}/",
            "definition": "A useful word for this lesson.",
            "translation_vi": "từ hữu ích",
            "example_sentence": f"This example uses word {index}.",
            "part_of_speech": "noun",
        }
        for index in range(5)
    ]
    quizzes = [
        {
            "question": f"Question {index}?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": "A is supported by the source.",
        }
        for index in range(3)
    ]
    return {
        "lesson_title": "A safe generated lesson",
        "lesson_description": "A concise description.",
        "learning_outcome": "You can discuss the lesson topic.",
        "estimated_minutes": 15,
        "vocabulary": vocabulary,
        "quizzes": quizzes,
    }


def _dependency_calls(route: APIRoute) -> set:
    calls = set()
    pending = list(route.dependant.dependencies)
    while pending:
        dependency = pending.pop()
        if dependency.call is not None:
            calls.add(dependency.call)
        pending.extend(dependency.dependencies)
    return calls


def test_generate_route_requires_admin():
    routes = [route for route in admin_ai_content.router.routes if isinstance(route, APIRoute)]
    assert len(routes) == 1
    assert get_current_admin in _dependency_calls(routes[0])


@pytest.mark.asyncio
async def test_generation_fails_closed_without_api_key(monkeypatch):
    monkeypatch.setattr("app.services.ai_content_studio.settings.GEMINI_API_KEY", None)

    with pytest.raises(AIContentConfigurationError):
        await AIContentStudioService.generate_lesson_content("Travel", "B1", "x" * 80)


@pytest.mark.asyncio
async def test_generation_uses_header_and_validates_provider_payload(monkeypatch):
    monkeypatch.setattr("app.services.ai_content_studio.settings.GEMINI_API_KEY", "test-secret")
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": __import__("json").dumps(_valid_payload())}]}}]
    }
    http = AsyncMock()
    http.post = AsyncMock(return_value=response)

    with patch("app.services.ai_content_studio.httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__ = AsyncMock(return_value=http)
        client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await AIContentStudioService.generate_lesson_content(
            "Travel", "B1", "A sufficiently long source passage about travelling safely."
        )

    assert result["lesson_title"] == "A safe generated lesson"
    request = http.post.call_args
    assert "test-secret" not in request.args[0]
    assert request.kwargs["headers"] == {"x-goog-api-key": "test-secret"}


@pytest.mark.asyncio
async def test_generation_rejects_invalid_quiz_answer(monkeypatch):
    monkeypatch.setattr("app.services.ai_content_studio.settings.GEMINI_API_KEY", "test-secret")
    payload = _valid_payload()
    payload["quizzes"][0]["correct_answer"] = "not-an-option"
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": __import__("json").dumps(payload)}]}}]
    }
    http = AsyncMock()
    http.post = AsyncMock(return_value=response)

    with patch("app.services.ai_content_studio.httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__ = AsyncMock(return_value=http)
        client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        with pytest.raises(AIContentProviderError):
            await AIContentStudioService.generate_lesson_content(
                "Travel", "B1", "A sufficiently long source passage about travelling safely."
            )


@pytest.mark.asyncio
async def test_persistence_rolls_back_on_failure(monkeypatch):
    db = AsyncMock()
    monkeypatch.setattr(
        AIContentStudioService,
        "generate_lesson_content",
        AsyncMock(return_value=_valid_payload()),
    )
    monkeypatch.setattr(
        AIContentStudioService,
        "_get_or_create_course",
        AsyncMock(return_value=SimpleNamespace(id="course")),
    )
    monkeypatch.setattr(
        AIContentStudioService,
        "_get_or_create_unit",
        AsyncMock(return_value=SimpleNamespace(id="unit")),
    )
    monkeypatch.setattr(
        AIContentStudioService,
        "_create_lesson",
        AsyncMock(side_effect=RuntimeError("database failure")),
    )

    with pytest.raises(RuntimeError, match="database failure"):
        await AIContentStudioService.generate_and_save(db, "Travel", "B1", "x" * 80)

    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_lesson_updates_denormalized_catalog_counters():
    db = MagicMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    count_result = MagicMock()
    count_result.scalar_one.return_value = 0
    db.execute.return_value = count_result
    course = SimpleNamespace(
        id="course",
        total_lessons=2,
        total_xp=20,
        estimated_duration=30,
        content_version=4,
    )
    unit = SimpleNamespace(id="unit", total_lessons=2)

    lesson = await AIContentStudioService._create_lesson(
        db,
        course,
        unit,
        _valid_payload(),
    )

    assert lesson.total_exercises == 3
    assert unit.total_lessons == 3
    assert course.total_lessons == 3
    assert course.total_xp == 35
    assert course.estimated_duration == 45
    assert course.content_version == 5
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_existing_vocabulary_is_linked_to_generated_lesson():
    db = MagicMock()
    db.execute = AsyncMock()
    existing = SimpleNamespace(id="existing-vocabulary")
    query_result = MagicMock()
    query_result.scalar_one_or_none.return_value = existing
    db.execute.return_value = query_result

    saved = await AIContentStudioService._save_vocabulary(
        db,
        SimpleNamespace(id="course"),
        SimpleNamespace(id="lesson"),
        [_valid_payload()["vocabulary"][0]],
        "B1",
    )

    assert saved == []
    memberships = [
        call.args[0]
        for call in db.add.call_args_list
        if isinstance(call.args[0], LessonVocabularyItem)
    ]
    assert len(memberships) == 1
    assert memberships[0].lesson_id == "lesson"
    assert memberships[0].vocabulary_id == "existing-vocabulary"
