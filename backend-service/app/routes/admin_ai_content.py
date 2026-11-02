"""
Admin – AI Content Studio Routes
=================================
POST /api/v1/admin/ai-content/generate-lesson

Generates a structured lesson (title, vocabulary, quizzes) from a topic and
optional source text using Google Gemini, and saves it automatically to the
database (Course → Unit → Lesson + VocabularyItems).
"""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
from app.services.ai_content_studio import (
    AIContentConfigurationError,
    AIContentProviderError,
    AIContentStudioService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/ai-content", tags=["AI Content Studio"])

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

CEFR_LEVELS = Literal["A1", "A2", "B1", "B2", "C1", "C2"]


class GenerateLessonRequest(BaseModel):
    """Request body for POST /admin/ai-content/generate-lesson."""

    topic: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Lesson topic or title, e.g. 'Job interviews', 'The environment'.",
        examples=["Job interviews in the modern workplace"],
    )
    cefr_level: str = Field(
        ...,
        description="CEFR level for the generated content (A1–C2).",
        examples=["B2"],
    )
    source_text: str = Field(
        ...,
        min_length=50,
        max_length=8000,
        description=(
            "Raw text or article excerpt that Gemini will analyse to extract "
            "vocabulary and generate reading-comprehension quizzes."
        ),
        examples=[
            "Job interviews can be nerve-wracking experiences. Whether you are "
            "applying for your first job or switching careers, preparation is key..."
        ],
    )

    @field_validator("cefr_level")
    @classmethod
    def validate_cefr(cls, value: str) -> str:
        normalized = value.upper().strip()
        valid = {"A1", "A2", "B1", "B2", "C1", "C2"}
        if normalized not in valid:
            raise ValueError(f"cefr_level must be one of {sorted(valid)}, got {value!r}")
        return normalized


class VocabularyItemOut(BaseModel):
    word: str
    pronunciation: str | None
    definition: str
    translation_vi: str
    example: str
    part_of_speech: str


class QuizOut(BaseModel):
    question: str
    options: list[str]
    correct_answer: str
    explanation: str


class CourseRef(BaseModel):
    id: str
    title: str
    level: str


class UnitRef(BaseModel):
    id: str
    title: str
    order_index: int


class LessonRef(BaseModel):
    id: str
    title: str
    description: str
    outcome: str
    estimated_minutes: int
    total_exercises: int
    xp_reward: int


class GenerateLessonResponse(BaseModel):
    success: bool = True
    message: str
    course: CourseRef
    unit: UnitRef
    lesson: LessonRef
    vocabulary_saved: int
    vocabulary: list[VocabularyItemOut]
    quizzes: list[QuizOut]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/generate-lesson",
    response_model=GenerateLessonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a lesson with AI",
    description=(
        "Uses Google Gemini (gemini-2.5-flash) to analyse the provided source "
        "text and generate a complete lesson including vocabulary items and "
        "reading-comprehension quizzes. The result is automatically saved to "
        "the database under a Course → Unit → Lesson hierarchy."
    ),
)
async def generate_lesson(
    payload: GenerateLessonRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> GenerateLessonResponse:
    """
    **AI Content Studio** – generate and persist a lesson from raw text.

    - Requires admin JWT.
    - Returns the persisted lesson, vocabulary, and quizzes.
    - The lesson is saved as **unpublished**; publish the parent course manually.
    """
    logger.info(
        "Admin %s requested AI lesson generation: topic=%r level=%s",
        current_admin.email,
        payload.topic,
        payload.cefr_level,
    )

    try:
        result = await AIContentStudioService.generate_and_save(
            db=db,
            topic=payload.topic,
            cefr_level=payload.cefr_level,
            source_text=payload.source_text,
        )
    except AIContentConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AIContentProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("AI Content Studio unexpected error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating lesson content. "
                   "Check server logs for details.",
        ) from exc

    return GenerateLessonResponse(
        message=(
            f"Lesson '{result['lesson']['title']}' generated successfully "
            f"and saved to the database."
        ),
        course=CourseRef(**result["course"]),
        unit=UnitRef(**result["unit"]),
        lesson=LessonRef(**result["lesson"]),
        vocabulary_saved=result["vocabulary_saved"],
        vocabulary=[VocabularyItemOut(**v) for v in result["vocabulary"]],
        quizzes=[QuizOut(**q) for q in result["quizzes"]],
    )
