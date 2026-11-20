"""Tests for T16-T18: Grammar Quiz 3 difficulty tiers (easy, medium, hard)."""

import pytest
from httpx import AsyncClient

from app.routes.games import GRAMMAR_DIFFICULTY_TIERS, GRAMMAR_QUIZ_BANK


def test_grammar_bank_has_all_three_tiers_for_every_cefr_level():
    for level, items in GRAMMAR_QUIZ_BANK.items():
        for tier in GRAMMAR_DIFFICULTY_TIERS:
            matching = [q for q in items if q.get("difficulty_tier") == tier]
            assert len(matching) >= 3, (
                f"CEFR {level} tier {tier} has only {len(matching)} questions"
            )


@pytest.mark.asyncio
class TestGrammarDifficultyTiersRoutes:
    @pytest.mark.parametrize(
        "tier,expected_timer",
        [("easy", 15), ("medium", 12), ("hard", 9)],
    )
    async def test_grammar_quiz_filters_strictly_by_tier(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        tier: str,
        expected_timer: int,
    ):
        res = await async_client.get(
            f"/api/v1/games/grammar-quiz?level=B1&difficulty={tier}&count=3",
            headers=auth_headers,
        )
        assert res.status_code == 200
        payload = res.json()
        assert payload["difficulty_tier"] == tier
        assert payload["timer_seconds_per_question"] == expected_timer
        assert len(payload["questions"]) == 3
        for q in payload["questions"]:
            assert q["difficulty_tier"] == tier

        # Resuming session retains selected difficulty_tier in snapshot
        session_id = payload["session_id"]
        session_res = await async_client.get(
            f"/api/v1/games/sessions/{session_id}",
            headers=auth_headers,
        )
        assert session_res.status_code == 200
        assert session_res.json()["content"]["difficulty_tier"] == tier

    async def test_grammar_quiz_rejects_invalid_difficulty_tier(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        res = await async_client.get(
            "/api/v1/games/grammar-quiz?level=A1&difficulty=impossible&count=3",
            headers=auth_headers,
        )
        assert res.status_code == 422
