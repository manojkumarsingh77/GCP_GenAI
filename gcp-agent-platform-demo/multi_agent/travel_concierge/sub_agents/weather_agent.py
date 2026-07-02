"""Weather specialist sub-agent."""

from google.adk.agents import Agent


def get_weather_forecast(city: str, date: str) -> dict:
    """Gets a (mock) weather forecast for a city on a given date.

    Args:
        city: City name, e.g. "Goa".
        date: Date in YYYY-MM-DD format.

    Returns:
        A dict with forecast details.
    """
    return {
        "city": city,
        "date": date,
        "forecast": "Partly cloudy",
        "temp_high_c": 31,
        "temp_low_c": 24,
        "rain_chance_pct": 20,
    }


weather_agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash",
    description="Specialist sub-agent that provides weather forecasts for trip planning.",
    instruction="""
You are a weather specialist. Use the get_weather_forecast tool to answer
questions about expected weather for a destination and travel date.
Mention if travelers should pack for rain. Be concise.
""",
    tools=[get_weather_forecast],
)
