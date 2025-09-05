import pytest

from backend.ai.rate_limiter import ErrorNormalizer
from backend.ai.providers.base_provider import (
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderType,
)


def test_error_normalizer_rate_limit_patterns():
    en = ErrorNormalizer()
    err = Exception("Too many requests: 429 Rate Limit exceeded")
    norm = en.normalize_error(err, ProviderType.GROK)
    assert isinstance(norm, ProviderRateLimitError)
    assert norm.error_code == "RATE_LIMIT"
    assert norm.provider_type == ProviderType.GROK


def test_error_normalizer_timeout_patterns_via_timeout_error_instance():
    en = ErrorNormalizer()
    err = TimeoutError("connection timeout after 10s")
    norm = en.normalize_error(err, ProviderType.LOCAL)
    assert isinstance(norm, ProviderTimeoutError)
    assert norm.error_code == "TIMEOUT"


def test_error_normalizer_unavailable_patterns_variants():
    en = ErrorNormalizer()
    # Include different variants to hit regex matching and case-insensitivity
    for msg in [
        "Service Unavailable",
        "SERVER ERROR 503",
        "Internal Server Error",
        "Bad Gateway 502",
        "Circuit breaker is open",
    ]:
        norm = en.normalize_error(Exception(msg), ProviderType.GROK)
        assert isinstance(norm, ProviderUnavailableError)
        assert norm.error_code == "UNAVAILABLE"


def test_error_normalizer_default_unknown_path():
    en = ErrorNormalizer()
    err = Exception("some odd client side issue")
    norm = en.normalize_error(err, ProviderType.GROK)
    assert isinstance(norm, ProviderError)
    assert not isinstance(norm, (ProviderTimeoutError, ProviderUnavailableError, ProviderRateLimitError))
    assert norm.error_code == "UNKNOWN"
