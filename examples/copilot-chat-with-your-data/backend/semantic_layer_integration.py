"""
Semantic Layer Integration for LIDA Enhanced Manager.

This module connects LIDA's data summarization to dbt MCP server and ClickHouse,
providing enhanced metric definitions, business entity mapping, and semantic
understanding beyond basic column analysis.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics supported by the semantic layer."""
    SUM = "sum"
    COUNT = "count"
    AVERAGE = "average"
    RATIO = "ratio"
    TIME_SERIES = "time_series"
    CALCULATED = "calculated"
    DISTRIBUTION = "distribution"
    DEVIATION = "deviation"


@dataclass
class SemanticMetric:
    """Definition of a semantic metric with business context."""
    name: str
    type: MetricType
    sql: str
    base_field: str
    dimensions: List[str]
    narrative_goal: str
    recommended_chart: str
    description: str
    focus_compliant: bool = False
    business_context: Optional[str] = None
    unit: Optional[str] = None
    format: Optional[str] = None


@dataclass
class BusinessEntity:
    """Business entity definition with relationships."""
    name: str
    type: str  # table, view, metric
    description: str
    primary_key: Optional[str] = None
    relationships: List[Dict[str, str]] = None
    business_rules: List[str] = None


@dataclass
class SemanticModel:
    """Complete semantic model with entities, metrics, and relationships."""
    name: str
    entities: List[BusinessEntity]
    metrics: List[SemanticMetric]
    relationships: List[Dict[str, Any]]
    business_glossary: Dict[str, str]


class SemanticLayerIntegration:
    """
    Integration layer connecting LIDA to dbt MCP server and semantic models.

    This class enhances LIDA's basic data summarization with:
    - dbt metric definitions and business logic
    - ClickHouse OLAP query optimization
    - Business entity relationship understanding
    - Semantic-aware data profiling
    """

    def __init__(
        self,
        dbt_mcp_client=None,
        clickhouse_mcp_client=None
    ):
        """
        Initialize semantic layer integration.

        Args:
            dbt_mcp_client: Optional dbt MCP client for semantic model access
            clickhouse_mcp_client: Optional ClickHouse MCP client for data queries
        """
        self.dbt_client = dbt_mcp_client
        self.clickhouse_client = clickhouse_mcp_client
        self.mock_mode = dbt_mcp_client is None or clickhouse_mcp_client is None

        # Cache for semantic models and metrics
        self._semantic_models: Dict[str, SemanticModel] = {}
        self._metric_cache: Dict[str, SemanticMetric] = {}

        # Initialize with default semantic model if in mock mode
        if self.mock_mode:
            self._initialize_mock_semantic_model()

        logger.info("SemanticLayerIntegration initialized (mock_mode=%s)", self.mock_mode)

    def _initialize_mock_semantic_model(self):
        """Initialize mock semantic model for testing."""

        # Define business entities
        entities = [
            BusinessEntity(
                name="sales_data",
                type="table",
                description="Core sales transaction data",
                primary_key="transaction_id",
                relationships=[
                    {"type": "belongs_to", "entity": "customer", "key": "customer_id"},
                    {"type": "belongs_to", "entity": "product", "key": "product_id"}
                ],
                business_rules=[
                    "Revenue must be positive for completed transactions",
                    "Date must be within current fiscal year for active reporting"
                ]
            ),
            BusinessEntity(
                name="customer",
                type="dimension",
                description="Customer dimension with demographics",
                primary_key="customer_id"
            ),
            BusinessEntity(
                name="product",
                type="dimension",
                description="Product catalog with categories",
                primary_key="product_id"
            )
        ]

        # Define semantic metrics
        metrics = [
            SemanticMetric(
                name="total_revenue",
                type=MetricType.SUM,
                sql="SUM(revenue)",
                base_field="revenue",
                dimensions=["region", "product_category", "time_period"],
                narrative_goal="magnitude_comparison",
                recommended_chart="bar",
                description="Total revenue across all transactions",
                business_context="Key financial performance indicator",
                unit="USD",
                format="currency"
            ),
            SemanticMetric(
                name="revenue_trend",
                type=MetricType.TIME_SERIES,
                sql="SUM(revenue) OVER (ORDER BY date)",
                base_field="revenue",
                dimensions=["date"],
                narrative_goal="change_over_time",
                recommended_chart="line",
                description="Revenue trend over time",
                business_context="Track business growth trajectory"
            ),
            SemanticMetric(
                name="customer_count",
                type=MetricType.COUNT,
                sql="COUNT(DISTINCT customer_id)",
                base_field="customer_id",
                dimensions=["region", "segment"],
                narrative_goal="magnitude_comparison",
                recommended_chart="bar",
                description="Number of unique customers",
                business_context="Customer base size indicator"
            ),
            SemanticMetric(
                name="average_order_value",
                type=MetricType.AVERAGE,
                sql="AVG(revenue)",
                base_field="revenue",
                dimensions=["customer_segment", "product_category"],
                narrative_goal="distribution",
                recommended_chart="box_plot",
                description="Average revenue per transaction",
                business_context="Customer spending behavior metric",
                unit="USD",
                format="currency"
            ),
            SemanticMetric(
                name="conversion_rate",
                type=MetricType.RATIO,
                sql="COUNT(CASE WHEN status = 'completed' THEN 1 END) / COUNT(*)",
                base_field="status",
                dimensions=["channel", "campaign"],
                narrative_goal="magnitude_comparison",
                recommended_chart="bullet_chart",
                description="Percentage of successful conversions",
                business_context="Sales effectiveness measure",
                unit="percent",
                format="percentage"
            )
        ]

        # Create mock semantic model
        mock_model = SemanticModel(
            name="sales_analytics",
            entities=entities,
            metrics=metrics,
            relationships=[
                {
                    "type": "one_to_many",
                    "from": "customer",
                    "to": "sales_data",
                    "description": "Each customer can have multiple transactions"
                },
                {
                    "type": "many_to_one",
                    "from": "sales_data",
                    "to": "product",
                    "description": "Each transaction references one product"
                }
            ],
            business_glossary={
                "revenue": "Total monetary value of completed transactions",
                "customer_segment": "Classification of customers by value or behavior",
                "conversion": "Completion of desired business action",
                "churn": "Customer discontinuation of service"
            }
        )

        self._semantic_models["sales_analytics"] = mock_model

        # Populate metric cache
        for metric in metrics:
            self._metric_cache[metric.name] = metric

    async def get_semantic_model(self, model_name: str) -> Optional[SemanticModel]:
        """
        Retrieve semantic model by name.

        Args:
            model_name: Name of the semantic model

        Returns:
            SemanticModel if found, None otherwise
        """
        if self.mock_mode:
            return self._semantic_models.get(model_name)

        try:
            # In production, query dbt MCP server for semantic model
            if self.dbt_client:
                model_data = await self.dbt_client.get_semantic_model(model_name)
                return self._parse_dbt_semantic_model(model_data)

            return None

        except Exception as exc:
            logger.error("Failed to retrieve semantic model '%s': %s", model_name, exc)
            return None

    async def get_available_metrics(
        self,
        entity_name: Optional[str] = None
    ) -> List[SemanticMetric]:
        """
        Get list of available metrics, optionally filtered by entity.

        Args:
            entity_name: Optional entity name to filter metrics

        Returns:
            List of available semantic metrics
        """
        try:
            if self.mock_mode:
                all_metrics = list(self._metric_cache.values())

                if entity_name:
                    # Filter metrics relevant to the entity
                    filtered_metrics = []
                    for metric in all_metrics:
                        if (entity_name in metric.base_field or
                            entity_name in metric.sql.lower() or
                            any(entity_name in dim for dim in metric.dimensions)):
                            filtered_metrics.append(metric)
                    return filtered_metrics

                return all_metrics

            # In production, query dbt MCP server
            if self.dbt_client:
                metrics_data = await self.dbt_client.list_metrics(entity=entity_name)
                return [self._parse_dbt_metric(metric) for metric in metrics_data]

            return []

        except Exception as exc:
            logger.error("Failed to get available metrics: %s", exc)
            return []

    async def enhance_data_summary(
        self,
        data_summary: Dict[str, Any],
        domain: str = "sales_analytics"
    ) -> Dict[str, Any]:
        """
        Enhance LIDA data summary with semantic layer insights.

        Args:
            data_summary: Original LIDA data summary
            domain: Semantic model domain

        Returns:
            Enhanced data summary with semantic insights
        """
        try:
            # Get semantic model
            semantic_model = await self.get_semantic_model(domain)
            if not semantic_model:
                logger.warning("No semantic model found for domain '%s'", domain)
                return data_summary

            # Extract column information
            columns = data_summary.get('columns', [])
            data_types = data_summary.get('data_types', {})

            # Map columns to business entities
            entity_mappings = self._map_columns_to_entities(columns, semantic_model)

            # Get relevant metrics for the data
            relevant_metrics = await self._get_relevant_metrics(columns, semantic_model)

            # Generate business insights
            business_insights = self._generate_business_insights(
                columns, data_types, semantic_model
            )

            # Create enhanced summary
            enhanced_summary = data_summary.copy()
            enhanced_summary.update({
                'semantic_model': domain,
                'entity_mappings': entity_mappings,
                'available_metrics': [
                    {
                        'name': metric.name,
                        'type': metric.type.value,
                        'description': metric.description,
                        'recommended_chart': metric.recommended_chart,
                        'narrative_goal': metric.narrative_goal,
                        'business_context': metric.business_context
                    }
                    for metric in relevant_metrics
                ],
                'business_insights': business_insights,
                'semantic_relationships': self._extract_relationships(semantic_model),
                'business_glossary': semantic_model.business_glossary
            })

            logger.info("Enhanced data summary for domain '%s' with %d metrics",
                       domain, len(relevant_metrics))
            return enhanced_summary

        except Exception as exc:
            logger.error("Failed to enhance data summary: %s", exc)
            return data_summary

    def _map_columns_to_entities(
        self,
        columns: List[str],
        semantic_model: SemanticModel
    ) -> Dict[str, str]:
        """Map data columns to business entities."""
        mappings = {}

        for column in columns:
            column_lower = column.lower()

            # Check direct entity matches
            for entity in semantic_model.entities:
                entity_name_lower = entity.name.lower()

                if (column_lower == entity_name_lower or
                    column_lower.endswith(f"_{entity_name_lower}") or
                    column_lower.startswith(f"{entity_name_lower}_")):
                    mappings[column] = entity.name
                    break

            # Check metric base fields
            if column not in mappings:
                for metric in semantic_model.metrics:
                    if column_lower in metric.base_field.lower():
                        mappings[column] = f"metric_{metric.name}"
                        break

        return mappings

    async def _get_relevant_metrics(
        self,
        columns: List[str],
        semantic_model: SemanticModel
    ) -> List[SemanticMetric]:
        """Get metrics relevant to the available columns."""
        relevant_metrics = []

        for metric in semantic_model.metrics:
            # Check if metric's base field or dimensions match available columns
            metric_relevant = False

            # Check base field
            base_field_lower = metric.base_field.lower()
            for column in columns:
                if column.lower() in base_field_lower or base_field_lower in column.lower():
                    metric_relevant = True
                    break

            # Check dimensions
            if not metric_relevant:
                for dimension in metric.dimensions:
                    dimension_lower = dimension.lower()
                    for column in columns:
                        if column.lower() in dimension_lower or dimension_lower in column.lower():
                            metric_relevant = True
                            break
                    if metric_relevant:
                        break

            if metric_relevant:
                relevant_metrics.append(metric)

        return relevant_metrics

    def _generate_business_insights(
        self,
        columns: List[str],
        data_types: Dict[str, str],
        semantic_model: SemanticModel
    ) -> List[str]:
        """Generate business insights based on semantic understanding."""
        insights = []

        # Check for key business dimensions
        numeric_columns = [col for col, dtype in data_types.items() if dtype == 'numeric']
        categorical_columns = [col for col, dtype in data_types.items() if dtype == 'categorical']

        if numeric_columns:
            insights.append(f"Found {len(numeric_columns)} numeric measures suitable for aggregation")

        if categorical_columns:
            insights.append(f"Identified {len(categorical_columns)} dimensions for grouping and filtering")

        # Check for time dimensions
        time_columns = [col for col in columns if any(time_word in col.lower()
                      for time_word in ['date', 'time', 'period', 'month', 'year'])]
        if time_columns:
            insights.append("Time dimensions detected - trend analysis available")

        # Check for entity relationships
        entity_matches = len([col for col in columns
                            if any(entity.name.lower() in col.lower()
                                  for entity in semantic_model.entities)])
        if entity_matches > 1:
            insights.append("Multiple business entities present - relationship analysis possible")

        # Business context insights
        revenue_indicators = [col for col in columns
                            if any(word in col.lower()
                                  for word in ['revenue', 'sales', 'amount', 'value', 'cost'])]
        if revenue_indicators:
            insights.append("Financial metrics detected - KPI analysis recommended")

        return insights

    def _extract_relationships(self, semantic_model: SemanticModel) -> List[Dict[str, str]]:
        """Extract simplified relationship information."""
        return [
            {
                'type': rel['type'],
                'description': rel.get('description', ''),
                'from_entity': rel.get('from', ''),
                'to_entity': rel.get('to', '')
            }
            for rel in semantic_model.relationships
        ]

    async def query_metric(
        self,
        metric_name: str,
        dimensions: List[str] = None,
        filters: Dict[str, Any] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Query a specific metric with dimensions and filters.

        Args:
            metric_name: Name of the metric to query
            dimensions: List of dimensions to group by
            filters: Dict of filter conditions
            limit: Maximum number of results

        Returns:
            Query results with data and metadata
        """
        try:
            # Get metric definition
            metric = self._metric_cache.get(metric_name)
            if not metric:
                raise ValueError(f"Metric '{metric_name}' not found")

            if self.mock_mode:
                # Generate mock data for the metric
                return self._generate_mock_metric_data(metric, dimensions, filters, limit)

            # In production, use ClickHouse MCP client
            if self.clickhouse_client:
                query_sql = self._build_metric_query(metric, dimensions, filters, limit)
                result = await self.clickhouse_client.execute_query(query_sql)
                return self._format_query_result(result, metric)

            raise RuntimeError("No data client available")

        except Exception as exc:
            logger.error("Failed to query metric '%s': %s", metric_name, exc)
            raise

    def _generate_mock_metric_data(
        self,
        metric: SemanticMetric,
        dimensions: List[str],
        filters: Dict[str, Any],
        limit: int
    ) -> Dict[str, Any]:
        """Generate mock data for metric queries."""

        # Mock data based on metric type
        if metric.type == MetricType.SUM and "revenue" in metric.name:
            mock_data = [
                {"dimension": "North", "value": 125000},
                {"dimension": "South", "value": 98000},
                {"dimension": "East", "value": 142000},
                {"dimension": "West", "value": 87000}
            ]
        elif metric.type == MetricType.COUNT:
            mock_data = [
                {"dimension": "Enterprise", "value": 45},
                {"dimension": "SMB", "value": 123},
                {"dimension": "Consumer", "value": 298}
            ]
        elif metric.type == MetricType.TIME_SERIES:
            mock_data = [
                {"dimension": "2024-01", "value": 95000},
                {"dimension": "2024-02", "value": 108000},
                {"dimension": "2024-03", "value": 125000},
                {"dimension": "2024-04", "value": 142000}
            ]
        else:
            mock_data = [
                {"dimension": "Category A", "value": 100},
                {"dimension": "Category B", "value": 150},
                {"dimension": "Category C", "value": 75}
            ]

        return {
            "metric": metric.name,
            "data": mock_data[:limit],
            "dimensions": dimensions or ["dimension"],
            "filters": filters or {},
            "metadata": {
                "type": metric.type.value,
                "description": metric.description,
                "unit": metric.unit,
                "format": metric.format,
                "business_context": metric.business_context
            }
        }

    def _build_metric_query(
        self,
        metric: SemanticMetric,
        dimensions: List[str],
        filters: Dict[str, Any],
        limit: int
    ) -> str:
        """Build SQL query for metric."""

        # Build SELECT clause
        select_parts = []

        if dimensions:
            select_parts.extend(dimensions)

        select_parts.append(f"{metric.sql} as {metric.name}")

        # Build FROM clause (simplified - would be more complex in production)
        from_clause = "FROM sales_data"  # Would be determined by semantic model

        # Build WHERE clause
        where_parts = []
        if filters:
            for key, value in filters.items():
                if isinstance(value, str):
                    where_parts.append(f"{key} = '{value}'")
                else:
                    where_parts.append(f"{key} = {value}")

        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

        # Build GROUP BY clause
        group_by_clause = f"GROUP BY {', '.join(dimensions)}" if dimensions else ""

        # Combine query parts
        query_parts = [
            f"SELECT {', '.join(select_parts)}",
            from_clause,
            where_clause,
            group_by_clause,
            f"LIMIT {limit}"
        ]

        return " ".join(part for part in query_parts if part)

    def _format_query_result(
        self,
        result: Dict[str, Any],
        metric: SemanticMetric
    ) -> Dict[str, Any]:
        """Format query result with metadata."""
        return {
            "metric": metric.name,
            "data": result.get("data", []),
            "metadata": {
                "type": metric.type.value,
                "description": metric.description,
                "unit": metric.unit,
                "format": metric.format,
                "business_context": metric.business_context
            }
        }

    def _parse_dbt_semantic_model(self, model_data: Dict[str, Any]) -> SemanticModel:
        """Parse dbt semantic model data into SemanticModel."""
        # This would parse actual dbt semantic model structure
        # For now, return a placeholder
        return SemanticModel(
            name=model_data.get("name", "unknown"),
            entities=[],
            metrics=[],
            relationships=[],
            business_glossary={}
        )

    def _parse_dbt_metric(self, metric_data: Dict[str, Any]) -> SemanticMetric:
        """Parse dbt metric data into SemanticMetric."""
        # This would parse actual dbt metric structure
        return SemanticMetric(
            name=metric_data.get("name", "unknown"),
            type=MetricType.SUM,
            sql=metric_data.get("sql", ""),
            base_field="",
            dimensions=[],
            narrative_goal="magnitude_comparison",
            recommended_chart="bar",
            description=metric_data.get("description", "")
        )


# Factory function for integration
async def create_semantic_layer_integration(
    dbt_mcp_client=None,
    clickhouse_mcp_client=None
) -> SemanticLayerIntegration:
    """
    Factory function to create SemanticLayerIntegration instance.

    Args:
        dbt_mcp_client: Optional dbt MCP client
        clickhouse_mcp_client: Optional ClickHouse MCP client

    Returns:
        Configured SemanticLayerIntegration instance
    """
    integration = SemanticLayerIntegration(dbt_mcp_client, clickhouse_mcp_client)
    logger.info("Created SemanticLayerIntegration for LIDA enhancement")
    return integration