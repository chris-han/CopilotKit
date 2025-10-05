#!/usr/bin/env python3
"""
Final approach: ECharts MCP Server that runs directly without asyncio.run()
"""

import logging
import os
import sys

from fastmcp import FastMCP

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_echarts_mcp_server() -> FastMCP:
    """Create and configure the ECharts MCP server with chart generation tools"""

    # Create FastMCP server instance
    echarts_mcp = FastMCP("ECharts Dynamic Server")

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
        """
        logger.info(f"Generating {chart_type} chart for persona: {persona}")

        # Enhanced chart generation based on type and data
        base_config = {
            "title": {"text": title or f"{chart_type.title()} Chart"},
            "tooltip": {"trigger": "axis" if chart_type != "pie" else "item"},
            "legend": {"data": []},
            "toolbox": {
                "feature": {
                    "saveAsImage": {},
                    "dataView": {"readOnly": False},
                    "magicType": {"type": ["line", "bar"]},
                    "restore": {},
                    "dataZoom": {}
                }
            }
        }

        # Extract data for visualization
        if isinstance(data, dict) and "values" in data:
            values = data["values"]
            if values and len(values) > 0:
                categories = [str(i) for i in range(len(values))]

                if chart_type.lower() == "pie":
                    base_config.update({
                        "series": [{
                            "name": title or "Data",
                            "type": "pie",
                            "radius": "50%",
                            "data": [{"value": val, "name": f"Item {i+1}"} for i, val in enumerate(values[:10])]
                        }]
                    })
                else:
                    base_config.update({
                        "xAxis": {"type": "category", "data": categories},
                        "yAxis": {"type": "value"},
                        "series": [{
                            "name": title or "Data",
                            "type": chart_type.lower(),
                            "data": values[:20]  # Limit to 20 points for performance
                        }]
                    })
            else:
                # Fallback mock data
                base_config.update({
                    "xAxis": {"type": "category", "data": ["A", "B", "C", "D", "E"]},
                    "yAxis": {"type": "value"},
                    "series": [{
                        "name": "Sample Data",
                        "type": chart_type.lower(),
                        "data": [10, 20, 30, 25, 15]
                    }]
                })
        else:
            # Default mock configuration
            if chart_type.lower() == "pie":
                base_config.update({
                    "series": [{
                        "name": "Sample Data",
                        "type": "pie",
                        "radius": "50%",
                        "data": [
                            {"value": 335, "name": "Category A"},
                            {"value": 310, "name": "Category B"},
                            {"value": 234, "name": "Category C"},
                            {"value": 135, "name": "Category D"}
                        ]
                    }]
                })
            else:
                base_config.update({
                    "xAxis": {"type": "category", "data": ["Mon", "Tue", "Wed", "Thu", "Fri"]},
                    "yAxis": {"type": "value"},
                    "series": [{
                        "name": "Sample Data",
                        "type": chart_type.lower(),
                        "data": [120, 200, 150, 80, 70]
                    }]
                })

        # Apply persona-specific styling
        if persona == "executive":
            base_config["color"] = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
            base_config["title"]["textStyle"] = {"fontSize": 18, "fontWeight": "bold"}
        elif persona == "analyst":
            base_config["color"] = ["#2563eb", "#dc2626", "#16a34a", "#ea580c"]
            base_config["grid"] = {"left": "10%", "right": "10%", "bottom": "15%"}
        elif persona == "developer":
            base_config["color"] = ["#334155", "#64748b", "#94a3b8", "#cbd5e1"]
            base_config["backgroundColor"] = "#f8fafc"

        # Apply custom styling if provided
        if customizations:
            base_config.update(customizations)

        return base_config

    @echarts_mcp.tool()
    async def generate_chart_suggestions(
        data: dict,
        analysis_context: str = "",
        persona: str = "default",
        max_suggestions: int = 5
    ) -> list:
        """
        Generate multiple chart suggestions for given data.
        """
        logger.info(f"Generating {max_suggestions} chart suggestions for persona: {persona}")

        suggestions = [
            {
                "type": "bar",
                "rationale": "Bar charts are excellent for comparing discrete categories and showing relative magnitudes",
                "score": 0.9
            },
            {
                "type": "line",
                "rationale": "Line charts effectively show trends and changes over time or ordered categories",
                "score": 0.8
            },
            {
                "type": "pie",
                "rationale": "Pie charts are ideal for showing parts of a whole and proportional relationships",
                "score": 0.7
            },
            {
                "type": "scatter",
                "rationale": "Scatter plots reveal correlations and patterns between two variables",
                "score": 0.6
            },
            {
                "type": "area",
                "rationale": "Area charts emphasize magnitude of change over time with filled regions",
                "score": 0.5
            }
        ]

        # Add configurations to suggestions
        for suggestion in suggestions:
            suggestion["config"] = await get_chart(suggestion["type"], data, persona, f"{suggestion['type'].title()} Chart", "", {})

        # Filter and sort suggestions based on data characteristics
        if isinstance(data, dict) and "values" in data:
            values = data["values"]
            if len(values) > 10:
                # For larger datasets, prioritize charts that handle many points well
                suggestions[0]["score"] = 0.95  # Bar charts
                suggestions[1]["score"] = 0.9   # Line charts
            if len(values) <= 5:
                # For small datasets, pie charts work well
                suggestions[2]["score"] = 0.95

        # Sort by score and return top suggestions
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions[:max_suggestions]

    logger.info("ECharts MCP server tools registered successfully")
    return echarts_mcp


def main():
    """Main function to start the ECharts MCP server - using direct run without asyncio.run()"""

    # Create the server
    server = create_echarts_mcp_server()

    # Configure transport
    port = int(os.getenv("ECHARTS_MCP_PORT", "8081"))
    host = os.getenv("ECHARTS_MCP_HOST", "127.0.0.1")

    logger.info(f"Starting ECharts MCP server on {host}:{port} with SSE transport")

    try:
        # Use the server's direct run method which should handle the event loop internally
        server.run_sync(transport="sse", host=host, port=port)

    except AttributeError:
        logger.error("run_sync method not available, trying alternative approach")
        try:
            # Alternative: try to run in a different way
            import anyio
            anyio.run(server.run, transport="sse", host=host, port=port)
        except Exception as e2:
            logger.error(f"Alternative approach failed: {e2}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()