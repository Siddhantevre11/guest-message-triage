from typing import Literal, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from backend.llm import llm
from backend.resilience import RetriesExhaustedError, invoke_with_retry
from backend.run_logger import logged_node
from backend.state import TriageState

SYSTEM_PROMPT = """You are a triage orchestrator for Besty, an AI-powered guest communication platform for short-term rental hosts.

Your role is to read an incoming guest message and produce a routing plan for the pipeline.

Think carefully about:
- What is the guest's primary intent?
- Are there signals that make this message tricky to classify (emotional language, multiple topics, ambiguity, hostility)?
- Is the message so unclear, threatening, or off-topic that it should skip classification and escalate immediately to a human?

Categories available to the Classifier downstream:
- Booking: check-in/out times, extensions, cancellations, confirmation questions
- Maintenance: physical issues or defects at the property requiring attention
- Complaint: dissatisfaction about property, stay, or host — takes precedence over Maintenance when a physical issue is reported with emotional language
- Other: small talk, thanks, general questions unrelated to the above

Set escalate_immediately=true only when the message is genuinely unclassifiable or requires urgent human intervention (e.g., threats, medical emergencies, complete gibberish).

Your context_notes and routing_rationale will be passed directly to the Classifier agent to help it make the right decision."""


class RoutingPlan(BaseModel):
    preferred_category: Optional[Literal["Booking", "Maintenance", "Complaint", "Other"]]
    escalate_immediately: bool
    context_notes: str
    routing_rationale: str


orchestrator_chain = llm.with_structured_output(RoutingPlan)


@logged_node("orchestrator")
def orchestrator_node(state: TriageState) -> dict:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
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
