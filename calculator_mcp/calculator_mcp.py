from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field
from config.custom_logging_config import RequestLoggingMiddleware
from config.logging_config import configure_logging

configure_logging()

mcp = FastMCP("Calculator Server")
mcp.add_middleware(RequestLoggingMiddleware())


@mcp.tool()
def add_numbers(
    a: Annotated[float, Field(description="First number to add")],
    b: Annotated[float, Field(description="Second number to add")],
) -> float:
    """Adds two numbers together and returns the result."""
    return a + b


@mcp.tool()
def divide_numbers(
    a: Annotated[float, Field(description="Numerator (number to be divided)")],
    b: Annotated[float, Field(description="Denominator (number to divide by)")],
) -> float:
    """Divides two numbers together and returns the result."""
    return a / b


if __name__ == "__main__":
    import asyncio

    asyncio.run(
        mcp.run_http_async(
            host="0.0.0.0",
            port=8001,
            log_level="warning",
        )
    )
