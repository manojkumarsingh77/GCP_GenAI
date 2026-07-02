"""Hotel specialist sub-agent."""

from google.adk.agents import Agent


def search_hotels(city: str, checkin: str, checkout: str) -> dict:
    """Searches for hotels in a city for a given date range.

    Args:
        city: City to search in, e.g. "Goa".
        checkin: Check-in date, YYYY-MM-DD.
        checkout: Check-out date, YYYY-MM-DD.

    Returns:
        A dict with a list of mock hotel options.
    """
    return {
        "city": city,
        "checkin": checkin,
        "checkout": checkout,
        "options": [
            {"name": "Sea Breeze Resort", "rating": 4.5, "price_per_night_inr": 6200},
            {"name": "Palm Grove Inn", "rating": 4.1, "price_per_night_inr": 3800},
            {"name": "Coastal Heritage Hotel", "rating": 4.7, "price_per_night_inr": 8900},
        ],
    }


hotel_agent = Agent(
    name="hotel_agent",
    model="gemini-2.5-flash",
    description="Specialist sub-agent that searches and recommends hotels.",
    instruction="""
You are a hotel-booking specialist. Use the search_hotels tool to find options
and recommend one based on rating and budget. Be concise.
""",
    tools=[search_hotels],
)
