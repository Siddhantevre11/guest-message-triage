import os
from unittest.mock import MagicMock

os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")

import pytest

from backend.agents import classifier as classifier_module
from backend.agents import judge as judge_module
from backend.agents import orchestrator as orchestrator_module


@pytest.fixture(autouse=True)
def _no_retry_backoff(monkeypatch):
    monkeypatch.setattr("backend.resilience.time.sleep", lambda _: None)


@pytest.fixture(autouse=True)
def _isolated_run_log(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.run_logger.DEFAULT_LOG_PATH", str(tmp_path / "test-triage.jsonl"))


@pytest.fixture
def mock_orchestrator(monkeypatch):
    def _set(plan):
        mock = MagicMock()
        mock.invoke.return_value = plan
        monkeypatch.setattr(orchestrator_module, "get_orchestrator_chain", lambda: mock)
        return mock

    return _set


@pytest.fixture
def mock_classifier(monkeypatch):
    def _set(*outputs):
        mock = MagicMock()
        mock.invoke.side_effect = list(outputs)
        monkeypatch.setattr(classifier_module, "get_classifier_chain", lambda: mock)
        return mock

    return _set


@pytest.fixture
def mock_judge(monkeypatch):
    def _set(*outputs):
        mock = MagicMock()
        mock.invoke.side_effect = list(outputs)
        monkeypatch.setattr(judge_module, "get_judge_chain", lambda: mock)
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
