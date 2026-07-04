from backend.agents.classifier import ClassificationOutput, classifier_node, get_classifier_chain
from backend.agents.judge import JudgeOutput, get_judge_chain, judge_node
from backend.agents.orchestrator import RoutingPlan, get_orchestrator_chain, orchestrator_node
from backend.handlers import (
    booking_handler,
    complaint_handler,
    escalation_handler,
    maintenance_handler,
    other_handler,
)


def test_get_orchestrator_chain_returns_the_same_constructed_chain_each_call():
    assert get_orchestrator_chain() is get_orchestrator_chain()


def test_get_classifier_chain_returns_the_same_constructed_chain_each_call():
    assert get_classifier_chain() is get_classifier_chain()


def test_get_judge_chain_returns_the_same_constructed_chain_each_call():
    assert get_judge_chain() is get_judge_chain()


def test_orchestrator_node_returns_routing_plan_fields(mock_orchestrator, make_state):
    mock_orchestrator(
        RoutingPlan(
            preferred_category="Booking",
            escalate_immediately=False,
            context_notes="Guest asking about checkout.",
            routing_rationale="Clear booking question.",
        )
    )

    result = orchestrator_node(make_state(message="What time is checkout?"))

    assert result["preferred_category"] == "Booking"
    assert result["escalate_immediately"] is False
    assert "Guest asking about checkout." in result["orchestrator_context"]


def test_classifier_node_returns_classification_and_increments_retry_count(
    mock_classifier, make_state
):
    mock_classifier(
        ClassificationOutput(
            category="Booking",
            confidence=0.9,
            summary="Guest asks about checkout time.",
            suggested_action="handle_booking",
        )
    )

    result = classifier_node(make_state(retry_count=0))

    assert result["category"] == "Booking"
    assert result["confidence"] == 0.9
    assert result["suggested_action"] == "handle_booking"
    assert result["retry_count"] == 1


def test_judge_node_returns_approval(mock_judge, make_state):
    mock_judge(JudgeOutput(approved=True, reason="Looks correct."))

    result = judge_node(make_state(category="Booking", confidence=0.9, summary="..."))

    assert result == {"judge_approved": True}


def test_escalation_handler_sets_suggested_action_to_escalate(make_state):
    result = escalation_handler(make_state(retry_count=3))

    assert result == {"suggested_action": "escalate"}


def test_category_handlers_complete_without_mutating_state(make_state):
    state = make_state(category="Booking", summary="Guest asks about checkout time.")

    assert booking_handler(state) == {}
    assert maintenance_handler(state) == {}
    assert complaint_handler(state) == {}
    assert other_handler(state) == {}
