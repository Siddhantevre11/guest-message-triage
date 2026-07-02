from langgraph.graph import END, StateGraph

from models import TriageState
from nodes import (
    booking_handler,
    check_source_id_node,
    classifier_node,
    complaint_handler,
    escalation_handler,
    hitl_node,
    judge_node,
    maintenance_handler,
    orchestrator_node,
    other_handler,
)


def _route_after_source_check(state: TriageState) -> str:
    return "hitl" if state.get("hitl_triggered") else "orchestrator"


def _route_after_orchestrator(state: TriageState) -> str:
    return "escalate" if state.get("escalate_immediately") else "classifier"


def _route_after_judge(state: TriageState) -> str:
    if state.get("judge_approved"):
        return state.get("suggested_action", "escalate")
    if state.get("retry_count", 0) >= 3:
        return "escalate"
    return "classifier"


def build_graph():
    graph = StateGraph(TriageState)

    graph.add_node("check_source_id", check_source_id_node)
    graph.add_node("hitl", hitl_node)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("classifier", classifier_node)
    graph.add_node("judge", judge_node)
    graph.add_node("escalate", escalation_handler)
    graph.add_node("handle_booking", booking_handler)
    graph.add_node("dispatch_maintenance", maintenance_handler)
    graph.add_node("handle_complaint", complaint_handler)
    graph.add_node("handle_other", other_handler)

    graph.set_entry_point("check_source_id")

    graph.add_conditional_edges(
        "check_source_id",
        _route_after_source_check,
        {"hitl": "hitl", "orchestrator": "orchestrator"},
    )
    graph.add_edge("hitl", "orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        _route_after_orchestrator,
        {"escalate": "escalate", "classifier": "classifier"},
    )

    graph.add_edge("classifier", "judge")

    graph.add_conditional_edges(
        "judge",
        _route_after_judge,
        {
            "handle_booking": "handle_booking",
            "dispatch_maintenance": "dispatch_maintenance",
            "handle_complaint": "handle_complaint",
            "handle_other": "handle_other",
            "escalate": "escalate",
            "classifier": "classifier",
        },
    )

    for terminal in ["escalate", "handle_booking", "dispatch_maintenance", "handle_complaint", "handle_other"]:
        graph.add_edge(terminal, END)

    return graph.compile()
