# Guest Message Triage

Classifies incoming messages from guests and routes them to the appropriate handler. Part of the Besty host tooling.

## Language

**Guest**:
A person with an active or pending stay at a property managed by a host on Besty.
_Avoid_: User, customer, tenant

**Host**:
The property owner or manager who receives and acts on guest messages via Besty.
_Avoid_: Owner, operator

**Message**:
A raw text string sent by a Guest to a Host.
_Avoid_: Request, query, ticket

## Agents

**Orchestrator**:
A full reasoning LLM agent that is the first node in the pipeline. Reads the raw message, reasons about signals and context, produces a Routing Plan, and may hard-escalate without invoking the Classifier.
_Avoid_: Planner, router, dispatcher

**Classifier**:
An LLM agent that assigns a Category, Confidence, Summary, and Suggested Action to a message. Receives the Orchestrator's Routing Plan as enriched context.
_Avoid_: Labeler, tagger, model

**Judge**:
An LLM agent that independently verifies the Classifier's output. Approves or rejects the classification — rejection triggers a retry or escalation.
_Avoid_: Validator, reviewer, verifier

**Routing Plan**:
The structured output of the Orchestrator — a preferred category hint, an immediate-escalation flag, and a reasoning note passed to the Classifier as context.
_Avoid_: Plan, strategy, orchestrator output

## Classification Output

**Summary**:
A one-sentence human-readable restatement of the guest message's core intent, generated alongside classification. Intended for a host scanning a list — not a rationale for the classification decision.
_Avoid_: Description, explanation, rationale

**Suggested Action**:
A fixed enum value indicating what should happen next with a classified message. One-to-one with category plus escalation: `dispatch_maintenance`, `handle_booking`, `handle_complaint`, `handle_other`, `escalate`.
_Avoid_: Recommended response, next step, action string

**Confidence**:
A float between 0 and 1 representing how certain the classifier is about the assigned category. Messages below the escalation threshold are routed to Escalation instead of their category handler.
_Avoid_: Score, certainty, probability

**Escalation**:
The sole human-handoff path in the pipeline — taken when the Orchestrator flags a message as unclassifiable, when the Judge rejects a classification three times, or when an LLM call exhausts its retries. Terminal: hands the message to a human with no pause-and-resume step. Not gated on any per-message provenance data (see ADR-0008).
_Avoid_: HITL, fallback, catch-all, unknown

## Categories

**Booking**:
A message about the terms, logistics, or status of the guest's reservation — check-in/out times, extensions, cancellations, confirmation questions.
_Avoid_: Reservation inquiry

**Maintenance**:
A message about a physical issue or defect at the property requiring attention or repair.
_Avoid_: Repair request, property issue

**Complaint**:
A message expressing dissatisfaction — about the property, the stay, or the host. Takes precedence over Maintenance when a physical issue is reported with emotional language.
_Avoid_: Negative feedback, dispute

**Other**:
A message that does not fit Booking, Maintenance, or Complaint — including small talk, thanks, and general questions.
_Avoid_: Miscellaneous, unknown
