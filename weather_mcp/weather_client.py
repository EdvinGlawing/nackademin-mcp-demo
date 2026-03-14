from datetime import datetime

import httpx

"""
This module contains the client for the Open Meteo API.

Documentation: https://open-meteo.com/en/docs#api_documentation
"""

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


async def geocode(location: str) -> dict | None:
    """Resolve a place name to coordinates. Returns None if no match is found."""
    params = {
        "name": location,
        "count": 1,
        "language": "sv",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(GEOCODING_URL, params=params)
        response.raise_for_status()

    data = response.json()
    results = data.get("results")
    if not results:
        return None

    hit = results[0]
    return {
        "name": hit.get("name"),
        "country": hit.get("country"),
        "latitude": hit["latitude"],
        "longitude": hit["longitude"],
    }


async def fetch_hourly_temperature(location: str) -> dict:
    """Resolve a place name to coordinates and fetch hourly temperature (°C) from now until end of day."""
    place = await geocode(location)
    if place is None:
        return {"error": f"Could not find the location '{location}'. Try with a different search term."}

    today = datetime.now().strftime("%Y-%m-%d")

    params = {
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "hourly": "temperature_2m",
        "temperature_unit": "celsius",
        "timezone": "Europe/Stockholm",
        "start_date": today,
        "end_date": today,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(FORECAST_URL, params=params)
        response.raise_for_status()

    data = response.json()
    times: list[str] = data["hourly"]["time"]
    temps: list[float] = data["hourly"]["temperature_2m"]

    current_hour = datetime.now().strftime("%Y-%m-%dT%H:00")

    filtered = {
        t: f"{temp} °C"
        for t, temp in zip(times, temps)
        if t >= current_hour
    }

    return {
        "location": f"{place['name']}, {place['country']}",
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "timezone": data["timezone"],
        "unit": "°C",
        "hourly_temperature": filtered,
    }
