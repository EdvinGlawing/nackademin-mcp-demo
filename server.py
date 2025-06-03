from fastmcp import FastMCP
import datetime
import pytz
import os


if __name__ == "__main__":
    import asyncio
    port = int(os.environ.get("PORT", 8000))
    asyncio.run(
        mcp.run_streamable_http_async(
            host="0.0.0.0",
            port=port,
            log_level="debug"
        )
    ) 