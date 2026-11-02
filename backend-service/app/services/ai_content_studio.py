"""
AI Content Studio Service
=========================
Uses Google Gemini (gemini-2.5-flash) to generate structured lesson content
(title, vocabulary, quizzes) from a topic + source text, then persists the
result to the database under a Course → Unit → Lesson hierarchy.

Usage
-----
    from app.services.ai_content_studio import AIContentStudioService
    result = await AIContentStudioService.generate_and_save(db, request)
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any, Literal

import httpx
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.content_agent import LessonVocabularyItem
from app.models.course import Course, Lesson, Unit
from app.models.vocabulary import DifficultyLevel, PartOfSpeech, VocabularyItem

logger = logging.getLogger(__name__)


class AIContentStudioError(Exception):
    """Base exception safe for route-level error mapping."""


class AIContentConfigurationError(AIContentStudioError):
    """The server is not configured to call its AI provider."""


class AIContentProviderError(AIContentStudioError):
    """The upstream AI provider failed or returned unusable content."""


class _GeneratedVocabulary(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    word: str = Field(min_length=1, max_length=255)
    pronunciation: str | None = Field(default=None, max_length=100)
    definition: str = Field(min_length=1, max_length=500)
    translation_vi: str = Field(min_length=1, max_length=500)
    example_sentence: str = Field(min_length=1, max_length=1000)
    part_of_speech: Literal[
        "noun", "verb", "adjective", "adverb", "pronoun",
        "preposition", "conjunction", "interjection", "phrase",
    ]


class _GeneratedQuiz(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=1000)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: str = Field(min_length=1, max_length=500)
    explanation: str = Field(min_length=1, max_length=1000)

    @field_validator("options")
    @classmethod
    def validate_options(cls, options: list[str]) -> list[str]:
        cleaned = [option.strip() for option in options]
        if any(not option or len(option) > 500 for option in cleaned):
            raise ValueError("quiz options must be non-empty and at most 500 characters")
        if len({option.casefold() for option in cleaned}) != len(cleaned):
            raise ValueError("quiz options must be unique")
        return cleaned

    @model_validator(mode="after")
    def validate_correct_answer(self) -> _GeneratedQuiz:
        if self.correct_answer not in self.options:
            raise ValueError("correct_answer must exactly match one option")
        return self


class _GeneratedLesson(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    lesson_title: str = Field(min_length=1, max_length=80)
    lesson_description: str = Field(min_length=1, max_length=1000)
    learning_outcome: str = Field(min_length=1, max_length=1000)
    estimated_minutes: int = Field(ge=5, le=30)
    vocabulary: list[_GeneratedVocabulary] = Field(min_length=5, max_length=10)
    quizzes: list[_GeneratedQuiz] = Field(min_length=3, max_length=3)

# ---------------------------------------------------------------------------
# Gemini prompt template
# ---------------------------------------------------------------------------

_SYSTEM_INSTRUCTION = """\
You are an expert English language curriculum designer. Your job is to analyse
the provided source material and return a SINGLE, VALID JSON object (no markdown
fences, no extra text). Follow the schema exactly.\
"""

_PROMPT_TEMPLATE = """\
Topic: {topic}
CEFR Level: {cefr_level}

Source text:
---
{source_text}
---

Generate a complete English lesson plan based on the source text above.
Return ONLY a valid JSON object matching this exact schema:

{{
  "lesson_title": "<string – catchy, ≤ 80 chars>",
  "lesson_description": "<string – 1-2 sentences summarising the lesson>",
  "learning_outcome": "<string – CEFR can-do statement, e.g. 'You can …'>",
  "estimated_minutes": <integer 5-30>,
  "vocabulary": [
    {{
      "word": "<English word or short phrase>",
      "pronunciation": "<IPA transcription, e.g. /wɜːrd/>",
      "part_of_speech": "<one of: noun, verb, adjective, adverb, pronoun, preposition, conjunction, interjection, phrase>",
      "definition": "<clear English definition ≤ 20 words>",
      "translation_vi": "<Vietnamese translation>",
      "example_sentence": "<natural example sentence using the word>"
    }}
  ],
  "quizzes": [
    {{
      "question": "<reading-comprehension question about the source text>",
      "options": ["<A>", "<B>", "<C>", "<D>"],
      "correct_answer": "<must be one of the 4 options exactly>",
      "explanation": "<1-sentence explanation of why the answer is correct>"
    }}
  ]
}}

Rules:
- vocabulary: provide 5 to 10 items, chosen to match CEFR level {cefr_level}.
- quizzes: provide exactly 3 items; each must have 4 options and 1 correct answer.
- All strings must be valid JSON (escape double quotes, no trailing commas).
- Return raw JSON only — no markdown, no commentary.\
"""


# ---------------------------------------------------------------------------
# Helper: extract JSON from Gemini response even if it's wrapped in fences
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Parse JSON from Gemini output, stripping markdown code fences if present."""
    # Strip ```json … ``` or ``` … ``` wrappers
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Helper: normalise part_of_speech to a valid enum value
# ---------------------------------------------------------------------------

_POS_MAP = {
    "noun": PartOfSpeech.NOUN,
    "verb": PartOfSpeech.VERB,
    "adjective": PartOfSpeech.ADJECTIVE,
    "adverb": PartOfSpeech.ADVERB,
    "pronoun": PartOfSpeech.PRONOUN,
    "preposition": PartOfSpeech.PREPOSITION,
    "conjunction": PartOfSpeech.CONJUNCTION,
    "interjection": PartOfSpeech.INTERJECTION,
    "phrase": PartOfSpeech.PHRASE,
}

def _parse_pos(raw: str) -> PartOfSpeech:
    return _POS_MAP.get(raw.lower().strip(), PartOfSpeech.NOUN)


# ---------------------------------------------------------------------------
# Helper: normalise CEFR level to DifficultyLevel enum
# ---------------------------------------------------------------------------

_CEFR_MAP = {
    "A1": DifficultyLevel.A1,
    "A2": DifficultyLevel.A2,
    "B1": DifficultyLevel.B1,
    "B2": DifficultyLevel.B2,
    "C1": DifficultyLevel.C1,
    "C2": DifficultyLevel.C2,
}

def _parse_cefr(raw: str) -> DifficultyLevel:
    return _CEFR_MAP.get(raw.upper().strip(), DifficultyLevel.A1)


# ---------------------------------------------------------------------------
# Build quiz exercises in the Lesson.content format
# ---------------------------------------------------------------------------

def _build_quiz_exercises(quizzes: list[dict]) -> list[dict]:
    """
    Convert Gemini quiz items to the LexiLingo exercise schema accepted by
    the learner endpoint (type=multiple_choice, ui_type=reading_comprehension).
    """
    exercises = []
    for quiz in quizzes:
        options = quiz.get("options", [])
        correct = quiz.get("correct_answer", "")
        exercises.append({
            "type": "multiple_choice",
            "ui_type": "reading_comprehension",
            "question": quiz.get("question", ""),
            "options": [{"text": opt, "is_correct": opt == correct} for opt in options],
            "correct_answer": correct,
            "explanation": quiz.get("explanation", ""),
        })
    return exercises


# ---------------------------------------------------------------------------
# Main service class
# ---------------------------------------------------------------------------

class AIContentStudioService:
    """Orchestrates Gemini generation + DB persistence for lesson content."""

    @staticmethod
    async def generate_lesson_content(
        topic: str,
        cefr_level: str,
        source_text: str,
    ) -> dict[str, Any]:
        """
        Call Gemini 2.5 Flash to generate structured lesson content.

        Returns the parsed JSON dict from Gemini.
        Raises a typed AIContentStudioError on configuration/provider errors.
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key or api_key.startswith("your-gemini"):
            raise AIContentConfigurationError("AI Content Studio is not configured")

        prompt = _PROMPT_TEMPLATE.format(
            topic=topic,
            cefr_level=cefr_level.upper(),
            source_text=source_text[:8000],  # guard against very long inputs
        )

        model = settings.GEMINI_MODEL.strip() or "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        request_body = {
            "systemInstruction": {"parts": [{"text": _SYSTEM_INSTRUCTION}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 4096,
                "responseMimeType": "application/json",
            },
        }

        logger.info("Calling Gemini model=%s for topic=%r level=%s", model, topic, cefr_level)
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(settings.AI_CONTENT_STUDIO_TIMEOUT_SECONDS)
            ) as client:
                response = await client.post(
                    url,
                    headers={"x-goog-api-key": api_key},
                    json=request_body,
                )
                response.raise_for_status()
                payload = response.json()
            raw_text = payload["candidates"][0]["content"]["parts"][0]["text"]
            if not isinstance(raw_text, str) or not raw_text.strip():
                raise KeyError("empty provider response")
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            logger.warning("Gemini request failed: %s", type(exc).__name__)
            raise AIContentProviderError("AI provider is temporarily unavailable") from exc
        except httpx.HTTPStatusError as exc:
            logger.warning("Gemini returned HTTP %s", exc.response.status_code)
            raise AIContentProviderError("AI provider rejected the generation request") from exc
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Gemini returned an unexpected response envelope")
            raise AIContentProviderError("AI provider returned an invalid response") from exc

        try:
            data = _extract_json(raw_text)
            return _GeneratedLesson.model_validate(data).model_dump()
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            logger.warning("Gemini lesson payload failed schema validation: %s", exc)
            raise AIContentProviderError("AI provider returned invalid lesson content") from exc

    # ------------------------------------------------------------------ #

    @staticmethod
    async def _get_or_create_course(
        db: AsyncSession,
        topic: str,
        cefr_level: str,
    ) -> Course:
        """
        Find an existing AI-generated course for this level, or create one.
        Course titles follow the pattern: 'AI Generated – {level}'.
        """
        ai_course_title = f"AI Generated – {cefr_level.upper()}"
        result = await db.execute(
            select(Course).where(
                Course.title == ai_course_title,
                Course.level == cefr_level.upper(),
            ).limit(1)
        )
        course = result.scalar_one_or_none()
        if course:
            return course

        course = Course(
            id=uuid.uuid4(),
            title=ai_course_title,
            description=(
                f"Auto-generated course for CEFR level {cefr_level.upper()} "
                "by AI Content Studio."
            ),
            language="en",
            level=cefr_level.upper(),
            tags=["ai-generated"],
            is_published=False,
        )
        db.add(course)
        await db.flush()  # get the PK before adding children
        return course

    @staticmethod
    async def _get_or_create_unit(
        db: AsyncSession,
        course: Course,
        topic: str,
    ) -> Unit:
        """
        Create a new unit per topic inside the course.
        """
        # Count existing units to assign order_index
        result = await db.execute(
            select(func.count()).where(Unit.course_id == course.id)
        )
        unit_count = result.scalar_one()

        unit = Unit(
            id=uuid.uuid4(),
            course_id=course.id,
            title=topic[:255],
            description=f"Unit auto-generated for topic: {topic}",
            order_index=unit_count + 1,
        )
        db.add(unit)
        await db.flush()
        return unit

    @staticmethod
    async def _create_lesson(
        db: AsyncSession,
        course: Course,
        unit: Unit,
        gemini_data: dict,
    ) -> Lesson:
        """
        Persist the Lesson with quiz exercises embedded in content JSON.
        """
        quizzes = gemini_data.get("quizzes", [])
        exercises = _build_quiz_exercises(quizzes)

        result = await db.execute(
            select(func.count()).where(Lesson.unit_id == unit.id)
        )
        lesson_count = result.scalar_one()

        lesson = Lesson(
            id=uuid.uuid4(),
            course_id=course.id,
            unit_id=unit.id,
            title=gemini_data.get("lesson_title", "AI Generated Lesson")[:255],
            description=gemini_data.get("lesson_description", ""),
            outcome=gemini_data.get("learning_outcome", ""),
            order_index=lesson_count + 1,
            estimated_minutes=int(gemini_data.get("estimated_minutes", 10)),
            xp_reward=15,
            lesson_type="lesson",
            content={"exercises": exercises},
        )
        db.add(lesson)
        # Keep the denormalized catalog counters consistent with the regular
        # course CRUD path so generated drafts render correctly in Admin/App.
        unit.total_lessons = (unit.total_lessons or 0) + 1
        course.total_lessons = (course.total_lessons or 0) + 1
        course.total_xp = (course.total_xp or 0) + lesson.xp_reward
        course.estimated_duration = (
            (course.estimated_duration or 0) + lesson.estimated_minutes
        )
        course.content_version = (course.content_version or 0) + 1
        await db.flush()
        return lesson

    @staticmethod
    async def _save_vocabulary(
        db: AsyncSession,
        course: Course,
        lesson: Lesson,
        vocab_items: list[dict],
        cefr_level: str,
    ) -> list[VocabularyItem]:
        """
        Reuse master vocabulary rows and always attach them to this lesson.
        The master table is unique by word + part of speech, while
        LessonVocabularyItem preserves membership across multiple lessons.
        """
        saved = []
        difficulty = _parse_cefr(cefr_level)

        for order_index, item in enumerate(vocab_items):
            word = (item.get("word") or "").strip()[:255]
            if not word:
                continue

            # Reuse duplicate word+part-of-speech rows from the master catalog.
            pos = _parse_pos(item.get("part_of_speech", "noun"))
            existing = await db.execute(
                select(VocabularyItem).where(
                    VocabularyItem.word == word,
                    VocabularyItem.part_of_speech == pos,
                ).limit(1)
            )
            vocab = existing.scalar_one_or_none()
            if vocab is None:
                vocab = VocabularyItem(
                    id=uuid.uuid4(),
                    word=word,
                    definition=item.get("definition", "")[:500],
                    pronunciation=item.get("pronunciation", "")[:100] or None,
                    part_of_speech=pos,
                    difficulty_level=difficulty,
                    course_id=course.id,
                    lesson_id=lesson.id,
                    translation={
                        "vi": item.get("translation_vi", ""),
                        "examples": [item.get("example_sentence", "")],
                    },
                    tags=["ai-generated"],
                )
                db.add(vocab)
                saved.append(vocab)

            db.add(
                LessonVocabularyItem(
                    lesson_id=lesson.id,
                    vocabulary_id=vocab.id,
                    order_index=order_index,
                    is_primary=True,
                )
            )

        return saved

    # ------------------------------------------------------------------ #

    @classmethod
    async def generate_and_save(
        cls,
        db: AsyncSession,
        topic: str,
        cefr_level: str,
        source_text: str,
    ) -> dict[str, Any]:
        """
        Full pipeline:
          1. Call Gemini to generate content.
          2. Persist Course / Unit / Lesson / VocabularyItems.
          3. Commit and return a summary dict.

        Raises ValueError on configuration or Gemini errors.
        """
        # Step 1: Generate
        gemini_data = await cls.generate_lesson_content(topic, cefr_level, source_text)

        # Step 2: Persist atomically. Roll back explicitly because this service
        # can be called outside FastAPI's session dependency in scripts/tests.
        try:
            course = await cls._get_or_create_course(db, topic, cefr_level)
            unit = await cls._get_or_create_unit(db, course, topic)
            lesson = await cls._create_lesson(db, course, unit, gemini_data)

            vocab_items = gemini_data.get("vocabulary", [])
            saved_vocab = await cls._save_vocabulary(db, course, lesson, vocab_items, cefr_level)

            await db.commit()
            await db.refresh(lesson)
        except Exception:
            await db.rollback()
            raise

        logger.info(
            "AI Content Studio: saved lesson %s in course %s (unit %s), "
            "%d vocab items.",
            lesson.id, course.id, unit.id, len(saved_vocab),
        )

        # Step 3: Build response summary
        return {
            "course": {
                "id": str(course.id),
                "title": course.title,
                "level": course.level,
            },
            "unit": {
                "id": str(unit.id),
                "title": unit.title,
                "order_index": unit.order_index,
            },
            "lesson": {
                "id": str(lesson.id),
                "title": lesson.title,
                "description": lesson.description,
                "outcome": lesson.outcome,
                "estimated_minutes": lesson.estimated_minutes,
                "total_exercises": lesson.total_exercises,
                "xp_reward": lesson.xp_reward,
            },
            "vocabulary_saved": len(saved_vocab),
            "vocabulary": [
                {
                    "word": v.word,
                    "pronunciation": v.pronunciation,
                    "definition": v.definition,
                    "translation_vi": (v.translation or {}).get("vi", ""),
                    "example": ((v.translation or {}).get("examples") or [""])[0],
                    "part_of_speech": v.part_of_speech,
                }
                for v in saved_vocab
            ],
            "quizzes": gemini_data.get("quizzes", []),
        }
