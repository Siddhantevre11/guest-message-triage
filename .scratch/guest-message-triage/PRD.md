# Guest Message Triage — PRD

Status: ready-for-agent

## Problem Statement

Hosts on Besty receive a constant stream of raw guest Messages — about bookings, property issues, complaints, and everything else — and need each one routed to the right handler quickly and correctly. Reading and triaging every Message by hand doesn't scale as a Host's guest volume grows. Worse, a wrong guess has real relationship cost: a Complaint routed like small talk, or a Maintenance issue that never reaches dispatch, erodes guest trust and creates work Hosts didn't know they had. Hosts need incoming Messages automatically read, classified, and routed — with a system that knows when it isn't sure, and never lets an unverified guess reach a handler silently.

## Solution

A multi-agent triage pipeline — Orchestrator, Classifier, Judge — built as a LangGraph state machine. The Orchestrator reads the raw Message first and reasons about it, producing a Routing Plan (a preferred-category hint plus rationale) that it hands to the Classifier as context, and can short-circuit straight to Escalation for messages that are clearly unclassifiable (threats, medical emergencies, gibberish) without spending a Classifier call on them. The Classifier assigns a Category, Confidence, Summary, and Suggested Action. The Judge independently re-checks that output before anything downstream sees it: it rejects low-Confidence or wrong-looking classifications, which either triggers a retry (up to 3 attempts) or falls through to Escalation. A Message missing its Source ID pauses the pipeline in a HITL step that asks the Host for it before continuing. Every classified Message ultimately lands in exactly one of five places: the Booking, Maintenance, Complaint, or Other handler, or Escalation.

## User Stories

1. As a Host, I want every incoming guest Message automatically classified into Booking, Maintenance, Complaint, or Other, so that I don't have to manually read and sort every Message myself.
2. As a Host, I want a one-sentence Summary attached to each classified Message, so that I can scan a list of triaged Messages and understand each one's intent at a glance.
3. As a Host, I want a Suggested Action attached to each classification, so that I know what should happen next without re-reading the Message.
4. As a Host, I want messages that report a physical property issue expressed with frustration or anger classified as Complaint rather than Maintenance, so that emotionally charged issues get the escalation-aware handling they need, not routine dispatch.
5. As a Host, I want the Orchestrator to reason about a Message's signals (ambiguity, hostility, multiple topics) before classification happens, so that tricky Messages get enriched context instead of being classified cold.
6. As a Host, I want Messages that are threatening, medically urgent, or otherwise unclassifiable to skip straight to Escalation without wasting a classification attempt, so that urgent cases reach a human as fast as possible.
7. As a Host, I want every Classifier output independently re-checked by a Judge before it reaches a handler, so that I never have a misrouted Message silently sent to the wrong workflow.
8. As a Host, I want low-Confidence classifications (below 0.7) automatically rejected and retried, so that the system doesn't act on a guess it isn't sure about.
9. As a Host, I want the pipeline to retry classification up to 3 times before giving up, so that a single bad Classifier call doesn't immediately dump a Message into Escalation.
10. As a Host, I want a Message that fails Judge approval 3 times in a row to route to Escalation, so that no Message gets stuck retrying forever.
11. As a Host, I want to be prompted for a Source ID when one is missing from an incoming Message, so that every classification I later see can be traced back to where the Message came from.
12. As a Host, I want the pipeline to resume automatically from where it paused once I supply the missing Source ID, so that I don't have to restart the triage from scratch.
13. As a Host, I want Escalated Messages to show me the Source ID, the original Message text, and how many classification attempts were made, so that I have full context when I pick up the handoff myself.
14. As a Host, I want each Category to route to a distinct handler (Booking, Maintenance, Complaint, Other), so that downstream logic per category can evolve independently.
15. As a Host, I want the Suggested Action to always be consistent with the assigned Category (e.g. `dispatch_maintenance` only for Maintenance), so that I can trust the action label without cross-checking the category myself.
16. As a Host, I want to run the triage pipeline against a single Message from a command line, so that I can test and demo classification behavior without needing a frontend.
17. As a Developer extending this pipeline, I want the Orchestrator's reasoning passed to the Classifier as enriched prompt context (not just a bare category hint), so that the Classifier benefits from the Orchestrator's full analysis of the Message.
18. As a Developer extending this pipeline, I want Classifier, Judge, and Orchestrator outputs enforced through structured output schemas, so that malformed LLM responses can't silently corrupt pipeline state.
19. As a Host, I want small talk, thanks, and Messages that don't fit the other three categories classified as Other rather than forced into a mismatched category, so that my Booking/Maintenance/Complaint queues stay clean.
20. As a Host, I want the same Message content re-classified identically on retry given the same inputs, so that retries are a meaningful check rather than random noise.
21. As a Developer debugging a triage run, I want each pipeline stage (Orchestrator, Classifier attempt N, Judge verdict, Escalation) to print a visible trace of its decision, so that I can follow why a Message ended up where it did.
22. As a Host, I want the system to work end-to-end without any per-message API cost, so that triaging high volumes of guest Messages doesn't become a cost center.

## Implementation Decisions

- **Architecture**: Three specialized LLM agents — Orchestrator, Classifier, Judge — implemented as LangGraph nodes over a single shared `TriageState`, per ADR-0007. This is a genuine multi-agent pipeline (agents collaborate via passed context), not one classifier call wrapped in a validation gate.
- **Orchestrator**: Full reasoning agent, runs first. Produces a Routing Plan (`preferred_category`, `escalate_immediately`, `context_notes`, `routing_rationale`) via structured output. `escalate_immediately=true` short-circuits directly to Escalation, bypassing the Classifier entirely.
- **Classifier**: Receives the Orchestrator's Routing Plan rendered into its system prompt as enriched context (not just a category hint). Produces `category`, `confidence`, `summary`, `suggested_action` via structured output. Suggested Action is 1:1 with category plus escalation (`handle_booking`, `dispatch_maintenance`, `handle_complaint`, `handle_other`, `escalate`).
- **Judge**: Independently re-evaluates the Classifier's output regardless of stated confidence. Approves only if the category looks correct AND confidence ≥ 0.7. Sits as a hard inline gate per ADR-0002 — nothing reaches a handler without Judge approval.
- **Retry loop**: On Judge rejection, the pipeline routes back to the Classifier, incrementing `retry_count`. After 3 rejected attempts, routing falls through to Escalation instead of retrying again.
- **HITL**: Triggered when `source_id` is missing on entry. Pauses the pipeline, prompts the Host (currently via CLI `input()`, per ADR-0006), injects the response into state, then proceeds to the Orchestrator. Frontend replacement of the `input()` mechanism is expected later without touching pipeline logic.
- **Structured output**: All three agent outputs (`RoutingPlan`, `ClassificationOutput`, `JudgeOutput`) are Pydantic models enforced via `.with_structured_output()`, per ADR-0001 — no prompt-and-parse JSON.
- **Model/runtime**: LangGraph `StateGraph` for control flow (conditional edges for source-ID check, escalate-immediately branch, and judge-approval routing), per ADR-0003. Groq `llama3-8b-8192` at temperature 0 backs all three agents, per ADR-0004 — a capability-for-cost trade-off that the retry+Judge pipeline is designed to compensate for.
- **State shape**: A single `TriageState` TypedDict threads through the whole graph, carrying the raw Message and Source ID, Orchestrator output, Classifier output, and control-flow fields (`retry_count`, `judge_approved`, `hitl_triggered`). No separate state objects per agent.
- **Explicitly deferred** (per ADR-0005): no booking-context lookup before classification, no urgency as a separate output axis alongside Category.

## Testing Decisions

- **Seam**: Tests invoke the compiled graph end-to-end — `build_graph().invoke(initial_state)` — and assert on the resulting `TriageState`. This is the single seam for this feature: it exercises HITL, Orchestrator short-circuiting, the Classifier/Judge retry loop, and final routing all through one entry point, matching how `main.py` actually drives the pipeline.
- **Mock boundary**: Only the three LLM chains (`orchestrator_chain`, `classifier_chain`, `judge_chain` in `nodes.py`) are mocked, at their `.invoke()` call. No real Groq API calls in tests, and no reaching into individual node functions to test them in isolation — a good test here observes pipeline behavior (final category, action, escalation, retry count), not which internal function got called.
- **What good coverage looks like**:
  - Missing Source ID triggers HITL and the pipeline resumes correctly once supplied.
  - Present Source ID skips HITL entirely.
  - Orchestrator `escalate_immediately=true` routes straight to Escalation without invoking the Classifier.
  - A Judge-approved classification for each of the four categories reaches the matching handler.
  - A Judge rejection triggers exactly one retry with `retry_count` incremented.
  - Three consecutive Judge rejections route to Escalation rather than retrying a 4th time.
  - Suggested Action returned in final state matches the approved Category.
- **Prior art**: None — this is the first test suite in the repo. `pytest` should be added to `requirements.txt` as the runner; no existing test conventions to match.

## Out of Scope

- Booking context lookup (check-in date, property, guest history) before classification — deferred per ADR-0005.
- Urgency as a classification axis separate from Category — deferred per ADR-0005.
- Any frontend or non-CLI entry point — deferred per ADR-0006; the CLI `input()` HITL mechanism is an intentional placeholder.
- Real business logic inside `booking_handler`, `maintenance_handler`, `complaint_handler`, `other_handler` — they currently print and return; implementing actual downstream actions is separate work.
- Persistence or checkpointing of pipeline runs (e.g. LangGraph `MemorySaver`) — not wired in.
- Projects 2–5 of the broader Besty interview-prep mission (upsell detection agent, policy Q&A agent, memory-aware agent, pricing planner) — separate PRDs.
- Any real integration with Besty's production systems (auth, deployment, real message ingestion).

## Further Notes

- **Doc/code discrepancy to resolve**: `CONTEXT.md`'s HITL definition states it triggers on "missing source ID or confidence below threshold after 3 retries," but the current `graph.py` routes exhausted retries straight to `escalate`, not back to `hitl`. Either the domain doc or the routing behavior should be corrected so they agree — flagging here rather than silently picking one.
- This is Project 1 of 5 in a Besty interview-prep mission (see `MISSION.md`); the Orchestrator-Worker-Judge pattern established here is expected to generalize to the remaining four projects (tool use with approval gates, RAG with self-correction, flaky-tool retries, multi-signal explainable planning).
- Code for this feature already exists (`main.py`, `models.py`, `nodes.py`, `prompts.py`, `graph.py`) and is not blocked by this PRD — this document formalizes the requirements and decisions already reflected in that code and its ADRs, primarily to scope the test suite described above.
