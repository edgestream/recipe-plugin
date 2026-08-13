from recipe_plugin.chefkoch import RateLimitedError
from recipe_plugin.server import _error


def test_rate_limited_error_is_reported_without_exposing_internals() -> None:
    assert _error(RateLimitedError()) == {
        "outcome": "rate_limited",
        "message": "Chefkoch is currently rate-limiting this service's upstream IP. Please try again later.",
    }


def test_rate_limited_error_includes_positive_retry_after() -> None:
    assert _error(RateLimitedError("30")) == {
        "outcome": "rate_limited",
        "message": "Chefkoch is currently rate-limiting this service's upstream IP. Please try again later. Retry after 30 seconds.",
    }
