# Guest Message Triage

Classifies incoming guest messages and routes them to the appropriate handler. See `CONTEXT.md` for domain vocabulary and `docs/adr/` for architecture decisions.

## Setup

```
pip install -r requirements-dev.txt
```

Copy `.env.example` to `.env` and set `GROQ_API_KEY`.

## Run

```
python main.py
```

Non-interactive modes for scripted/demo runs:

```
python main.py --message "What time is checkout?"
python main.py --batch messages.jsonl   # one {"message": ...} per line
```

## Web frontend

```
python app.py
```

Open http://127.0.0.1:5000 — a Host-inbox view: paste a guest message, see the triage result (category, summary, suggested action) as a clean card. This is a demo frontend, not production-hardened (no auth, no persistence). The Orchestrator/Classifier/Judge reasoning trace never reaches the browser — it stays in the console and `logs/triage.jsonl` for the developer.

## Test

```
pytest
```

The suite mocks the orchestrator/classifier/judge LLM calls, so it runs offline with no API key required.

## Structure

```
backend/
  agents/           one file per agent — prompt, schema, node function together
    orchestrator.py
    classifier.py
    judge.py
  graph.py           LangGraph wiring: how the agents connect
  handlers.py         plain routing handlers (booking/maintenance/complaint/other/escalate) — not agents
  pipeline.py         run_single() / run_batch() — the one interface both entry points call
  llm.py              shared ChatGroq client
  config.py           env validation
  resilience.py        retry/backoff for transient LLM failures
  run_logger.py         structured JSON-lines logging
  bootstrap.py          load_environment() — .env loading + config validation, shared by both launchers
frontend/
  app.py              Flask routes + Host-facing presentation mapping
  templates/index.html
main.py                thin CLI launcher over backend.pipeline
app.py                 thin Flask launcher over frontend.app
```

`main.py` and `app.py` never change how you run the project — `python main.py` and `python app.py` still work exactly as before. The frontend never imports agent internals directly; it only calls `backend.pipeline.run_single()`.
