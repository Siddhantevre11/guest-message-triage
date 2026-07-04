# CLI with stdin input() for HITL; frontend deferred

The initial entry point is a CLI script. HITL prompts the Host via stdin `input()` — the script pauses, prints what's missing, reads the response, injects it into state, and restarts the pipeline. A frontend will be added later; the `input()` mechanism is a placeholder that gets replaced without touching pipeline logic.

## Superseded (2026-07-04)

The HITL-for-missing-metadata mechanism this ADR describes was removed — see ADR-0008. The CLI remains as one entry point alongside the new frontend; it is no longer the sole one, and there is no HITL `input()` prompt left to replace.
