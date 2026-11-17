from unittest.mock import AsyncMock, patch

import pytest

from app.core.token_blacklist import TokenBlacklist


@pytest.mark.asyncio
async def test_user_access_cutoff_rejects_only_older_tokens():
    redis = AsyncMock()
    redis.get.return_value = "100.5"

    with patch(
        "app.core.token_blacklist.RedisClient.get_instance",
        new=AsyncMock(return_value=redis),
    ):
        assert await TokenBlacklist.is_user_access_token_revoked("user-id", 100.0)
        assert not await TokenBlacklist.is_user_access_token_revoked("user-id", 101.0)


@pytest.mark.asyncio
async def test_revoke_user_access_tokens_stores_expiring_cutoff():
    redis = AsyncMock()

    with patch(
        "app.core.token_blacklist.RedisClient.get_instance",
        new=AsyncMock(return_value=redis),
    ):
        assert await TokenBlacklist.revoke_user_access_tokens("user-id")

    redis.setex.assert_awaited_once()
    key, ttl, cutoff = redis.setex.await_args.args
    assert key == "blacklist:user-cutoff:user-id"
    assert ttl > 0
    assert float(cutoff) > 0


@pytest.mark.asyncio
async def test_revocation_checks_report_unavailable_redis():
    with patch(
        "app.core.token_blacklist.RedisClient.get_instance",
        new=AsyncMock(return_value=None),
    ):
        assert await TokenBlacklist.is_blacklisted("access-token") is None
        assert (
            await TokenBlacklist.is_user_access_token_revoked("user-id", 100.0)
            is None
        )
