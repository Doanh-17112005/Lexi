"""Public Guest Trial Pack & Public Course Preview routes (T19-T22).

Provides unauthenticated learner-safe trial content without creating user
accounts, bypassing RBAC, or leaking quiz answers in the manifest payload.
"""

import hashlib
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.course import Course
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/guest", tags=["Guest Trial"])

TRIAL_MANIFEST_VERSION = "2026.1.0"


def _answer_digest(question_id: str, expected_text: str) -> str:
    normalized = f"{question_id}:{expected_text.strip().lower()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


_GUEST_VOCABULARY = [
    {
        "id": "guest-vocab-1",
        "word": "commute",
        "phonetic": "/kəˈmjuːt/",
        "part_of_speech": "verb",
        "meaning": "To travel regularly between home and work or school.",
        "cefr_level": "A2",
        "topic": "work",
        "example": "I commute by train every morning.",
    },
    {
        "id": "guest-vocab-2",
        "word": "schedule",
        "phonetic": "/ˈskedʒuːl/",
        "part_of_speech": "noun",
        "meaning": "A plan of activities and when they will happen.",
        "cefr_level": "A2",
        "topic": "daily_life",
        "example": "Let me check my schedule for tomorrow.",
    },
    {
        "id": "guest-vocab-3",
        "word": "confirm",
        "phonetic": "/kənˈfɜːrm/",
        "part_of_speech": "verb",
        "meaning": "To state or show that something is definitely true or arranged.",
        "cefr_level": "A2",
        "topic": "communication",
        "example": "Please confirm your reservation before Friday.",
    },
    {
        "id": "guest-vocab-4",
        "word": "neighborhood",
        "phonetic": "/ˈneɪbərhʊd/",
        "part_of_speech": "noun",
        "meaning": "The area of a town or city around where someone lives.",
        "cefr_level": "A2",
        "topic": "community",
        "example": "There is a quiet park in my neighborhood.",
    },
    {
        "id": "guest-vocab-5",
        "word": "prepare",
        "phonetic": "/prɪˈper/",
        "part_of_speech": "verb",
        "meaning": "To get ready for an event or task.",
        "cefr_level": "A1",
        "topic": "daily_life",
        "example": "She prepares breakfast at seven.",
    },
    {
        "id": "guest-vocab-6",
        "word": "polite",
        "phonetic": "/pəˈlaɪt/",
        "part_of_speech": "adjective",
        "meaning": "Behaving in a respectful and considerate way.",
        "cefr_level": "A2",
        "topic": "communication",
        "example": "Using 'could you' is a polite way to ask.",
    },
]

_GUEST_GRAMMAR_THEORY = {
    "id": "guest-grammar-1",
    "version": TRIAL_MANIFEST_VERSION,
    "title": "Present Simple for Routines & Prepositions (at / on / in)",
    "level": "A1",
    "topic": "tenses_and_time",
    "summary": "Express daily habits cleanly and pair them with accurate time prepositions.",
    "explanation": (
        "Use the base verb with I/you/we/they and add -s/-es with he/she/it for daily routines. "
        "Pair clock times with 'at' (at 8:00), days with 'on' (on Monday), and months/parts of the day with 'in' (in the morning)."
    ),
    "grammar_points": [
        "Subject (he/she/it) + Verb-s/-es: 'She commutes by bus.'",
        "Time prepositions: at + clock time, on + day, in + morning/month.",
    ],
    "examples": [
        {
            "sentence": "She prepares breakfast at 7:00 every morning.",
            "translation": "Cô ấy chuẩn bị bữa sáng lúc 7 giờ mỗi sáng.",
        },
        {
            "sentence": "Our team meets on Monday to confirm the schedule.",
            "translation": "Nhóm của chúng tôi họp vào thứ Hai để xác nhận lịch trình.",
        },
    ],
}

_GUEST_QUESTIONS_BANK = [
    {
        "id": "gq-1",
        "skill": "grammar",
        "topic": "present_simple",
        "prompt": "She ___ to work by train every morning.",
        "options": ["commute", "commutes", "commuting", "commuted"],
        "correct_option": "commutes",
        "explanation": "Third-person singular subjects ('She') take -s in the Present Simple.",
    },
    {
        "id": "gq-2",
        "skill": "grammar",
        "topic": "time_prepositions",
        "prompt": "The English club meets ___ Friday evening.",
        "options": ["in", "at", "on", "to"],
        "correct_option": "on",
        "explanation": "Use 'on' before specific days such as Friday or Monday morning.",
    },
    {
        "id": "gq-3",
        "skill": "vocabulary",
        "topic": "daily_life",
        "prompt": "Before buying train tickets, please ___ the departure time.",
        "options": ["confirm", "neighborhood", "polite", "ignore"],
        "correct_option": "confirm",
        "explanation": "'Confirm' means to check and make sure an arrangement is definite.",
    },
    {
        "id": "gq-4",
        "skill": "vocabulary",
        "topic": "communication",
        "prompt": "Saying 'Could you help me, please?' sounds ___.",
        "options": ["polite", "schedule", "ancient", "rare"],
        "correct_option": "polite",
        "explanation": "'Polite' describes respectful and considerate language.",
    },
]


class GuestAnswerItem(BaseModel):
    question_id: str = Field(..., min_length=1, max_length=64)
    selected_option: str = Field(..., max_length=256)


class GuestGradeRequest(BaseModel):
    answers: List[GuestAnswerItem] = Field(default_factory=list, max_length=20)


@router.get("/trial-pack", response_model=ApiResponse[dict])
async def get_guest_trial_pack():
    """Return the public, versioned guest trial pack manifest without leaking answers."""
    sanitized_questions = [
        {
            "id": q["id"],
            "skill": q["skill"],
            "topic": q["topic"],
            "prompt": q["prompt"],
            "options": list(q["options"]),
            "answer_digest": _answer_digest(q["id"], q["correct_option"]),
        }
        for q in _GUEST_QUESTIONS_BANK
    ]
    return ApiResponse(
        success=True,
        message="Guest trial pack retrieved",
        data={
            "manifest_version": TRIAL_MANIFEST_VERSION,
            "policy": {
                "requires_auth": False,
                "creates_user": False,
                "offline_capable": True,
                "premium_included": False,
                "gated_features": ["leaderboard", "social", "ai_chat", "premium"],
            },
            "vocabulary_items": _GUEST_VOCABULARY,
            "grammar_theory": _GUEST_GRAMMAR_THEORY,
            "quiz_questions": sanitized_questions,
            "total_items": len(_GUEST_VOCABULARY) + len(sanitized_questions),
        },
    )


@router.post("/trial-pack/grade", response_model=ApiResponse[dict])
async def grade_guest_trial_pack(payload: GuestGradeRequest):
    """Evaluate submitted guest trial quiz answers without mutating user DB state."""
    bank = {q["id"]: q for q in _GUEST_QUESTIONS_BANK}
    submitted_map = {
        a.question_id: a.selected_option.strip() for a in payload.answers
    }
    results = []
    correct_count = 0
    for q in _GUEST_QUESTIONS_BANK:
        selected = submitted_map.get(q["id"], "")
        is_correct = selected.lower() == q["correct_option"].strip().lower()
        if is_correct:
            correct_count += 1
        results.append(
            {
                "question_id": q["id"],
                "selected_option": selected,
                "correct_option": q["correct_option"],
                "is_correct": is_correct,
                "explanation": q["explanation"],
            }
        )

    total = len(_GUEST_QUESTIONS_BANK)
    score_pct = round((correct_count / total) * 100, 1) if total else 0.0
    return ApiResponse(
        success=True,
        message="Guest trial graded",
        data={
            "manifest_version": TRIAL_MANIFEST_VERSION,
            "correct_count": correct_count,
            "total_questions": total,
            "score_percentage": score_pct,
            "results": results,
        },
    )


@router.get("/courses", response_model=ApiResponse[list[dict]])
async def list_public_guest_courses(
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Return non-sensitive metadata for published courses so guests can preview catalog."""
    res = await db.execute(
        select(Course)
        .where(Course.is_published == True)
        .order_by(Course.level.asc(), Course.title.asc())
        .limit(limit)
    )
    courses = res.scalars().all()
    items = [
        {
            "id": str(c.id),
            "title": c.title,
            "description": c.description,
            "language": c.language,
            "level": c.level,
            "skill": c.skill,
            "total_lessons": c.total_lessons,
            "estimated_duration": c.estimated_duration,
            "thumbnail_url": c.thumbnail_url,
        }
        for c in courses
    ]
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(items)} public courses",
        data=items,
    )
