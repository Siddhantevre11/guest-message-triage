import json
import os
import time
from functools import wraps

DEFAULT_LOG_PATH = os.path.join("logs", "triage.jsonl")


def log_event(fields, log_path=DEFAULT_LOG_PATH):
    log_path = str(log_path)
    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
    record = {"timestamp": time.time(), **fields}
    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")


TRACKED_STATE_FIELDS = (
    "category",
    "confidence",
    "retry_count",
    "suggested_action",
    "judge_approved",
    "escalate_immediately",
    "llm_call_failed",
)


def logged_node(node_name):
    def decorator(fn):
        @wraps(fn)
        def wrapper(state):
            start = time.perf_counter()
            result = fn(state)
            latency_ms = (time.perf_counter() - start) * 1000
            merged = {**state, **result}
            fields = {"node": node_name, "latency_ms": round(latency_ms, 2)}
            fields.update({key: merged.get(key) for key in TRACKED_STATE_FIELDS})
            log_event(fields, log_path=DEFAULT_LOG_PATH)
            return result

        return wrapper

    return decorator
