#!/usr/bin/env python3
"""
Minimal test to see if FastMCP can run standalone
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from fastmcp import FastMCP

    async def main():
        # Create minimal server
        server = FastMCP("Test Server")

        @server.tool()
        async def test_tool() -> str:
            return "Hello from test tool"

        logger.info("Starting test server on 127.0.0.1:8081")
        await server.run(transport="sse", host="127.0.0.1", port=8081)

    if __name__ == "__main__":
        asyncio.run(main())

except Exception as e:
    logger.error(f"Failed: {e}")
    import traceback
    traceback.print_exc()