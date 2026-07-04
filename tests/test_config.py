import pytest

from backend.config import MissingConfigError, validate_environment


def test_validate_environment_raises_when_groq_api_key_missing(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(MissingConfigError, match="GROQ_API_KEY"):
        validate_environment()


def test_validate_environment_passes_when_groq_api_key_present(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "some-key")

    validate_environment()
