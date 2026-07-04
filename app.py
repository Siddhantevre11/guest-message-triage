from flask import Flask, render_template, request

from main import run_single

app = Flask(__name__)

CATEGORY_LABELS = {
    "Booking": "Booking",
    "Maintenance": "Maintenance",
    "Complaint": "Complaint",
    "Other": "Other",
}

ACTION_LABELS = {
    "handle_booking": "Routed to booking",
    "dispatch_maintenance": "Maintenance dispatched",
    "handle_complaint": "Routed to complaint handling",
    "handle_other": "Routed to general handling",
    "escalate": "Escalated to a human",
}


def host_view(result):
    category = result.get("category")
    suggested_action = result.get("suggested_action")
    return {
        "category": CATEGORY_LABELS.get(category, "Escalated"),
        "summary": result.get("summary") or "This message needs a human's attention.",
        "action_label": ACTION_LABELS.get(suggested_action, "Escalated to a human"),
        "is_escalated": suggested_action == "escalate",
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", result=None, error=None)


@app.route("/triage", methods=["POST"])
def triage():
    message = request.form.get("message", "").strip()
    if not message:
        return render_template(
            "index.html", result=None, error="Please enter a guest message."
        )

    result = run_single(message)
    return render_template(
        "index.html", result=host_view(result), message=message, error=None
    )


if __name__ == "__main__":
    app.run(debug=True)
