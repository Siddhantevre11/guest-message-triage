from backend.agents.classifier import ClassificationOutput
from backend.agents.judge import JudgeOutput
from backend.agents.orchestrator import RoutingPlan
from main import main, parse_args


def test_parse_args_defaults_to_interactive_mode_when_no_args_given():
    args = parse_args([])

    assert args.message is None
    assert args.batch is None


def test_parse_args_reads_message_flag():
    args = parse_args(["--message", "Hi there"])

    assert args.message == "Hi there"
    assert args.batch is None


def test_main_with_message_flag_skips_interactive_prompt(
    mock_orchestrator, mock_classifier, mock_judge, monkeypatch
):
    def _fail_if_called(_):
        raise AssertionError("input() should not be called in non-interactive mode")

    monkeypatch.setattr("builtins.input", _fail_if_called)
    mock_orchestrator(
        RoutingPlan(
            preferred_category="Booking",
            escalate_immediately=False,
            context_notes="",
            routing_rationale="",
        )
    )
    mock_classifier(
        ClassificationOutput(
            category="Booking",
            confidence=0.9,
            summary="Summary.",
            suggested_action="handle_booking",
        )
    )
    mock_judge(JudgeOutput(approved=True, reason="Correct."))

    main(["--message", "What time is checkout?"])


def test_main_with_no_args_falls_back_to_interactive_prompt(
    mock_orchestrator, mock_classifier, mock_judge, monkeypatch
):
    monkeypatch.setattr("builtins.input", lambda _: "What time is checkout?")
    mock_orchestrator(
        RoutingPlan(
            preferred_category="Booking",
            escalate_immediately=False,
            context_notes="",
            routing_rationale="",
        )
    )
    mock_classifier(
        ClassificationOutput(
            category="Booking",
            confidence=0.9,
            summary="Summary.",
            suggested_action="handle_booking",
        )
    )
    mock_judge(JudgeOutput(approved=True, reason="Correct."))

    main([])


def test_main_with_batch_flag_processes_each_line_without_prompting(
    mock_orchestrator, mock_classifier, mock_judge, monkeypatch, tmp_path, capsys
):
    batch_file = tmp_path / "batch.jsonl"
    batch_file.write_text(
        '{"message": "What time is checkout?"}\n'
        '{"message": "The sink is leaking."}\n'
    )

    def _fail_if_called(_):
        raise AssertionError("input() should not be called in batch mode")

    monkeypatch.setattr("builtins.input", _fail_if_called)
    plan = RoutingPlan(
        preferred_category="Booking",
        escalate_immediately=False,
        context_notes="",
        routing_rationale="",
    )
    classification = ClassificationOutput(
        category="Booking",
        confidence=0.9,
        summary="Summary.",
        suggested_action="handle_booking",
    )
    approval = JudgeOutput(approved=True, reason="Correct.")
    mock_orchestrator(plan)
    mock_classifier(classification, classification)
    mock_judge(approval, approval)

    main(["--batch", str(batch_file)])

    output = capsys.readouterr().out
    assert output.count("=== Final Triage Result ===") == 2
