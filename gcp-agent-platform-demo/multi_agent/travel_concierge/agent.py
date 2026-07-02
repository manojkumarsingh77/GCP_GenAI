"""
MULTI-AGENT DEMO
----------------
A "Travel Concierge" root agent that ORCHESTRATES three specialist
sub-agents: flight_agent, hotel_agent, weather_agent.

Learning goal: show learners the hierarchical multi-agent pattern in ADK.
  - Each sub-agent is a fully independent Agent (own model, own tools,
    own instruction) — exactly like the single-agent demo.
  - The root_agent lists them in `sub_agents=[...]`.
  - ADK's LLM-driven routing automatically transfers control to whichever
    sub-agent is best suited to handle the user's current request, based
    on each sub-agent's `description`.
  - This is the same "agent platform" concept as the single-agent demo —
    it just composes multiple agents instead of one.
"""

from google.adk.agents import Agent

from .sub_agents.flight_agent import flight_agent
from .sub_agents.hotel_agent import hotel_agent
from .sub_agents.weather_agent import weather_agent

root_agent = Agent(
    name="travel_concierge",
    model="gemini-2.5-flash",
    description="Top-level travel planning concierge that delegates to specialists.",
    instruction="""
You are a friendly travel concierge. You coordinate trip planning by routing
the conversation to the right specialist:

- For anything about flights, airfare, or scheduling -> use flight_agent.
- For anything about hotels, lodging, or accommodation -> use hotel_agent.
- For anything about weather, climate, or what to pack -> use weather_agent.

If the user asks something broad like "help me plan a trip to Goa next week",
gather the missing details (dates, origin city) first, then call the relevant
sub-agents in a sensible order (flights -> hotels -> weather) and summarize
all results together at the end in a friendly itinerary-style summary.
""",
    sub_agents=[flight_agent, hotel_agent, weather_agent],
)
