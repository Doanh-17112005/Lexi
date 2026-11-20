"""
Tests for Vocabulary API Routes
/Users/nguyenhuuthang/Documents/RepoGitHub/LexiLingo/backend-service/app/routes/vocabulary.py

Covers:
- GET  /api/v1/vocabulary/items              — list vocab items (public)
- GET  /api/v1/vocabulary/items/{id}         — get vocab item (public)
- GET  /api/v1/vocabulary/collection         — user vocab collection (auth)
- POST /api/v1/vocabulary/collection         — add to collection (auth, query param)
- POST /api/v1/vocabulary/collection/quick-save — quick-save from app surfaces
- POST /api/v1/vocabulary/collection/bulk    — bulk add (auth)
- GET  /api/v1/vocabulary/due                — due for review (auth)
- POST /api/v1/vocabulary/review/{id}        — submit review (auth)
- GET  /api/v1/vocabulary/stats              — vocab stats (auth)
- POST /api/v1/vocabulary/decks              — create deck (auth, query params)
- GET  /api/v1/vocabulary/decks              — list decks (auth)
"""

import pytest
import uuid
from datetime import UTC, datetime, date, timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.models.progress import DailyActivity

BASE = "/api/v1/vocabulary"
VOCAB_ID = "00000000-0000-0000-0000-000000000050"
USER_VOCAB_ID = "00000000-0000-0000-0000-000000000060"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def auth_client():
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
    mock_user.level = "A1"
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
        yield client, mock_session, mock_result, mock_user
    app.dependency_overrides.clear()


@pytest.fixture
async def no_auth_client():
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


def _make_mock_vocab_item(vocab_id: str = VOCAB_ID):
    """Build a mock VocabularyItem."""
    item = MagicMock()
    item.id = uuid.UUID(vocab_id)
    item.word = "hello"
    item.definition = "A greeting"
    item.translation = {"vi": "xin chào"}
    item.part_of_speech = "interjection"
    item.pronunciation = "həˈləʊ"
    item.difficulty_level = "A1"
    item.audio_url = None
    item.examples = ["Hello, how are you?"]
    item.tags = None
    item.course_id = None
    item.lesson_id = None
    item.usage_frequency = 0
    item.created_at = datetime.now(UTC)
    item.updated_at = datetime.now(UTC)
    return item


def _make_mock_user_vocab():
    """Build a mock UserVocabulary."""
    uv = MagicMock()
    uv.id = uuid.UUID(USER_VOCAB_ID)
    uv.vocabulary_id = uuid.UUID(VOCAB_ID)
    uv.user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    uv.status = "learning"
    uv.ease_factor = 2.5
    uv.interval = 1
    uv.streak = 0
    uv.repetitions = 0
    uv.next_review_date = datetime.now(UTC)
    uv.last_reviewed_at = None
    uv.fsrs_stability = 0.0
    uv.fsrs_difficulty = 0.0
    uv.fsrs_elapsed_days = 0
    uv.fsrs_scheduled_days = 0
    uv.fsrs_reps = 0
    uv.fsrs_lapses = 0
    uv.fsrs_state = 0
    uv.fsrs_last_review = None
    uv.is_due = False
    uv.accuracy = 0.0
    uv.total_reviews = 0
    uv.correct_reviews = 0
    uv.longest_streak = 0
    uv.total_xp_earned = 0
    uv.notes = None
    uv.added_at = datetime.now(UTC)
    return uv


# ============================================================================
# GET /api/v1/vocabulary/items  — List vocab items (public)
# ============================================================================

class TestGetVocabularyItems:
    """Tests for GET /api/v1/vocabulary/items."""

    @pytest.mark.asyncio
    async def test_returns_200_with_empty_list(self, no_auth_client: AsyncClient):
        with patch("app.crud.vocabulary.vocabulary_crud.get_vocabulary_items", new=AsyncMock(return_value=[])):
            response = await no_auth_client.get(f"{BASE}/items")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("stored_tags", "expected_tags"),
        [
            (None, []),
            ([], []),
            ([" Travel ", "daily_life", "travel"], ["travel", "daily"]),
            (
                {
                    "source": "AI_GENERATED",
                    "source_reference": None,
                    "qa_status": "NEEDS_REVIEW",
                    "topic": ["daily_life", "Travel"],
                },
                ["ai_generated", "daily", "travel", "needs_review"],
            ),
        ],
    )
    async def test_normalizes_legacy_tag_shapes(
        self,
        no_auth_client: AsyncClient,
        stored_tags,
        expected_tags,
    ):
        item = _make_mock_vocab_item()
        item.tags = stored_tags
        with patch(
            "app.crud.vocabulary.vocabulary_crud.get_vocabulary_items",
            new=AsyncMock(return_value=[item]),
        ):
            response = await no_auth_client.get(f"{BASE}/items")

        assert response.status_code == 200
        assert response.json()[0]["tags"] == expected_tags

    @pytest.mark.asyncio
    async def test_normalizes_legacy_tags_from_cached_response(
        self,
        no_auth_client: AsyncClient,
    ):
        now = datetime.now(UTC).isoformat()
        cached_item = {
            "id": VOCAB_ID,
            "word": "hello",
            "definition": "A greeting",
            "translation": {"vi": "xin chào"},
            "part_of_speech": "interjection",
            "pronunciation": "həˈləʊ",
            "difficulty_level": "A1",
            "audio_url": None,
            "tags": {
                "source": "AI_GENERATED",
                "qa_status": "NEEDS_REVIEW",
            },
            "course_id": None,
            "lesson_id": None,
            "usage_frequency": 0,
            "created_at": now,
            "updated_at": now,
        }
        with patch(
            "app.routes.vocabulary.get_cached",
            new=AsyncMock(return_value=[cached_item]),
        ):
            response = await no_auth_client.get(f"{BASE}/items")

        assert response.status_code == 200
        assert response.json()[0]["tags"] == ["ai_generated", "needs_review"]

    @pytest.mark.asyncio
    async def test_does_not_require_auth(self, no_auth_client: AsyncClient):
        with patch("app.crud.vocabulary.vocabulary_crud.get_vocabulary_items", new=AsyncMock(return_value=[])):
            response = await no_auth_client.get(f"{BASE}/items")
        assert response.status_code != 401

    @pytest.mark.asyncio
    async def test_search_param_calls_search_method(self, no_auth_client: AsyncClient):
        mock_search = AsyncMock(return_value=[])
        with patch("app.crud.vocabulary.vocabulary_crud.search_vocabulary", new=mock_search):
            response = await no_auth_client.get(f"{BASE}/items?search=hello")
        assert response.status_code == 200
        mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_limit_max_is_100(self, no_auth_client: AsyncClient):
        """limit > 100 should fail validation."""
        response = await no_auth_client.get(f"{BASE}/items?limit=101")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_limit_min_is_1(self, no_auth_client: AsyncClient):
        response = await no_auth_client.get(f"{BASE}/items?limit=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_difficulty_level_filter_is_forwarded(self, no_auth_client: AsyncClient):
        mock_get_items = AsyncMock(return_value=[])
        with patch("app.crud.vocabulary.vocabulary_crud.get_vocabulary_items", new=mock_get_items):
            await no_auth_client.get(f"{BASE}/items?difficulty_level=B1")
        _, call_kwargs = mock_get_items.call_args
        assert call_kwargs.get("difficulty_level") == "B1"


# ============================================================================
# GET /api/v1/vocabulary/items/{id}  — Get single vocab item (public)
# ============================================================================

class TestGetVocabularyItem:
    """Tests for GET /api/v1/vocabulary/items/{vocabulary_id}."""

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, no_auth_client: AsyncClient):
        with patch("app.crud.vocabulary.vocabulary_crud.get_vocabulary_item", new=AsyncMock(return_value=None)):
            response = await no_auth_client.get(f"{BASE}/items/{VOCAB_ID}")
        assert response.status_code == 404
        assert "not found" in response.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_returns_item_when_found(self, no_auth_client: AsyncClient):
        mock_item = _make_mock_vocab_item()
        with patch("app.crud.vocabulary.vocabulary_crud.get_vocabulary_item", new=AsyncMock(return_value=mock_item)):
            response = await no_auth_client.get(f"{BASE}/items/{VOCAB_ID}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_422(self, no_auth_client: AsyncClient):
        response = await no_auth_client.get(f"{BASE}/items/not-a-uuid")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_does_not_require_auth(self, no_auth_client: AsyncClient):
        with patch("app.crud.vocabulary.vocabulary_crud.get_vocabulary_item", new=AsyncMock(return_value=None)):
            response = await no_auth_client.get(f"{BASE}/items/{VOCAB_ID}")
        assert response.status_code != 401


# ============================================================================
# GET /api/v1/vocabulary/collection  — User vocabulary collection (auth)
# ============================================================================

class TestGetUserCollection:
    """Tests for GET /api/v1/vocabulary/collection."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, no_auth_client: AsyncClient):
        response = await no_auth_client.get(f"{BASE}/collection")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_200_with_empty_collection(self, auth_client):
        client, _, _, _ = auth_client
        with patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary_list", new=AsyncMock(return_value=[])):
            response = await client.get(f"{BASE}/collection")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_has_items_and_total(self, auth_client):
        client, _, _, _ = auth_client
        with patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary_list", new=AsyncMock(return_value=[])):
            response = await client.get(f"{BASE}/collection")
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_total_comes_from_count_query(self, auth_client):
        client, _, _, _ = auth_client
        with patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary_list", new=AsyncMock(return_value=[])), \
             patch("app.crud.vocabulary.vocabulary_crud.count_user_vocabulary", new=AsyncMock(return_value=42)):
            response = await client.get(f"{BASE}/collection")
        assert response.status_code == 200
        assert response.json()["total"] == 42

    @pytest.mark.asyncio
    async def test_invalid_status_returns_400(self, auth_client):
        client, _, _, _ = auth_client
        with patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary_list", new=AsyncMock(return_value=[])):
            response = await client.get(f"{BASE}/collection?status=invalid_status")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_valid_status_learning_accepted(self, auth_client):
        client, _, _, _ = auth_client
        with patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary_list", new=AsyncMock(return_value=[])):
            response = await client.get(f"{BASE}/collection?status=learning")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_valid_status_mastered_accepted(self, auth_client):
        client, _, _, _ = auth_client
        with patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary_list", new=AsyncMock(return_value=[])):
            response = await client.get(f"{BASE}/collection?status=mastered")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_limit_100_is_accepted(self, auth_client):
        client, _, _, _ = auth_client
        with patch(
            "app.crud.vocabulary.vocabulary_crud.get_user_vocabulary_list",
            new=AsyncMock(return_value=[]),
        ):
            response = await client.get(f"{BASE}/collection?limit=100")
        assert response.status_code == 200
        assert response.json()["limit"] == 100

    @pytest.mark.asyncio
    async def test_limit_above_1000_is_rejected(self, auth_client):
        client, _, _, _ = auth_client
        response = await client.get(f"{BASE}/collection?limit=1001")
        assert response.status_code == 422


# ============================================================================
# POST /api/v1/vocabulary/collection  — Add to collection (auth, query param)
# ============================================================================

class TestAddToCollection:
    """Tests for POST /api/v1/vocabulary/collection?vocabulary_id=<uuid>."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, no_auth_client: AsyncClient):
        response = await no_auth_client.post(
            f"{BASE}/collection", params={"vocabulary_id": VOCAB_ID}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_404_when_vocab_not_found(self, auth_client):
        client, _, _, _ = auth_client
        with patch("app.crud.vocabulary.vocabulary_crud.get_vocabulary_item", new=AsyncMock(return_value=None)):
            response = await client.post(
                f"{BASE}/collection", params={"vocabulary_id": VOCAB_ID}
            )
        assert response.status_code == 404
        assert "not found" in response.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_adds_to_collection_successfully(self, auth_client):
        client, _, _, _ = auth_client
        mock_item = _make_mock_vocab_item()
        mock_user_vocab = _make_mock_user_vocab()
        with patch("app.crud.vocabulary.vocabulary_crud.get_vocabulary_item", new=AsyncMock(return_value=mock_item)), \
             patch("app.crud.vocabulary.vocabulary_crud.add_to_collection", new=AsyncMock(return_value=mock_user_vocab)):
            response = await client.post(
                f"{BASE}/collection", params={"vocabulary_id": VOCAB_ID}
            )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_missing_vocabulary_id_returns_422(self, auth_client):
        client, _, _, _ = auth_client
        response = await client.post(f"{BASE}/collection")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_422(self, auth_client):
        client, _, _, _ = auth_client
        response = await client.post(
            f"{BASE}/collection", params={"vocabulary_id": "not-a-uuid"}
        )
        assert response.status_code == 422


# ============================================================================
# POST /api/v1/vocabulary/collection/quick-save  — Quick save (auth)
# ============================================================================

class TestQuickSaveToCollection:
    """Tests for POST /api/v1/vocabulary/collection/quick-save."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, no_auth_client: AsyncClient):
        response = await no_auth_client.post(
            f"{BASE}/collection/quick-save",
            json={"word": "consistency", "source_type": "lexi_chat"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_creates_new_vocab_item_when_missing(self, auth_client):
        client, _, _, _ = auth_client
        mock_vocab = _make_mock_vocab_item()
        mock_vocab.word = "consistency"
        mock_user_vocab = _make_mock_user_vocab()

        with patch("app.crud.vocabulary.vocabulary_crud.find_vocabulary_by_word", new=AsyncMock(return_value=None)), \
             patch("app.crud.vocabulary.vocabulary_crud.create_vocabulary_item", new=AsyncMock(return_value=mock_vocab)), \
             patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary", new=AsyncMock(return_value=None)), \
             patch("app.crud.vocabulary.vocabulary_crud.add_to_collection", new=AsyncMock(return_value=mock_user_vocab)):
            response = await client.post(
                f"{BASE}/collection/quick-save",
                json={
                    "word": "Consistency",
                    "source_type": "news",
                    "source_reference": "article_123",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["created_new_item"] is True
        assert data["already_in_collection"] is False
        assert "user_vocabulary" in data
        assert "vocabulary" in data

    @pytest.mark.asyncio
    async def test_uses_existing_item_when_already_in_collection(self, auth_client):
        client, _, _, _ = auth_client
        mock_vocab = _make_mock_vocab_item()
        mock_vocab.word = "curiosity"
        mock_user_vocab = _make_mock_user_vocab()

        mock_add = AsyncMock(return_value=mock_user_vocab)
        with patch("app.crud.vocabulary.vocabulary_crud.find_vocabulary_by_word", new=AsyncMock(return_value=mock_vocab)), \
             patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary", new=AsyncMock(return_value=mock_user_vocab)), \
             patch("app.crud.vocabulary.vocabulary_crud.add_to_collection", new=mock_add):
            response = await client.post(
                f"{BASE}/collection/quick-save",
                json={"word": "curiosity", "source_type": "topic_chat"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["created_new_item"] is False
        assert data["already_in_collection"] is True
        mock_add.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejects_blank_word(self, auth_client):
        client, _, _, _ = auth_client
        response = await client.post(
            f"{BASE}/collection/quick-save",
            json={"word": "   "},
        )
        assert response.status_code == 422


# ============================================================================
# POST /api/v1/vocabulary/collection/bulk  — Bulk add to collection (auth)
# ============================================================================

class TestBulkAddToCollection:
    """Tests for POST /api/v1/vocabulary/collection/bulk."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, no_auth_client: AsyncClient):
        payload = {"vocabulary_ids": [VOCAB_ID]}
        response = await no_auth_client.post(f"{BASE}/collection/bulk", json=payload)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_valid_ids(self, auth_client):
        client, _, _, _ = auth_client
        # All IDs are invalid (not found), so they are skipped
        with patch(
            "app.crud.vocabulary.vocabulary_crud.bulk_add_to_collection",
            new=AsyncMock(return_value=[]),
        ):
            response = await client.post(
                f"{BASE}/collection/bulk",
                json={"vocabulary_ids": [VOCAB_ID]},
            )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_bulk_adds_valid_items(self, auth_client):
        client, _, _, _ = auth_client
        mock_user_vocab = _make_mock_user_vocab()
        with patch(
            "app.crud.vocabulary.vocabulary_crud.bulk_add_to_collection",
            new=AsyncMock(return_value=[mock_user_vocab]),
        ):
            response = await client.post(
                f"{BASE}/collection/bulk",
                json={"vocabulary_ids": [VOCAB_ID]},
            )
        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_missing_body_returns_422(self, auth_client):
        client, _, _, _ = auth_client
        response = await client.post(f"{BASE}/collection/bulk", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_more_than_200_ids(self, auth_client):
        client, _, _, _ = auth_client
        response = await client.post(
            f"{BASE}/collection/bulk",
            json={"vocabulary_ids": [str(uuid.uuid4()) for _ in range(201)]},
        )
        assert response.status_code == 422


# ============================================================================
# GET /api/v1/vocabulary/due  — Due for review (auth)
# ============================================================================


class TestEvaluatePronunciation:
    """Tests for POST /api/v1/vocabulary/pronunciation/evaluate."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, no_auth_client: AsyncClient):
        response = await no_auth_client.post(
            f"{BASE}/pronunciation/evaluate",
            data={"vocabulary_id": VOCAB_ID},
            files={"audio": ("recording.wav", b"audio-bytes", "audio/wav")},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_maps_ai_score_to_feedback(self, auth_client):
        client, _, _, _ = auth_client
        mock_item = _make_mock_vocab_item()
        ai_response = {
            "overall_score": 84.5,
            "transcription": "hello",
            "phoneme_scores": {"overall_confidence": 0.91},
            "errors": [],
            "duration_ms": 42.0,
        }

        with patch("app.crud.vocabulary.vocabulary_crud.get_vocabulary_item", new=AsyncMock(return_value=mock_item)), \
             patch("app.routes.vocabulary.AIServiceClient.assess_pronunciation", new=AsyncMock(return_value=ai_response)):
            response = await client.post(
                f"{BASE}/pronunciation/evaluate",
                data={"vocabulary_id": VOCAB_ID},
                files={"audio": ("recording.wav", b"audio-bytes", "audio/wav")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 84.5
        assert data["stars"] == 3
        assert data["feedback_label"] == "Amazing"

    @pytest.mark.asyncio
    async def test_returns_404_when_vocabulary_missing(self, auth_client):
        client, _, _, _ = auth_client
        with patch("app.crud.vocabulary.vocabulary_crud.get_vocabulary_item", new=AsyncMock(return_value=None)):
            response = await client.post(
                f"{BASE}/pronunciation/evaluate",
                data={"vocabulary_id": VOCAB_ID},
                files={"audio": ("recording.wav", b"audio-bytes", "audio/wav")},
            )

        assert response.status_code == 404

class TestGetDueVocabulary:
    """Tests for GET /api/v1/vocabulary/due."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, no_auth_client: AsyncClient):
        response = await no_auth_client.get(f"{BASE}/due")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_200_with_no_due_items(self, auth_client):
        client, _, _, _ = auth_client
        with patch("app.crud.vocabulary.vocabulary_crud.get_due_vocabulary", new=AsyncMock(return_value=[])), \
             patch("app.crud.vocabulary.vocabulary_crud.count_due_vocabulary", new=AsyncMock(return_value=0)):
            response = await client.get(f"{BASE}/due")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_has_required_fields(self, auth_client):
        client, _, _, _ = auth_client
        with patch("app.crud.vocabulary.vocabulary_crud.get_due_vocabulary", new=AsyncMock(return_value=[])), \
             patch("app.crud.vocabulary.vocabulary_crud.count_due_vocabulary", new=AsyncMock(return_value=0)):
            response = await client.get(f"{BASE}/due")
        data = response.json()
        assert "items" in data
        assert "total_due" in data
        assert "daily_target" in data
        assert "progress_percentage" in data

    @pytest.mark.asyncio
    async def test_limit_param_accepted(self, auth_client):
        client, _, _, _ = auth_client
        with patch("app.crud.vocabulary.vocabulary_crud.get_due_vocabulary", new=AsyncMock(return_value=[])), \
             patch("app.crud.vocabulary.vocabulary_crud.count_due_vocabulary", new=AsyncMock(return_value=0)):
            response = await client.get(f"{BASE}/due?limit=10")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_limit_max_is_50(self, auth_client):
        client, _, _, _ = auth_client
        response = await client.get(f"{BASE}/due?limit=51")
        assert response.status_code == 422


# ============================================================================
# POST /api/v1/vocabulary/review/{id}  — Submit review (auth)
# ============================================================================

class TestSubmitReview:
    """Tests for POST /api/v1/vocabulary/review/{user_vocabulary_id}."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, no_auth_client: AsyncClient):
        response = await no_auth_client.post(
            f"{BASE}/review/{USER_VOCAB_ID}", json={"quality": 4, "time_spent_ms": 2000}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, auth_client):
        client, mock_session, mock_result, _ = auth_client
        mock_result.scalar_one_or_none.return_value = None
        with patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary", new=AsyncMock(return_value=None)):
            response = await client.post(
                f"{BASE}/review/{USER_VOCAB_ID}",
                json={"quality": 4, "time_spent_ms": 2000},
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_403_when_wrong_user(self, auth_client):
        client, mock_session, mock_result, mock_user = auth_client
        mock_user_vocab = _make_mock_user_vocab()
        mock_user_vocab.user_id = "00000000-0000-0000-0000-999999999999"  # different user
        mock_result.scalar_one_or_none.return_value = mock_user_vocab
        with patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary", new=AsyncMock(return_value=None)):
            response = await client.post(
                f"{BASE}/review/{USER_VOCAB_ID}",
                json={"quality": 4, "time_spent_ms": 2000},
            )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_submits_review_successfully(self, auth_client):
        client, mock_session, mock_result, mock_user = auth_client
        mock_user_vocab = _make_mock_user_vocab()
        mock_user_vocab.user_id = mock_user.id

        # The route runs two queries: the UserVocabulary it is reviewing, then
        # today's DailyActivity. Returning one mock for both handed the route a
        # DailyActivity whose xp_earned was a MagicMock, and the route used to
        # carry an `isinstance(..., Mock)` branch in production to survive it.
        # A real DailyActivity keeps the arithmetic honest.
        # Three queries now: the UserVocabulary, today's DailyActivity, and the
        # weekly LeaderboardEntry that record_daily_activity credits.
        mock_result.scalar_one_or_none.side_effect = [
            mock_user_vocab,
            DailyActivity(
                user_id=mock_user.id,
                activity_date=date.today(),
                xp_earned=10,
                daily_goal_xp=20,
                vocabulary_reviewed=1,
                daily_goal_met=False,
            ),
            None,
        ]

        updated_vocab = _make_mock_user_vocab()
        updated_vocab.streak = 1
        updated_vocab.interval = 3

        with patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary", new=AsyncMock(return_value=None)), \
             patch("app.crud.vocabulary.vocabulary_crud.submit_review", new=AsyncMock(return_value=updated_vocab)), \
             patch("app.services.check_achievements_for_user", new=AsyncMock(return_value=[])):
            response = await client.post(
                f"{BASE}/review/{USER_VOCAB_ID}",
                json={"quality": 4, "time_spent_ms": 2000},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_quality_returns_422(self, auth_client):
        client, _, _, _ = auth_client
        response = await client.post(
            f"{BASE}/review/{USER_VOCAB_ID}", json={"time_spent_ms": 2000}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_422(self, auth_client):
        client, _, _, _ = auth_client
        response = await client.post(
            f"{BASE}/review/not-a-uuid", json={"quality": 3, "time_spent_ms": 1000}
        )
        assert response.status_code == 422


# ============================================================================
# GET /api/v1/vocabulary/stats  — Vocabulary stats (auth)
# ============================================================================

class TestGetVocabularyStats:
    """Tests for GET /api/v1/vocabulary/stats."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, no_auth_client: AsyncClient):
        response = await no_auth_client.get(f"{BASE}/stats")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_200(self, auth_client):
        client, _, _, _ = auth_client
        mock_stats = {
            "total": 10,
            "learning": 5,
            "reviewing": 3,
            "mastered": 2,
            "due_for_review": 1,
            "total_xp": 50,
            "best_streak": 7,
        }
        with patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary_stats", new=AsyncMock(return_value=mock_stats)):
            response = await client.get(f"{BASE}/stats")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_has_total_words(self, auth_client):
        client, _, _, _ = auth_client
        mock_stats = {
            "total": 10,
            "learning": 5,
            "reviewing": 3,
            "mastered": 2,
            "due_for_review": 1,
            "total_xp": 50,
            "best_streak": 7,
        }
        with patch("app.crud.vocabulary.vocabulary_crud.get_user_vocabulary_stats", new=AsyncMock(return_value=mock_stats)):
            response = await client.get(f"{BASE}/stats")
        data = response.json()
        assert "total" in data


# ============================================================================
# POST /api/v1/vocabulary/decks  — Create deck (auth, query params)
# ============================================================================

class TestCreateDeck:
    """Tests for POST /api/v1/vocabulary/decks?name=<name>."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, no_auth_client: AsyncClient):
        response = await no_auth_client.post(
            f"{BASE}/decks", params={"name": "Travel Phrases"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_name_returns_422(self, auth_client):
        client, _, _, _ = auth_client
        response = await client.post(f"{BASE}/decks")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_creates_deck_successfully(self, auth_client):
        client, _, _, _ = auth_client
        mock_deck = MagicMock()
        mock_deck.id = uuid.UUID("00000000-0000-0000-0000-000000000070")
        mock_deck.name = "Travel Phrases"
        mock_deck.description = "Words for travel"
        mock_deck.color = "#2196F3"
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.user_id = "00000000-0000-0000-0000-000000000001"
        mock_deck.word_count = 0
        with patch("app.crud.vocabulary.vocabulary_crud.create_deck", new=AsyncMock(return_value=mock_deck)):
            response = await client.post(
                f"{BASE}/decks",
                params={"name": "Travel Phrases", "description": "Words for travel"},
            )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_name_max_length_100(self, auth_client):
        """Name exceeding 100 chars fails validation."""
        client, _, _, _ = auth_client
        long_name = "A" * 101
        response = await client.post(f"{BASE}/decks", params={"name": long_name})
        assert response.status_code == 422


# ============================================================================
# GET /api/v1/vocabulary/decks  — List decks (auth)
# ============================================================================

class TestGetUserDecks:
    """Tests for GET /api/v1/vocabulary/decks."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, no_auth_client: AsyncClient):
        response = await no_auth_client.get(f"{BASE}/decks")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_200_with_empty_list(self, auth_client):
        client, _, _, _ = auth_client
        with patch("app.crud.vocabulary.vocabulary_crud.get_user_decks", new=AsyncMock(return_value=[])):
            response = await client.get(f"{BASE}/decks")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_user_decks(self, auth_client):
        client, _, _, _ = auth_client
        mock_deck = MagicMock()
        mock_deck.id = uuid.UUID("00000000-0000-0000-0000-000000000070")
        mock_deck.name = "Travel Phrases"
        mock_deck.description = "Words for travel"
        mock_deck.color = "#2196F3"
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.user_id = "00000000-0000-0000-0000-000000000001"
        mock_deck.word_count = 5
        with patch("app.crud.vocabulary.vocabulary_crud.get_user_decks", new=AsyncMock(return_value=[mock_deck])):
            response = await client.get(f"{BASE}/decks")
        assert response.status_code == 200


class TestGetWordOfDay:
    """GET /vocabulary/word-of-day — public, no auth.

    Regression coverage for a real production 500: build_cache_key(prefix,
    **params) was called with a positional date arg instead of a keyword,
    raising TypeError before the DB was ever touched. No test exercised
    this route at all, so it shipped and only surfaced live.
    """

    @pytest.fixture
    async def word_of_day_client(self):
        from app.main import app
        from app.core.database import get_db

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        item_result = MagicMock()
        item_result.scalar_one_or_none.return_value = _make_mock_vocab_item()

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(side_effect=[count_result, item_result])

        async def mock_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = mock_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_returns_a_word(self, word_of_day_client):
        response = await word_of_day_client.get(f"{BASE}/word-of-day")
        assert response.status_code == 200
        assert response.json()["word"] == "hello"

    @pytest.mark.asyncio
    async def test_404_when_no_vocabulary_exists(self):
        from app.main import app
        from app.core.database import get_db

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=count_result)

        async def mock_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = mock_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"{BASE}/word-of-day")
        app.dependency_overrides.clear()
        assert response.status_code == 404



class TestVocabularyCatalogMultiPagePagination:
    """Multi-page deterministic pagination tests against isolated test DB."""

    @pytest.mark.asyncio
    async def test_items_pagination_across_multiple_pages_no_duplicates_or_skips(
        self, async_client: AsyncClient, db_session
    ):
        from app.models.vocabulary import DifficultyLevel, PartOfSpeech, VocabularyItem

        fixed_created = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
        words = [f"catalog_{i:02d}" for i in range(7)]
        for word in words:
            db_session.add(
                VocabularyItem(
                    word=word,
                    definition=f"Definition for {word}",
                    part_of_speech=PartOfSpeech.NOUN,
                    difficulty_level=DifficultyLevel.A2,
                    usage_frequency=100,
                    tags=["travel"],
                    created_at=fixed_created,
                )
            )
        await db_session.commit()

        seen: list[str] = []
        for offset in (0, 3, 6):
            res = await async_client.get(f"{BASE}/items?limit=3&offset={offset}")
            assert res.status_code == 200
            seen.extend(item["word"] for item in res.json())

        assert len(seen) == 7
        assert len(set(seen)) == 7
        assert set(seen) == set(words)

    @pytest.mark.asyncio
    async def test_items_search_supports_offset_and_cefr_filter(
        self, async_client: AsyncClient, db_session
    ):
        from app.models.vocabulary import DifficultyLevel, PartOfSpeech, VocabularyItem

        for idx, level in enumerate(
            [
                DifficultyLevel.B1,
                DifficultyLevel.B1,
                DifficultyLevel.B1,
                DifficultyLevel.A1,
                DifficultyLevel.B1,
            ]
        ):
            db_session.add(
                VocabularyItem(
                    word=f"spark_{idx}",
                    definition=f"Meaning {idx}",
                    part_of_speech=PartOfSpeech.VERB,
                    difficulty_level=level,
                    tags=["science"],
                )
            )
        await db_session.commit()

        page1 = await async_client.get(
            f"{BASE}/items?search=spark_&difficulty_level=B1&limit=2&offset=0"
        )
        page2 = await async_client.get(
            f"{BASE}/items?search=spark_&difficulty_level=B1&limit=2&offset=2"
        )
        assert page1.status_code == 200
        assert page2.status_code == 200
        w1 = [item["word"] for item in page1.json()]
        w2 = [item["word"] for item in page2.json()]
        assert len(w1) == 2
        assert len(w2) == 2
        assert set(w1).isdisjoint(set(w2))
        assert set(w1 + w2) == {"spark_0", "spark_1", "spark_2", "spark_4"}

    @pytest.mark.asyncio
    async def test_collection_pagination_with_tied_added_at_and_exact_has_more(
        self, async_client: AsyncClient, auth_headers: dict, db_session, test_user
    ):
        from app.models.vocabulary import (
            DifficultyLevel,
            PartOfSpeech,
            UserVocabulary,
            VocabularyItem,
        )

        test_user.has_seeded_basic_words = True
        db_session.add(test_user)

        same_time = datetime(2026, 11, 1, 10, 0, tzinfo=UTC)
        created_words = [f"coll_{i}" for i in range(4)]
        for word in created_words:
            vocab = VocabularyItem(
                word=word,
                definition=f"Def {word}",
                part_of_speech=PartOfSpeech.NOUN,
                difficulty_level=DifficultyLevel.A1,
            )
            db_session.add(vocab)
            await db_session.flush()
            db_session.add(
                UserVocabulary(
                    user_id=test_user.id,
                    vocabulary_id=vocab.id,
                    added_at=same_time,
                )
            )
        await db_session.commit()

        p1 = await async_client.get(
            f"{BASE}/collection?limit=2&offset=0", headers=auth_headers
        )
        p2 = await async_client.get(
            f"{BASE}/collection?limit=2&offset=2", headers=auth_headers
        )
        assert p1.status_code == 200
        assert p2.status_code == 200
        d1, d2 = p1.json(), p2.json()
        assert d1["total"] == 4
        assert d1["has_more"] is True
        assert d2["has_more"] is False
        words1 = [x["vocabulary"]["word"] for x in d1["items"]]
        words2 = [x["vocabulary"]["word"] for x in d2["items"]]
        assert len(words1) == 2 and len(words2) == 2
        assert set(words1).isdisjoint(set(words2))
        assert set(words1 + words2) == set(created_words)


class TestVocabularyTopicTaxonomyAndFilters:
    """T03 regression tests for canonical topic taxonomy and level/tag filtering."""

    def test_canonical_topics_match_ui_and_aliases(self):
        from app.services.vocabulary_catalog_policy import (
            CANONICAL_TOPICS,
            canonical_topic,
        )

        assert CANONICAL_TOPICS == (
            "general",
            "travel",
            "business",
            "daily",
            "science",
            "technology",
        )
        assert canonical_topic("daily_life") == "daily"
        assert canonical_topic("daily-life") == "daily"
        assert canonical_topic(" daily life ") == "daily"
        assert canonical_topic(" Travel ") == "travel"

    @pytest.mark.asyncio
    async def test_items_filter_level_only_topic_only_and_combined(
        self, async_client: AsyncClient, db_session
    ):
        from app.models.vocabulary import DifficultyLevel, PartOfSpeech, VocabularyItem

        seed_rows = [
            ("t03_gen", DifficultyLevel.A1, ["general"]),
            ("t03_trv", DifficultyLevel.A2, ["travel"]),
            ("t03_biz", DifficultyLevel.B1, {"topic": "business"}),
            ("t03_dly1", DifficultyLevel.B1, ["daily"]),
            ("t03_dly2", DifficultyLevel.B1, {"topic": "daily_life"}),
            ("t03_dly3", DifficultyLevel.A1, ["daily-life"]),
            ("t03_sci", DifficultyLevel.B2, ["science"]),
            ("t03_tec", DifficultyLevel.C1, ["technology"]),
        ]
        for word, level, tags in seed_rows:
            db_session.add(
                VocabularyItem(
                    word=word,
                    definition=f"Valid definition for {word}",
                    part_of_speech=PartOfSpeech.NOUN,
                    difficulty_level=level,
                    tags=tags,
                )
            )
        await db_session.commit()

        # Level-only (case-insensitive normalization)
        lvl_res = await async_client.get(f"{BASE}/items?difficulty_level=b1")
        assert lvl_res.status_code == 200
        assert {item["word"] for item in lvl_res.json()} == {
            "t03_biz",
            "t03_dly1",
            "t03_dly2",
        }

        # Topic-only with alias
        tag_res = await async_client.get(f"{BASE}/items?tag=daily_life")
        assert tag_res.status_code == 200
        assert {item["word"] for item in tag_res.json()} == {
            "t03_dly1",
            "t03_dly2",
            "t03_dly3",
        }
        assert all(item["tags"] == ["daily"] for item in tag_res.json())

        # Combined level + topic + search
        combo_res = await async_client.get(
            f"{BASE}/items?search=t03_&difficulty_level=b1&tag=daily-life"
        )
        assert combo_res.status_code == 200
        assert {item["word"] for item in combo_res.json()} == {
            "t03_dly1",
            "t03_dly2",
        }

    @pytest.mark.asyncio
    async def test_items_invalid_difficulty_level_returns_422(
        self, async_client: AsyncClient
    ):
        response = await async_client.get(f"{BASE}/items?difficulty_level=invalid")
        assert response.status_code == 422


class TestVocabularyT04ReviewIdempotencyFlow:
    """T04 integration tests for due -> review -> retry idempotency -> stats."""

    @pytest.mark.asyncio
    async def test_due_review_retry_idempotency_and_stats(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session,
        test_user,
    ):
        from sqlalchemy import func, select

        from app.models.games import XPTransaction
        from app.models.vocabulary import (
            DifficultyLevel,
            PartOfSpeech,
            UserVocabulary,
            VocabularyItem,
            VocabularyReview,
        )

        test_user.has_seeded_basic_words = True
        initial_xp = test_user.total_xp or 0
        db_session.add(test_user)

        vocab = VocabularyItem(
            word="t04_resilient",
            definition="Able to recover quickly from setbacks.",
            part_of_speech=PartOfSpeech.ADJECTIVE,
            difficulty_level=DifficultyLevel.B2,
            tags={"topic": ["general"], "qa_status": "NEEDS_REVIEW"},
        )
        db_session.add(vocab)
        await db_session.flush()

        user_vocab = UserVocabulary(
            user_id=test_user.id,
            vocabulary_id=vocab.id,
            next_review_date=datetime.now(UTC) - timedelta(hours=1),
        )
        db_session.add(user_vocab)
        await db_session.commit()

        # 1. Verify due list includes the item
        due_before = await async_client.get(f"{BASE}/due?limit=20", headers=auth_headers)
        assert due_before.status_code == 200
        assert due_before.json()["total_due"] >= 1
        assert any(
            item["id"] == str(user_vocab.id)
            for item in due_before.json()["items"]
        )

        # 2. Submit review with idempotency_key
        idem_key = f"t04-idem-{uuid.uuid4()}"
        first_res = await async_client.post(
            f"{BASE}/review/{user_vocab.id}",
            headers=auth_headers,
            json={
                "quality": 4,
                "time_spent_ms": 1800,
                "idempotency_key": idem_key,
            },
        )
        assert first_res.status_code == 200
        first_data = first_res.json()
        assert first_data["xp_awarded"] == 13  # 5 + 4*2 + 0
        assert first_data["next_review_in_days"] >= 1
        assert first_data["user_vocabulary"]["total_reviews"] == 1

        # 3. Retry identical request (network retry) — must NOT double XP or reviews
        retry_res = await async_client.post(
            f"{BASE}/review/{user_vocab.id}",
            headers=auth_headers,
            json={
                "quality": 4,
                "time_spent_ms": 1800,
                "idempotency_key": idem_key,
            },
        )
        assert retry_res.status_code == 200
        assert retry_res.json() == first_data

        # 4. Verify DB counts & user XP incremented exactly once
        await db_session.refresh(test_user)
        assert test_user.total_xp == initial_xp + 13

        review_count = await db_session.scalar(
            select(func.count(VocabularyReview.id)).where(
                VocabularyReview.user_vocabulary_id == user_vocab.id
            )
        )
        xp_tx_count = await db_session.scalar(
            select(func.count(XPTransaction.id)).where(
                XPTransaction.user_id == test_user.id,
                XPTransaction.source == "vocab_review",
                XPTransaction.source_id == f"{user_vocab.id}:1",
            )
        )
        assert review_count == 1
        assert xp_tx_count == 1

        # 5. Stats reflect 1 review and due list no longer includes this scheduled item
        stats_res = await async_client.get(f"{BASE}/stats", headers=auth_headers)
        assert stats_res.status_code == 200
        assert stats_res.json()["total"] >= 1
        assert stats_res.json()["due_for_review"] == 0

        due_after = await async_client.get(f"{BASE}/due?limit=20", headers=auth_headers)
        assert due_after.status_code == 200
        assert all(
            item["id"] != str(user_vocab.id)
            for item in due_after.json()["items"]
        )
