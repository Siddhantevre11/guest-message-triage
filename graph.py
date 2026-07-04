from langgraph.graph import END, StateGraph

from models import TriageState
from nodes import (
    booking_handler,
    classifier_node,
    complaint_handler,
    escalation_handler,
    judge_node,
    maintenance_handler,
    orchestrator_node,
    other_handler,
)


def _route_after_orchestrator(state: TriageState) -> str:
    if state.get("llm_call_failed") or state.get("escalate_immediately"):
        return "escalate"
    return "classifier"


def _route_after_classifier(state: TriageState) -> str:
    return "escalate" if state.get("llm_call_failed") else "judge"


def _route_after_judge(state: TriageState) -> str:
    if state.get("llm_call_failed"):
        return "escalate"
    if state.get("judge_approved"):
        return state.get("suggested_action", "escalate")
    if state.get("retry_count", 0) >= 3:
        return "escalate"
    return "classifier"


def build_graph():
    graph = StateGraph(TriageState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("classifier", classifier_node)
    graph.add_node("judge", judge_node)
    graph.add_node("escalate", escalation_handler)
    graph.add_node("handle_booking", booking_handler)
    graph.add_node("dispatch_maintenance", maintenance_handler)
    graph.add_node("handle_complaint", complaint_handler)
    graph.add_node("handle_other", other_handler)

    graph.set_entry_point("orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        _route_after_orchestrator,
        {"escalate": "escalate", "classifier": "classifier"},
    )

    graph.add_conditional_edges(
        "classifier",
        _route_after_classifier,
        {"escalate": "escalate", "judge": "judge"},
    )

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
