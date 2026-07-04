from unittest.mock import MagicMock

import pytest
from groq import APIConnectionError, BadRequestError

from resilience import RetriesExhaustedError, invoke_with_retry


def _api_connection_error():
    return APIConnectionError(request=MagicMock())


def test_invoke_with_retry_returns_result_after_transient_error_then_success(monkeypatch):
    monkeypatch.setattr("resilience.time.sleep", lambda _: None)
    chain = MagicMock()
    chain.invoke.side_effect = [_api_connection_error(), "the result"]

    result = invoke_with_retry(chain, ["messages"])

    assert result == "the result"
    assert chain.invoke.call_count == 2


def test_invoke_with_retry_raises_after_exhausting_all_attempts(monkeypatch):
    monkeypatch.setattr("resilience.time.sleep", lambda _: None)
    chain = MagicMock()
    chain.invoke.side_effect = [
        _api_connection_error(),
        _api_connection_error(),
        _api_connection_error(),
    ]

    with pytest.raises(RetriesExhaustedError):
        invoke_with_retry(chain, ["messages"], max_attempts=3)

    assert chain.invoke.call_count == 3


def test_invoke_with_retry_does_not_retry_non_transient_errors(monkeypatch):
    monkeypatch.setattr("resilience.time.sleep", lambda _: None)
    chain = MagicMock()
    bad_request = BadRequestError("invalid request", response=MagicMock(), body=None)
    chain.invoke.side_effect = bad_request

    with pytest.raises(BadRequestError):
        invoke_with_retry(chain, ["messages"], max_attempts=3)

    assert chain.invoke.call_count == 1
