#!/usr/bin/env python3
"""
Standalone ECharts MCP Server for Claude Code Integration

This script starts the ECharts MCP server on port 8081 with SSE transport,
providing the dynamic chart generation capabilities needed for LIDA integration.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the current directory to Python path to import from main.py
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_echarts_mcp_server() -> FastMCP:
    """Create and configure the ECharts MCP server with tools from main.py"""

    # Create FastMCP server instance
    echarts_mcp = FastMCP("ECharts Dynamic Server")

    # Import chart generation functions from main.py
    try:
        from main import generate_echarts_config, generate_chart_suggestions_data

        @echarts_mcp.tool()
        async def get_chart(
            chart_type: str,
            data: dict,
            persona: str = "default",
            title: str = "",
            description: str = "",
            customizations: dict = None
        ) -> dict:
            """
            Generate ECharts configuration for a given chart type and data.

            Args:
                chart_type: Type of chart to generate (line, bar, pie, scatter, etc.)
                data: The data to visualize
                persona: The target persona for customization (executive, analyst, developer, default)
                title: Chart title
                description: Chart description
                customizations: Additional chart customizations

            Returns:
                ECharts configuration object
            """
            return await generate_echarts_config(
                chart_type=chart_type,
                data=data,
                persona=persona,
                title=title,
                description=description,
                customizations=customizations or {}
            )

        @echarts_mcp.tool()
        async def generate_chart_suggestions(
            data: dict,
            analysis_context: str = "",
            persona: str = "default",
            max_suggestions: int = 5
        ) -> list:
            """
            Generate multiple chart suggestions for given data.

            Args:
                data: The data to analyze and create suggestions for
                analysis_context: Context about the analysis being performed
                persona: Target persona for suggestions
                max_suggestions: Maximum number of suggestions to generate

            Returns:
                List of chart suggestion objects with type, rationale, and config
            """
            return await generate_chart_suggestions_data(
                data=data,
                analysis_context=analysis_context,
                persona=persona,
                max_suggestions=max_suggestions
            )

        logger.info("ECharts MCP server tools registered successfully")

    except ImportError as e:
        logger.error(f"Failed to import chart generation functions: {e}")
        logger.warning("Running in mock mode - tools will return mock data")

        @echarts_mcp.tool()
        async def get_chart(
            chart_type: str,
            data: dict,
            persona: str = "default",
            title: str = "",
            description: str = "",
            customizations: dict = None
        ) -> dict:
            """Mock chart generation for development/testing"""
            return {
                "title": {"text": title or f"Mock {chart_type.title()} Chart"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": ["A", "B", "C"]},
                "yAxis": {"type": "value"},
                "series": [{
                    "type": chart_type,
                    "data": [10, 20, 30]
                }]
            }

        @echarts_mcp.tool()
        async def generate_chart_suggestions(
            data: dict,
            analysis_context: str = "",
            persona: str = "default",
            max_suggestions: int = 5
        ) -> list:
            """Mock chart suggestions for development/testing"""
            return [
                {
                    "type": "bar",
                    "rationale": "Bar charts are effective for comparing categories",
                    "config": {"title": {"text": "Mock Bar Chart"}}
                },
                {
                    "type": "line",
                    "rationale": "Line charts show trends over time",
                    "config": {"title": {"text": "Mock Line Chart"}}
                }
            ]

    return echarts_mcp


async def main():
    """Main function to start the ECharts MCP server"""

    # Create the server
    server = await create_echarts_mcp_server()

    # Configure transport
    port = int(os.getenv("ECHARTS_MCP_PORT", "8081"))
    host = os.getenv("ECHARTS_MCP_HOST", "127.0.0.1")

    logger.info(f"Starting ECharts MCP server on {host}:{port} with SSE transport")

    try:
        # Start server with SSE transport
        await server.run(transport="sse", host=host, port=port)

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())