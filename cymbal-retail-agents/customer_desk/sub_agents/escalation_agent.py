"""Escalation Agent — files tickets for human teams via a Python function tool.

This deliberately uses a plain function tool (the third tool style in ADK,
alongside the RAG retrieval tool and the MCP toolset) so learners see all
three integration patterns in one project.
"""

import os
import uuid
from datetime import datetime

from google.adk.agents import LlmAgent

from ..prompts import ESCALATION_INSTRUCTION

_SLA = {
    "PRIORITY_SAFETY": "2 hours",
    "SUPERVISOR_APPROVAL": "4 business hours",
    "LOGISTICS": "1 business day",
    "WARRANTY_REVIEW": "2 business days",
    "TRUST_AND_SAFETY": "1 business day",
    "GENERAL": "1 business day",
}

# In-memory ticket store — swap for Jira/ServiceNow/Firestore in production.
_TICKETS: dict[str, dict] = {}


def create_escalation_ticket(
    queue: str,
    summary: str,
    customer_or_order_id: str,
    details: str,
) -> dict:
    """File an escalation ticket to a human support queue.

    Args:
        queue: one of PRIORITY_SAFETY, SUPERVISOR_APPROVAL, LOGISTICS,
            WARRANTY_REVIEW, TRUST_AND_SAFETY, GENERAL.
        summary: one-line description of the issue.
        customer_or_order_id: the customer ID or order ID involved.
        details: full context a human agent needs to act.

    Returns:
        Ticket ID, queue, and response SLA.
    """
    queue = queue.strip().upper()
    if queue not in _SLA:
        return {
            "success": False,
            "message": f"Unknown queue '{queue}'. Valid queues: {', '.join(_SLA)}.",
        }

    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    _TICKETS[ticket_id] = {
        "ticket_id": ticket_id,
        "queue": queue,
        "summary": summary,
        "reference": customer_or_order_id,
        "details": details,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "OPEN",
    }
    return {
        "success": True,
        "ticket_id": ticket_id,
        "queue": queue,
        "sla": _SLA[queue],
        "message": f"Ticket {ticket_id} filed to {queue}. Response SLA: {_SLA[queue]}.",
    }


def get_ticket_status(ticket_id: str) -> dict:
    """Look up an escalation ticket by its ID (e.g. 'TKT-1A2B3C4D')."""
    ticket = _TICKETS.get(ticket_id.strip().upper())
    if not ticket:
        return {"found": False, "message": f"No ticket found with ID {ticket_id}."}
    return {"found": True, **ticket}


escalation_agent = LlmAgent(
    name="escalation_agent",
    model=os.environ.get("MODEL", "gemini-2.5-flash"),
    description=(
        "Files escalation tickets to human teams: supervisor approvals, "
        "logistics investigations, warranty disputes, fraud, and safety issues."
    ),
    instruction=ESCALATION_INSTRUCTION,
    tools=[create_escalation_ticket, get_ticket_status],
)
