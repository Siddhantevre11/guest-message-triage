import argparse
import json
import sys

from dotenv import load_dotenv

load_dotenv()

from config import MissingConfigError, validate_environment

try:
    validate_environment()
except MissingConfigError as e:
    print(f"Configuration error: {e}")
    sys.exit(1)

from graph import build_graph


def make_initial_state(message, source_id=None):
    return {
        "message": message,
        "source_id": source_id,
        "preferred_category": None,
        "escalate_immediately": False,
        "orchestrator_context": "",
        "category": None,
        "confidence": None,
        "summary": None,
        "suggested_action": None,
        "retry_count": 0,
        "judge_approved": None,
        "hitl_triggered": False,
        "llm_call_failed": False,
    }


def run_single(message, source_id=None):
    app = build_graph()
    return app.invoke(make_initial_state(message, source_id))


def run_batch(batch_path):
    results = []
    with open(batch_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            results.append(run_single(item["message"], item.get("source_id")))
    return results


def print_result(result):
    print("\n=== Final Triage Result ===")
    print(f"  Category        : {result.get('category')}")
    print(f"  Confidence      : {result.get('confidence')}")
    print(f"  Summary         : {result.get('summary')}")
    print(f"  Suggested Action: {result.get('suggested_action')}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Guest Message Triage — Besty")
    parser.add_argument("--message", help="Guest message to triage")
    parser.add_argument("--source-id", dest="source_id", help="Source ID for the message")
    parser.add_argument("--batch", help="Path to a JSONL file of {message, source_id} objects")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.batch:
        for result in run_batch(args.batch):
            print_result(result)
        return

    if args.message:
        print_result(run_single(args.message, args.source_id))
        return

    print("=== Guest Message Triage — Besty ===\n")
    message = input("Guest message: ").strip()
    source_id = input("Source ID (press Enter to leave blank): ").strip() or None
    print_result(run_single(message, source_id))


if __name__ == "__main__":
    main()
