"""Persistence layer for LIDA semantic models."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
import os

import asyncpg


class LidaSemanticModelStore:
    """Stores semantic models per dataset, with Postgres or in-memory fallback."""

    def __init__(self) -> None:
        self._pool: Optional[asyncpg.pool.Pool] = None
        self._memory: Dict[str, Dict[str, Any]] = {}
        self._dataset_index: Dict[str, str] = {}
        self._memory_lock = asyncio.Lock()
        self._table_initialized = False

        self._db_host = os.getenv("POSTGRES_HOST")
        self._db_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self._db_name = os.getenv("POSTGRES_DB")
        self._db_user = os.getenv("POSTGRES_USER")
        self._db_password = os.getenv("POSTGRES_PASSWORD")
        self._db_ssl = (
            os.getenv("POSTGRES_SSL", "").lower() in {"1", "true", "yes"}
            or (self._db_host is not None and "azure" in self._db_host.lower())
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
            async with conn.transaction():
                await conn.execute("CREATE SCHEMA IF NOT EXISTS dashboards")
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dashboards.lida_semantic_models (
                        id UUID PRIMARY KEY,
                        dataset_name TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        definition JSONB NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
        self._table_initialized = True

    async def fetch_all(self) -> List[Dict[str, Any]]:
        if self._pool:
            await self._ensure_table()
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, dataset_name, name, description, definition, created_at, updated_at
                    FROM dashboards.lida_semantic_models
                    ORDER BY dataset_name ASC
                    """
                )
            return [self._row_to_dict(row) for row in rows]

        async with self._memory_lock:
            return list(self._memory.values())

    async def get_by_dataset(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        if self._pool:
            await self._ensure_table()
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, dataset_name, name, description, definition, created_at, updated_at
                    FROM dashboards.lida_semantic_models
                    WHERE dataset_name = $1
                    """,
                    dataset_name,
                )
            return self._row_to_dict(row) if row else None

        async with self._memory_lock:
            model_id = self._dataset_index.get(dataset_name)
            if not model_id:
                return None
            return self._memory.get(model_id)

    async def upsert(self, semantic_model: Dict[str, Any]) -> Dict[str, Any]:
        model_id = semantic_model.get("id") or str(uuid4())
        now_dt = datetime.now(timezone.utc)

        payload = {
            "id": model_id,
            "dataset_name": semantic_model["dataset_name"],
            "name": semantic_model.get("name") or semantic_model["dataset_name"],
            "description": semantic_model.get("description") or "",
            "definition": semantic_model.get("definition") or {},
            "created_at": semantic_model.get("created_at") or now_dt,
            "updated_at": now_dt,
        }

        if self._pool:
            await self._ensure_table()
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO dashboards.lida_semantic_models
                        (id, dataset_name, name, description, definition, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (dataset_name) DO UPDATE
                      SET name = EXCLUDED.name,
                          description = EXCLUDED.description,
                          definition = EXCLUDED.definition,
                          updated_at = EXCLUDED.updated_at
                    RETURNING id, dataset_name, name, description, definition, created_at, updated_at
                    """,
                    payload["id"],
                    payload["dataset_name"],
                    payload["name"],
                    payload["description"],
                    json.dumps(payload["definition"]),
                    payload["created_at"],
                    payload["updated_at"],
                )
            return self._row_to_dict(row)

        async with self._memory_lock:
            memory_payload = {
                **payload,
                "created_at": payload["created_at"].isoformat()
                if isinstance(payload["created_at"], datetime)
                else payload["created_at"],
                "updated_at": payload["updated_at"].isoformat(),
            }
            self._memory[payload["id"]] = memory_payload
            self._dataset_index[payload["dataset_name"]] = payload["id"]
            return memory_payload

    async def update(self, model_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self._pool:
            await self._ensure_table()
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    UPDATE dashboards.lida_semantic_models
                    SET name = COALESCE($2, name),
                        description = COALESCE($3, description),
                        definition = COALESCE($4, definition),
                        updated_at = NOW()
                    WHERE id = $1
                    RETURNING id, dataset_name, name, description, definition, created_at, updated_at
                    """,
                    model_id,
                    updates.get("name"),
                    updates.get("description"),
                    json.dumps(updates["definition"]) if "definition" in updates else None,
                )
            return self._row_to_dict(row) if row else None

        async with self._memory_lock:
            existing = self._memory.get(model_id)
            if not existing:
                return None
            merged = {
                **existing,
                **{k: v for k, v in updates.items() if v is not None},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._memory[model_id] = merged
            return merged

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> Dict[str, Any]:
        return {
            "id": str(row["id"]),
            "dataset_name": row["dataset_name"],
            "name": row["name"],
            "description": row["description"],
            "definition": row["definition"] or {},
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        }
