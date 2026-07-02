"""Root agent — 'Cymbal Desk' coordinator for the multi-agent support team.

Architecture (LLM-driven delegation / agent transfer):

                       ┌──────────────────────────┐
        user ────────► │  customer_desk_coordinator│  (root LlmAgent)
                       └────────────┬─────────────┘
              ┌────────────────────┼──────────────────────┐
              ▼                    ▼                       ▼
      knowledge_agent       operations_agent        escalation_agent
      (Vertex AI RAG)       (custom MCP server)     (function tools)
"""

import os

from google.adk.agents import LlmAgent

from .prompts import COORDINATOR_INSTRUCTION
from .sub_agents.knowledge_agent import knowledge_agent
from .sub_agents.operations_agent import operations_agent
from .sub_agents.escalation_agent import escalation_agent

root_agent = LlmAgent(
    name="customer_desk_coordinator",
    model=os.environ.get("MODEL", "gemini-2.5-flash"),
    description=(
        "Cymbal Retail's front-door support coordinator. Understands the "
        "customer's need and delegates to policy, operations, or escalation "
        "specialists."
    ),
    instruction=COORDINATOR_INSTRUCTION,
    sub_agents=[knowledge_agent, operations_agent, escalation_agent],
)
