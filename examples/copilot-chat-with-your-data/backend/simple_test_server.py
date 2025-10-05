#!/usr/bin/env python3
"""
Simple HTTP server to test port 8081 connectivity
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        logger.info(f"GET request to {self.path}")

        if self.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"status": "ok", "server": "ECharts MCP Test Server"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def do_POST(self):
        logger.info(f"POST request to {self.path}")
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {"status": "ok", "message": "POST received"}
        self.wfile.write(json.dumps(response).encode())


def main():
    server = HTTPServer(('127.0.0.1', 8081), TestHandler)
    logger.info("Starting test server on 127.0.0.1:8081")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")


if __name__ == "__main__":
    main()