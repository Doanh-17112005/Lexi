"""Pure roadmap lesson-unlock policy shared across course detail, roadmap, and start_lesson."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from uuid import UUID

from app.services.content_publication_policy import is_lesson_learner_visible


@dataclass(frozen=True)
class LessonUnlockDecision:
    is_locked: bool
    missing_prerequisite_ids: tuple[UUID, ...]
    unlock_reason: str | None = None


def _ordered_playable_lessons(unit, *, playable_only: bool) -> list:
    lessons = getattr(unit, "lessons", None) or []
    if playable_only:
        lessons = [
            lesson
            for lesson in lessons
            if getattr(lesson, "exercise_count", 0) > 0
            and is_lesson_learner_visible(lesson)
        ]
    return sorted(
        lessons,
        key=lambda lesson: (getattr(lesson, "order_index", 0), str(lesson.id)),
    )


def evaluate_course_unlocks(
    units: Iterable,
    completed_lesson_ids: set[UUID],
    *,
    playable_only: bool = True,
) -> dict[UUID, LessonUnlockDecision]:
    """Evaluate unlock status for every lesson in a course.

    Rules:
    1. Already-completed lessons are always unlocked (replay allowed).
    2. First playable lesson of the first non-empty unit is unlocked unless it
       has explicit unmet `prerequisites`.
    3. Subsequent lessons in a unit require the previous playable lesson in
       that unit to be completed.
    4. The first playable lesson of any later unit requires all playable lessons
       in the immediately preceding non-empty unit to be completed.
    5. Any explicit `lesson.prerequisites` UUIDs must also be completed.
    """
    sorted_units = sorted(
        units,
        key=lambda unit: (getattr(unit, "order_index", 0), str(unit.id)),
    )

    decisions: dict[UUID, LessonUnlockDecision] = {}
    previous_unit_incomplete_ids: list[UUID] = []
    has_seen_non_empty_unit = False

    for unit in sorted_units:
        ordered_lessons = _ordered_playable_lessons(unit, playable_only=playable_only)
        if not ordered_lessons:
            continue

        for index, lesson in enumerate(ordered_lessons):
            lesson_id: UUID = lesson.id
            if lesson_id in completed_lesson_ids:
                decisions[lesson_id] = LessonUnlockDecision(
                    is_locked=False,
                    missing_prerequisite_ids=(),
                    unlock_reason=None,
                )
                continue

            missing: list[UUID] = []
            reason: str | None = None

            if index == 0:
                if has_seen_non_empty_unit and previous_unit_incomplete_ids:
                    missing.extend(previous_unit_incomplete_ids)
                    reason = "Complete all lessons in the previous unit to unlock."
            else:
                prev_lesson_id: UUID = ordered_lessons[index - 1].id
                if prev_lesson_id not in completed_lesson_ids:
                    missing.append(prev_lesson_id)
                    reason = "Complete the previous lesson to unlock."

            explicit_prereqs: Sequence[UUID] = getattr(lesson, "prerequisites", None) or []
            for prereq_id in explicit_prereqs:
                if prereq_id != lesson_id and prereq_id not in completed_lesson_ids:
                    if prereq_id not in missing:
                        missing.append(prereq_id)
                    if reason is None:
                        reason = "Complete required prerequisite lessons to unlock."

            decisions[lesson_id] = LessonUnlockDecision(
                is_locked=bool(missing),
                missing_prerequisite_ids=tuple(missing),
                unlock_reason=reason,
            )

        previous_unit_incomplete_ids = [
            lesson.id
            for lesson in ordered_lessons
            if lesson.id not in completed_lesson_ids
        ]
        has_seen_non_empty_unit = True

    return decisions
