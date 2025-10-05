#!/usr/bin/env python3
"""
Run ECharts MCP server using subprocess to avoid asyncio conflicts
"""

import os
import subprocess
import sys
import signal
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_echarts_server():
    """Run the ECharts MCP server in a subprocess"""

    # Path to the server script
    server_script = os.path.join(os.path.dirname(__file__), "echarts_mcp_standalone.py")

    # Virtual environment activation
    venv_python = os.path.join(os.path.dirname(__file__), ".venv", "bin", "python")

    # Use venv python if available, otherwise system python
    python_cmd = venv_python if os.path.exists(venv_python) else sys.executable

    # Environment variables
    env = os.environ.copy()
    env.update({
        "ECHARTS_MCP_PORT": "8081",
        "ECHARTS_MCP_HOST": "127.0.0.1"
    })

    logger.info(f"Starting ECharts MCP server subprocess...")
    logger.info(f"Python: {python_cmd}")
    logger.info(f"Script: {server_script}")

    try:
        # Start the server process
        process = subprocess.Popen(
            [python_cmd, server_script],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        logger.info(f"Server process started with PID: {process.pid}")

        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            logger.info("Received interrupt signal, stopping server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server didn't stop gracefully, killing...")
                process.kill()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # Monitor the process
        while True:
            # Check if process is still running
            if process.poll() is not None:
                # Process has terminated
                stdout, stderr = process.communicate()
                logger.error(f"Server process terminated with code: {process.returncode}")
                if stdout:
                    logger.info(f"STDOUT: {stdout}")
                if stderr:
                    logger.error(f"STDERR: {stderr}")
                break

            # Read some output
            try:
                if process.stdout and process.stdout.readable():
                    line = process.stdout.readline()
                    if line:
                        print(f"SERVER: {line.strip()}")

                if process.stderr and process.stderr.readable():
                    line = process.stderr.readline()
                    if line:
                        print(f"SERVER ERROR: {line.strip()}")
            except:
                pass

            time.sleep(0.1)

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return False

    return True


if __name__ == "__main__":
    run_echarts_server()