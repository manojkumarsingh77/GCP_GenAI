"""
SINGLE AGENT DEMO
-----------------
A Customer Support Agent built with Google's Agent Development Kit (ADK)
to run on GCP Agent Platform (Vertex AI Agent Engine).

Learning goal: show learners the minimum building blocks of ONE agent:
  1. A model (Gemini, via Vertex AI)
  2. An instruction (system prompt / persona)
  3. Tools (plain Python functions the LLM can call)
  4. A root_agent object that ADK auto-discovers
"""

from google.adk.agents import Agent

# ---------------------------------------------------------------------------
# TOOL 1: Look up an order status
# In a real deployment this would call your order-management DB/API.
# ADK turns the function's docstring + type hints into a tool schema
# automatically — no manual JSON schema needed.
# ---------------------------------------------------------------------------
def get_order_status(order_id: str) -> dict:
    """Looks up the current status of a customer order.

    Args:
        order_id: The unique order identifier, e.g. "ORD-1042".

    Returns:
        A dictionary with keys: status, eta_days, carrier.
    """
    # --- mock data store (replace with a real DB/API call) ---
    mock_orders = {
        "ORD-1042": {"status": "Shipped", "eta_days": 2, "carrier": "BlueDart"},
        "ORD-2099": {"status": "Processing", "eta_days": 5, "carrier": "N/A"},
        "ORD-3050": {"status": "Delivered", "eta_days": 0, "carrier": "DTDC"},
    }
    result = mock_orders.get(order_id)
    if not result:
        return {"error": f"No order found with id {order_id}"}
    return result


# ---------------------------------------------------------------------------
# TOOL 2: Issue a refund
# Shows a "write" tool, with simple guardrail logic baked into the function.
# ---------------------------------------------------------------------------
def initiate_refund(order_id: str, reason: str) -> dict:
    """Initiates a refund for a delivered or cancelled order.

    Args:
        order_id: The unique order identifier, e.g. "ORD-1042".
        reason: A short reason for the refund request.

    Returns:
        A dictionary confirming the refund ticket that was created.
    """
    return {
        "refund_ticket_id": f"RF-{order_id}",
        "order_id": order_id,
        "reason": reason,
        "status": "Refund initiated — funds in 5-7 business days",
    }


# ---------------------------------------------------------------------------
# THE AGENT
# ADK looks for a module-level variable named exactly `root_agent`.
# ---------------------------------------------------------------------------
root_agent = Agent(
    name="customer_support_agent",
    model="gemini-2.5-flash",
    description="Answers order-status questions and processes refund requests.",
    instruction="""
You are a polite, efficient customer support agent for an e-commerce company.

Rules:
- Always use the get_order_status tool before telling a customer their order status.
  Never guess or make up a status.
- Only call initiate_refund after the customer has clearly confirmed they want a refund,
  and only for orders that exist.
- Keep responses short (2-4 sentences) and professional.
- If an order id isn't found, ask the customer to double check it.
""",
    tools=[get_order_status, initiate_refund],
)
