"""
Course API Routes

Endpoints for course management, enrollment, and browsing.
Supports pagination, filtering, and user-specific data.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.ai_service_client import invalidate_learner_card
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.core.cache import build_cache_key, get_cached, set_cached
from app.models.user import User
from app.models.progress import UserCourseProgress
from app.crud.course import CourseCRUD, UnitCRUD, LessonCRUD
from app.services.content_publication_policy import is_lesson_learner_visible
from app.schemas.course import (
    CourseResponse,
    CourseListItem,
    CourseDetailResponse,
    EnrollmentResponse,
    UnitWithLessons,
    LessonInUnit
)
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
import uuid
from datetime import datetime, timezone

router = APIRouter(tags=["courses"])


# =====================
# Course Browsing (Public/Authenticated)
# =====================

@router.get("", response_model=PaginatedResponse[CourseListItem])
async def get_courses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    language: Optional[str] = Query(None, description="Filter by language (e.g., 'en', 'vi')"),
    level: Optional[str] = Query(None, description="Filter by CEFR level (A1-C2)"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get paginated list of courses.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **language**: Filter by language code
    - **level**: Filter by CEFR level (A1, A2, B1, B2, C1, C2)
    
    Returns enrollment status if user is authenticated.
    """
    skip = (page - 1) * page_size
    
    # Cache public course data (TTL 60s) — enrollment overlay is per-user
    cache_key = build_cache_key("courses", page=page, page_size=page_size,
                                language=language, level=level)
    cached = await get_cached(cache_key)
    
    if cached:
        course_dicts = cached["items"]
        total = cached["total"]
    else:
        courses, total = await CourseCRUD.get_courses(
            db,
            skip=skip,
            limit=page_size,
            language=language,
            level=level,
            published_only=True
        )
        course_dicts = [
            {
                "id": str(course.id),
                "title": course.title,
                "description": course.description,
                "language": course.language,
                "level": course.level,
                "tags": course.tags or [],
                "thumbnail_url": course.thumbnail_url,
                "total_lessons": course.total_lessons,
                "total_xp": course.total_xp,
                "estimated_duration": course.estimated_duration,
            }
            for course in courses
        ]
        await set_cached(cache_key, {"items": course_dicts, "total": total}, ttl=60)
    
    # Overlay enrollment & progress status (per-user, not cached)
    enrolled_progress: dict[uuid.UUID, float] = {}
    if current_user:
        course_ids = [uuid.UUID(c["id"]) for c in course_dicts]
        enrolled_progress = await CourseCRUD.get_enrolled_course_progress(
            db, current_user.id, course_ids
        )

    course_items = []
    for c in course_dicts:
        c_id = uuid.UUID(c["id"])
        is_enrolled = (c_id in enrolled_progress) if current_user else None
        item = CourseListItem(
            **{
                **c,
                "id": c_id,
                "is_enrolled": is_enrolled,
                "user_progress": enrolled_progress.get(c_id) if current_user else None,
            }
        )
        course_items.append(item)
    
    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        data=course_items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )
    )


# =====================
# Enrolled Courses (Must be before /{course_id} to avoid route conflict)
# =====================

@router.get("/enrolled", response_model=PaginatedResponse[CourseListItem])
async def get_enrolled_courses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all courses the current user is enrolled in.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    
    Returns courses with progress information.
    """
    from sqlalchemy import select, func
    from app.models.course import Course
    
    # Query for enrolled courses with progress
    skip = (page - 1) * page_size
    
    # Get total count
    count_query = select(func.count(UserCourseProgress.id)).where(
        UserCourseProgress.user_id == current_user.id
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get enrolled courses
    query = (
        select(Course, UserCourseProgress)
        .join(UserCourseProgress, Course.id == UserCourseProgress.course_id)
        .where(
            UserCourseProgress.user_id == current_user.id,
            Course.is_published == True
        )
        .order_by(UserCourseProgress.last_activity_at.desc())
        .offset(skip)
        .limit(page_size)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Convert to response models
    course_items = []
    for course, progress in rows:
        item_dict = {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "language": course.language,
            "level": course.level,
            "tags": course.tags or [],
            "thumbnail_url": course.thumbnail_url,
            "total_lessons": course.total_lessons,
            "total_xp": course.total_xp,
            "estimated_duration": course.estimated_duration,
            "is_enrolled": True,
            "user_progress": float(progress.progress_percentage or 0.0),
        }
        
        item = CourseListItem(**item_dict)
        course_items.append(item)
    
    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        data=course_items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )
    )


@router.get("/{course_id}", response_model=ApiResponse[CourseDetailResponse])
async def get_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get detailed course information including units and lessons.
    
    - Shows lesson lock status based on prerequisites
    - Shows completion status if user is authenticated
    """
    # Get course with all units and lessons
    course = await CourseCRUD.get_course_with_units(db, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if not course.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not available"
        )
    
    # Build response
    course_response = CourseResponse.model_validate(course)
    
    # Add enrollment & progress info if user is authenticated
    if current_user:
        from sqlalchemy import select
        ucp_result = await db.execute(
            select(UserCourseProgress).where(
                UserCourseProgress.user_id == current_user.id,
                UserCourseProgress.course_id == course.id,
            )
        )
        ucp = ucp_result.scalar_one_or_none()
        course_response.is_enrolled = ucp is not None
        if ucp is not None:
            course_response.user_progress = float(ucp.progress_percentage or 0.0)
    
    # Build units with lessons
    # Pre-fetch all completed lesson IDs in 1 query (avoid N+1)
    completed_lesson_ids: set = set()
    if current_user:
        all_lesson_ids = []
        for unit in course.units:
            for lesson in unit.lessons:
                all_lesson_ids.append(lesson.id)
                if lesson.prerequisites:
                    all_lesson_ids.extend(lesson.prerequisites)
        completed_lesson_ids = await LessonCRUD.get_completed_lesson_ids(
            db, current_user.id, list(set(all_lesson_ids))
        )

    from app.services.roadmap_unlock_policy import evaluate_course_unlocks

    unlock_decisions = evaluate_course_unlocks(
        course.units,
        completed_lesson_ids,
        playable_only=True,
    )

    units_with_lessons = []
    for unit in sorted(course.units, key=lambda u: u.order_index):
        lessons = []
        for lesson in sorted(unit.lessons, key=lambda l: l.order_index):
            # Hide empty or draft/quarantined lessons from learners until approved.
            if lesson.exercise_count == 0 or not is_lesson_learner_visible(lesson):
                continue
            lesson_data = LessonInUnit.model_validate(lesson)

            decision = unlock_decisions.get(lesson.id)
            lesson_data.is_locked = (
                decision.is_locked if decision is not None else bool(lesson.prerequisites)
            )
            
            # Check if lesson is completed
            if current_user:
                lesson_data.is_completed = lesson.id in completed_lesson_ids
            
            lessons.append(lesson_data)

        if not lessons:
            continue

        unit_with_lessons = UnitWithLessons(
            id=unit.id,
            title=unit.title,
            description=unit.description,
            order_index=unit.order_index,
            background_color=unit.background_color,
            icon_url=unit.icon_url,
            lessons=lessons
        )
        units_with_lessons.append(unit_with_lessons)
    
    # Create detailed response (reflecting only learner-visible published lessons)
    detail_payload = course_response.model_dump()
    detail_payload["total_lessons"] = sum(len(u.lessons) for u in units_with_lessons)
    course_detail = CourseDetailResponse(
        **detail_payload,
        units=units_with_lessons
    )
    
    return ApiResponse(data=course_detail)


@router.post("/{course_id}/enroll", response_model=ApiResponse[EnrollmentResponse])
async def enroll_in_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enroll the current user in a course.
    
    - Creates UserCourseProgress entry
    - Idempotent: returns success if already enrolled
    """
    # Check if course exists
    course = await CourseCRUD.get_course(db, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if not course.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course not available for enrollment"
        )
    
    # Check if already enrolled
    is_enrolled = await CourseCRUD.is_user_enrolled(db, current_user.id, course_id)
    if is_enrolled:
        return ApiResponse(
            data=EnrollmentResponse(
                course_id=course_id,
                user_id=current_user.id,
                enrolled_at=datetime.now(timezone.utc),
                message="Already enrolled in course"
            )
        )
    
    # Create enrollment — use IntegrityError to handle race condition
    progress = UserCourseProgress(
        user_id=current_user.id,
        course_id=course_id,
        progress_percentage=0.0
    )
    db.add(progress)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return ApiResponse(
            data=EnrollmentResponse(
                course_id=course_id,
                user_id=current_user.id,
                enrolled_at=datetime.now(timezone.utc),
                message="Already enrolled in course"
            )
        )
    await db.refresh(progress)

    # Closes the loop on Lexi's course cards: tap one, enrol, then ask Lexi
    # what you are studying and get the new course rather than the old list.
    await invalidate_learner_card(current_user.id)

    return ApiResponse(
        data=EnrollmentResponse(
            course_id=course_id,
            user_id=current_user.id,
            enrolled_at=progress.started_at,
            message="Successfully enrolled in course"
        )
    )
