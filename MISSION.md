# Mission: Building Multi-Agent AI Systems for Guest Communication

## Why
Preparing for a technical interview at Besty — an AI-powered guest communication platform for short-term rental hosts. The interview requires building 5 progressively complex AI agent projects in Python, demonstrating ability to design and implement systems that classify, route, and autonomously respond to guest messages.

## Success looks like
- Build a working guest message classifier that returns structured JSON and routes to the right handler
- Build an upsell detection agent with tool use and a human approval gate
- Build a policy Q&A agent that retrieves from documents and self-corrects
- Build a memory-aware agent that handles flaky tools and retries gracefully
- Build a multi-signal pricing planner that explains its reasoning
- Articulate tradeoffs out loud: why an agent vs. deterministic workflow, what breaks at scale, what to monitor

## Constraints
- Python is the primary language
- Stack already decided: LangGraph + Groq (Llama 3 8B) + LangChain
- No code written yet — design docs (CONTEXT.md, 6 ADRs) exist for Project 1
- Main bottleneck: steering AI tools to produce the right code, verifying output, diagnosing what's wrong

## Out of scope
- Frontend (deferred per ADR-0006)
- Booking context lookup before classification (deferred per ADR-0005)
- Urgency as a separate classification axis (deferred per ADR-0005)
- Projects beyond the Besty 5
