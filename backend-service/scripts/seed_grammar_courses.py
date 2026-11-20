"""Idempotent upsert script for CEFR A1-C2 GrammarItems, Grammar Lessons, and QuestionBank.

Safety guarantees:
- Defaults to --target test (refuses any DB name not ending in '_test') and --dry-run.
- Writing to local primary DB requires explicit `--target local --apply`.
- Never deletes users, progress, completions, wallets, or existing Lesson 1 rows.
- Never logs database credentials or secrets.

Usage:
    cd backend-service
    venv/Scripts/python.exe -m scripts.seed_grammar_courses --target test --apply
    venv/Scripts/python.exe -m scripts.seed_grammar_courses --target local --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, or_, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.cefr_vocabulary_data import PROVENANCE_AI_GENERATED, QA_STATUS_NEEDS_REVIEW
from app.core.config import settings
from app.core.database import Base
from app.core.grammar_course_data import (
    BASE_CEFR_COURSES,
    GRAMMAR_UNITS_AND_LESSONS,
    build_lesson_content_payload,
    deterministic_uuid,
    validate_grammar_course_catalog,
)
from app.models.content import GrammarItem, QuestionItem
from app.models.course import Course, Lesson, Unit
from app.models.course_category import CourseCategory
from app.services.content_publication_policy import is_lesson_learner_visible


def _resolve_target_url(target: str) -> str:
    if target == "test":
        env_test = os.getenv("TEST_DATABASE_URL")
        if env_test:
            url = make_url(env_test)
        else:
            base = make_url(settings.DATABASE_URL)
            url = base.set(database="lexilingo_test")
        if not (url.database or "").endswith("_test"):
            raise RuntimeError(
                f"Refusing test seed on non-test database '{url.database}'"
            )
        return url.render_as_string(hide_password=False)

    if target == "local":
        return settings.DATABASE_URL

    raise ValueError(f"Unsupported target: {target}")


async def _ensure_general_category(db: AsyncSession) -> CourseCategory:
    existing = await db.scalar(
        select(CourseCategory).where(
            or_(
                CourseCategory.slug == "general_english",
                CourseCategory.name == "General English CEFR",
            )
        )
    )
    if existing:
        return existing

    category = CourseCategory(
        id=deterministic_uuid("category:general_english"),
        name="General English CEFR",
        slug="general_english",
        description="Structured CEFR A1-C2 English learning path",
        icon="📘",
        color="#2563EB",
        order_index=1,
        is_active=True,
    )
    db.add(category)
    await db.flush()
    return category


async def _ensure_base_course(
    db: AsyncSession,
    level: str,
    category_id,
    stats: dict[str, dict[str, int]],
) -> tuple[Course, bool]:
    spec = next(item for item in BASE_CEFR_COURSES if item["level"] == level)
    course = await db.scalar(
        select(Course).where(
            Course.level == level,
            Course.title == spec["title"],
        )
    )
    if course is None:
        course = await db.scalar(
            select(Course)
            .where(
                Course.level == level,
                Course.is_published == True,  # noqa: E712
                Course.title.ilike(f"{level} - %"),
            )
            .order_by(Course.created_at.asc())
        )

    course_created = False
    if course is None:
        course = Course(
            id=deterministic_uuid(f"course:{level.lower()}"),
            title=spec["title"],
            description=spec["description"],
            language=spec["language"],
            level=level,
            category_id=category_id,
            tags=list(spec["tags"]),
            total_xp=50,
            estimated_duration=spec["estimated_duration"],
            total_lessons=1,
            is_published=True,
        )
        db.add(course)
        await db.flush()
        stats["courses"]["created"] += 1
        course_created = True

    # Ensure Unit 1 + Lesson 1 exists when seeding an empty test database,
    # without modifying existing Unit 1 / Lesson 1 rows in live databases.
    existing_units_count = await db.scalar(
        select(func.count(Unit.id)).where(Unit.course_id == course.id)
    )
    if (existing_units_count or 0) == 0:
        unit1 = Unit(
            id=deterministic_uuid(f"unit1:{level.lower()}"),
            course_id=course.id,
            title=spec["unit1_title"],
            description=spec["unit1_description"],
            order_index=1,
            total_lessons=1,
        )
        db.add(unit1)
        await db.flush()
        stats["units"]["created"] += 1

        lesson1 = Lesson(
            id=deterministic_uuid(f"lesson1:{level.lower()}"),
            course_id=course.id,
            unit_id=unit1.id,
            title=spec["lesson1_title"],
            description=spec["lesson1_description"],
            outcome=spec["lesson1_outcome"],
            order_index=1,
            pass_threshold=75,
            estimated_minutes=10,
            xp_reward=50,
            lesson_type="lesson",
            content={
                "version": 1,
                "cefr_level": level,
                "exercises": copy.deepcopy(spec["lesson1_exercises"]),
            },
        )
        db.add(lesson1)
        await db.flush()
        stats["lessons"]["created"] += 1

    return course, course_created


async def upsert_grammar_and_courses(
    db: AsyncSession,
    *,
    ensure_base_courses: bool = True,
) -> dict[str, Any]:
    """Idempotently upsert A1-C2 GrammarItems, Grammar Units/Lessons, and QuestionItems."""
    validate_grammar_course_catalog()

    stats: dict[str, dict[str, int]] = {
        "courses": {"created": 0, "updated": 0, "unchanged": 0},
        "units": {"created": 0, "updated": 0, "unchanged": 0},
        "grammar_items": {"created": 0, "updated": 0, "unchanged": 0},
        "lessons": {"created": 0, "updated": 0, "unchanged": 0},
        "question_bank": {"created": 0, "updated": 0, "unchanged": 0},
    }

    category = await _ensure_general_category(db) if ensure_base_courses else None

    for unit_spec in GRAMMAR_UNITS_AND_LESSONS:
        level = unit_spec["level"]
        if ensure_base_courses:
            course, course_created = await _ensure_base_course(db, level, category.id, stats)
        else:
            course = await db.scalar(
                select(Course)
                .where(Course.level == level, Course.is_published == True)  # noqa: E712
                .order_by(Course.created_at.asc())
            )
            if course is None:
                raise RuntimeError(f"Missing published course for CEFR level {level}")
            course_created = False

        # Upsert Unit 2 (Grammar Unit)
        unit_id = deterministic_uuid(unit_spec["unit_slug"])
        unit = await db.scalar(
            select(Unit).where(
                Unit.course_id == course.id,
                or_(
                    Unit.id == unit_id,
                    Unit.title == unit_spec["unit_title"],
                ),
            )
        )
        if unit is None:
            unit = Unit(
                id=unit_id,
                course_id=course.id,
                title=unit_spec["unit_title"],
                description=unit_spec["unit_description"],
                order_index=unit_spec["unit_order_index"],
                background_color=unit_spec["background_color"],
                total_lessons=len(unit_spec["lessons"]),
            )
            db.add(unit)
            await db.flush()
            stats["units"]["created"] += 1
        else:
            changed = False
            for field, value in (
                ("title", unit_spec["unit_title"]),
                ("description", unit_spec["unit_description"]),
                ("order_index", unit_spec["unit_order_index"]),
                ("background_color", unit_spec["background_color"]),
                ("total_lessons", len(unit_spec["lessons"])),
            ):
                if getattr(unit, field) != value:
                    setattr(unit, field, value)
                    changed = True
            stats["units"]["updated" if changed else "unchanged"] += 1

        for lesson_spec in unit_spec["lessons"]:
            g_spec = lesson_spec["grammar"]
            g_id = deterministic_uuid(g_spec["slug"])
            g_tags = [
                "grammar",
                level.lower(),
                g_spec["topic"],
                f"provenance:{PROVENANCE_AI_GENERATED.lower()}",
                f"qa_status:{QA_STATUS_NEEDS_REVIEW.lower()}",
            ]

            grammar_item = await db.scalar(
                select(GrammarItem).where(
                    or_(
                        GrammarItem.id == g_id,
                        (GrammarItem.title == g_spec["title"]) & (GrammarItem.level == level),
                    )
                )
            )
            if grammar_item is None:
                grammar_item = GrammarItem(
                    id=g_id,
                    title=g_spec["title"],
                    level=level,
                    topic=g_spec["topic"],
                    summary=g_spec["summary"],
                    content=g_spec["content"],
                    examples=copy.deepcopy(g_spec["examples"]),
                    tags=g_tags,
                    is_active=False,
                )
                db.add(grammar_item)
                await db.flush()
                stats["grammar_items"]["created"] += 1
            else:
                changed = False
                for field, value in (
                    ("title", g_spec["title"]),
                    ("level", level),
                    ("topic", g_spec["topic"]),
                    ("summary", g_spec["summary"]),
                    ("content", g_spec["content"]),
                    ("examples", copy.deepcopy(g_spec["examples"])),
                    ("tags", g_tags),
                    ("is_active", False),
                ):
                    if getattr(grammar_item, field) != value:
                        setattr(grammar_item, field, value)
                        changed = True
                stats["grammar_items"]["updated" if changed else "unchanged"] += 1

            # Upsert Grammar Lesson
            l_id = deterministic_uuid(lesson_spec["slug"])
            lesson_payload = build_lesson_content_payload(
                lesson_spec,
                level=level,
                grammar_item_id=grammar_item.id,
            )
            lesson = await db.scalar(
                select(Lesson).where(
                    Lesson.course_id == course.id,
                    or_(
                        Lesson.id == l_id,
                        (Lesson.unit_id == unit.id) & (Lesson.title == lesson_spec["title"]),
                    ),
                )
            )
            if lesson is None:
                lesson = Lesson(
                    id=l_id,
                    course_id=course.id,
                    unit_id=unit.id,
                    title=lesson_spec["title"],
                    description=lesson_spec["description"],
                    outcome=lesson_spec["outcome"],
                    order_index=lesson_spec["order_index"],
                    pass_threshold=lesson_spec["pass_threshold"],
                    estimated_minutes=lesson_spec["estimated_minutes"],
                    xp_reward=lesson_spec["xp_reward"],
                    lesson_type="grammar",
                    skill="grammar",
                    content=lesson_payload,
                )
                db.add(lesson)
                await db.flush()
                stats["lessons"]["created"] += 1
            else:
                changed = False
                for field, value in (
                    ("unit_id", unit.id),
                    ("title", lesson_spec["title"]),
                    ("description", lesson_spec["description"]),
                    ("outcome", lesson_spec["outcome"]),
                    ("order_index", lesson_spec["order_index"]),
                    ("pass_threshold", lesson_spec["pass_threshold"]),
                    ("estimated_minutes", lesson_spec["estimated_minutes"]),
                    ("xp_reward", lesson_spec["xp_reward"]),
                    ("lesson_type", "grammar"),
                    ("skill", "grammar"),
                    ("content", lesson_payload),
                ):
                    if getattr(lesson, field) != value:
                        setattr(lesson, field, value)
                        changed = True
                stats["lessons"]["updated" if changed else "unchanged"] += 1

            # Upsert linked QuestionBank items (3 tiers per GrammarItem)
            for idx, qb in enumerate(lesson_spec["question_bank"], start=1):
                q_id = deterministic_uuid(f"qb:{lesson_spec['slug']}:{idx}")
                q_tags = [
                    "grammar",
                    level.lower(),
                    g_spec["topic"],
                    f"difficulty_tier:{qb['difficulty_tier']}",
                    f"provenance:{PROVENANCE_AI_GENERATED.lower()}",
                    f"qa_status:{QA_STATUS_NEEDS_REVIEW.lower()}",
                ]
                answer_payload = {"correct": qb["answer"]}
                q_item = await db.scalar(
                    select(QuestionItem).where(
                        or_(
                            QuestionItem.id == q_id,
                            (QuestionItem.grammar_id == grammar_item.id)
                            & (QuestionItem.prompt == qb["prompt"]),
                        )
                    )
                )
                if q_item is None:
                    q_item = QuestionItem(
                        id=q_id,
                        prompt=qb["prompt"],
                        question_type="mcq",
                        options=list(qb["options"]),
                        answer=answer_payload,
                        explanation=qb["explanation"],
                        difficulty_level=level,
                        tags=q_tags,
                        is_active=False,
                        grammar_id=grammar_item.id,
                    )
                    db.add(q_item)
                    await db.flush()
                    stats["question_bank"]["created"] += 1
                else:
                    changed = False
                    for field, value in (
                        ("prompt", qb["prompt"]),
                        ("question_type", "mcq"),
                        ("options", list(qb["options"])),
                        ("answer", answer_payload),
                        ("explanation", qb["explanation"]),
                        ("difficulty_level", level),
                        ("tags", q_tags),
                        ("is_active", False),
                        ("grammar_id", grammar_item.id),
                    ):
                        if getattr(q_item, field) != value:
                            setattr(q_item, field, value)
                            changed = True
                    stats["question_bank"]["updated" if changed else "unchanged"] += 1

        # Refresh course denormalized counters using ONLY learner-published lessons
        # so draft NEEDS_REVIEW lessons stay hidden from public course cards.
        course_lessons = (
            await db.execute(select(Lesson).where(Lesson.course_id == course.id))
        ).scalars().all()
        published_lessons = [
            item for item in course_lessons if is_lesson_learner_visible(item)
        ]
        new_total_lessons = len(published_lessons)
        new_total_xp = sum(int(item.xp_reward or 0) for item in published_lessons)
        new_duration = sum(int(item.estimated_minutes or 0) for item in published_lessons)
        if (
            course.total_lessons != new_total_lessons
            or course.total_xp != new_total_xp
            or course.estimated_duration != new_duration
        ):
            course.total_lessons = new_total_lessons
            course.total_xp = new_total_xp
            course.estimated_duration = new_duration
            course.content_version = (course.content_version or 1) + 1
            if not course_created:
                stats["courses"]["updated"] += 1
        elif not course_created:
            stats["courses"]["unchanged"] += 1

    await db.flush()
    return stats


async def _run_cli(target: str, apply: bool) -> dict[str, Any]:
    dsn = _resolve_target_url(target)
    engine = create_async_engine(dsn, poolclass=NullPool, echo=False)
    try:
        if target == "test":
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as db:
            stats = await upsert_grammar_and_courses(db, ensure_base_courses=True)
            if apply:
                await db.commit()
            else:
                await db.rollback()
            return stats
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Idempotent upsert for CEFR A1-C2 grammar items & multi-lesson courses."
    )
    parser.add_argument(
        "--target",
        choices=["test", "local"],
        default="test",
        help="Target database: 'test' (lexilingo_test) or 'local' (configured DATABASE_URL).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit changes; without --apply, runs as a rolled-back dry run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicit dry run (default when --apply is omitted).",
    )
    args = parser.parse_args()
    apply = bool(args.apply and not args.dry_run)

    mode = "APPLY" if apply else "DRY-RUN (rolled back)"
    print(f"Running grammar/course upsert [target={args.target}, mode={mode}]...")
    stats = asyncio.run(_run_cli(args.target, apply))
    for table, counts in stats.items():
        print(
            f"  {table}: created={counts['created']}, "
            f"updated={counts['updated']}, unchanged={counts['unchanged']}"
        )


if __name__ == "__main__":
    main()
