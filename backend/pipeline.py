import json

from backend.graph import build_graph


def make_initial_state(message):
    return {
        "message": message,
        "preferred_category": None,
        "escalate_immediately": False,
        "orchestrator_context": "",
        "category": None,
        "confidence": None,
        "summary": None,
        "suggested_action": None,
        "retry_count": 0,
        "judge_approved": None,
        "llm_call_failed": False,
    }


def run_single(message):
    app = build_graph()
    return app.invoke(make_initial_state(message))


def run_batch(batch_path):
    results = []
    with open(batch_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            results.append(run_single(item["message"]))
    return results
