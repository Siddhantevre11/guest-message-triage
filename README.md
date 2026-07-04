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

## Test

```
pytest
```

The suite mocks the orchestrator/classifier/judge LLM calls, so it runs offline with no API key required.
