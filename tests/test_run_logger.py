import json

from backend.run_logger import log_event, logged_node


def test_log_event_appends_a_json_line_with_given_fields(tmp_path):
    log_path = tmp_path / "triage.jsonl"

    log_event({"node": "orchestrator", "category": "Booking"}, log_path=log_path)

    lines = log_path.read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["node"] == "orchestrator"
    assert record["category"] == "Booking"


def test_log_event_appends_rather_than_overwrites(tmp_path):
    log_path = tmp_path / "triage.jsonl"

    log_event({"node": "orchestrator"}, log_path=log_path)
    log_event({"node": "classifier"}, log_path=log_path)

    lines = log_path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["node"] == "orchestrator"
    assert json.loads(lines[1])["node"] == "classifier"


def test_logged_node_writes_merged_state_fields_and_latency(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.run_logger.DEFAULT_LOG_PATH", str(tmp_path / "triage.jsonl"))

    @logged_node("classifier")
    def fake_classifier_node(state):
        return {"category": "Booking", "confidence": 0.9, "retry_count": 1}

    state = {"retry_count": 0}
    result = fake_classifier_node(state)

    assert result == {"category": "Booking", "confidence": 0.9, "retry_count": 1}

    lines = (tmp_path / "triage.jsonl").read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["node"] == "classifier"
    assert record["category"] == "Booking"
    assert record["confidence"] == 0.9
    assert record["retry_count"] == 1
    assert isinstance(record["latency_ms"], (int, float))
