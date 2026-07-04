from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from backend.llm import llm
from backend.resilience import RetriesExhaustedError, invoke_with_retry
from backend.run_logger import logged_node
from backend.state import TriageState

SYSTEM_PROMPT = """You are a message classifier for Besty, an AI-powered guest communication platform for short-term rental hosts.

Your job is to classify a guest message into exactly one category and return structured output.

Categories:
- Booking: check-in/out times, extensions, cancellations, confirmation questions
- Maintenance: physical issues or defects at the property requiring attention or repair
- Complaint: dissatisfaction about property, stay, or host — takes precedence over Maintenance when emotional language is present alongside a physical issue
- Other: small talk, thanks, general questions

Suggested actions (must match category):
- handle_booking → Booking
- dispatch_maintenance → Maintenance
- handle_complaint → Complaint
- handle_other → Other
- escalate → only when you cannot classify at all

Confidence (0.0–1.0): reflect how certain you are. Use < 0.7 for genuinely ambiguous messages.

Summary: one sentence restating the guest's core intent — written for a host scanning a list, not an explanation of your decision.

{orchestrator_context}"""


class ClassificationOutput(BaseModel):
    category: Literal["Booking", "Maintenance", "Complaint", "Other"]
    confidence: float
    summary: str
    suggested_action: Literal[
        "dispatch_maintenance", "handle_booking", "handle_complaint", "handle_other", "escalate"
    ]


_classifier_chain = llm.with_structured_output(ClassificationOutput)


def get_classifier_chain():
    return _classifier_chain


@logged_node("classifier")
def classifier_node(state: TriageState) -> dict:
    system_prompt = SYSTEM_PROMPT.format(
        orchestrator_context=state.get("orchestrator_context", "")
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Guest message: {state['message']}"),
    ]
    try:
        result: ClassificationOutput = invoke_with_retry(get_classifier_chain(), messages)
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
