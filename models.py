from typing import Literal, Optional, TypedDict
from pydantic import BaseModel


class RoutingPlan(BaseModel):
    preferred_category: Optional[Literal["Booking", "Maintenance", "Complaint", "Other"]]
    escalate_immediately: bool
    context_notes: str
    routing_rationale: str


class ClassificationOutput(BaseModel):
    category: Literal["Booking", "Maintenance", "Complaint", "Other"]
    confidence: float
    summary: str
    suggested_action: Literal[
        "dispatch_maintenance", "handle_booking", "handle_complaint", "handle_other", "escalate"
    ]


class JudgeOutput(BaseModel):
    approved: bool
    reason: str


class TriageState(TypedDict):
    message: str
    source_id: Optional[str]
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
    hitl_triggered: bool
    llm_call_failed: bool
