"""Flight specialist sub-agent."""

from google.adk.agents import Agent


def search_flights(origin: str, destination: str, date: str) -> dict:
    """Searches for flights between two cities on a given date.

    Args:
        origin: Departure city, e.g. "Bengaluru".
        destination: Arrival city, e.g. "Goa".
        date: Travel date in YYYY-MM-DD format.

    Returns:
        A dict with a list of mock flight options.
    """
    return {
        "origin": origin,
        "destination": destination,
        "date": date,
        "options": [
            {"flight_no": "6E-204", "depart": "06:15", "price_inr": 3499},
            {"flight_no": "AI-588", "depart": "11:40", "price_inr": 4250},
            {"flight_no": "SG-117", "depart": "18:05", "price_inr": 3899},
        ],
    }


flight_agent = Agent(
    name="flight_agent",
    model="gemini-2.5-flash",
    description="Specialist sub-agent that searches and recommends flights.",
    instruction="""
You are a flight-booking specialist. Use the search_flights tool to find options
and recommend the best one based on price and timing. Be concise.
""",
    tools=[search_flights],
)
