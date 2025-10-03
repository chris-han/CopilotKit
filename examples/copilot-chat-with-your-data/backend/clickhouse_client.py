"""ClickHouse database client configuration."""

import os
from typing import Optional
import clickhouse_connect
from clickhouse_connect.driver.client import Client


def get_clickhouse_client() -> Client:
    """
    Create and return a ClickHouse client using environment variables.

    Returns:
        Client: ClickHouse client instance

    Raises:
        ValueError: If required environment variables are not set
    """
    host = os.getenv("CLICKHOUSE_HOST")
    port = os.getenv("CLICKHOUSE_PORT")
    user = os.getenv("CLICKHOUSE_USER")
    password = os.getenv("CLICKHOUSE_PASSWORD")
    secure = os.getenv("CLICKHOUSE_SECURE", "false").lower() in ("true", "1", "yes")

    if not host:
        raise ValueError("CLICKHOUSE_HOST environment variable is required")
    if not port:
        raise ValueError("CLICKHOUSE_PORT environment variable is required")
    if not user:
        raise ValueError("CLICKHOUSE_USER environment variable is required")
    if not password:
        raise ValueError("CLICKHOUSE_PASSWORD environment variable is required")

    client = clickhouse_connect.get_client(
        host=host,
        port=int(port),
        username=user,
        password=password,
        secure=secure
    )

    return client


# Example usage:
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    try:
        client = get_clickhouse_client()
        # Test the connection
        result = client.query("SELECT version()")
        print(f"Connected to ClickHouse version: {result.result_rows[0][0]}")
    except Exception as e:
        print(f"Error connecting to ClickHouse: {e}")
