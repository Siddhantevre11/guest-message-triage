import os

from dotenv import load_dotenv

load_dotenv()

from graph import build_graph


def main():
    print("=== Guest Message Triage — Besty ===\n")

    message = input("Guest message: ").strip()
    source_id = input("Source ID (press Enter to leave blank): ").strip() or None

    initial_state = {
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
    }

    app = build_graph()
    result = app.invoke(initial_state)

    print("\n=== Final Triage Result ===")
    print(f"  Category        : {result.get('category')}")
    print(f"  Confidence      : {result.get('confidence')}")
    print(f"  Summary         : {result.get('summary')}")
    print(f"  Suggested Action: {result.get('suggested_action')}")


if __name__ == "__main__":
    main()
