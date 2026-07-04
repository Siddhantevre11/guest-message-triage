from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from models import ClassificationOutput, JudgeOutput, RoutingPlan, TriageState
from prompts import CLASSIFIER_SYSTEM, JUDGE_SYSTEM, ORCHESTRATOR_SYSTEM
from resilience import RetriesExhaustedError, invoke_with_retry

_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

orchestrator_chain = _llm.with_structured_output(RoutingPlan)
classifier_chain = _llm.with_structured_output(ClassificationOutput)
judge_chain = _llm.with_structured_output(JudgeOutput)


def check_source_id_node(state: TriageState) -> dict:
    if not state.get("source_id"):
        return {"hitl_triggered": True}
    return {}


def hitl_node(state: TriageState) -> dict:
    print("\n[HITL] Pipeline paused — Source ID is missing.")
    print(f"  Message: {state['message']}")
    source_id = input("  Please provide the Source ID: ").strip()
    return {"source_id": source_id, "hitl_triggered": False}


def orchestrator_node(state: TriageState) -> dict:
    messages = [
        SystemMessage(content=ORCHESTRATOR_SYSTEM),
        HumanMessage(content=f"Guest message: {state['message']}"),
    ]
    try:
        plan: RoutingPlan = invoke_with_retry(orchestrator_chain, messages)
    except RetriesExhaustedError:
        print("\n[ORCHESTRATOR] LLM call failed after retries — escalating.")
        return {"llm_call_failed": True}

    print(f"\n[ORCHESTRATOR] Preferred: {plan.preferred_category} | Escalate immediately: {plan.escalate_immediately}")
    print(f"  Rationale: {plan.routing_rationale}")

    context = (
        f"\n[Orchestrator Routing Plan]\n"
        f"Preferred category: {plan.preferred_category or 'None'}\n"
        f"Context notes: {plan.context_notes}\n"
        f"Routing rationale: {plan.routing_rationale}\n"
    )
    return {
        "preferred_category": plan.preferred_category,
        "escalate_immediately": plan.escalate_immediately,
        "orchestrator_context": context,
    }


def classifier_node(state: TriageState) -> dict:
    system_prompt = CLASSIFIER_SYSTEM.format(
        orchestrator_context=state.get("orchestrator_context", "")
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Guest message: {state['message']}"),
    ]
    try:
        result: ClassificationOutput = invoke_with_retry(classifier_chain, messages)
    except RetriesExhaustedError:
        print("\n[CLASSIFIER] LLM call failed after retries — escalating.")
        return {"llm_call_failed": True}

    retry = state.get("retry_count", 0) + 1
    print(f"\n[CLASSIFIER] (attempt {retry}) Category: {result.category} | Confidence: {result.confidence:.2f}")
    print(f"  Summary: {result.summary}")

    return {
        "category": result.category,
        "confidence": result.confidence,
        "summary": result.summary,
        "suggested_action": result.suggested_action,
        "retry_count": retry,
    }


def judge_node(state: TriageState) -> dict:
    messages = [
        SystemMessage(content=JUDGE_SYSTEM),
        HumanMessage(
            content=(
                f"Message: {state['message']}\n"
                f"Category: {state['category']}\n"
                f"Confidence: {state['confidence']}\n"
                f"Summary: {state['summary']}"
            )
        ),
    ]
    try:
        result: JudgeOutput = invoke_with_retry(judge_chain, messages)
    except RetriesExhaustedError:
        print("\n[JUDGE] LLM call failed after retries — escalating.")
        return {"llm_call_failed": True}

    print(f"\n[JUDGE] {'APPROVED' if result.approved else 'REJECTED'} — {result.reason}")

    return {"judge_approved": result.approved}


def escalation_handler(state: TriageState) -> dict:
    print("\n[ESCALATE] Message routed to human escalation.")
    print(f"  Source ID : {state.get('source_id')}")
    print(f"  Message   : {state['message']}")
    print(f"  Retries   : {state.get('retry_count', 0)}")
    return {"suggested_action": "escalate"}


def booking_handler(state: TriageState) -> dict:
    print(f"\n[BOOKING] Routing to booking handler.")
    print(f"  {state['summary']}")
    return {}


def maintenance_handler(state: TriageState) -> dict:
    print(f"\n[MAINTENANCE] Dispatching maintenance request.")
    print(f"  {state['summary']}")
    return {}


def complaint_handler(state: TriageState) -> dict:
    print(f"\n[COMPLAINT] Routing to complaint handler.")
    print(f"  {state['summary']}")
    return {}


def other_handler(state: TriageState) -> dict:
    print(f"\n[OTHER] Routing to general handler.")
    print(f"  {state['summary']}")
    return {}
