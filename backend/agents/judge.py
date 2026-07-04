from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from backend.llm import llm
from backend.resilience import RetriesExhaustedError, invoke_with_retry
from backend.run_logger import logged_node
from backend.state import TriageState

SYSTEM_PROMPT = """You are a quality judge for a guest message classification pipeline at Besty.

You will receive the original guest message and the Classifier's output (category, confidence, summary).

Approve if: the category assignment is correct AND confidence >= 0.7.
Reject if: confidence < 0.7 OR the category seems wrong given the message content.

Be strict. A misrouted complaint treated as small talk causes real harm to the host relationship."""


class JudgeOutput(BaseModel):
    approved: bool
    reason: str


judge_chain = llm.with_structured_output(JudgeOutput)


@logged_node("judge")
def judge_node(state: TriageState) -> dict:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Message: {state['message']}\n"
                f"Category: {state['category']}\n"
                f"Confidence: {state['confidence']}\n"
                f"Summary: {state['summary']}"
            )
        ),
    ]
    try:
        result: JudgeOutput = invoke_with_retry(judge_chain, messages)
    except RetriesExhaustedError:
        print("\n[JUDGE] LLM call failed after retries — escalating.")
        return {"llm_call_failed": True}

    print(f"\n[JUDGE] {'APPROVED' if result.approved else 'REJECTED'} — {result.reason}")

    return {"judge_approved": result.approved}
