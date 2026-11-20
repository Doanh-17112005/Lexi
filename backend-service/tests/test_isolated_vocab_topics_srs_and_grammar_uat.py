"""Isolated PostgreSQL UAT suite for Task 2 (Vocab Topics/CEFR/Pagination/SRS) and Task 3 (Grammar Theory -> Practice & Roadmap Gate).

Runs strictly on the isolated test database (`lexilingo_test` via conftest.py)
and never touches live `lexilingo` records.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cefr_vocabulary_data import (
    CANONICAL_TOPICS,
    PROVENANCE_SOURCE_VERIFIED,
    QA_STATUS_VERIFIED,
    build_cefr_seed_tags,
)
from app.models.course import Course, Lesson, Unit
from app.models.gamification import Achievement, UserAchievement, UserWallet
from app.models.progress import UserCourseProgress
from app.models.user import User
from app.models.vocabulary import DifficultyLevel, PartOfSpeech, UserVocabulary, VocabularyItem
from scripts.backfill_achievements import ACHIEVEMENT_SEED, _cdn_badge_icon


@pytest.mark.asyncio
class TestIsolatedVocabularyTopicsSrsUAT:
    """Task 2: 6 topic cards, topic/CEFR filters, pagination, and SRS on isolated dataset."""

    async def test_six_topics_cefr_pagination_and_srs_idempotent(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        # Seed isolated test dataset spanning all 6 canonical topics & A1-C2 levels.
        test_specs = [
            ("alpha_general", "A1", "general", "A general starter term."),
            ("bravo_general", "B2", "general", "A general upper-intermediate term."),
            ("charlie_travel", "A2", "travel", "A ticket needed for boarding."),
            ("delta_travel", "C1", "travel", "A detailed itinerary plan."),
            ("echo_business", "B1", "business", "A quarterly budget summary."),
            ("foxtrot_business", "C2", "business", "A fiduciary board obligation."),
            ("golf_daily", "A1", "daily", "A routine morning habit."),
            ("hotel_daily", "B1", "daily", "An everyday household chore."),
            ("india_science", "B2", "science", "A repeatable laboratory hypothesis."),
            ("juliet_science", "C2", "science", "An empirical longitudinal study."),
            ("kilo_technology", "A2", "technology", "A wireless network adapter."),
            ("lima_technology", "C1", "technology", "An encrypted distributed ledger."),
        ]

        created_items: list[VocabularyItem] = []
        for idx, (word, level, topic, definition) in enumerate(test_specs):
            item = VocabularyItem(
                id=uuid.uuid4(),
                word=word,
                definition=definition,
                translation={"vi": f"nghia {word}", "examples": [f"Example sentence for {word}."]},
                pronunciation=f"/{word}/",
                difficulty_level=getattr(DifficultyLevel, level),
                part_of_speech=PartOfSpeech.NOUN,
                tags=build_cefr_seed_tags(
                    {
                        "word": word,
                        "provenance_type": PROVENANCE_SOURCE_VERIFIED,
                        "source_reference": "synthetic-test-fixture",
                        "qa_status": QA_STATUS_VERIFIED,
                        "audit_status": "CONFIRMED_SOURCE",
                        "topic": topic,
                    }
                ),
            )
            created_items.append(item)
        db_session.add_all(created_items)
        await db_session.commit()

        # 1. All 6 canonical topic cards return real matching records & normalized tags.
        for topic in CANONICAL_TOPICS:
            res = await async_client.get(
                f"/api/v1/vocabulary/items?tag={topic}&limit=50"
            )
            assert res.status_code == 200
            rows = res.json()
            assert len(rows) == 2
            for row in rows:
                assert topic in row["tags"]
                assert "verified" in row["tags"]

        # 2. Combined topic + CEFR filter narrows accurately.
        combo_res = await async_client.get(
            "/api/v1/vocabulary/items?tag=science&difficulty_level=C2"
        )
        assert combo_res.status_code == 200
        assert [r["word"] for r in combo_res.json()] == ["juliet_science"]

        # 3. Alphabetical pagination returns disjoint pages covering all 12 test items.
        p1 = await async_client.get("/api/v1/vocabulary/items?limit=4&offset=0")
        p2 = await async_client.get("/api/v1/vocabulary/items?limit=4&offset=4")
        p3 = await async_client.get("/api/v1/vocabulary/items?limit=4&offset=8")
        assert p1.status_code == p2.status_code == p3.status_code == 200
        words_p1 = [r["word"] for r in p1.json()]
        words_p2 = [r["word"] for r in p2.json()]
        words_p3 = [r["word"] for r in p3.json()]
        combined_words = words_p1 + words_p2 + words_p3
        assert len(combined_words) == 12
        assert len(set(combined_words)) == 12
        assert combined_words == sorted(w for w, *_ in test_specs)

        # 4. SRS Add -> Due -> Idempotent Review -> Schedule Advance (real DB).
        target_id = str(created_items[0].id)
        add_res = await async_client.post(
            "/api/v1/vocabulary/collection",
            headers=auth_headers,
            params={"vocabulary_id": target_id},
        )
        assert add_res.status_code in (200, 201)
        user_vocab_id = add_res.json()["id"]

        # Make the newly added card due now to verify real SRS due -> review -> cleared cycle
        uv_row = await db_session.scalar(
            select(UserVocabulary).where(UserVocabulary.id == uuid.UUID(user_vocab_id))
        )
        assert uv_row is not None
        uv_row.next_review_date = datetime.now(timezone.utc) - timedelta(minutes=5)
        await db_session.commit()

        due_res = await async_client.get(
            "/api/v1/vocabulary/due?limit=20",
            headers=auth_headers,
        )
        assert due_res.status_code == 200
        due_ids = [item["id"] for item in due_res.json()["items"]]
        assert user_vocab_id in due_ids

        xp_before = test_user.total_xp or 0
        idem_key = f"uat-srs-{uuid.uuid4()}"
        rev1 = await async_client.post(
            f"/api/v1/vocabulary/review/{user_vocab_id}",
            headers={**auth_headers, "Idempotency-Key": idem_key},
            json={"quality": 5, "time_spent_ms": 1400},
        )
        assert rev1.status_code == 200
        rev1_data = rev1.json()
        assert rev1_data["user_vocabulary"]["total_reviews"] == 1
        assert rev1_data["next_review_in_days"] >= 1
        next_due = datetime.fromisoformat(
            rev1_data["user_vocabulary"]["next_review_date"].replace("Z", "+00:00")
        )
        assert next_due > datetime.now(timezone.utc)

        due_after = await async_client.get(
            "/api/v1/vocabulary/due?limit=20",
            headers=auth_headers,
        )
        assert due_after.status_code == 200
        assert user_vocab_id not in [item["id"] for item in due_after.json()["items"]]

        # Replay same Idempotency-Key must NOT duplicate XP or review count.
        rev_replay = await async_client.post(
            f"/api/v1/vocabulary/review/{user_vocab_id}",
            headers={**auth_headers, "Idempotency-Key": idem_key},
            json={"quality": 5, "time_spent_ms": 1400},
        )
        assert rev_replay.status_code == 200
        assert rev_replay.json()["user_vocabulary"]["total_reviews"] == 1
        await db_session.refresh(test_user)
        expected_xp = xp_before + rev1_data["xp_awarded"] + rev1_data["streak_bonus"]
        assert (test_user.total_xp or 0) == expected_xp


@pytest.mark.asyncio
class TestIsolatedGrammarAndRoadmapUAT:
    """Task 3: Grammar Theory -> Practice, Roadmap Unlock Gate, no duplicate XP, reload persistence."""

    async def test_grammar_theory_roadmap_unlock_no_double_xp_and_reload(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        course = Course(
            id=uuid.uuid4(),
            title="Isolated Grammar & Roadmap UAT A2",
            description="Verified grammar + sequential unlock test course.",
            language="en",
            level="A2",
            is_published=True,
            total_lessons=2,
            total_xp=80,
        )
        db_session.add(course)
        await db_session.flush()

        unit = Unit(
            id=uuid.uuid4(),
            course_id=course.id,
            title="Unit 1: Subject-Verb Agreement & Practice",
            order_index=1,
            total_lessons=2,
        )
        db_session.add(unit)
        await db_session.flush()

        lesson1 = Lesson(
            id=uuid.uuid4(),
            course_id=course.id,
            unit_id=unit.id,
            title="Lesson 1: Present Simple Grammar",
            description="Third-person singular verbs",
            lesson_type="grammar",
            order_index=1,
            xp_reward=40,
            pass_threshold=50,
            estimated_minutes=10,
            content={
                "theory": {
                    "title": "Present Simple — 3rd Person Singular",
                    "explanation": "Add -s or -es to base verbs after he/she/it (Cambridge Dictionary).",
                    "examples": [
                        {"sentence": "She walks to school every morning."},
                        {"sentence": "He teaches English at a local school."},
                    ],
                },
                "exercises": [
                    {
                        "id": "uat-g1",
                        "type": "multiple_choice",
                        "question": "Choose the correct form: He ___ to work by bus.",
                        "options": ["goes", "go"],
                        "correct_answer": "goes",
                        "explanation": "With third-person singular subject 'He', 'go' takes '-es'.",
                    },
                    {
                        "id": "uat-g2",
                        "type": "multiple_choice",
                        "question": "She ___ coffee every morning.",
                        "options": ["drinks", "drink"],
                        "correct_answer": "drinks",
                        "explanation": "With 'She', add '-s' to 'drink'.",
                    },
                ],
            },
        )
        lesson2 = Lesson(
            id=uuid.uuid4(),
            course_id=course.id,
            unit_id=unit.id,
            title="Lesson 2: Daily Practice Checkpoint",
            description="Unlocked after Lesson 1",
            lesson_type="lesson",
            order_index=2,
            xp_reward=40,
            pass_threshold=50,
            estimated_minutes=8,
            content={
                "exercises": [
                    {
                        "id": "uat-p1",
                        "type": "multiple_choice",
                        "question": "They ___ English together.",
                        "options": ["study", "studies"],
                        "correct_answer": "study",
                        "explanation": "Plural subject 'They' uses base verb 'study'.",
                    }
                ]
            },
        )
        db_session.add_all([lesson1, lesson2])
        await db_session.commit()

        # Enroll & check initial Roadmap Unlock Gate
        enroll_res = await async_client.post(
            f"/api/v1/courses/{course.id}/enroll", headers=auth_headers
        )
        assert enroll_res.status_code in (200, 201)

        roadmap_1 = await async_client.get(
            f"/api/v1/learning/courses/{course.id}/roadmap", headers=auth_headers
        )
        assert roadmap_1.status_code == 200
        l_states_1 = roadmap_1.json()["data"]["units"][0]["lessons"]
        assert l_states_1[0]["is_locked"] is False
        assert l_states_1[1]["is_locked"] is True

        # Locked lesson 2 must reject direct start with HTTP 403
        locked_start = await async_client.post(
            f"/api/v1/learning/lessons/{lesson2.id}/start", headers=auth_headers
        )
        assert locked_start.status_code == 403

        # Theory -> Practice: fetch theory, record viewed (0 XP), start practice, complete
        xp_start = test_user.total_xp or 0
        content_res = await async_client.get(
            f"/api/v1/learning/lessons/{lesson1.id}/content", headers=auth_headers
        )
        assert content_res.status_code == 200
        assert "3rd Person Singular" in content_res.json()["data"]["grammar_theory"]["title"]

        viewed_res = await async_client.post(
            f"/api/v1/learning/lessons/{lesson1.id}/theory-viewed", headers=auth_headers
        )
        assert viewed_res.status_code == 200
        await db_session.refresh(test_user)
        assert (test_user.total_xp or 0) == xp_start

        start_l1 = await async_client.post(
            f"/api/v1/learning/lessons/{lesson1.id}/start", headers=auth_headers
        )
        assert start_l1.status_code == 200
        attempt_id = start_l1.json()["data"]["attempt_id"]

        for qid, ans in [("uat-g1", "goes"), ("uat-g2", "drinks")]:
            ans_res = await async_client.post(
                f"/api/v1/learning/attempts/{attempt_id}/answer",
                headers=auth_headers,
                json={
                    "question_id": qid,
                    "question_type": "multiple_choice",
                    "user_answer": ans,
                    "time_spent_ms": 900,
                },
            )
            assert ans_res.status_code == 200
            assert ans_res.json()["data"]["is_correct"] is True

        complete_res = await async_client.post(
            f"/api/v1/learning/attempts/{attempt_id}/complete", headers=auth_headers
        )
        assert complete_res.status_code == 200
        xp_earned = complete_res.json()["data"]["total_xp_earned"]
        assert xp_earned > 0

        await db_session.refresh(test_user)
        xp_after_complete = test_user.total_xp

        # Duplicate completion must fail (400) AND must not double XP
        dup_res = await async_client.post(
            f"/api/v1/learning/attempts/{attempt_id}/complete", headers=auth_headers
        )
        assert dup_res.status_code == 400
        await db_session.refresh(test_user)
        assert test_user.total_xp == xp_after_complete

        # Simulate reload by capturing IDs, clearing session identity map, and re-fetching
        course_id = course.id
        lesson2_id = lesson2.id
        user_id = test_user.id
        db_session.expire_all()

        roadmap_reloaded = await async_client.get(
            f"/api/v1/learning/courses/{course_id}/roadmap", headers=auth_headers
        )
        assert roadmap_reloaded.status_code == 200
        l_states_reloaded = roadmap_reloaded.json()["data"]["units"][0]["lessons"]
        assert l_states_reloaded[0]["is_completed"] is True
        assert l_states_reloaded[1]["is_locked"] is False

        course_reloaded = await async_client.get(
            f"/api/v1/courses/{course_id}", headers=auth_headers
        )
        assert course_reloaded.status_code == 200
        assert course_reloaded.json()["data"]["user_progress"] == pytest.approx(50.0)

        prog_row = await db_session.scalar(
            select(UserCourseProgress).where(
                UserCourseProgress.user_id == user_id,
                UserCourseProgress.course_id == course_id,
            )
        )
        assert prog_row is not None
        assert prog_row.lessons_completed == 1

        # Lesson 2 is now unlocked and startable
        start_l2 = await async_client.post(
            f"/api/v1/learning/lessons/{lesson2_id}/start", headers=auth_headers
        )
        assert start_l2.status_code == 200


@pytest.mark.asyncio
class TestIsolatedAchievementUnlockAndNoDoubleReward:
    """Step 3 (#3 & #4): Backfilled 48 achievements unlock cleanly once without duplicate Gems/XP."""

    async def test_achievement_backfill_unlock_once_no_duplicate_gems_or_xp(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        for item in ACHIEVEMENT_SEED:
            db_session.add(
                Achievement(**item, badge_icon=_cdn_badge_icon(item["slug"]))
            )
        await db_session.commit()

        # Verify public catalog returns all 48 real seeded definitions
        list_res = await async_client.get("/api/v1/gamification/achievements")
        assert list_res.status_code == 200
        assert len(list_res.json()["data"]) == 48

        # Give test_user 1 completed lesson -> eligible for "First Steps" (lessons=1, gems=5)
        course = Course(
            id=uuid.uuid4(),
            title="Ach Test Course",
            description="Achievement check",
            language="en",
            level="A1",
            is_published=True,
            total_lessons=1,
            total_xp=20,
        )
        db_session.add(course)
        await db_session.flush()
        db_session.add(
            UserCourseProgress(
                id=uuid.uuid4(),
                user_id=test_user.id,
                course_id=course.id,
                progress_percentage=100.0,
                lessons_completed=1,
            )
        )
        await db_session.commit()

        user_id = test_user.id
        wallet_before = await db_session.scalar(
            select(UserWallet).where(UserWallet.user_id == user_id)
        )
        gems_before = wallet_before.gems if wallet_before else 0
        xp_before = test_user.total_xp or 0

        # Check #1 unlocks eligible achievements and credits Gems once
        chk1 = await async_client.post(
            "/api/v1/gamification/achievements/check", headers=auth_headers
        )
        assert chk1.status_code == 200
        unlocked_1 = chk1.json()["data"]
        unlocked_names = {a["name"] for a in unlocked_1}
        assert "Course Explorer" in unlocked_names
        expected_gems_delta = sum(int(a["gems_reward"]) for a in unlocked_1)
        assert expected_gems_delta > 0

        db_session.expire_all()
        wallet_after_1 = await db_session.scalar(
            select(UserWallet).where(UserWallet.user_id == user_id)
        )
        user_after_1 = await db_session.scalar(
            select(User).where(User.id == user_id)
        )
        assert wallet_after_1 is not None
        assert wallet_after_1.gems == gems_before + expected_gems_delta
        assert (user_after_1.total_xp or 0) == xp_before

        # Check #2 must NOT unlock again or award duplicate Gems/XP
        chk2 = await async_client.post(
            "/api/v1/gamification/achievements/check", headers=auth_headers
        )
        assert chk2.status_code == 200
        assert chk2.json()["data"] == []

        db_session.expire_all()
        wallet_after_2 = await db_session.scalar(
            select(UserWallet).where(UserWallet.user_id == user_id)
        )
        user_after_2 = await db_session.scalar(
            select(User).where(User.id == user_id)
        )
        assert wallet_after_2.gems == gems_before + expected_gems_delta
        assert (user_after_2.total_xp or 0) == xp_before

        ua_count = (
            await db_session.execute(
                select(UserAchievement).where(UserAchievement.user_id == user_id)
            )
        ).scalars().all()
        assert len(ua_count) == len(unlocked_1)
