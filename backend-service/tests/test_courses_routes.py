"""
Tests for Course API Routes
/Users/nguyenhuuthang/Documents/RepoGitHub/LexiLingo/backend-service/app/routes/courses.py

Covers:
- GET  /api/v1/courses           — paginated public list
- GET  /api/v1/courses/enrolled  — enrolled courses (auth required)
- GET  /api/v1/courses/{id}      — course detail (public)
- POST /api/v1/courses/{id}/enroll — enroll (auth required)
"""

import pytest
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

BASE = "/api/v1/courses"
COURSE_ID = "00000000-0000-0000-0000-000000000010"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def auth_client():
    """Authenticated async HTTP client with fully mocked DB and user."""
    from app.main import app
    from app.core.database import get_db
    from app.core.dependencies import get_current_user

    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock_result.all.return_value = []
    mock_session = MagicMock()

    async def fake_execute(query):
        return mock_result

    mock_session.execute = fake_execute
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    mock_user = MagicMock()
    mock_user.id = "00000000-0000-0000-0000-000000000001"
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.is_verified = True
    mock_user.level = "beginner"
    mock_user.native_language = "vi"
    mock_user.target_language = "en"
    mock_user.total_xp = 100
    mock_user.display_name = "Test User"

    async def mock_get_db():
        yield mock_session

    async def mock_get_current_user():
        return mock_user

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_current_user] = mock_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def no_auth_client():
    """Unauthenticated async HTTP client with mocked DB."""
    from app.main import app
    from app.core.database import get_db

    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock_result.all.return_value = []
    mock_session = MagicMock()

    async def fake_execute(query):
        return mock_result

    mock_session.execute = fake_execute

    async def mock_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = mock_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ============================================================================
# GET /api/v1/courses  — Public list
# ============================================================================

class TestGetCourses:
    """Tests for GET /api/v1/courses (public, paginated)."""

    @pytest.mark.asyncio
    async def test_returns_200_with_empty_list(self, no_auth_client: AsyncClient):
        with patch("app.crud.course.CourseCRUD.get_courses", new=AsyncMock(return_value=([], 0))):
            response = await no_auth_client.get(BASE)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_has_pagination_meta(self, no_auth_client: AsyncClient):
        with patch("app.crud.course.CourseCRUD.get_courses", new=AsyncMock(return_value=([], 0))):
            response = await no_auth_client.get(BASE)
        data = response.json()
        assert "pagination" in data
        assert "data" in data

    @pytest.mark.asyncio
    async def test_pagination_defaults_to_page_1(self, no_auth_client: AsyncClient):
        with patch("app.crud.course.CourseCRUD.get_courses", new=AsyncMock(return_value=([], 0))):
            response = await no_auth_client.get(BASE)
        pagination = response.json()["pagination"]
        assert pagination["page"] == 1
        assert pagination["page_size"] == 20

    @pytest.mark.asyncio
    async def test_page_size_validation_rejects_zero(self, no_auth_client: AsyncClient):
        response = await no_auth_client.get(f"{BASE}?page_size=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_page_size_validation_rejects_over_100(self, no_auth_client: AsyncClient):
        response = await no_auth_client.get(f"{BASE}?page_size=101")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_language_filter_is_forwarded(self, no_auth_client: AsyncClient):
        mock_get_courses = AsyncMock(return_value=([], 0))
        with patch("app.crud.course.CourseCRUD.get_courses", new=mock_get_courses):
            response = await no_auth_client.get(f"{BASE}?language=en")
        assert response.status_code == 200
        _, call_kwargs = mock_get_courses.call_args
        assert call_kwargs["language"] == "en"

    @pytest.mark.asyncio
    async def test_level_filter_is_forwarded(self, no_auth_client: AsyncClient):
        mock_get_courses = AsyncMock(return_value=([], 0))
        with patch("app.crud.course.CourseCRUD.get_courses", new=mock_get_courses):
            response = await no_auth_client.get(f"{BASE}?level=A1")
        assert response.status_code == 200
        _, call_kwargs = mock_get_courses.call_args
        assert call_kwargs["level"] == "A1"

    @pytest.mark.asyncio
    async def test_returns_course_items(self, no_auth_client: AsyncClient):
        mock_course = MagicMock()
        mock_course.id = uuid.UUID(COURSE_ID)
        mock_course.title = "English Basics"
        mock_course.description = "Beginner English"
        mock_course.language = "en"
        mock_course.level = "A1"
        mock_course.tags = ["grammar"]
        mock_course.thumbnail_url = None
        mock_course.total_lessons = 10
        mock_course.total_xp = 500
        mock_course.estimated_duration = 60

        with patch("app.crud.course.CourseCRUD.get_courses", new=AsyncMock(return_value=([mock_course], 1))):
            response = await no_auth_client.get(BASE)

        data = response.json()
        assert data["pagination"]["total"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "English Basics"

    @pytest.mark.asyncio
    async def test_page_param_respected(self, no_auth_client: AsyncClient):
        mock_get_courses = AsyncMock(return_value=([], 0))
        with patch("app.crud.course.CourseCRUD.get_courses", new=mock_get_courses):
            response = await no_auth_client.get(f"{BASE}?page=3&page_size=5")
        assert response.status_code == 200
        pagination = response.json()["pagination"]
        assert pagination["page"] == 3
        assert pagination["page_size"] == 5

    @pytest.mark.asyncio
    async def test_authenticated_returns_user_progress(self, auth_client: AsyncClient):
        from app.main import app
        from app.core.dependencies import get_current_user_optional

        course_uuid = uuid.UUID(COURSE_ID)
        mock_course = MagicMock()
        mock_course.id = course_uuid
        mock_course.title = "English Basics"
        mock_course.description = "Beginner English"
        mock_course.language = "en"
        mock_course.level = "A1"
        mock_course.tags = ["grammar"]
        mock_course.thumbnail_url = None
        mock_course.total_lessons = 1
        mock_course.total_xp = 100
        mock_course.estimated_duration = 60

        mock_user = MagicMock()
        mock_user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        async def mock_get_current_user_optional():
            return mock_user

        app.dependency_overrides[get_current_user_optional] = mock_get_current_user_optional
        try:
            with patch("app.crud.course.CourseCRUD.get_courses", new=AsyncMock(return_value=([mock_course], 1))), \
                 patch("app.crud.course.CourseCRUD.get_enrolled_course_progress", new=AsyncMock(return_value={course_uuid: 100.0})), \
                 patch("app.routes.courses.get_cached", new=AsyncMock(return_value=None)), \
                 patch("app.routes.courses.set_cached", new=AsyncMock()):
                response = await auth_client.get(BASE)
        finally:
            app.dependency_overrides.pop(get_current_user_optional, None)

        assert response.status_code == 200
        item = response.json()["data"][0]
        assert item["is_enrolled"] is True
        assert item["user_progress"] == 100.0


# ============================================================================
# GET /api/v1/courses/enrolled  — Auth required
# ============================================================================

class TestGetEnrolledCourses:
    """Tests for GET /api/v1/courses/enrolled (auth required)."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, no_auth_client: AsyncClient):
        response = await no_auth_client.get(f"{BASE}/enrolled")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticated_returns_200(self, auth_client: AsyncClient):
        response = await auth_client.get(f"{BASE}/enrolled")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_enrollments(self, auth_client: AsyncClient):
        response = await auth_client.get(f"{BASE}/enrolled")
        data = response.json()
        assert "data" in data
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_pagination_meta_present(self, auth_client: AsyncClient):
        response = await auth_client.get(f"{BASE}/enrolled")
        data = response.json()
        assert "pagination" in data
        assert "page" in data["pagination"]


# ============================================================================
# GET /api/v1/courses/{course_id}  — Course detail (public)
# ============================================================================

class TestGetCourseDetail:
    """Tests for GET /api/v1/courses/{course_id}."""

    @pytest.mark.asyncio
    async def test_returns_404_when_course_not_found(self, no_auth_client: AsyncClient):
        with patch("app.crud.course.CourseCRUD.get_course_with_units", new=AsyncMock(return_value=None)):
            response = await no_auth_client.get(f"{BASE}/{COURSE_ID}")
        assert response.status_code == 404
        assert "not found" in response.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_returns_404_for_unpublished_course(self, no_auth_client: AsyncClient):
        mock_course = MagicMock()
        mock_course.is_published = False
        mock_course.units = []
        with patch("app.crud.course.CourseCRUD.get_course_with_units", new=AsyncMock(return_value=mock_course)):
            response = await no_auth_client.get(f"{BASE}/{COURSE_ID}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_422(self, no_auth_client: AsyncClient):
        response = await no_auth_client.get(f"{BASE}/not-a-uuid")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_course_data_when_found(self, no_auth_client: AsyncClient):
        mock_course = MagicMock()
        mock_course.id = uuid.UUID(COURSE_ID)
        mock_course.title = "English Basics"
        mock_course.description = "Learn basics"
        mock_course.language = "en"
        mock_course.level = "A1"
        mock_course.skill = None
        mock_course.tags = []
        mock_course.thumbnail_url = None
        mock_course.total_lessons = 5
        mock_course.total_xp = 250
        mock_course.estimated_duration = 30
        mock_course.is_published = True
        mock_course.is_enrolled = None
        mock_course.units = []

        with patch("app.crud.course.CourseCRUD.get_course_with_units", new=AsyncMock(return_value=mock_course)):
            response = await no_auth_client.get(f"{BASE}/{COURSE_ID}")

        assert response.status_code == 200
        assert "data" in response.json()

    @pytest.mark.asyncio
    async def test_authenticated_course_detail_includes_user_progress(self):
        from app.main import app
        from app.core.database import get_db
        from app.core.dependencies import get_current_user_optional

        course_uuid = uuid.UUID(COURSE_ID)
        mock_course = MagicMock()
        mock_course.id = course_uuid
        mock_course.title = "English Basics"
        mock_course.description = "Learn basics"
        mock_course.language = "en"
        mock_course.level = "A1"
        mock_course.skill = None
        mock_course.tags = []
        mock_course.thumbnail_url = None
        mock_course.total_lessons = 1
        mock_course.total_xp = 100
        mock_course.estimated_duration = 60
        mock_course.is_published = True
        mock_course.is_enrolled = None
        mock_course.units = []

        mock_ucp = MagicMock()
        mock_ucp.progress_percentage = 100.0
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_ucp

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_user = MagicMock()
        mock_user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        async def mock_get_db():
            yield mock_session

        async def mock_get_current_user_optional():
            return mock_user

        app.dependency_overrides[get_db] = mock_get_db
        app.dependency_overrides[get_current_user_optional] = mock_get_current_user_optional

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                with patch("app.crud.course.CourseCRUD.get_course_with_units", new=AsyncMock(return_value=mock_course)), \
                     patch("app.crud.course.LessonCRUD.get_completed_lesson_ids", new=AsyncMock(return_value=set())):
                    response = await client.get(f"{BASE}/{COURSE_ID}")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        detail = response.json()["data"]
        assert detail["is_enrolled"] is True
        assert detail["user_progress"] == 100.0


# ============================================================================
# POST /api/v1/courses/{course_id}/enroll  — Auth required
# ============================================================================

class TestEnrollInCourse:
    """Tests for POST /api/v1/courses/{course_id}/enroll."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, no_auth_client: AsyncClient):
        response = await no_auth_client.post(f"{BASE}/{COURSE_ID}/enroll")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_404_when_course_not_found(self, auth_client: AsyncClient):
        with patch("app.crud.course.CourseCRUD.get_course", new=AsyncMock(return_value=None)):
            response = await auth_client.post(f"{BASE}/{COURSE_ID}/enroll")
        assert response.status_code == 404
        assert "not found" in response.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_returns_400_for_unpublished_course(self, auth_client: AsyncClient):
        mock_course = MagicMock()
        mock_course.is_published = False
        with patch("app.crud.course.CourseCRUD.get_course", new=AsyncMock(return_value=mock_course)):
            response = await auth_client.post(f"{BASE}/{COURSE_ID}/enroll")
        assert response.status_code == 400
        assert "not available" in response.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_already_enrolled_returns_200_with_message(self, auth_client: AsyncClient):
        mock_course = MagicMock()
        mock_course.is_published = True
        with patch("app.crud.course.CourseCRUD.get_course", new=AsyncMock(return_value=mock_course)), \
             patch("app.crud.course.CourseCRUD.is_user_enrolled", new=AsyncMock(return_value=True)):
            response = await auth_client.post(f"{BASE}/{COURSE_ID}/enroll")
        assert response.status_code == 200
        assert "already enrolled" in response.json()["data"]["message"].lower()

    @pytest.mark.asyncio
    async def test_new_enrollment_returns_200_with_success_message(self, auth_client: AsyncClient):
        mock_course = MagicMock()
        mock_course.is_published = True
        mock_progress = MagicMock()
        mock_progress.started_at = datetime.now(UTC)

        with patch("app.crud.course.CourseCRUD.get_course", new=AsyncMock(return_value=mock_course)), \
             patch("app.crud.course.CourseCRUD.is_user_enrolled", new=AsyncMock(return_value=False)), \
             patch("app.routes.courses.UserCourseProgress", return_value=mock_progress):
            response = await auth_client.post(f"{BASE}/{COURSE_ID}/enroll")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_422(self, auth_client: AsyncClient):
        response = await auth_client.post(f"{BASE}/not-a-uuid/enroll")
        assert response.status_code == 422


class TestGetCoursesByCategory:
    """Tests for GET /api/v1/categories/{category_id}/courses."""

    @pytest.mark.asyncio
    async def test_authenticated_category_courses_include_user_progress(self):
        from app.main import app
        from app.core.database import get_db
        from app.core.dependencies import get_current_user_optional

        category_uuid = uuid.UUID("00000000-0000-0000-0000-000000000099")
        course_uuid = uuid.UUID(COURSE_ID)
        mock_category = MagicMock()
        mock_category.id = category_uuid

        mock_course = MagicMock()
        mock_course.id = course_uuid
        mock_course.title = "English Basics"
        mock_course.description = "Learn basics"
        mock_course.language = "en"
        mock_course.level = "A1"
        mock_course.tags = ["grammar"]
        mock_course.thumbnail_url = None
        mock_course.total_lessons = 2
        mock_course.total_xp = 100
        mock_course.estimated_duration = 30

        mock_session = MagicMock()
        mock_user = MagicMock()
        mock_user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        async def mock_get_db():
            yield mock_session

        async def mock_get_current_user_optional():
            return mock_user

        app.dependency_overrides[get_db] = mock_get_db
        app.dependency_overrides[get_current_user_optional] = mock_get_current_user_optional

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                with patch(
                    "app.crud.course_category.CourseCategoryCRUD.get_category_by_id",
                    new=AsyncMock(return_value=mock_category),
                ), patch(
                    "app.crud.course_category.CourseCategoryCRUD.get_courses_by_category",
                    new=AsyncMock(return_value=([mock_course], 1)),
                ), patch(
                    "app.crud.course.CourseCRUD.get_enrolled_course_progress",
                    new=AsyncMock(return_value={course_uuid: 100.0}),
                ):
                    response = await client.get(
                        f"/api/v1/categories/{category_uuid}/courses"
                    )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        items = response.json()["data"]
        assert len(items) == 1
        assert items[0]["is_enrolled"] is True
        assert items[0]["user_progress"] == 100.0
