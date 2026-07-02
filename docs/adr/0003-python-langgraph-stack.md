# Use Python + LangGraph as the pipeline runtime

The triage pipeline is built with Python and LangGraph. LangGraph's graph-based state machine maps directly onto the pipeline's control flow — classifier node, judge node, router, retry loop, and HITL branch are all first-class graph constructs. A plain sequential script could handle the happy path but would require ad-hoc retry/loop logic that LangGraph provides natively via conditional edges and state management.
