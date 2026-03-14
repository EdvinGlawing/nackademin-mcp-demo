from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field
from config.custom_logging_config import RequestLoggingMiddleware
from config.logging_config import configure_logging
from weather_mcp.weather_client import fetch_hourly_temperature

configure_logging()

mcp = FastMCP("Weather Server")
mcp.add_middleware(RequestLoggingMiddleware())


@mcp.tool()
async def get_temperature(
    location: Annotated[str, Field(description="Place name to search for, e.g. 'Stockholm' or 'Göteborg'")],
) -> dict:
    """Fetch hourly temperature in °C from now until end of day for a given place name."""
    return await fetch_hourly_temperature(location)


if __name__ == "__main__":
    import asyncio

    asyncio.run(
        mcp.run_http_async(
            host="0.0.0.0",
            port=8002,
            log_level="warning",
        )
    )
