from backend.run_logger import logged_node
from backend.state import TriageState


@logged_node("escalate")
def escalation_handler(state: TriageState) -> dict:
    print("\n[ESCALATE] Message routed to human escalation.")
    print(f"  Message   : {state['message']}")
    print(f"  Retries   : {state.get('retry_count', 0)}")
    return {"suggested_action": "escalate"}


@logged_node("handle_booking")
def booking_handler(state: TriageState) -> dict:
    print(f"\n[BOOKING] Routing to booking handler.")
    print(f"  {state['summary']}")
    return {}


@logged_node("dispatch_maintenance")
def maintenance_handler(state: TriageState) -> dict:
    print(f"\n[MAINTENANCE] Dispatching maintenance request.")
    print(f"  {state['summary']}")
    return {}


@logged_node("handle_complaint")
def complaint_handler(state: TriageState) -> dict:
    print(f"\n[COMPLAINT] Routing to complaint handler.")
    print(f"  {state['summary']}")
    return {}


@logged_node("handle_other")
def other_handler(state: TriageState) -> dict:
    print(f"\n[OTHER] Routing to general handler.")
    print(f"  {state['summary']}")
    return {}
