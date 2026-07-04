import json

import run_logger
from graph import build_graph
from models import ClassificationOutput, JudgeOutput, RoutingPlan


def test_running_the_pipeline_writes_well_formed_log_lines(
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
    mock_judge(JudgeOutput(approved=True, reason="Correct."))

    app = build_graph()
    app.invoke(make_state(message="What time is checkout?"))

    lines = open(run_logger.DEFAULT_LOG_PATH).read().splitlines()
    assert len(lines) >= 1
    record = json.loads(lines[0])
    assert "node" in record
    assert "latency_ms" in record
    assert "category" in record
