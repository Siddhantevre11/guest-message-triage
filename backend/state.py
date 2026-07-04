from typing import Optional, TypedDict


class TriageState(TypedDict):
    message: str
    # Orchestrator output
    preferred_category: Optional[str]
    escalate_immediately: bool
    orchestrator_context: str
    # Classifier output
    category: Optional[str]
    confidence: Optional[float]
    summary: Optional[str]
    suggested_action: Optional[str]
    # Control flow
    retry_count: int
    judge_approved: Optional[bool]
    llm_call_failed: bool
