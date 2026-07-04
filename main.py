import argparse

from backend.bootstrap import load_environment

load_environment()

from backend.pipeline import run_batch, run_single


def print_result(result):
    print("\n=== Final Triage Result ===")
    print(f"  Category        : {result.get('category')}")
    print(f"  Confidence      : {result.get('confidence')}")
    print(f"  Summary         : {result.get('summary')}")
    print(f"  Suggested Action: {result.get('suggested_action')}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Guest Message Triage — Besty")
    parser.add_argument("--message", help="Guest message to triage")
    parser.add_argument("--batch", help="Path to a JSONL file of {message} objects")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.batch:
        for result in run_batch(args.batch):
            print_result(result)
        return

    if args.message:
        print_result(run_single(args.message))
        return

    print("=== Guest Message Triage — Besty ===\n")
    message = input("Guest message: ").strip()
    print_result(run_single(message))


if __name__ == "__main__":
    main()
