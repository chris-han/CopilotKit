"""Persistence for LIDA dbt model catalogue."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import os

import asyncpg


_SEED_MODELS: List[Dict[str, Any]] = [
    {
        "id": "salesData",
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
        "aliases": ["salesdata", "sales_data", "sales-performance"],
    },
    {
        "id": "productData",
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
        "aliases": ["productdata", "product_data", "product-performance"],
    },
    {
        "id": "categoryData",
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
        "aliases": ["categorydata", "category_data", "category-mix"],
    },
    {
        "id": "regionalData",
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
        "aliases": ["regionaldata", "regional_data", "regional-sales"],
    },
    {
        "id": "demographicsData",
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
        "aliases": ["demographicsdata", "customer-demographics"],
    },
    {
        "id": "enterprise_multi_cloud",
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
        sum(usage_quantity) as usage_quantity,
        sum(credits) as credits,
        sum(reserved_savings) as reserved_savings,
        sum(spot_savings) as spot_savings
    from source
    group by 1, 2, 3, 4
)
select *
from aggregated
order by billing_period_start desc, provider asc, service asc;""",
        "aliases": [
            "enterprise-multi-cloud",
            "enterprise_multi_cloud",
            "enterprise_multi_cloud.csv",
            "enterprise_multi_cloud_dataset",
        ],
    },
    {
        "id": "small_company_finops",
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
            "small-company-finops",
            "small_company_finops",
            "small_company_finops.csv",
            "small_company_finops_dataset",
        ],
    },
    {
        "id": "startup_aws_only",
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
            "startup-aws-only",
            "startup_aws_only",
            "startup_aws_only.csv",
            "startup_aws_only_dataset",
        ],
    },
]


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace(" ", "_")


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
                self._register_memory(model)

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
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dashboards.lida_dbt_models (
                    id TEXT PRIMARY KEY,
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
                    await conn.execute(
                        """
                        INSERT INTO dashboards.lida_dbt_models
                            (id, name, description, path, sql, aliases)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (id) DO UPDATE
                          SET name = EXCLUDED.name,
                              description = EXCLUDED.description,
                              path = EXCLUDED.path,
                              sql = EXCLUDED.sql,
                              aliases = EXCLUDED.aliases,
                              updated_at = NOW()
                        """,
                        model["id"],
                        model["name"],
                        model.get("description", ""),
                        model.get("path", ""),
                        model.get("sql", ""),
                        model.get("aliases", []),
                    )

    def _register_memory(self, model: Dict[str, Any]) -> None:
        model_id = model["id"]
        aliases = model.get("aliases") or []
        normalized_aliases = {_normalize_key(model_id), *( _normalize_key(alias) for alias in aliases )}
        payload = {
            **model,
            "aliases": list(sorted(normalized_aliases)),
            "created_at": model.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "updated_at": model.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        }
        self._memory[model_id] = payload
        for alias in normalized_aliases:
            self._alias_index[alias] = model_id

    async def fetch_all(self) -> List[Dict[str, Any]]:
        if self._pool:
            await self._ensure_table()
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, name, description, path, sql, aliases, created_at, updated_at
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

        if self._pool:
            await self._ensure_table()
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, name, description, path, sql, aliases, created_at, updated_at
                    FROM dashboards.lida_dbt_models
                    WHERE id = $1 OR $1 = ANY(aliases)
                    """,
                    identifier,
                )
                if row:
                    return self._row_to_dict(row)

                # Try normalized key if 1st lookup fails.
                if normalized != identifier:
                    row = await conn.fetchrow(
                        """
                        SELECT id, name, description, path, sql, aliases, created_at, updated_at
                        FROM dashboards.lida_dbt_models
                        WHERE id = $1 OR $1 = ANY(aliases)
                        """,
                        normalized,
                    )
                    if row:
                        return self._row_to_dict(row)
            return None

        async with self._memory_lock:
            lookup_id = self._alias_index.get(normalized) or identifier
            return self._memory.get(lookup_id)

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "path": row["path"],
            "sql": row["sql"],
            "aliases": row["aliases"] or [],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        }
