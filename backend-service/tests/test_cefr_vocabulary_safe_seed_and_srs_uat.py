"""Isolated PostgreSQL UAT tests for idempotent CEFR 180-word seed, multi-topic filtering, and SRS 1-4 ratings."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cefr_vocabulary_data import (
    PROVENANCE_AI_GENERATED,
    QA_STATUS_NEEDS_REVIEW,
    QA_STATUS_VERIFIED,
    get_cefr_audit_summary,
)
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.vocabulary import DifficultyLevel, PartOfSpeech, UserVocabulary, VocabularyItem
from scripts.seed_cefr_vocabulary import select_cefr_items, upsert_cefr_vocabulary


@pytest.mark.asyncio
class TestCefrVocabularySafeSeedAndSrsUat:
    async def test_idempotent_seed_preserves_extra_rows_and_user_vocabulary(
        self,
        db_session: AsyncSession,
        test_user: User,
    ) -> None:
        # Simulate pre-existing live-like legacy rows:
        # 1 CEFR word missing tags, 1 non-CEFR word, and 1 UserVocabulary link.
        legacy_cefr = VocabularyItem(
            id=uuid.uuid4(),
            word="family",
            definition="Old untagged definition",
            translation={"vi": "gia dinh"},
            part_of_speech=PartOfSpeech.NOUN,
            difficulty_level=DifficultyLevel.A1,
            tags=None,
        )
        legacy_custom = VocabularyItem(
            id=uuid.uuid4(),
            word="collaborate",
            definition="Work jointly with others.",
            translation={"vi": "hop tac"},
            part_of_speech=PartOfSpeech.VERB,
            difficulty_level=DifficultyLevel.B2,
            tags=None,
        )
        db_session.add_all([legacy_cefr, legacy_custom])
        await db_session.flush()

        existing_uv = UserVocabulary(
            id=uuid.uuid4(),
            user_id=test_user.id,
            vocabulary_id=legacy_custom.id,
        )
        db_session.add(existing_uv)
        await db_session.commit()

        # Run 1: updates 1 legacy CEFR row, creates 179 remaining CEFR rows, preserves 1 extra row.
        run1 = await upsert_cefr_vocabulary(db_session, only_verified=False)
        await db_session.commit()
        assert run1 == {
            "selected": 180,
            "created": 179,
            "updated": 1,
            "unchanged": 0,
            "preserved_non_cefr": 1,
        }

        total_vocab = await db_session.scalar(select(func.count(VocabularyItem.id)))
        assert total_vocab == 181

        # Existing custom word & user_vocabulary remain intact.
        kept_uv = await db_session.scalar(
            select(UserVocabulary).where(UserVocabulary.id == existing_uv.id)
        )
        assert kept_uv is not None

        # Run 2: strict no-op idempotency check.
        run2 = await upsert_cefr_vocabulary(db_session, only_verified=False)
        await db_session.commit()
        assert run2 == {
            "selected": 180,
            "created": 0,
            "updated": 0,
            "unchanged": 180,
            "preserved_non_cefr": 1,
        }

        # --only-verified returns 0 selected while items remain NEEDS_REVIEW.
        verified_only = await upsert_cefr_vocabulary(db_session, only_verified=True)
        assert verified_only["selected"] == 0

    async def test_multitopic_search_collection_srs_1_to_4_and_isolation(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ) -> None:
        stats = await upsert_cefr_vocabulary(db_session, only_verified=False)
        await db_session.commit()
        assert stats["created"] == 180

        # Draft/unverified NEEDS_REVIEW + CONFLICT/BLOCKED items must NOT leak to learner catalog
        pre_approve_items = await async_client.get("/api/v1/vocabulary/items?limit=100")
        assert pre_approve_items.status_code == 200
        assert pre_approve_items.json() == []

        # Inside isolated lexilingo_test only: simulate editorial verification of all CONFIRMED_SOURCE rows
        # (and test synthetic clearance for the remaining test fixture rows) so we can verify
        # multi-topic filtering, pagination, collection, and SRS 1-4 transitions on published items.
        all_rows = (await db_session.execute(select(VocabularyItem))).scalars().all()
        for row in all_rows:
            tags = dict(row.tags or {})
            tags["qa_status"] = QA_STATUS_VERIFIED
            tags["source_reference"] = "lexilingo_test_editorial_fixture"
            if tags.get("audit_status") in {"CONFLICT", "BLOCKED"}:
                tags["audit_status"] = "CONFIRMED_SOURCE"
            row.tags = tags
        await db_session.commit()

        # 1. Multi-topic canonical filtering: "airport" appears under BOTH travel & business.
        travel_res = await async_client.get(
            "/api/v1/vocabulary/items?tag=travel&difficulty_level=A2&limit=50"
        )
        business_res = await async_client.get(
            "/api/v1/vocabulary/items?tag=business&difficulty_level=A2&limit=50"
        )
        assert travel_res.status_code == 200
        assert business_res.status_code == 200
        travel_words = {row["word"] for row in travel_res.json()}
        business_words = {row["word"] for row in business_res.json()}
        assert "airport" in travel_words
        assert "airport" in business_words

        # 2. Combined topic + level + search narrows cleanly.
        search_res = await async_client.get(
            "/api/v1/vocabulary/items?tag=science&difficulty_level=C2&search=serendipity"
        )
        assert search_res.status_code == 200
        rows = search_res.json()
        assert len(rows) == 1
        assert rows[0]["word"] == "serendipity"
        assert "science" in rows[0]["tags"]
        assert "general" in rows[0]["tags"]
        vocab_id = rows[0]["id"]

        # 3. Pagination across all 180 seeded items has zero duplicates.
        seen_ids: set[str] = set()
        for offset in range(0, 180, 60):
            page = await async_client.get(
                f"/api/v1/vocabulary/items?limit=60&offset={offset}"
            )
            assert page.status_code == 200
            for item in page.json():
                seen_ids.add(item["id"])
        assert len(seen_ids) == 180

        # 4. Save to collection twice is idempotent (same UserVocabulary row returned).
        add1 = await async_client.post(
            "/api/v1/vocabulary/collection",
            headers=auth_headers,
            params={"vocabulary_id": vocab_id},
        )
        add2 = await async_client.post(
            "/api/v1/vocabulary/collection",
            headers=auth_headers,
            params={"vocabulary_id": vocab_id},
        )
        assert add1.status_code == 201
        assert add2.status_code == 201
        uv_id = add1.json()["id"]
        assert add2.json()["id"] == uv_id

        # Make due now and exercise Again (1) -> keeps card learnable -> Good (3) -> advances schedule.
        uv_row = await db_session.scalar(
            select(UserVocabulary).where(UserVocabulary.id == uuid.UUID(uv_id))
        )
        assert uv_row is not None
        uv_row.next_review_date = datetime.now(UTC) - timedelta(minutes=10)
        await db_session.commit()

        due_before = await async_client.get(
            "/api/v1/vocabulary/due?limit=20", headers=auth_headers
        )
        assert due_before.status_code == 200
        assert uv_id in [item["id"] for item in due_before.json()["items"]]

        # Again (quality=1): wrong recall keeps interval short / resets repetitions.
        again_res = await async_client.post(
            f"/api/v1/vocabulary/review/{uv_id}",
            headers={**auth_headers, "Idempotency-Key": f"again-{uuid.uuid4()}"},
            json={"quality": 1, "time_spent_ms": 900},
        )
        assert again_res.status_code == 200
        again_payload = again_res.json()
        assert again_payload["user_vocabulary"]["total_reviews"] == 1
        assert again_payload["user_vocabulary"]["repetitions"] == 0

        # Good (quality=3): advances repetitions & pushes next_review_date into future.
        good_res = await async_client.post(
            f"/api/v1/vocabulary/review/{uv_id}",
            headers={**auth_headers, "Idempotency-Key": f"good-{uuid.uuid4()}"},
            json={"quality": 3, "time_spent_ms": 1100},
        )
        assert good_res.status_code == 200
        good_payload = good_res.json()
        assert good_payload["user_vocabulary"]["total_reviews"] == 2
        assert good_payload["next_review_in_days"] >= 1
        next_due = datetime.fromisoformat(
            good_payload["user_vocabulary"]["next_review_date"].replace("Z", "+00:00")
        )
        assert next_due > datetime.now(UTC)

        # Due queue no longer lists the reviewed card once next_review_date is future.
        due_after = await async_client.get(
            "/api/v1/vocabulary/due?limit=20", headers=auth_headers
        )
        assert due_after.status_code == 200
        assert uv_id not in [item["id"] for item in due_after.json()["items"]]

        # 5. Cross-user isolation: another user cannot review test_user's card.
        other_user = User(
            id=uuid.uuid4(),
            email="other.vocab@example.com",
            username="other_vocab_user",
            hashed_password=get_password_hash("TestPass123!"),
            is_active=True,
            is_verified=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        other_token = create_access_token({"sub": str(other_user.id)})
        forbidden = await async_client.post(
            f"/api/v1/vocabulary/review/{uv_id}",
            headers={"Authorization": f"Bearer {other_token}"},
            json={"quality": 4},
        )
        assert forbidden.status_code in (403, 404)

    async def test_selective_confirmed_source_seed_is_idempotent_and_never_publishes_verified(
        self,
        db_session: AsyncSession,
    ) -> None:
        summary = get_cefr_audit_summary()
        confirmed_total = summary["TOTAL"]["CONFIRMED_SOURCE"]
        assert confirmed_total == 88
        assert summary["TOTAL"]["CONFLICT"] == 66
        assert summary["TOTAL"]["BLOCKED"] == 26

        # Non-CEFR custom word must remain untouched throughout selective & full imports.
        custom = VocabularyItem(
            id=uuid.uuid4(),
            word="ephemeral",
            definition="Lasting for a very short time.",
            translation={"vi": "phù du, ngắn ngủi"},
            part_of_speech=PartOfSpeech.ADJECTIVE,
            difficulty_level=DifficultyLevel.C2,
            tags={"topic": ["general"]},
        )
        db_session.add(custom)
        await db_session.commit()

        # Selective C2 confirmed-source preview matches the 6 verified-source C2 entries.
        c2_confirmed = select_cefr_items(only_confirmed_source=True, levels=["C2"])
        assert {item["word"] for item in c2_confirmed} == {
            "acquiesce",
            "apocryphal",
            "meticulous",
            "intransigent",
            "magnanimous",
            "zeitgeist",
        }

        # Run 1: selective CONFIRMED_SOURCE import only.
        sel_run1 = await upsert_cefr_vocabulary(
            db_session, only_confirmed_source=True
        )
        await db_session.commit()
        assert sel_run1 == {
            "selected": confirmed_total,
            "created": confirmed_total,
            "updated": 0,
            "unchanged": 0,
            "preserved_non_cefr": 1,
        }

        # Run 2: strict no-op idempotency on selective subset.
        sel_run2 = await upsert_cefr_vocabulary(
            db_session, only_confirmed_source=True
        )
        await db_session.commit()
        assert sel_run2 == {
            "selected": confirmed_total,
            "created": 0,
            "updated": 0,
            "unchanged": confirmed_total,
            "preserved_non_cefr": 1,
        }

        # Every seeded item keeps AI_GENERATED + NEEDS_REVIEW (0 VERIFIED).
        seeded_rows = (await db_session.execute(select(VocabularyItem))).scalars().all()
        assert len(seeded_rows) == confirmed_total + 1
        for row in seeded_rows:
            if row.word == "ephemeral":
                continue
            assert row.tags["source"] == PROVENANCE_AI_GENERATED
            assert row.tags["source_reference"] is None
            assert row.tags["qa_status"] == QA_STATUS_NEEDS_REVIEW
            assert row.tags["qa_status"] != QA_STATUS_VERIFIED

        # Expanding to full catalog adds only the remaining 92 CONFLICT+BLOCKED rows.
        full_run = await upsert_cefr_vocabulary(
            db_session, only_confirmed_source=False
        )
        await db_session.commit()
        assert full_run == {
            "selected": 180,
            "created": 180 - confirmed_total,
            "updated": 0,
            "unchanged": confirmed_total,
            "preserved_non_cefr": 1,
        }
