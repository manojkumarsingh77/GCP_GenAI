"""Operations Agent — connects to the custom Retail Ops MCP server.

Two connection modes, controlled by the MCP_SERVER_URL env var:
  - unset  → launch mcp_server/retail_ops_server.py locally over stdio
             (perfect for `adk web` classroom demos)
  - set    → connect to a remote MCP server over streamable HTTP
             (e.g. the same server deployed to Cloud Run)
"""

import os
import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
    StreamableHTTPConnectionParams,
)
from mcp import StdioServerParameters

from ..prompts import OPERATIONS_INSTRUCTION

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "").strip()
LOCAL_SERVER = Path(__file__).resolve().parents[2] / "mcp_server" / "retail_ops_server.py"

if MCP_SERVER_URL:
    # Remote MCP server (Cloud Run) — required when deploying to Agent Engine.
    connection_params = StreamableHTTPConnectionParams(url=MCP_SERVER_URL)
else:
    # Local MCP server spawned as a subprocess over stdio.
    connection_params = StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,          # current Python interpreter
            args=[str(LOCAL_SERVER)],
        ),
        timeout=30,
    )

retail_ops_toolset = McpToolset(connection_params=connection_params)

operations_agent = LlmAgent(
    name="operations_agent",
    model=os.environ.get("MODEL", "gemini-2.5-flash"),
    description=(
        "Operations specialist with live access to Cymbal Retail's systems "
        "via MCP: order lookup, shipment tracking, inventory checks, and "
        "return/refund initiation."
    ),
    instruction=OPERATIONS_INSTRUCTION,
    tools=[retail_ops_toolset],
)
