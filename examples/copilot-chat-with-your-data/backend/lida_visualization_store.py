"""Persistence layer for LIDA-generated visualizations."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import os

import asyncpg
from asyncpg import UndefinedColumnError


def _parse_bool(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    return value.lower() in {"1", "true", "yes"}


class LidaVisualizationStore:
    """Stores LIDA visualizations in Postgres when configured, otherwise in-memory."""

    def __init__(self) -> None:
        self._pool: Optional[asyncpg.pool.Pool] = None
        self._memory: Dict[str, Dict[str, Any]] = {}
        self._memory_lock = asyncio.Lock()
        self._table_initialized = False

        self._db_host = os.getenv("POSTGRES_HOST")
        self._db_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self._db_name = os.getenv("POSTGRES_DB")
        self._db_user = os.getenv("POSTGRES_USER")
        self._db_password = os.getenv("POSTGRES_PASSWORD")
        self._db_ssl = _parse_bool(os.getenv("POSTGRES_SSL", "")) or (
            self._db_host is not None and "azure" in self._db_host.lower()
        )

    @property
    def configured(self) -> bool:
        return all([self._db_host, self._db_name, self._db_user])

    async def init(self) -> None:
        if not self.configured or self._pool is not None:
            return

        self._pool = await asyncpg.create_pool(
            host=self._db_host,
            port=self._db_port,
            database=self._db_name,
            user=self._db_user,
            password=self._db_password,
            ssl="require" if self._db_ssl else None,
        )
        await self._ensure_table()

    async def _ensure_table(self) -> None:
        if not self._pool or self._table_initialized:
            return
        async with self._pool.acquire() as conn:
            await conn.execute("CREATE SCHEMA IF NOT EXISTS dashboards")
            async with conn.transaction():
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dashboards.lida_visualizations (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        chart_type TEXT NOT NULL,
                        chart_config JSONB NOT NULL,
                        code TEXT,
                        echar_code TEXT,
                        insights JSONB,
                        dataset_name TEXT,
                        semantic_model_id UUID,
                        dbt_metadata JSONB,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                await conn.execute(
                    "ALTER TABLE dashboards.lida_visualizations ADD COLUMN IF NOT EXISTS dbt_metadata JSONB"
                )
                await conn.execute(
                    "ALTER TABLE dashboards.lida_visualizations ADD COLUMN IF NOT EXISTS echar_code TEXT"
                )
                await conn.execute(
                    "ALTER TABLE dashboards.lida_visualizations ADD COLUMN IF NOT EXISTS semantic_model_id UUID"
                )
        self._table_initialized = True

    async def fetch_all(self) -> List[Dict[str, Any]]:
        if self._pool:
            await self._ensure_table()
            async with self._pool.acquire() as conn:
                try:
                    rows = await conn.fetch(
                        """
                        SELECT id, title, description, chart_type, chart_config, code, echar_code, insights, dataset_name, semantic_model_id, dbt_metadata, created_at, updated_at
                        FROM dashboards.lida_visualizations
                        ORDER BY created_at DESC
                        """
                    )
                except UndefinedColumnError:
                    await conn.execute(
                        "ALTER TABLE dashboards.lida_visualizations ADD COLUMN IF NOT EXISTS dbt_metadata JSONB"
                    )
                    await conn.execute(
                        "ALTER TABLE dashboards.lida_visualizations ADD COLUMN IF NOT EXISTS echar_code TEXT"
                    )
                    await conn.execute(
                        "ALTER TABLE dashboards.lida_visualizations ADD COLUMN IF NOT EXISTS semantic_model_id UUID"
                    )
                    rows = await conn.fetch(
                        """
                        SELECT id, title, description, chart_type, chart_config, code, echar_code, insights, dataset_name, semantic_model_id, dbt_metadata, created_at, updated_at
                        FROM dashboards.lida_visualizations
                        ORDER BY created_at DESC
                        """
                    )
            return [self._row_to_dict(row) for row in rows]

        async with self._memory_lock:
            return sorted(
                self._memory.values(),
                key=lambda item: item["created_at"],
                reverse=True,
            )

    async def upsert(self, visualization: Dict[str, Any]) -> Dict[str, Any]:
        viz_id = visualization.get("id") or f"viz-{datetime.now(timezone.utc).timestamp()}-{os.urandom(4).hex()}"
        now_dt = datetime.now(timezone.utc)

        # Parse created_at if it's a string, otherwise use current time
        created_at = visualization.get("created_at")
        if created_at and isinstance(created_at, str):
            try:
                created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                created_at_dt = now_dt
        else:
            created_at_dt = created_at if isinstance(created_at, datetime) else now_dt

        chart_config_raw = visualization.get("chart_config", {}) or {}
        chart_config_obj: Any
        if isinstance(chart_config_raw, str):
            try:
                chart_config_obj = json.loads(chart_config_raw)
            except json.JSONDecodeError:
                chart_config_obj = {}
        else:
            chart_config_obj = chart_config_raw

        echar_code = visualization.get("echar_code")
        if echar_code is None:
            if isinstance(chart_config_raw, str):
                echar_code = chart_config_raw
            else:
                try:
                    echar_code = json.dumps(chart_config_obj)
                except (TypeError, ValueError):
                    echar_code = None

        payload = {
            "id": viz_id,
            "title": visualization["title"],
            "description": visualization.get("description", ""),
            "chart_type": visualization["chart_type"],
            "chart_config": chart_config_obj or {},
            "code": visualization.get("code", ""),
            "echar_code": echar_code,
            "insights": visualization.get("insights", []) or [],
            "dataset_name": visualization.get("dataset_name"),
            "semantic_model_id": visualization.get("semantic_model_id"),
            "dbt_metadata": visualization.get("dbt_metadata"),
            "created_at": created_at_dt,
            "updated_at": now_dt,
        }

        if self._pool:
            row: Optional[asyncpg.Record] = None
            await self._ensure_table()
            async with self._pool.acquire() as conn:
                try:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO dashboards.lida_visualizations
                            (id, title, description, chart_type, chart_config, code, echar_code, insights, dataset_name, semantic_model_id, dbt_metadata, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        ON CONFLICT (id) DO UPDATE
                          SET title = EXCLUDED.title,
                              description = EXCLUDED.description,
                              chart_type = EXCLUDED.chart_type,
                              chart_config = EXCLUDED.chart_config,
                              code = EXCLUDED.code,
                              echar_code = EXCLUDED.echar_code,
                              insights = EXCLUDED.insights,
                              dataset_name = EXCLUDED.dataset_name,
                              semantic_model_id = EXCLUDED.semantic_model_id,
                              dbt_metadata = EXCLUDED.dbt_metadata,
                              updated_at = EXCLUDED.updated_at
                        RETURNING id, title, description, chart_type, chart_config, code, echar_code, insights, dataset_name, semantic_model_id, dbt_metadata, created_at, updated_at
                        """,
                        payload["id"],
                        payload["title"],
                        payload["description"],
                        payload["chart_type"],
                        json.dumps(payload["chart_config"]),
                        payload["code"],
                        payload["echar_code"],
                        json.dumps(payload["insights"]),
                        payload["dataset_name"],
                        payload["semantic_model_id"],
                        json.dumps(payload["dbt_metadata"]) if payload["dbt_metadata"] is not None else None,
                        payload["created_at"],
                        payload["updated_at"],
                    )
                except UndefinedColumnError:
                    await conn.execute(
                        "ALTER TABLE dashboards.lida_visualizations ADD COLUMN IF NOT EXISTS dbt_metadata JSONB"
                    )
                    await conn.execute(
                        "ALTER TABLE dashboards.lida_visualizations ADD COLUMN IF NOT EXISTS echar_code TEXT"
                    )
                    await conn.execute(
                        "ALTER TABLE dashboards.lida_visualizations ADD COLUMN IF NOT EXISTS semantic_model_id UUID"
                    )
                    row = await conn.fetchrow(
                        """
                        INSERT INTO dashboards.lida_visualizations
                            (id, title, description, chart_type, chart_config, code, echar_code, insights, dataset_name, semantic_model_id, dbt_metadata, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        ON CONFLICT (id) DO UPDATE
                          SET title = EXCLUDED.title,
                              description = EXCLUDED.description,
                              chart_type = EXCLUDED.chart_type,
                              chart_config = EXCLUDED.chart_config,
                              code = EXCLUDED.code,
                              echar_code = EXCLUDED.echar_code,
                              insights = EXCLUDED.insights,
                              dataset_name = EXCLUDED.dataset_name,
                              semantic_model_id = EXCLUDED.semantic_model_id,
                              dbt_metadata = EXCLUDED.dbt_metadata,
                              updated_at = EXCLUDED.updated_at
                        RETURNING id, title, description, chart_type, chart_config, code, echar_code, insights, dataset_name, semantic_model_id, dbt_metadata, created_at, updated_at
                        """,
                        payload["id"],
                        payload["title"],
                        payload["description"],
                        payload["chart_type"],
                        json.dumps(payload["chart_config"]),
                        payload["code"],
                        payload["echar_code"],
                        json.dumps(payload["insights"]),
                        payload["dataset_name"],
                        payload["semantic_model_id"],
                        json.dumps(payload["dbt_metadata"]) if payload["dbt_metadata"] is not None else None,
                        payload["created_at"],
                        payload["updated_at"],
                    )
        if row:
            return self._row_to_dict(row)

        async with self._memory_lock:
            # Convert datetime objects to ISO strings for memory storage
            memory_payload = {
                **payload,
                "created_at": payload["created_at"].isoformat() if isinstance(payload["created_at"], datetime) else payload["created_at"],
                "updated_at": payload["updated_at"].isoformat() if isinstance(payload["updated_at"], datetime) else payload["updated_at"],
            }
            self._memory[payload["id"]] = memory_payload
            return memory_payload

    async def delete(self, visualization_id: str) -> bool:
        """Delete a visualization by identifier.

        Returns True when a record was removed, False otherwise.
        """

        if self._pool:
            await self._ensure_table()
            async with self._pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM dashboards.lida_visualizations WHERE id = $1",
                    visualization_id,
                )
            try:
                deleted_count = int(result.split()[-1])
            except (IndexError, ValueError):  # pragma: no cover - defensive parsing
                deleted_count = 0
            return deleted_count > 0

        async with self._memory_lock:
            return self._memory.pop(visualization_id, None) is not None

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "chart_type": row["chart_type"],
            "chart_config": row["chart_config"] or {},
            "code": row["code"] or "",
            "echar_code": row.get("echar_code"),
            "insights": row["insights"] or [],
            "dataset_name": row["dataset_name"],
            "semantic_model_id": str(row["semantic_model_id"]) if row.get("semantic_model_id") else None,
            "dbt_metadata": row.get("dbt_metadata") or {},
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        }
