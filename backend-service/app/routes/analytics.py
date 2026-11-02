"""
Admin Analytics Routes
Endpoints for dashboard charts, user metrics, content performance, and vocabulary analytics.
"""

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.course import Course, Lesson
from app.models.progress import (
    DailyActivity,
    LessonAttempt,
    LessonCompletion,
    UserCourseProgress,
)
from app.models.user import User
from app.models.vocabulary import UserVocabulary, VocabularyItem

router = APIRouter(prefix="/admin/analytics", tags=["Analytics"])


def _retention_rate(
    user_ids: set,
    signup_dates: dict,
    activity_dates: dict,
    offset_days: int,
    as_of: date,
) -> float:
    """Return exact-day cohort retention using only users old enough to qualify."""
    eligible = {
        user_id
        for user_id in user_ids
        if signup_dates[user_id] + timedelta(days=offset_days) <= as_of
    }
    if not eligible:
        return 0.0
    retained = sum(
        1
        for user_id in eligible
        if signup_dates[user_id] + timedelta(days=offset_days)
        in activity_dates.get(user_id, set())
    )
    return round(retained / len(eligible) * 100, 2)


# ============================================================================
# Dashboard Analytics
# ============================================================================

@router.get("/dashboard/kpis")
async def get_dashboard_kpis(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get key performance indicators for the main dashboard.
    """
    # Total users
    total_users = await db.scalar(select(func.count(User.id)))

    # Active users in last 7 days
    seven_days_ago = datetime.now(UTC) - timedelta(days=7)
    active_users_7d = await db.scalar(
        select(func.count(func.distinct(DailyActivity.user_id)))
        .where(DailyActivity.activity_date >= seven_days_ago.date())
    )

    # Total courses
    total_courses = await db.scalar(
        select(func.count(Course.id)).where(Course.is_published.is_(True))
    )

    # Total lessons completed today
    today = datetime.now(UTC).date()
    lessons_completed_today = await db.scalar(
        select(func.count(LessonCompletion.id))
        .where(func.date(LessonCompletion.completed_at) == today)
    )

    # Average DAU in last 30 days
    thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
    dau_data = await db.execute(
        select(
            DailyActivity.activity_date,
            func.count(func.distinct(DailyActivity.user_id)).label("dau")
        )
        .where(DailyActivity.activity_date >= thirty_days_ago.date())
        .group_by(DailyActivity.activity_date)
    )
    dau_list = [row.dau for row in dau_data.fetchall()]
    avg_dau_30d = sum(dau_list) / len(dau_list) if dau_list else 0

    return {
        "kpis": {
            "total_users": total_users or 0,
            "active_users_7d": active_users_7d or 0,
            "total_courses": total_courses or 0,
            "total_lessons_completed_today": lessons_completed_today or 0,
            "avg_dau_30d": avg_dau_30d,
        }
    }


@router.get("/dashboard/user-growth")
async def get_user_growth(
    days: int = Query(30, ge=7, le=90),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user growth data for the specified number of days.
    Returns daily new users and cumulative total users.
    """
    end_date = datetime.now(UTC).date()
    start_date = end_date - timedelta(days=days)

    # Get daily registrations
    daily_signups = await db.execute(
        select(
            func.date(User.created_at).label("date"),
            func.count(User.id).label("new_users")
        )
        .where(func.date(User.created_at) >= start_date)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )

    signup_dict = {row.date: row.new_users for row in daily_signups.fetchall()}

    # Get total users up to start date
    initial_total = await db.scalar(
        select(func.count(User.id))
        .where(func.date(User.created_at) < start_date)
    ) or 0

    # Build daily data
    data = []
    running_total = initial_total
    current_date = start_date

    while current_date <= end_date:
        new_users = signup_dict.get(current_date, 0)
        running_total += new_users
        data.append({
            "date": current_date.isoformat(),
            "new_users": new_users,
            "total_users": running_total,
        })
        current_date += timedelta(days=1)

    return {"data": data}


@router.get("/dashboard/engagement")
async def get_engagement(
    weeks: int = Query(12, ge=4, le=52),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get DAU, WAU, MAU engagement metrics by week.
    """
    end_date = datetime.now(UTC).date()
    ranges = []
    expressions = []
    for index, i in enumerate(reversed(range(weeks))):
        week_end = end_date - timedelta(weeks=i)
        week_start = week_end - timedelta(days=7)
        month_start = week_end - timedelta(days=30)
        week_condition = and_(
            DailyActivity.activity_date >= week_start,
            DailyActivity.activity_date < week_end,
        )
        month_condition = and_(
            DailyActivity.activity_date >= month_start,
            DailyActivity.activity_date < week_end,
        )
        active_days = func.count(
            func.distinct(case((week_condition, DailyActivity.activity_date)))
        )
        expressions.extend((
            (
                func.count(case((week_condition, DailyActivity.id))) * 1.0
                / func.nullif(active_days, 0)
            ).label(f"dau_{index}"),
            func.count(
                func.distinct(case((week_condition, DailyActivity.user_id)))
            ).label(f"wau_{index}"),
            func.count(
                func.distinct(case((month_condition, DailyActivity.user_id)))
            ).label(f"mau_{index}"),
        ))
        ranges.append((week_start, week_end))

    range_start = ranges[0][1] - timedelta(days=30)
    metrics = (
        await db.execute(
            select(*expressions).where(
                DailyActivity.activity_date >= range_start,
                DailyActivity.activity_date < end_date,
            )
        )
    ).one()._mapping

    data = []
    for index, (week_start, week_end) in enumerate(ranges):
        data.append({
            "week": f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')}",
            "dau": int(metrics[f"dau_{index}"] or 0),
            "wau": metrics[f"wau_{index}"] or 0,
            "mau": metrics[f"mau_{index}"] or 0,
        })

    return {"data": data}


@router.get("/dashboard/course-popularity")
async def get_course_popularity(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get top 6 courses by enrollment count.
    """
    result = await db.execute(
        select(
            Course.title,
            func.count(UserCourseProgress.id).label("enrollments")
        )
        .join(UserCourseProgress, UserCourseProgress.course_id == Course.id)
        .where(Course.is_published.is_(True))
        .group_by(Course.id, Course.title)
        .order_by(func.count(UserCourseProgress.id).desc())
        .limit(6)
    )

    data = [
        {
            "course_title": row.title,
            "enrollments": row.enrollments,
        }
        for row in result.fetchall()
    ]

    return {"data": data}


@router.get("/dashboard/completion-funnel")
async def get_completion_funnel(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get course completion funnel: Enrolled → Started → 50% → Completed.
    """
    # Total enrollments
    total_enrolled = await db.scalar(
        select(func.count(UserCourseProgress.id))
    ) or 1  # Avoid division by zero

    # Started (has progress > 0)
    started = await db.scalar(
        select(func.count(UserCourseProgress.id))
        .where(UserCourseProgress.progress_percentage > 0)
    ) or 0

    # 50% complete
    halfway = await db.scalar(
        select(func.count(UserCourseProgress.id))
        .where(UserCourseProgress.progress_percentage >= 50)
    ) or 0

    # Completed
    completed = await db.scalar(
        select(func.count(UserCourseProgress.id))
        .where(UserCourseProgress.progress_percentage >= 100)
    ) or 0

    data = [
        {
            "stage": "Đăng ký",
            "count": total_enrolled,
            "percentage": 100.0,
        },
        {
            "stage": "Bắt đầu",
            "count": started,
            "percentage": (started / total_enrolled * 100) if total_enrolled else 0,
        },
        {
            "stage": "50% hoàn thành",
            "count": halfway,
            "percentage": (halfway / total_enrolled * 100) if total_enrolled else 0,
        },
        {
            "stage": "Hoàn thành",
            "count": completed,
            "percentage": (completed / total_enrolled * 100) if total_enrolled else 0,
        },
    ]

    return {"data": data}


# ============================================================================
# User Analytics
# ============================================================================

@router.get("/user-metrics")
async def get_user_metrics(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user engagement metrics: DAU, WAU, MAU, signups.
    """
    if end_date:
        end = datetime.fromisoformat(end_date).date()
    else:
        end = datetime.now(UTC).date()

    if start_date:
        start = datetime.fromisoformat(start_date).date()
    else:
        start = end - timedelta(days=30)

    # DAU (average)
    dau_result = await db.execute(
        select(
            DailyActivity.activity_date,
            func.count(func.distinct(DailyActivity.user_id)).label("users")
        )
        .where(
            and_(
                DailyActivity.activity_date >= start,
                DailyActivity.activity_date <= end
            )
        )
        .group_by(DailyActivity.activity_date)
    )
    dau_values = [row.users for row in dau_result.fetchall()]
    avg_dau = sum(dau_values) / len(dau_values) if dau_values else 0

    # WAU (last 7 days from end)
    wau_start = end - timedelta(days=7)
    wau = await db.scalar(
        select(func.count(func.distinct(DailyActivity.user_id)))
        .where(
            and_(
                DailyActivity.activity_date >= wau_start,
                DailyActivity.activity_date <= end
            )
        )
    ) or 0

    # MAU (last 30 days from end)
    mau_start = end - timedelta(days=30)
    mau = await db.scalar(
        select(func.count(func.distinct(DailyActivity.user_id)))
        .where(
            and_(
                DailyActivity.activity_date >= mau_start,
                DailyActivity.activity_date <= end
            )
        )
    ) or 0

    # Total signups in date range
    signups = await db.scalar(
        select(func.count(User.id))
        .where(
            and_(
                func.date(User.created_at) >= start,
                func.date(User.created_at) <= end
            )
        )
    ) or 0

    avg_session_duration = await db.scalar(
        select(func.avg(LessonAttempt.time_spent_ms / 60000.0)).where(
            and_(
                LessonAttempt.finished_at.is_not(None),
                LessonAttempt.time_spent_ms > 0,
                func.date(LessonAttempt.finished_at) >= start,
                func.date(LessonAttempt.finished_at) <= end,
            )
        )
    ) or 0

    return {
        "metrics": {
            "dau": int(avg_dau),
            "wau": wau,
            "mau": mau,
            "total_signups": signups,
            "avg_session_duration": float(avg_session_duration),
        }
    }


@router.get("/retention-cohorts")
async def get_retention_cohorts(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cohort retention analysis.
    Cohorts are grouped by signup week.
    """
    # Use Monday-based signup cohorts. Retention is exact-day D1/D7/D30 and
    # only includes users old enough to have reached the requested horizon.
    end_date = datetime.now(UTC).date()
    current_week = end_date - timedelta(days=end_date.weekday())
    start_date = current_week - timedelta(weeks=11)
    range_end = current_week + timedelta(days=7)

    user_result = await db.execute(
        select(User.id, User.created_at).where(
            and_(
                User.created_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=UTC),
                User.created_at < datetime.combine(range_end, datetime.min.time(), tzinfo=UTC),
            )
        )
    )
    signup_dates = {row.id: row.created_at.date() for row in user_result.fetchall()}

    activity_dates: dict = defaultdict(set)
    if signup_dates:
        activity_result = await db.execute(
            select(DailyActivity.user_id, DailyActivity.activity_date).where(
                and_(
                    DailyActivity.user_id.in_(signup_dates),
                    DailyActivity.activity_date >= start_date,
                    DailyActivity.activity_date <= end_date,
                )
            )
        )
        for row in activity_result.fetchall():
            activity_dates[row.user_id].add(row.activity_date)

    cohort_users: dict = defaultdict(set)
    for user_id, signup_date in signup_dates.items():
        week_start = signup_date - timedelta(days=signup_date.weekday())
        cohort_users[week_start].add(user_id)

    cohorts = []
    for index in range(12):
        cohort_date = start_date + timedelta(weeks=index)
        user_ids = cohort_users.get(cohort_date, set())
        cohorts.append(
            {
                "cohort_date": cohort_date.isoformat(),
                "users": len(user_ids),
                "d1_retention": _retention_rate(
                    user_ids, signup_dates, activity_dates, 1, end_date
                ),
                "d7_retention": _retention_rate(
                    user_ids, signup_dates, activity_dates, 7, end_date
                ),
                "d30_retention": _retention_rate(
                    user_ids, signup_dates, activity_dates, 30, end_date
                ),
            }
        )

    return {"cohorts": cohorts}


# ============================================================================
# Content Performance
# ============================================================================

@router.get("/content-performance")
async def get_content_performance(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get course and lesson performance metrics.
    """
    # Aggregate enrollments independently from lesson attempts. Joining all
    # three tables directly multiplies rows and silently skews averages.
    progress_metrics = (
        select(
            UserCourseProgress.course_id.label("course_id"),
            func.count(UserCourseProgress.id).label("enrollments"),
            func.count(
                case((UserCourseProgress.progress_percentage >= 100, 1))
            ).label("completions"),
        )
        .group_by(UserCourseProgress.course_id)
        .subquery()
    )
    attempt_metrics = (
        select(
            Lesson.course_id.label("course_id"),
            func.avg(LessonAttempt.score).label("avg_score"),
            func.avg(LessonAttempt.time_spent_ms / 60000.0).label("avg_time_minutes"),
        )
        .join(LessonAttempt, LessonAttempt.lesson_id == Lesson.id)
        .where(LessonAttempt.finished_at.is_not(None))
        .group_by(Lesson.course_id)
        .subquery()
    )

    course_result = await db.execute(
        select(
            Course.id,
            Course.title,
            func.coalesce(progress_metrics.c.enrollments, 0).label("enrollments"),
            func.coalesce(progress_metrics.c.completions, 0).label("completions"),
            func.coalesce(attempt_metrics.c.avg_score, 0.0).label("avg_score"),
            func.coalesce(attempt_metrics.c.avg_time_minutes, 0.0).label("avg_time_minutes"),
        )
        .outerjoin(progress_metrics, progress_metrics.c.course_id == Course.id)
        .outerjoin(attempt_metrics, attempt_metrics.c.course_id == Course.id)
        .where(Course.is_published.is_(True))
        .order_by(Course.title)
    )

    courses = []
    for row in course_result.fetchall():
        completion_rate = (row.completions / row.enrollments * 100) if row.enrollments > 0 else 0
        courses.append({
            "course_id": str(row.id),
            "course_title": row.title,
            "enrollments": row.enrollments,
            "completions": row.completions,
            "completion_rate": completion_rate,
            "avg_score": float(row.avg_score or 0),
            "avg_time_minutes": float(row.avg_time_minutes or 0),
        })

    lesson_result = await db.execute(
        select(
            Lesson.id,
            Lesson.title,
            func.count(LessonAttempt.id).label("attempts"),
            func.count(case((LessonAttempt.passed.is_(True), 1))).label("completions"),
            func.coalesce(func.avg(LessonAttempt.score), 0.0).label("avg_score"),
        )
        .join(LessonAttempt, LessonAttempt.lesson_id == Lesson.id)
        .where(LessonAttempt.finished_at.is_not(None))
        .group_by(Lesson.id, Lesson.title)
        .order_by(func.avg(LessonAttempt.score).asc(), Lesson.title)
    )
    lessons = [
        {
            "lesson_id": str(row.id),
            "lesson_title": row.title,
            "attempts": row.attempts,
            "completions": row.completions,
            "avg_score": float(row.avg_score or 0),
        }
        for row in lesson_result.fetchall()
    ]

    return {
        "courses": courses,
        "lessons": lessons,
    }


# ============================================================================
# Vocabulary Effectiveness
# ============================================================================

@router.get("/vocabulary-effectiveness")
async def get_vocabulary_effectiveness(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get vocabulary mastery statistics and hardest words.
    """
    # Total vocabulary items
    total_words = await db.scalar(
        select(func.count(VocabularyItem.id))
    ) or 0

    # Average mastery rate (users with mastery_level >= 3)
    total_user_vocab = await db.scalar(
        select(func.count(UserVocabulary.id))
    ) or 1

    mastered_count = await db.scalar(
        select(func.count(UserVocabulary.id))
        .where(UserVocabulary.status == 'mastered')
    ) or 0

    avg_mastery_rate = (mastered_count / total_user_vocab * 100) if total_user_vocab > 0 else 0

    # Average reviews to master
    avg_reviews = await db.scalar(
        select(func.avg(UserVocabulary.total_reviews))
        .where(UserVocabulary.status == 'mastered')
    ) or 0

    # Hardest words (lowest mastery rate)
    hardest_result = await db.execute(
        select(
            VocabularyItem.word,
            func.count(UserVocabulary.id).label("total"),
            func.count(
                case((UserVocabulary.status == 'mastered', 1))
            ).label("mastered"),
            func.avg(UserVocabulary.total_reviews).label("avg_reviews"),
        )
        .join(UserVocabulary, UserVocabulary.vocabulary_id == VocabularyItem.id)
        .group_by(VocabularyItem.id, VocabularyItem.word)
        .having(func.count(UserVocabulary.id) >= 5)  # At least 5 users
        .order_by((func.count(case((UserVocabulary.status == 'mastered', 1))) / func.count(UserVocabulary.id)).asc())
        .limit(10)
    )

    hardest_words = []
    for row in hardest_result.fetchall():
        mastery_rate = (row.mastered / row.total * 100) if row.total > 0 else 0
        hardest_words.append({
            "word": row.word,
            "mastery_rate": mastery_rate,
            "avg_reviews": float(row.avg_reviews or 0),
        })

    return {
        "total_words": total_words,
        "avg_mastery_rate": avg_mastery_rate,
        "avg_reviews_to_master": avg_reviews,
        "hardest_words": hardest_words,
    }
