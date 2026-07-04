from unittest.mock import MagicMock

import pytest
from groq import APIConnectionError

from graph import build_graph
from models import ClassificationOutput, JudgeOutput, RoutingPlan


def _transient_error():
    return APIConnectionError(request=MagicMock())


def test_approved_booking_message_routes_to_booking_handler(
    mock_orchestrator, mock_classifier, mock_judge, make_state
):
    mock_orchestrator(
        RoutingPlan(
            preferred_category="Booking",
            escalate_immediately=False,
            context_notes="Guest asking about check-in time.",
            routing_rationale="Clear booking question.",
        )
    )
    mock_classifier(
        ClassificationOutput(
            category="Booking",
            confidence=0.95,
            summary="Guest wants to know check-in time.",
            suggested_action="handle_booking",
        )
    )
    mock_judge(JudgeOutput(approved=True, reason="Correct category and high confidence."))

    app = build_graph()
    result = app.invoke(make_state(message="What time can I check in tomorrow?"))

    assert result["category"] == "Booking"
    assert result["suggested_action"] == "handle_booking"
    assert result["judge_approved"] is True


def test_orchestrator_escalate_immediately_skips_classifier(
    mock_orchestrator, mock_classifier, mock_judge, make_state
):
    mock_orchestrator(
        RoutingPlan(
            preferred_category=None,
            escalate_immediately=True,
            context_notes="Message contains a threat.",
            routing_rationale="Unclassifiable, needs a human immediately.",
        )
    )
    classifier = mock_classifier()
    mock_judge()

    app = build_graph()
    result = app.invoke(make_state(message="I will burn this place down."))

    assert result["suggested_action"] == "escalate"
    classifier.invoke.assert_not_called()


def test_judge_rejection_retries_classifier_then_approves(
    mock_orchestrator, mock_classifier, mock_judge, make_state
):
    mock_orchestrator(
        RoutingPlan(
            preferred_category="Maintenance",
            escalate_immediately=False,
            context_notes="Guest reports a leak.",
            routing_rationale="Physical issue, no emotional language.",
        )
    )
    classifier = mock_classifier(
        ClassificationOutput(
            category="Maintenance",
            confidence=0.5,
            summary="Guest reports a leaking faucet.",
            suggested_action="dispatch_maintenance",
        ),
        ClassificationOutput(
            category="Maintenance",
            confidence=0.85,
            summary="Guest reports a leaking faucet.",
            suggested_action="dispatch_maintenance",
        ),
    )
    mock_judge(
        JudgeOutput(approved=False, reason="Confidence too low."),
        JudgeOutput(approved=True, reason="Confidence now acceptable."),
    )

    app = build_graph()
    result = app.invoke(make_state(message="The bathroom faucet is leaking."))

    assert classifier.invoke.call_count == 2
    assert result["retry_count"] == 2
    assert result["suggested_action"] == "dispatch_maintenance"
    assert result["judge_approved"] is True


def test_judge_rejection_three_times_escalates_instead_of_retrying_forever(
    mock_orchestrator, mock_classifier, mock_judge, make_state
):
    mock_orchestrator(
        RoutingPlan(
            preferred_category="Complaint",
            escalate_immediately=False,
            context_notes="Guest is unhappy.",
            routing_rationale="Ambiguous complaint.",
        )
    )
    ambiguous_classification = ClassificationOutput(
        category="Complaint",
        confidence=0.4,
        summary="Guest seems unhappy about something.",
        suggested_action="handle_complaint",
    )
    classifier = mock_classifier(
        ambiguous_classification, ambiguous_classification, ambiguous_classification
    )
    rejected = JudgeOutput(approved=False, reason="Confidence too low.")
    judge = mock_judge(rejected, rejected, rejected)

    app = build_graph()
    result = app.invoke(make_state(message="This is not what I expected."))

    assert classifier.invoke.call_count == 3
    assert judge.invoke.call_count == 3
    assert result["retry_count"] == 3
    assert result["suggested_action"] == "escalate"


@pytest.mark.parametrize(
    "category,suggested_action",
    [
        ("Maintenance", "dispatch_maintenance"),
        ("Complaint", "handle_complaint"),
        ("Other", "handle_other"),
    ],
)
def test_approved_classification_routes_to_matching_handler(
    category, suggested_action, mock_orchestrator, mock_classifier, mock_judge, make_state
):
    mock_orchestrator(
        RoutingPlan(
            preferred_category=category,
            escalate_immediately=False,
            context_notes="",
            routing_rationale="",
        )
    )
    mock_classifier(
        ClassificationOutput(
            category=category,
            confidence=0.9,
            summary="Summary.",
            suggested_action=suggested_action,
        )
    )
    mock_judge(JudgeOutput(approved=True, reason="Correct category and high confidence."))

    app = build_graph()
    result = app.invoke(make_state(message="Some message."))

    assert result["suggested_action"] == suggested_action


def test_orchestrator_exhausting_retries_escalates_without_calling_classifier(
    mock_orchestrator, mock_classifier, mock_judge, make_state
):
    orchestrator = mock_orchestrator(None)
    orchestrator.invoke.side_effect = [
        _transient_error(),
        _transient_error(),
        _transient_error(),
    ]
    classifier = mock_classifier()
    mock_judge()

    app = build_graph()
    result = app.invoke(make_state(message="Some message."))

    assert result["suggested_action"] == "escalate"
    classifier.invoke.assert_not_called()


def test_classifier_exhausting_retries_escalates_without_calling_judge(
    mock_orchestrator, mock_classifier, mock_judge, make_state
):
    mock_orchestrator(
        RoutingPlan(
            preferred_category="Booking",
            escalate_immediately=False,
            context_notes="",
            routing_rationale="",
        )
    )
    classifier = mock_classifier(None)
    classifier.invoke.side_effect = [
        _transient_error(),
        _transient_error(),
        _transient_error(),
    ]
    judge = mock_judge()

    app = build_graph()
    result = app.invoke(make_state(message="Some message."))

    assert result["suggested_action"] == "escalate"
    judge.invoke.assert_not_called()


def test_judge_exhausting_retries_escalates(
    mock_orchestrator, mock_classifier, mock_judge, make_state
):
    mock_orchestrator(
        RoutingPlan(
            preferred_category="Booking",
            escalate_immediately=False,
            context_notes="",
            routing_rationale="",
        )
    )
    mock_classifier(
        ClassificationOutput(
            category="Booking",
            confidence=0.9,
            summary="Summary.",
            suggested_action="handle_booking",
        )
    )
    judge = mock_judge(None)
    judge.invoke.side_effect = [_transient_error(), _transient_error(), _transient_error()]

    app = build_graph()
    result = app.invoke(make_state(message="Some message."))

    assert result["suggested_action"] == "escalate"
