import pytest


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset slowapi in-memory rate limit counters between tests."""
    from app.limiter import limiter

    limiter._storage.reset()
    yield
    limiter._storage.reset()
