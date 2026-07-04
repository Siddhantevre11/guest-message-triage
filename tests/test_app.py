import pytest

from backend.agents.classifier import ClassificationOutput
from backend.agents.judge import JudgeOutput
from backend.agents.orchestrator import RoutingPlan
from frontend.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_index_get_renders_a_message_form(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"<textarea" in response.data
    assert b"Triage message" in response.data


def test_post_triage_shows_host_facing_result_without_internal_details(
    client, mock_orchestrator, mock_classifier, mock_judge
):
    mock_orchestrator(
        RoutingPlan(
            preferred_category="Booking",
            escalate_immediately=False,
            context_notes="Guest asking about checkout, low ambiguity.",
            routing_rationale="Clear booking question, no special handling needed.",
        )
    )
    mock_classifier(
        ClassificationOutput(
            category="Booking",
            confidence=0.95,
            summary="Guest wants to know checkout time.",
            suggested_action="handle_booking",
        )
    )
    mock_judge(JudgeOutput(approved=True, reason="Correct category and high confidence."))

    response = client.post("/triage", data={"message": "What time is checkout?"})
    body = response.data.decode()

    assert response.status_code == 200
    assert "Guest wants to know checkout time." in body
    assert "Booking" in body

    for internal_detail in [
        "ORCHESTRATOR",
        "CLASSIFIER",
        "JUDGE",
        "Routing Plan",
        "routing_rationale",
        "context_notes",
        "0.95",
        "APPROVED",
    ]:
        assert internal_detail not in body


def test_post_triage_with_empty_message_shows_error_and_no_result(client):
    response = client.post("/triage", data={"message": ""})
    body = response.data.decode()

    assert response.status_code == 200
    assert "Please enter a guest message." in body
    assert '<div class="result-card' not in body
