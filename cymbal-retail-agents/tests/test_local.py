"""
Quick local smoke test — verifies the environment before class.

1. Checks the SQLite DB is seeded.
2. Directly exercises the MCP server tools over stdio (no LLM cost).
3. Optionally runs one end-to-end coordinator query (needs GCP auth + .env).

Usage:
    python tests/test_local.py            # steps 1–2 only (free, offline)
    python tests/test_local.py --full     # adds the end-to-end agent query
"""

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB = ROOT / "data" / "retail.db"


def check_db() -> None:
    print("── 1. Database check ─────────────────────────────")
    if not DB.exists():
        sys.exit("❌ data/retail.db missing. Run: python setup/seed_database.py")
    import sqlite3
    n = sqlite3.connect(DB).execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    print(f"✅ retail.db found with {n} orders\n")


async def check_mcp() -> None:
    print("── 2. MCP server check (stdio, no LLM) ───────────")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / "mcp_server" / "retail_ops_server.py")],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print(f"✅ MCP server exposes {len(names)} tools: {', '.join(names)}")

            result = await session.call_tool(
                "get_order_details", {"order_id": "ORD-78002"}
            )
            print(f"✅ get_order_details(ORD-78002) → {result.content[0].text[:120]}...")

            result = await session.call_tool(
                "track_shipment", {"order_id": "ORD-78002"}
            )
            print(f"✅ track_shipment(ORD-78002)   → {result.content[0].text[:120]}...\n")


async def full_agent_query() -> None:
    print("── 3. End-to-end coordinator query ───────────────")
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")

    from google.adk.runners import InMemoryRunner
    from google.genai import types
    from customer_desk.agent import root_agent

    runner = InMemoryRunner(agent=root_agent, app_name="smoke_test")
    session = await runner.session_service.create_session(
        app_name="smoke_test", user_id="tester"
    )
    msg = types.Content(
        role="user",
        parts=[types.Part(text="Where is my order ORD-78002? It seems late.")],
    )
    print("👤 User: Where is my order ORD-78002? It seems late.\n")
    async for event in runner.run_async(
        user_id="tester", session_id=session.id, new_message=msg
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"🤖 [{event.author}] {part.text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true",
                        help="Also run an end-to-end LLM query (needs GCP auth)")
    args = parser.parse_args()

    check_db()
    asyncio.run(check_mcp())
    if args.full:
        asyncio.run(full_agent_query())
    print("🎉 Smoke test complete.")
