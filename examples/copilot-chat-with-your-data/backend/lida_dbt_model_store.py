"""Persistence for LIDA dbt model catalogue."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import asyncpg


_SEED_MODELS: List[Dict[str, Any]] = [
    {
        "id": "26de45e4-6c01-4d0e-bc50-47546d336e07",
        "slug": "sales_data",
        "name": "Sales Performance Model",
        "description": "Aggregates revenue, profit, and expense metrics by month for executive dashboards.",
        "path": "models/marts/finance/sales_performance.sql",
        "sql": """with source as (
    select * from {{ ref('fct_sales_transactions') }}
),
calendar as (
    select * from {{ ref('dim_calendar') }}
)
select
    c.month_start as billing_period_start,
    sum(s.revenue) as revenue,
    sum(s.profit) as profit,
    sum(s.expense) as expense,
    sum(s.customer_count) as customers
from source s
left join calendar c
    on s.date_id = c.date_id
group by 1
order by 1;""",
        "aliases": [
            "sales_data",
            "salesdata",
            "sales-performance",
            "sales performance",
        ],
    },
    {
        "id": "b284a37e-893c-4b48-ad59-219fafbc33a8",
        "slug": "product_data",
        "name": "Product Performance Model",
        "description": "Computes sales, units, and growth percentages by product for ranking visualizations.",
        "path": "models/marts/finance/product_performance.sql",
        "sql": """select
    p.product_id,
    p.product_name,
    sum(f.revenue) as sales,
    sum(f.units) as units,
    avg(f.growth_pct) as growth_percentage
from {{ ref('dim_product') }} p
join {{ ref('fct_product_revenue') }} f
    on p.product_id = f.product_id
group by 1,2
order by sales desc;""",
        "aliases": [
            "product_data",
            "productdata",
            "product-performance",
            "product performance",
        ],
    },
    {
        "id": "7a8f6a7f-b3b2-4e04-9dea-9e2093c4b43c",
        "slug": "category_data",
        "name": "Category Mix Model",
        "description": "Provides revenue share and growth metrics across product categories.",
        "path": "models/marts/finance/category_mix.sql",
        "sql": """select
    c.category_name,
    sum(f.revenue) as revenue,
    sum(f.revenue) / sum(sum(f.revenue)) over () as revenue_share,
    avg(f.growth_pct) as growth_percentage
from {{ ref('dim_category') }} c
join {{ ref('fct_category_revenue') }} f
    on c.category_id = f.category_id
group by 1
order by revenue desc;""",
        "aliases": [
            "category_data",
            "categorydata",
            "category-mix",
            "category mix",
        ],
    },
    {
        "id": "9b9ccbcc-2a5e-429f-8de8-38cb827772cf",
        "slug": "regional_data",
        "name": "Regional Sales Model",
        "description": "Summarizes sales and market share by region for geographic comparisons.",
        "path": "models/marts/finance/regional_sales.sql",
        "sql": """select
    r.region_name,
    sum(f.revenue) as revenue,
    sum(f.revenue) / sum(sum(f.revenue)) over () as market_share
from {{ ref('dim_region') }} r
join {{ ref('fct_regional_revenue') }} f
    on r.region_id = f.region_id
group by 1
order by revenue desc;""",
        "aliases": [
            "regional_data",
            "regionaldata",
            "regional-sales",
            "regional sales",
        ],
    },
    {
        "id": "b913115e-66fd-4fff-96c2-3e898d84628f",
        "slug": "demographics_data",
        "name": "Customer Demographics Model",
        "description": "Tracks spend distribution by age cohort for demographic analysis.",
        "path": "models/marts/finance/customer_demographics.sql",
        "sql": """select
    d.age_group,
    sum(f.spend) as total_spend,
    sum(f.customers) as customers
from {{ ref('dim_demographic') }} d
join {{ ref('fct_customer_spend') }} f
    on d.demographic_id = f.demographic_id
group by 1
order by total_spend desc;""",
        "aliases": [
            "demographics_data",
            "demographicsdata",
            "customer-demographics",
            "demographics",
        ],
    },
    {
        "id": "f998cac3-9d1e-445c-8574-473091412bc0",
        "slug": "enterprise_multi_cloud",
        "name": "Enterprise Multi-Cloud Spend",
        "description": "Normalised cloud cost data across AWS, Azure, and GCP with provider, service, and environment dimensions.",
        "path": "models/marts/finops/enterprise_multi_cloud.sql",
        "sql": """with source as (
    select * from {{ ref('fct_enterprise_cloud_costs') }}
),
aggregated as (
    select
        billing_period_start,
        provider,
        service,
        environment,
        sum(cost) as total_cost,
        sum(list_price) as total_list_price,
        sum(savings) as total_savings
    from source
    group by 1,2,3,4
)
select
    billing_period_start,
    provider,
    service,
    environment,
    total_cost,
    total_list_price,
    total_savings,
    total_savings / nullif(total_list_price, 0) as discount_rate,
    (total_list_price - total_cost) as savings_amount,
    (total_list_price - total_cost) / nullif(total_list_price, 0) as effective_discount,
    sum(total_cost) over (partition by provider order by billing_period_start) as provider_cumulative_cost,
    sum(total_cost) over (partition by service order by billing_period_start) as service_cumulative_cost
from aggregated
order by billing_period_start, provider, service;""",
        "aliases": [
            "enterprise_multi_cloud",
            "enterprise-multi-cloud",
            "enterprise multi cloud",
            "multi_cloud",
        ],
    },
    {
        "id": "2b537e54-71ee-4b49-930e-8c8c19861304",
        "slug": "small_company_finops",
        "name": "Small Company FinOps Spend Model",
        "description": "Aggregates cost, usage, and savings metrics for small company FinOps datasets across providers.",
        "path": "models/marts/finops/small_company_finops.sql",
        "sql": """with source as (
    select * from {{ ref('fct_small_company_finops_costs') }}
),
normalized as (
    select
        billing_period_start,
        cloud_provider,
        service_name,
        environment,
        product_family,
        sum(cost) as total_cost,
        sum(usage_quantity) as usage_quantity,
        sum(reserved_savings) as reserved_savings,
        sum(spot_savings) as spot_savings,
        sum(credits) as credits
    from source
    group by 1,2,3,4,5
)
select *
from normalized
order by billing_period_start desc, cloud_provider asc, service_name asc;""",
        "aliases": [
            "small_company_finops",
            "small-company-finops",
            "small company finops",
            "small_company_finops_dataset",
        ],
    },
    {
        "id": "a645bf3f-c81a-43be-90c3-53149b5f8a75",
        "slug": "startup_aws_only",
        "name": "Startup AWS Only Spend Model",
        "description": "Aggregates AWS cost and usage metrics for startup-focused dashboards.",
        "path": "models/marts/finops/startup_aws_only.sql",
        "sql": """with source as (
    select * from {{ ref('fct_startup_aws_costs') }}
),
summarised as (
    select
        billing_period_start,
        service_name,
        usage_type,
        environment,
        sum(cost) as total_cost,
        sum(usage_quantity) as usage_quantity,
        sum(savings_plan_savings) as savings_plan_savings,
        sum(reserved_instance_savings) as reserved_instance_savings
    from source
    group by 1,2,3,4
)
select *
from summarised
order by billing_period_start desc, service_name asc;""",
        "aliases": [
            "startup_aws_only",
            "startup-aws-only",
            "startup aws only",
            "startup_aws_only_dataset",
        ],
    },
]


def _normalize_key(key: str) -> str:
    return (
        key.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace(".", "_")
    )


class LidaDbtModelStore:
    """Manages persisted dbt model metadata."""

    def __init__(self) -> None:
        self._pool: Optional[asyncpg.pool.Pool] = None
        self._memory: Dict[str, Dict[str, Any]] = {}
        self._alias_index: Dict[str, str] = {}
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

        if not self.configured:
            for model in _SEED_MODELS:
                coerced_id = str(self._coerce_uuid(model.get("id")))
                normalized_model = {**model, "id": coerced_id}
                self._register_memory(normalized_model)

    @staticmethod
    def _coerce_uuid(value: Optional[Any]) -> UUID:
        if isinstance(value, UUID):
            return value
        if value:
            try:
                return UUID(str(value))
            except (ValueError, TypeError):
                return uuid4()
        return uuid4()

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
        await self._seed_defaults()

    async def _ensure_table(self) -> None:
        if not self._pool or self._table_initialized:
            return
        async with self._pool.acquire() as conn:
            await conn.execute("CREATE SCHEMA IF NOT EXISTS dashboards")
            try:
                await conn.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
            except asyncpg.PostgresError:
                # Extension creation may require elevated privileges; continue even if it fails.
                pass
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dashboards.lida_dbt_models (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    slug TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    path TEXT,
                    sql TEXT,
                    aliases TEXT[] DEFAULT ARRAY[]::TEXT[],
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        self._table_initialized = True

    async def _seed_defaults(self) -> None:
        if not self._pool:
            return
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                for model in _SEED_MODELS:
                    model_uuid = self._coerce_uuid(model.get("id"))
                    slug = model.get("slug") or _normalize_key(str(model_uuid))
                    normalized_aliases = sorted(
                        {
                            _normalize_key(slug),
                            *(_normalize_key(alias) for alias in model.get("aliases", [])),
                        }
                    )
                    await conn.execute(
                        """
                        INSERT INTO dashboards.lida_dbt_models
                            (id, slug, name, description, path, sql, aliases)
                        VALUES ($1::uuid, $2, $3, $4, $5, $6, $7::text[])
                        ON CONFLICT (slug) DO UPDATE
                          SET name = EXCLUDED.name,
                              description = EXCLUDED.description,
                              path = EXCLUDED.path,
                              sql = EXCLUDED.sql,
                              aliases = EXCLUDED.aliases,
                              updated_at = NOW()
                        """,
                        model_uuid,
                        slug,
                        model["name"],
                        model.get("description", ""),
                        model.get("path", ""),
                        model.get("sql", ""),
                        normalized_aliases,
                    )

    def _register_memory(self, model: Dict[str, Any]) -> None:
        model_uuid = self._coerce_uuid(model.get("id"))
        model_id = str(model_uuid)
        slug = model.get("slug") or _normalize_key(model_id)
        aliases = model.get("aliases") or []
        normalized_aliases = {_normalize_key(slug), *(_normalize_key(alias) for alias in aliases)}
        normalized_aliases.add(_normalize_key(model_id))
        normalized_aliases.add(slug)
        payload = {
            **model,
            "id": model_id,
            "slug": slug,
            "aliases": list(sorted(normalized_aliases)),
            "created_at": model.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "updated_at": model.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        }
        self._memory[model_id] = payload
        self._memory[slug] = payload
        for alias in normalized_aliases:
            self._alias_index[alias] = model_id

    async def fetch_all(self) -> List[Dict[str, Any]]:
        if self._pool:
            await self._ensure_table()
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, slug, name, description, path, sql, aliases, created_at, updated_at
                    FROM dashboards.lida_dbt_models
                    ORDER BY name ASC
                    """
                )
            return [self._row_to_dict(row) for row in rows]

        async with self._memory_lock:
            return list(self._memory.values())

    async def get_by_id_or_alias(self, identifier: Optional[str]) -> Optional[Dict[str, Any]]:
        if not identifier:
            return None
        normalized = _normalize_key(identifier)
        try:
            uuid_identifier: Optional[UUID] = UUID(str(identifier))
        except (ValueError, TypeError):
            uuid_identifier = None

        if self._pool:
            await self._ensure_table()
            async with self._pool.acquire() as conn:
                if uuid_identifier:
                    row = await conn.fetchrow(
                        """
                        SELECT id, slug, name, description, path, sql, aliases, created_at, updated_at
                        FROM dashboards.lida_dbt_models
                        WHERE id = $1
                        """,
                        uuid_identifier,
                    )
                    if row:
                        return self._row_to_dict(row)

                row = await conn.fetchrow(
                    """
                    SELECT id, slug, name, description, path, sql, aliases, created_at, updated_at
                    FROM dashboards.lida_dbt_models
                    WHERE slug = $1
                       OR slug = $2
                       OR $2 = ANY(aliases)
                    """,
                    identifier,
                    normalized,
                )
                if row:
                    return self._row_to_dict(row)
            return None

        async with self._memory_lock:
            lookup_id = self._alias_index.get(normalized)
            if lookup_id and lookup_id in self._memory:
                return self._memory.get(lookup_id)
            if uuid_identifier:
                uuid_key = str(uuid_identifier)
                if uuid_key in self._memory:
                    return self._memory[uuid_key]
            return self._memory.get(identifier) or self._memory.get(normalized)

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> Dict[str, Any]:
        return {
            "id": str(row["id"]) if row["id"] is not None else None,
            "slug": row["slug"],
            "name": row["name"],
            "description": row["description"],
            "path": row["path"],
            "sql": row["sql"],
            "aliases": row["aliases"] or [],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        }
