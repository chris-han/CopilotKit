#!/bin/bash
# Start ECharts MCP Server on port 8081

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Set environment variables
export ECHARTS_MCP_PORT=8081
export ECHARTS_MCP_HOST=127.0.0.1

echo "Starting ECharts MCP Server on $ECHARTS_MCP_HOST:$ECHARTS_MCP_PORT"
echo "Server URL: http://$ECHARTS_MCP_HOST:$ECHARTS_MCP_PORT/sse"
echo ""
echo "Available tools:"
echo "  - get_chart: Generate ECharts configuration"
echo "  - generate_chart_suggestions: Get multiple chart recommendations"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the server using FastMCP CLI
exec fastmcp run echarts_mcp_server.py --transport sse --host $ECHARTS_MCP_HOST --port $ECHARTS_MCP_PORT