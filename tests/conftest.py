import os
from unittest.mock import MagicMock

os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")

import pytest

import nodes


@pytest.fixture(autouse=True)
def _no_retry_backoff(monkeypatch):
    monkeypatch.setattr("resilience.time.sleep", lambda _: None)


@pytest.fixture(autouse=True)
def _isolated_run_log(tmp_path, monkeypatch):
    monkeypatch.setattr("run_logger.DEFAULT_LOG_PATH", str(tmp_path / "test-triage.jsonl"))


@pytest.fixture
def mock_orchestrator(monkeypatch):
    def _set(plan):
        mock = MagicMock()
        mock.invoke.return_value = plan
        monkeypatch.setattr(nodes, "orchestrator_chain", mock)
        return mock

    return _set


@pytest.fixture
def mock_classifier(monkeypatch):
    def _set(*outputs):
        mock = MagicMock()
        mock.invoke.side_effect = list(outputs)
        monkeypatch.setattr(nodes, "classifier_chain", mock)
        return mock

    return _set


@pytest.fixture
def mock_judge(monkeypatch):
    def _set(*outputs):
        mock = MagicMock()
        mock.invoke.side_effect = list(outputs)
        monkeypatch.setattr(nodes, "judge_chain", mock)
        return mock

    return _set


@pytest.fixture
def make_state():
    def _make(**overrides):
        state = {
            "message": "Test message",
            "preferred_category": None,
            "escalate_immediately": False,
            "orchestrator_context": "",
            "category": None,
            "confidence": None,
            "summary": None,
            "suggested_action": None,
            "retry_count": 0,
            "judge_approved": None,
            "llm_call_failed": False,
        }
        state.update(overrides)
        return state

    return _make
