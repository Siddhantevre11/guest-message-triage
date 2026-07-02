# CLI with stdin input() for HITL; frontend deferred

The initial entry point is a CLI script. HITL prompts the Host via stdin `input()` — the script pauses, prints what's missing, reads the response, injects it into state, and restarts the pipeline. A frontend will be added later; the `input()` mechanism is a placeholder that gets replaced without touching pipeline logic.
