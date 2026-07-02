"""
Cymbal Retail Operations — Custom MCP Server
============================================
Exposes the company's order management, inventory, logistics, and returns
systems as Model Context Protocol (MCP) tools. Any MCP-compatible client
(ADK agents, Claude Desktop, IDEs) can consume these tools.

Transports:
    stdio (default, for local ADK dev):   python mcp_server/retail_ops_server.py
    streamable HTTP (for Cloud Run):      python mcp_server/retail_ops_server.py --transport http --port 8080

Prerequisite: run `python setup/seed_database.py` first.
"""

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "retail.db"

mcp = FastMCP(
    "cymbal-retail-ops",
    instructions=(
        "Tools for Cymbal Retail's live operational systems: order lookup, "
        "shipment tracking, inventory checks, and return/refund initiation."
    ),
)


def _query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    if not DB_PATH.exists():
        raise RuntimeError(
            "retail.db not found. Run `python setup/seed_database.py` first."
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _execute(sql: str, params: tuple = ()) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------------------
# TOOLS
# --------------------------------------------------------------------------

@mcp.tool()
def get_order_details(order_id: str) -> dict:
    """Look up a single order by its order ID (e.g. 'ORD-78002').

    Returns order status, amount, payment method, line items, and the
    customer's membership tier. Use this before any refund or return action.
    """
    orders = _query(
        """SELECT o.*, c.name AS customer_name, c.tier AS customer_tier
           FROM orders o JOIN customers c ON o.customer_id = c.customer_id
           WHERE o.order_id = ?""",
        (order_id.strip().upper(),),
    )
    if not orders:
        return {"found": False, "message": f"No order found with ID {order_id}."}
    order = orders[0]
    order["items"] = _query(
        "SELECT sku, product_name, quantity, unit_price FROM order_items WHERE order_id = ?",
        (order["order_id"],),
    )
    order["found"] = True
    return order


@mcp.tool()
def list_customer_orders(customer_id: str) -> dict:
    """List all orders for a customer ID (e.g. 'CUST-1001'), newest first."""
    rows = _query(
        """SELECT order_id, order_date, status, total_amount, currency
           FROM orders WHERE customer_id = ? ORDER BY order_date DESC""",
        (customer_id.strip().upper(),),
    )
    return {"customer_id": customer_id, "order_count": len(rows), "orders": rows}


@mcp.tool()
def track_shipment(order_id: str) -> dict:
    """Get live shipment tracking for an order: carrier, status, last scan
    location, promised delivery date, and last update timestamp."""
    rows = _query("SELECT * FROM shipments WHERE order_id = ?", (order_id.strip().upper(),))
    if not rows:
        return {
            "found": False,
            "message": f"No shipment record for {order_id}. It may still be PROCESSING.",
        }
    shipment = rows[0]
    shipment["found"] = True
    # Flag delayed shipments so the agent can apply the goodwill-voucher policy.
    if shipment["status"] == "DELAYED":
        shipment["agent_hint"] = (
            "Shipment is DELAYED. Per policy, if delayed >48h offer a new ETA "
            "plus a goodwill voucher. If 7+ days past promised date, treat as lost."
        )
    return shipment


@mcp.tool()
def check_inventory(sku_or_name: str) -> dict:
    """Check stock levels for a product by SKU (e.g. 'SKU-TV-43') or by a
    partial product name (e.g. 'kettle'). Returns per-warehouse stock."""
    term = f"%{sku_or_name.strip()}%"
    rows = _query(
        """SELECT sku, product_name, category, price,
                  stock_bengaluru, stock_mumbai, stock_delhi,
                  (stock_bengaluru + stock_mumbai + stock_delhi) AS total_stock
           FROM inventory WHERE sku LIKE ? OR product_name LIKE ?""",
        (term, term),
    )
    return {"matches": len(rows), "products": rows}


@mcp.tool()
def initiate_return(order_id: str, reason: str, refund_amount: float) -> dict:
    """Create a return request for a DELIVERED order.

    Args:
        order_id: the order to return, e.g. 'ORD-78001'.
        reason: short reason, e.g. 'defective screen', 'wrong size'.
        refund_amount: amount to refund. Must not exceed the order total.

    Policy guardrails enforced here:
      - Only DELIVERED orders can be returned.
      - Refunds above 20000 INR are created in PENDING_APPROVAL state and
        must be escalated to a supervisor.
    """
    order = _query("SELECT * FROM orders WHERE order_id = ?", (order_id.strip().upper(),))
    if not order:
        return {"success": False, "message": f"Order {order_id} not found."}
    order = order[0]

    if order["status"] != "DELIVERED":
        return {
            "success": False,
            "message": f"Order {order_id} is {order['status']}; only DELIVERED orders are returnable.",
        }
    if refund_amount > order["total_amount"]:
        return {
            "success": False,
            "message": f"Refund {refund_amount} exceeds order total {order['total_amount']}.",
        }

    return_id = f"RET-{datetime.now().strftime('%y%m%d%H%M%S')}"
    needs_approval = refund_amount > 20000
    status = "PENDING_APPROVAL" if needs_approval else "APPROVED"

    _execute(
        "INSERT INTO returns VALUES (?,?,?,?,?,?)",
        (return_id, order["order_id"], reason, status, refund_amount,
         datetime.now().isoformat(timespec="seconds")),
    )
    _execute("UPDATE orders SET status = 'RETURN_REQUESTED' WHERE order_id = ?",
             (order["order_id"],))

    return {
        "success": True,
        "return_id": return_id,
        "status": status,
        "refund_amount": refund_amount,
        "needs_supervisor_approval": needs_approval,
        "message": (
            "Return created and PENDING supervisor approval (amount > ₹20,000). "
            "Escalate a ticket for approval."
            if needs_approval
            else "Return approved. Pickup label will be emailed within 2 hours."
        ),
    }


@mcp.tool()
def get_return_status(return_id: str) -> dict:
    """Check the status of an existing return by return ID (e.g. 'RET-...')."""
    rows = _query("SELECT * FROM returns WHERE return_id = ?", (return_id.strip().upper(),))
    if not rows:
        return {"found": False, "message": f"No return found with ID {return_id}."}
    result = rows[0]
    result["found"] = True
    return result


# --------------------------------------------------------------------------
# ENTRYPOINT
# --------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cymbal Retail Ops MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    if args.transport == "http":
        # Streamable HTTP — suitable for Cloud Run deployment.
        mcp.settings.host = "0.0.0.0"
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
