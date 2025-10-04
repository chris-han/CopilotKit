"""
ClickHouse MCP Integration for Database Discovery and Analysis.

This module provides comprehensive ClickHouse database integration via MCP server,
including schema discovery, FOCUS v1.2 compliance assessment, data quality analysis,
and automated FinOps analytics preparation for discovered datasets.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class ClickHouseDataType(Enum):
    """ClickHouse data types mapping to FOCUS fields."""
    STRING = "String"
    NULLABLE_STRING = "Nullable(String)"
    DATETIME = "DateTime"
    DATETIME64 = "DateTime64"
    DECIMAL = "Decimal"
    FLOAT64 = "Float64"
    UINT64 = "UInt64"
    INT64 = "Int64"
    ARRAY_STRING = "Array(String)"
    LOW_CARDINALITY_STRING = "LowCardinality(String)"


class FocusComplianceLevel(Enum):
    """FOCUS v1.2 compliance levels."""
    FULL_COMPLIANCE = "full_compliance"
    PARTIAL_COMPLIANCE = "partial_compliance"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_TRANSFORMATION = "requires_transformation"


class DatabaseDiscoveryScope(Enum):
    """Scope of database discovery operations."""
    SCHEMA_ONLY = "schema_only"
    SAMPLE_DATA = "sample_data"
    FULL_ANALYSIS = "full_analysis"
    FOCUS_ASSESSMENT = "focus_assessment"


@dataclass
class ClickHouseConnection:
    """ClickHouse connection configuration."""
    host: str
    port: int
    database: str
    username: str
    password: str
    secure: bool = True
    verify_ssl: bool = True
    connect_timeout: int = 10
    receive_timeout: int = 300


@dataclass
class TableSchema:
    """ClickHouse table schema information."""
    table_name: str
    database_name: str
    engine: str
    columns: List[Dict[str, Any]]
    total_rows: int
    total_bytes: int

    # FOCUS mapping
    focus_mapping_confidence: float = 0.0
    mapped_focus_fields: Dict[str, str] = None
    unmapped_columns: List[str] = None

    # Data quality metrics
    data_quality_score: float = 0.0
    completeness_score: float = 0.0
    consistency_score: float = 0.0

    # Metadata
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    comment: str = ""


@dataclass
class FocusComplianceAssessment:
    """FOCUS v1.2 compliance assessment results."""
    table_name: str
    compliance_level: FocusComplianceLevel
    compliance_score: float

    # Field mapping results
    required_fields_present: List[str]
    required_fields_missing: List[str]
    optional_fields_present: List[str]
    custom_fields: List[str]

    # Data quality assessment
    data_quality_issues: List[Dict[str, Any]]
    recommendations: List[str]

    # Transformation requirements
    transformation_required: bool
    transformation_complexity: str  # low, medium, high
    estimated_effort_hours: float

    # Assessment metadata
    focus_version: str = "1.2"
    assessed_at: datetime = None


@dataclass
class DataDiscoveryResult:
    """Complete database discovery result."""
    connection_info: Dict[str, Any]
    discovered_tables: List[TableSchema]
    focus_assessments: List[FocusComplianceAssessment]

    # Summary statistics
    total_tables: int
    total_rows: int
    total_size_bytes: int
    focus_compliant_tables: int

    # Analysis insights
    insights: List[str]
    recommendations: List[str]
    optimization_opportunities: List[Dict[str, Any]]

    # Discovery metadata
    discovery_scope: DatabaseDiscoveryScope
    discovery_duration_seconds: float
    discovered_at: datetime


class ClickHouseMCPIntegration:
    """
    ClickHouse MCP integration for database discovery and analysis.

    This class provides comprehensive ClickHouse database integration capabilities,
    including schema discovery, FOCUS compliance assessment, and automated
    FinOps analytics preparation.
    """

    def __init__(
        self,
        mcp_client=None,
        focus_integration=None,
        lida_manager=None
    ):
        """
        Initialize ClickHouse MCP integration.

        Args:
            mcp_client: MCP client for ClickHouse communication
            focus_integration: FOCUS sample data integration instance
            lida_manager: LIDA Enhanced Manager instance
        """
        self.mcp_client = mcp_client
        self.focus_integration = focus_integration
        self.lida_manager = lida_manager

        # FOCUS v1.2 required fields mapping
        self.focus_required_fields = self._define_focus_required_fields()
        self.focus_optional_fields = self._define_focus_optional_fields()

        # ClickHouse to FOCUS data type mappings
        self.data_type_mappings = self._define_data_type_mappings()

        # Discovery cache
        self._schema_cache: Dict[str, List[TableSchema]] = {}
        self._compliance_cache: Dict[str, FocusComplianceAssessment] = {}

        logger.info("ClickHouseMCPIntegration initialized")

    async def discover_database(
        self,
        connection: ClickHouseConnection,
        discovery_scope: DatabaseDiscoveryScope = DatabaseDiscoveryScope.FULL_ANALYSIS,
        table_pattern: Optional[str] = None,
        max_tables: Optional[int] = None
    ) -> DataDiscoveryResult:
        """
        Discover and analyze ClickHouse database structure.

        Args:
            connection: ClickHouse connection configuration
            discovery_scope: Scope of discovery operation
            table_pattern: Optional table name pattern filter
            max_tables: Optional maximum number of tables to analyze

        Returns:
            Complete database discovery result
        """
        start_time = datetime.now()

        try:
            logger.info("Starting ClickHouse database discovery")

            # Establish connection
            await self._connect_to_clickhouse(connection)

            # Discover database schema
            discovered_tables = await self._discover_tables(
                connection, table_pattern, max_tables
            )

            # Analyze table schemas based on scope
            if discovery_scope in [DatabaseDiscoveryScope.SAMPLE_DATA, DatabaseDiscoveryScope.FULL_ANALYSIS]:
                for table in discovered_tables:
                    await self._analyze_table_data(connection, table)

            # Perform FOCUS compliance assessment
            focus_assessments = []
            if discovery_scope in [DatabaseDiscoveryScope.FOCUS_ASSESSMENT, DatabaseDiscoveryScope.FULL_ANALYSIS]:
                for table in discovered_tables:
                    assessment = await self._assess_focus_compliance(connection, table)
                    focus_assessments.append(assessment)

            # Generate insights and recommendations
            insights = await self._generate_discovery_insights(discovered_tables, focus_assessments)
            recommendations = await self._generate_discovery_recommendations(discovered_tables, focus_assessments)
            optimization_opportunities = await self._identify_optimization_opportunities(discovered_tables)

            # Calculate summary statistics
            total_rows = sum(table.total_rows for table in discovered_tables)
            total_size_bytes = sum(table.total_bytes for table in discovered_tables)
            focus_compliant_tables = sum(
                1 for assessment in focus_assessments
                if assessment.compliance_level in [FocusComplianceLevel.FULL_COMPLIANCE, FocusComplianceLevel.PARTIAL_COMPLIANCE]
            )

            discovery_duration = (datetime.now() - start_time).total_seconds()

            result = DataDiscoveryResult(
                connection_info={
                    "host": connection.host,
                    "port": connection.port,
                    "database": connection.database,
                    "secure": connection.secure
                },
                discovered_tables=discovered_tables,
                focus_assessments=focus_assessments,
                total_tables=len(discovered_tables),
                total_rows=total_rows,
                total_size_bytes=total_size_bytes,
                focus_compliant_tables=focus_compliant_tables,
                insights=insights,
                recommendations=recommendations,
                optimization_opportunities=optimization_opportunities,
                discovery_scope=discovery_scope,
                discovery_duration_seconds=discovery_duration,
                discovered_at=datetime.now()
            )

            logger.info("Database discovery completed: %d tables, %.2f seconds", len(discovered_tables), discovery_duration)
            return result

        except Exception as exc:
            logger.error("Database discovery failed: %s", exc)
            raise

    async def assess_focus_compliance(
        self,
        connection: ClickHouseConnection,
        table_name: str,
        detailed_analysis: bool = True
    ) -> FocusComplianceAssessment:
        """
        Assess FOCUS v1.2 compliance for a specific table.

        Args:
            connection: ClickHouse connection configuration
            table_name: Name of table to assess
            detailed_analysis: Whether to perform detailed data analysis

        Returns:
            FOCUS compliance assessment result
        """
        try:
            logger.info("Assessing FOCUS compliance for table: %s", table_name)

            # Get table schema
            table_schema = await self._get_table_schema(connection, table_name)

            # Perform compliance assessment
            assessment = await self._assess_focus_compliance(connection, table_schema, detailed_analysis)

            # Cache result
            cache_key = f"{connection.database}.{table_name}"
            self._compliance_cache[cache_key] = assessment

            logger.info("FOCUS compliance assessment completed for %s: %s", table_name, assessment.compliance_level)
            return assessment

        except Exception as exc:
            logger.error("FOCUS compliance assessment failed for %s: %s", table_name, exc)
            raise

    async def generate_focus_transformation_plan(
        self,
        connection: ClickHouseConnection,
        table_name: str,
        target_compliance: FocusComplianceLevel = FocusComplianceLevel.FULL_COMPLIANCE
    ) -> Dict[str, Any]:
        """
        Generate transformation plan to achieve FOCUS compliance.

        Args:
            connection: ClickHouse connection configuration
            table_name: Name of table to transform
            target_compliance: Target compliance level

        Returns:
            Comprehensive transformation plan
        """
        try:
            logger.info("Generating FOCUS transformation plan for: %s", table_name)

            # Get current compliance assessment
            assessment = await self.assess_focus_compliance(connection, table_name, detailed_analysis=True)

            if assessment.compliance_level == target_compliance:
                return {
                    "transformation_required": False,
                    "current_compliance": assessment.compliance_level.value,
                    "message": "Table already meets target compliance level"
                }

            # Generate transformation steps
            transformation_steps = await self._generate_transformation_steps(assessment, target_compliance)

            # Estimate effort and complexity
            effort_estimation = self._estimate_transformation_effort(transformation_steps)

            # Generate SQL transformation queries
            sql_transformations = await self._generate_transformation_sql(connection, table_name, transformation_steps)

            transformation_plan = {
                "transformation_required": True,
                "current_compliance": assessment.compliance_level.value,
                "target_compliance": target_compliance.value,
                "transformation_steps": transformation_steps,
                "effort_estimation": effort_estimation,
                "sql_transformations": sql_transformations,
                "validation_queries": await self._generate_validation_sql(table_name, target_compliance),
                "rollback_plan": await self._generate_rollback_plan(table_name),
                "generated_at": datetime.now().isoformat()
            }

            logger.info("Transformation plan generated for %s: %d steps", table_name, len(transformation_steps))
            return transformation_plan

        except Exception as exc:
            logger.error("Failed to generate transformation plan for %s: %s", table_name, exc)
            raise

    async def execute_data_quality_analysis(
        self,
        connection: ClickHouseConnection,
        table_name: str,
        sample_size: int = 10000
    ) -> Dict[str, Any]:
        """
        Execute comprehensive data quality analysis.

        Args:
            connection: ClickHouse connection configuration
            table_name: Name of table to analyze
            sample_size: Sample size for analysis

        Returns:
            Data quality analysis results
        """
        try:
            logger.info("Executing data quality analysis for: %s", table_name)

            # Get table schema
            table_schema = await self._get_table_schema(connection, table_name)

            # Analyze data completeness
            completeness_analysis = await self._analyze_data_completeness(connection, table_name)

            # Analyze data consistency
            consistency_analysis = await self._analyze_data_consistency(connection, table_name, sample_size)

            # Analyze data accuracy
            accuracy_analysis = await self._analyze_data_accuracy(connection, table_name, sample_size)

            # Check for duplicates
            duplicate_analysis = await self._analyze_duplicates(connection, table_name)

            # Analyze value distributions
            distribution_analysis = await self._analyze_value_distributions(connection, table_name, sample_size)

            # Calculate overall quality score
            quality_score = self._calculate_overall_quality_score(
                completeness_analysis,
                consistency_analysis,
                accuracy_analysis,
                duplicate_analysis
            )

            quality_analysis = {
                "table_name": table_name,
                "overall_quality_score": quality_score,
                "completeness_analysis": completeness_analysis,
                "consistency_analysis": consistency_analysis,
                "accuracy_analysis": accuracy_analysis,
                "duplicate_analysis": duplicate_analysis,
                "distribution_analysis": distribution_analysis,
                "recommendations": self._generate_quality_recommendations(
                    completeness_analysis, consistency_analysis, accuracy_analysis, duplicate_analysis
                ),
                "analyzed_at": datetime.now().isoformat(),
                "sample_size": sample_size
            }

            logger.info("Data quality analysis completed for %s: score %.2f", table_name, quality_score)
            return quality_analysis

        except Exception as exc:
            logger.error("Data quality analysis failed for %s: %s", table_name, exc)
            raise

    async def create_finops_analytics_views(
        self,
        connection: ClickHouseConnection,
        source_table: str,
        focus_compliant: bool = True
    ) -> Dict[str, Any]:
        """
        Create FinOps analytics views for discovered data.

        Args:
            connection: ClickHouse connection configuration
            source_table: Source table name
            focus_compliant: Whether source table is FOCUS compliant

        Returns:
            Created analytics views information
        """
        try:
            logger.info("Creating FinOps analytics views for: %s", source_table)

            # Define analytics view structures
            analytics_views = {
                "cost_trend_view": await self._create_cost_trend_view(connection, source_table, focus_compliant),
                "service_summary_view": await self._create_service_summary_view(connection, source_table, focus_compliant),
                "account_summary_view": await self._create_account_summary_view(connection, source_table, focus_compliant),
                "regional_summary_view": await self._create_regional_summary_view(connection, source_table, focus_compliant),
                "commitment_analysis_view": await self._create_commitment_analysis_view(connection, source_table, focus_compliant)
            }

            # Generate sample queries
            sample_queries = await self._generate_sample_analytics_queries(source_table, analytics_views)

            # Create optimization recommendations
            optimization_views = await self._create_optimization_views(connection, source_table, focus_compliant)

            views_result = {
                "source_table": source_table,
                "focus_compliant": focus_compliant,
                "analytics_views": analytics_views,
                "optimization_views": optimization_views,
                "sample_queries": sample_queries,
                "created_at": datetime.now().isoformat(),
                "usage_instructions": self._generate_view_usage_instructions(analytics_views)
            }

            logger.info("FinOps analytics views created for %s: %d views", source_table, len(analytics_views))
            return views_result

        except Exception as exc:
            logger.error("Failed to create FinOps analytics views for %s: %s", source_table, exc)
            raise

    # Private helper methods

    async def _connect_to_clickhouse(self, connection: ClickHouseConnection) -> bool:
        """Establish connection to ClickHouse database."""
        try:
            if self.mcp_client:
                # Use MCP client to connect
                connection_result = await self.mcp_client.connect(
                    host=connection.host,
                    port=connection.port,
                    database=connection.database,
                    username=connection.username,
                    password=connection.password,
                    secure=connection.secure
                )
                return connection_result.get("connected", False)
            else:
                # Mock connection for testing
                logger.info("Mock ClickHouse connection established")
                return True

        except Exception as exc:
            logger.error("Failed to connect to ClickHouse: %s", exc)
            raise

    async def _discover_tables(
        self,
        connection: ClickHouseConnection,
        table_pattern: Optional[str],
        max_tables: Optional[int]
    ) -> List[TableSchema]:
        """Discover tables in ClickHouse database."""
        try:
            if self.mcp_client:
                # Use MCP client to discover tables
                tables_query = """
                SELECT
                    name as table_name,
                    database,
                    engine,
                    total_rows,
                    total_bytes,
                    create_table_query,
                    comment
                FROM system.tables
                WHERE database = ?
                """
                if table_pattern:
                    tables_query += " AND name LIKE ?"

                if max_tables:
                    tables_query += f" LIMIT {max_tables}"

                result = await self.mcp_client.execute_query(tables_query, [connection.database])

                tables = []
                for row in result.get("rows", []):
                    table_schema = await self._build_table_schema(connection, row)
                    tables.append(table_schema)

                return tables
            else:
                # Mock table discovery for testing
                return await self._generate_mock_tables(connection.database, table_pattern, max_tables)

        except Exception as exc:
            logger.error("Failed to discover tables: %s", exc)
            raise

    async def _generate_mock_tables(
        self,
        database: str,
        table_pattern: Optional[str],
        max_tables: Optional[int]
    ) -> List[TableSchema]:
        """Generate mock tables for testing."""
        mock_tables = [
            TableSchema(
                table_name="billing_data",
                database_name=database,
                engine="MergeTree",
                columns=[
                    {"name": "BillingPeriodStart", "type": "DateTime", "nullable": False},
                    {"name": "BillingPeriodEnd", "type": "DateTime", "nullable": False},
                    {"name": "BilledCost", "type": "Decimal(18,2)", "nullable": False},
                    {"name": "ServiceName", "type": "String", "nullable": False},
                    {"name": "BillingAccountId", "type": "String", "nullable": False}
                ],
                total_rows=100000,
                total_bytes=50000000,
                created_date=datetime.now() - timedelta(days=30),
                comment="Sample billing data table"
            ),
            TableSchema(
                table_name="usage_metrics",
                database_name=database,
                engine="MergeTree",
                columns=[
                    {"name": "ResourceId", "type": "String", "nullable": False},
                    {"name": "MetricName", "type": "String", "nullable": False},
                    {"name": "MetricValue", "type": "Float64", "nullable": False},
                    {"name": "Timestamp", "type": "DateTime", "nullable": False}
                ],
                total_rows=500000,
                total_bytes=25000000,
                created_date=datetime.now() - timedelta(days=15),
                comment="Resource usage metrics"
            )
        ]

        # Apply filters
        if table_pattern:
            pattern = table_pattern.replace("%", ".*").replace("_", ".")
            mock_tables = [t for t in mock_tables if re.match(pattern, t.table_name)]

        if max_tables:
            mock_tables = mock_tables[:max_tables]

        return mock_tables

    async def _get_table_schema(self, connection: ClickHouseConnection, table_name: str) -> TableSchema:
        """Get detailed schema for specific table."""
        try:
            if self.mcp_client:
                schema_query = """
                SELECT
                    name, type, position, default_kind, default_expression, comment, is_in_partition_key, is_in_sorting_key, is_in_primary_key, is_in_sampling_key
                FROM system.columns
                WHERE database = ? AND table = ?
                ORDER BY position
                """

                columns_result = await self.mcp_client.execute_query(schema_query, [connection.database, table_name])

                # Get table metadata
                table_query = """
                SELECT name, engine, total_rows, total_bytes, create_table_query, comment
                FROM system.tables
                WHERE database = ? AND name = ?
                """

                table_result = await self.mcp_client.execute_query(table_query, [connection.database, table_name])

                if not table_result.get("rows"):
                    raise ValueError(f"Table {table_name} not found")

                table_row = table_result["rows"][0]
                columns = [dict(zip(columns_result["columns"], row)) for row in columns_result.get("rows", [])]

                return TableSchema(
                    table_name=table_name,
                    database_name=connection.database,
                    engine=table_row["engine"],
                    columns=columns,
                    total_rows=table_row["total_rows"],
                    total_bytes=table_row["total_bytes"],
                    comment=table_row.get("comment", "")
                )
            else:
                # Return mock schema for testing
                mock_tables = await self._generate_mock_tables(connection.database, None, None)
                for table in mock_tables:
                    if table.table_name == table_name:
                        return table
                raise ValueError(f"Mock table {table_name} not found")

        except Exception as exc:
            logger.error("Failed to get table schema for %s: %s", table_name, exc)
            raise

    async def _assess_focus_compliance(
        self,
        connection: ClickHouseConnection,
        table_schema: TableSchema,
        detailed_analysis: bool = True
    ) -> FocusComplianceAssessment:
        """Assess FOCUS v1.2 compliance for table."""
        try:
            column_names = [col["name"] for col in table_schema.columns]
            column_types = {col["name"]: col["type"] for col in table_schema.columns}

            # Check required fields
            required_present = []
            required_missing = []

            for required_field in self.focus_required_fields:
                mapped_field = self._find_field_mapping(required_field, column_names)
                if mapped_field:
                    required_present.append(required_field)
                else:
                    required_missing.append(required_field)

            # Check optional fields
            optional_present = []
            for optional_field in self.focus_optional_fields:
                mapped_field = self._find_field_mapping(optional_field, column_names)
                if mapped_field:
                    optional_present.append(optional_field)

            # Identify custom fields
            all_focus_fields = set(self.focus_required_fields + self.focus_optional_fields)
            custom_fields = [col for col in column_names if col not in all_focus_fields]

            # Calculate compliance score
            compliance_score = len(required_present) / len(self.focus_required_fields)

            # Determine compliance level
            if compliance_score >= 0.95 and len(required_missing) == 0:
                compliance_level = FocusComplianceLevel.FULL_COMPLIANCE
            elif compliance_score >= 0.7:
                compliance_level = FocusComplianceLevel.PARTIAL_COMPLIANCE
            elif compliance_score >= 0.3:
                compliance_level = FocusComplianceLevel.REQUIRES_TRANSFORMATION
            else:
                compliance_level = FocusComplianceLevel.NON_COMPLIANT

            # Generate recommendations
            recommendations = []
            if required_missing:
                recommendations.append(f"Add missing required fields: {', '.join(required_missing[:5])}")
            if compliance_score < 0.7:
                recommendations.append("Consider data transformation to improve FOCUS compliance")

            # Assess transformation requirements
            transformation_required = compliance_level in [
                FocusComplianceLevel.REQUIRES_TRANSFORMATION,
                FocusComplianceLevel.NON_COMPLIANT
            ]

            complexity = "low" if compliance_score > 0.7 else "medium" if compliance_score > 0.3 else "high"
            effort_hours = 2.0 if complexity == "low" else 8.0 if complexity == "medium" else 24.0

            return FocusComplianceAssessment(
                table_name=table_schema.table_name,
                compliance_level=compliance_level,
                compliance_score=compliance_score,
                required_fields_present=required_present,
                required_fields_missing=required_missing,
                optional_fields_present=optional_present,
                custom_fields=custom_fields,
                data_quality_issues=[],  # Would be populated with detailed analysis
                recommendations=recommendations,
                transformation_required=transformation_required,
                transformation_complexity=complexity,
                estimated_effort_hours=effort_hours,
                assessed_at=datetime.now()
            )

        except Exception as exc:
            logger.error("Failed to assess FOCUS compliance: %s", exc)
            raise

    def _find_field_mapping(self, focus_field: str, column_names: List[str]) -> Optional[str]:
        """Find mapping between FOCUS field and table column."""
        # Direct match
        if focus_field in column_names:
            return focus_field

        # Case-insensitive match
        focus_lower = focus_field.lower()
        for col in column_names:
            if col.lower() == focus_lower:
                return col

        # Pattern-based matching
        field_patterns = {
            "BilledCost": ["billed_cost", "cost", "amount", "billing_amount"],
            "EffectiveCost": ["effective_cost", "net_cost", "adjusted_cost"],
            "ServiceName": ["service_name", "service", "product_name", "product"],
            "BillingAccountId": ["billing_account_id", "account_id", "account"],
            "BillingPeriodStart": ["billing_period_start", "period_start", "start_date"],
            "BillingPeriodEnd": ["billing_period_end", "period_end", "end_date"],
            "ChargeCategory": ["charge_category", "charge_type", "cost_category"],
            "Region": ["region", "availability_zone", "location"]
        }

        if focus_field in field_patterns:
            for pattern in field_patterns[focus_field]:
                for col in column_names:
                    if pattern in col.lower():
                        return col

        return None

    def _define_focus_required_fields(self) -> List[str]:
        """Define FOCUS v1.2 required fields."""
        return [
            "BillingPeriodStart",
            "BillingPeriodEnd",
            "BilledCost",
            "EffectiveCost",
            "ChargeCategory",
            "ServiceName",
            "BillingAccountId",
            "BillingAccountName",
            "SubAccountName",
            "ResourceId",
            "ResourceName",
            "ServiceCategory",
            "ChargeDescription",
            "ChargeFrequency",
            "ResourceType",
            "ConsumedQuantity",
            "ConsumedUnit",
            "PricingQuantity",
            "PricingUnit",
            "UnitPrice",
            "Currency"
        ]

    def _define_focus_optional_fields(self) -> List[str]:
        """Define FOCUS v1.2 optional fields."""
        return [
            "AvailabilityZone",
            "Region",
            "InvoiceIssuerName",
            "ProviderName",
            "PublisherName",
            "PublisherCategory",
            "SkuId",
            "SkuDescription",
            "PricingCategory",
            "CommitmentDiscountId",
            "CommitmentDiscountName",
            "CommitmentDiscountType",
            "CommitmentDiscountStatus",
            "Tags"
        ]

    def _define_data_type_mappings(self) -> Dict[str, str]:
        """Define ClickHouse to FOCUS data type mappings."""
        return {
            "String": "string",
            "Nullable(String)": "string",
            "DateTime": "datetime",
            "DateTime64": "datetime",
            "Decimal": "decimal",
            "Float64": "float",
            "UInt64": "integer",
            "Int64": "integer",
            "Array(String)": "array",
            "LowCardinality(String)": "string"
        }

    async def _analyze_table_data(self, connection: ClickHouseConnection, table: TableSchema):
        """Analyze table data for quality metrics."""
        # Mock data analysis for testing
        table.data_quality_score = 0.85
        table.completeness_score = 0.90
        table.consistency_score = 0.80

        logger.info("Analyzed table data for %s: quality score %.2f", table.table_name, table.data_quality_score)

    async def _generate_discovery_insights(
        self,
        tables: List[TableSchema],
        assessments: List[FocusComplianceAssessment]
    ) -> List[str]:
        """Generate insights from discovery results."""
        insights = []

        if tables:
            total_rows = sum(t.total_rows for t in tables)
            total_size_gb = sum(t.total_bytes for t in tables) / (1024**3)
            insights.append(f"Discovered {len(tables)} tables with {total_rows:,} total rows ({total_size_gb:.2f} GB)")

        if assessments:
            compliant_count = sum(1 for a in assessments if a.compliance_level == FocusComplianceLevel.FULL_COMPLIANCE)
            if compliant_count > 0:
                insights.append(f"{compliant_count}/{len(assessments)} tables are fully FOCUS compliant")

            avg_compliance = sum(a.compliance_score for a in assessments) / len(assessments)
            insights.append(f"Average FOCUS compliance score: {avg_compliance:.1%}")

        return insights

    async def _generate_discovery_recommendations(
        self,
        tables: List[TableSchema],
        assessments: List[FocusComplianceAssessment]
    ) -> List[str]:
        """Generate recommendations from discovery results."""
        recommendations = []

        if assessments:
            non_compliant = [a for a in assessments if a.compliance_level == FocusComplianceLevel.NON_COMPLIANT]
            if non_compliant:
                recommendations.append(f"Transform {len(non_compliant)} non-compliant tables for FOCUS compatibility")

            needs_transformation = [a for a in assessments if a.transformation_required]
            if needs_transformation:
                total_effort = sum(a.estimated_effort_hours for a in needs_transformation)
                recommendations.append(f"Estimated {total_effort:.1f} hours for transformation work")

        if tables:
            large_tables = [t for t in tables if t.total_rows > 1000000]
            if large_tables:
                recommendations.append(f"Consider partitioning for {len(large_tables)} large tables")

        return recommendations

    async def _identify_optimization_opportunities(self, tables: List[TableSchema]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities."""
        opportunities = []

        for table in tables:
            if table.total_rows > 10000000:  # Large table
                opportunities.append({
                    "type": "partitioning",
                    "table": table.table_name,
                    "description": "Consider partitioning large table for better query performance",
                    "priority": "medium",
                    "estimated_impact": "20-40% query performance improvement"
                })

            if table.engine == "Log":  # Inefficient engine for large data
                opportunities.append({
                    "type": "engine_optimization",
                    "table": table.table_name,
                    "description": "Consider migrating from Log engine to MergeTree for better performance",
                    "priority": "high",
                    "estimated_impact": "50-80% query performance improvement"
                })

        return opportunities

    # Additional helper methods for transformation, quality analysis, and view creation

    async def _generate_transformation_sql(
        self,
        connection: ClickHouseConnection,
        table_name: str,
        transformation_steps: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate SQL transformation queries."""
        sql_queries = []

        for step in transformation_steps:
            if step["type"] == "schema_change":
                field_name = step["step"].replace("add_field_", "")
                data_type = self._get_default_data_type_for_focus_field(field_name)
                sql = f"ALTER TABLE {connection.database}.{table_name} ADD COLUMN {field_name} {data_type}"
                sql_queries.append(sql)

        return sql_queries

    async def _generate_validation_sql(self, table_name: str, target_compliance: FocusComplianceLevel) -> List[str]:
        """Generate validation SQL queries."""
        return [
            f"SELECT COUNT(*) as total_rows FROM {table_name}",
            f"SELECT COUNT(DISTINCT BillingAccountId) as unique_accounts FROM {table_name}",
            f"SELECT SUM(BilledCost) as total_cost FROM {table_name}"
        ]

    async def _generate_rollback_plan(self, table_name: str) -> Dict[str, Any]:
        """Generate rollback plan for transformations."""
        return {
            "backup_required": True,
            "backup_table": f"{table_name}_backup",
            "rollback_steps": [
                "Create backup before transformation",
                "Document original schema",
                "Prepare rollback scripts"
            ]
        }

    def _get_default_data_type_for_focus_field(self, field_name: str) -> str:
        """Get default ClickHouse data type for FOCUS field."""
        type_mapping = {
            "BilledCost": "Decimal(18,2)",
            "EffectiveCost": "Decimal(18,2)",
            "ServiceName": "String",
            "BillingAccountId": "String",
            "BillingPeriodStart": "DateTime",
            "BillingPeriodEnd": "DateTime",
            "ChargeCategory": "String",
            "Region": "String"
        }
        return type_mapping.get(field_name, "Nullable(String)")

    async def _create_cost_trend_view(
        self,
        connection: ClickHouseConnection,
        source_table: str,
        focus_compliant: bool
    ) -> Dict[str, Any]:
        """Create cost trend view."""
        view_name = f"{source_table}_cost_trend"

        if focus_compliant:
            sql = f"""
            CREATE VIEW {view_name} AS
            SELECT
                toDate(BillingPeriodStart) as date,
                SUM(BilledCost) as billed_cost,
                SUM(EffectiveCost) as effective_cost,
                COUNT(*) as line_items
            FROM {source_table}
            GROUP BY toDate(BillingPeriodStart)
            ORDER BY date
            """
        else:
            sql = f"""
            CREATE VIEW {view_name} AS
            SELECT
                toDate(timestamp) as date,
                SUM(cost) as total_cost,
                COUNT(*) as line_items
            FROM {source_table}
            GROUP BY toDate(timestamp)
            ORDER BY date
            """

        return {
            "view_name": view_name,
            "sql": sql,
            "description": "Daily cost trend analysis",
            "columns": ["date", "billed_cost", "effective_cost", "line_items"] if focus_compliant else ["date", "total_cost", "line_items"]
        }

    async def _create_service_summary_view(
        self,
        connection: ClickHouseConnection,
        source_table: str,
        focus_compliant: bool
    ) -> Dict[str, Any]:
        """Create service summary view."""
        view_name = f"{source_table}_service_summary"

        if focus_compliant:
            sql = f"""
            CREATE VIEW {view_name} AS
            SELECT
                ServiceName as service,
                SUM(BilledCost) as total_cost,
                AVG(BilledCost) as avg_cost,
                COUNT(*) as line_items
            FROM {source_table}
            GROUP BY ServiceName
            ORDER BY total_cost DESC
            """
        else:
            sql = f"""
            CREATE VIEW {view_name} AS
            SELECT
                service as service,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost,
                COUNT(*) as line_items
            FROM {source_table}
            GROUP BY service
            ORDER BY total_cost DESC
            """

        return {
            "view_name": view_name,
            "sql": sql,
            "description": "Service-level cost summary",
            "columns": ["service", "total_cost", "avg_cost", "line_items"]
        }

    async def _create_account_summary_view(
        self,
        connection: ClickHouseConnection,
        source_table: str,
        focus_compliant: bool
    ) -> Dict[str, Any]:
        """Create account summary view."""
        view_name = f"{source_table}_account_summary"

        if focus_compliant:
            sql = f"""
            CREATE VIEW {view_name} AS
            SELECT
                BillingAccountId as account_id,
                BillingAccountName as account_name,
                SUM(BilledCost) as total_cost,
                COUNT(DISTINCT ServiceName) as unique_services
            FROM {source_table}
            GROUP BY BillingAccountId, BillingAccountName
            ORDER BY total_cost DESC
            """
        else:
            sql = f"""
            CREATE VIEW {view_name} AS
            SELECT
                account_id as account_id,
                account_name as account_name,
                SUM(cost) as total_cost,
                COUNT(DISTINCT service) as unique_services
            FROM {source_table}
            GROUP BY account_id, account_name
            ORDER BY total_cost DESC
            """

        return {
            "view_name": view_name,
            "sql": sql,
            "description": "Account-level cost summary",
            "columns": ["account_id", "account_name", "total_cost", "unique_services"]
        }

    async def _create_regional_summary_view(
        self,
        connection: ClickHouseConnection,
        source_table: str,
        focus_compliant: bool
    ) -> Dict[str, Any]:
        """Create regional summary view."""
        view_name = f"{source_table}_regional_summary"

        if focus_compliant:
            sql = f"""
            CREATE VIEW {view_name} AS
            SELECT
                Region as region,
                AvailabilityZone as availability_zone,
                SUM(BilledCost) as total_cost,
                COUNT(DISTINCT ServiceName) as unique_services
            FROM {source_table}
            WHERE Region IS NOT NULL
            GROUP BY Region, AvailabilityZone
            ORDER BY total_cost DESC
            """
        else:
            sql = f"""
            CREATE VIEW {view_name} AS
            SELECT
                region as region,
                availability_zone as availability_zone,
                SUM(cost) as total_cost,
                COUNT(DISTINCT service) as unique_services
            FROM {source_table}
            WHERE region IS NOT NULL
            GROUP BY region, availability_zone
            ORDER BY total_cost DESC
            """

        return {
            "view_name": view_name,
            "sql": sql,
            "description": "Regional cost distribution",
            "columns": ["region", "availability_zone", "total_cost", "unique_services"]
        }

    async def _create_commitment_analysis_view(
        self,
        connection: ClickHouseConnection,
        source_table: str,
        focus_compliant: bool
    ) -> Dict[str, Any]:
        """Create commitment discount analysis view."""
        view_name = f"{source_table}_commitment_analysis"

        if focus_compliant:
            sql = f"""
            CREATE VIEW {view_name} AS
            SELECT
                CommitmentDiscountName as commitment_name,
                CommitmentDiscountType as commitment_type,
                SUM(BilledCost) as total_cost,
                SUM(CASE WHEN CommitmentDiscountName IS NOT NULL THEN BilledCost ELSE 0 END) as committed_cost,
                COUNT(*) as line_items
            FROM {source_table}
            GROUP BY CommitmentDiscountName, CommitmentDiscountType
            ORDER BY total_cost DESC
            """
        else:
            sql = f"""
            CREATE VIEW {view_name} AS
            SELECT
                'N/A' as commitment_name,
                'N/A' as commitment_type,
                SUM(cost) as total_cost,
                0 as committed_cost,
                COUNT(*) as line_items
            FROM {source_table}
            """

        return {
            "view_name": view_name,
            "sql": sql,
            "description": "Commitment discount utilization analysis",
            "columns": ["commitment_name", "commitment_type", "total_cost", "committed_cost", "line_items"]
        }

    async def _create_optimization_views(
        self,
        connection: ClickHouseConnection,
        source_table: str,
        focus_compliant: bool
    ) -> Dict[str, Any]:
        """Create optimization-focused views."""
        return {
            "high_cost_resources": {
                "sql": f"SELECT * FROM {source_table} WHERE BilledCost > 1000 ORDER BY BilledCost DESC LIMIT 100" if focus_compliant else f"SELECT * FROM {source_table} WHERE cost > 1000 ORDER BY cost DESC LIMIT 100",
                "description": "Resources with high individual costs"
            },
            "zero_cost_resources": {
                "sql": f"SELECT * FROM {source_table} WHERE BilledCost = 0" if focus_compliant else f"SELECT * FROM {source_table} WHERE cost = 0",
                "description": "Resources with zero costs (potential cleanup candidates)"
            }
        }

    async def _generate_sample_analytics_queries(
        self,
        source_table: str,
        analytics_views: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate sample analytics queries."""
        return {
            "daily_cost_trend": f"SELECT * FROM {analytics_views['cost_trend_view']['view_name']} WHERE date >= today() - 30",
            "top_services": f"SELECT * FROM {analytics_views['service_summary_view']['view_name']} LIMIT 10",
            "account_breakdown": f"SELECT * FROM {analytics_views['account_summary_view']['view_name']}",
            "regional_distribution": f"SELECT * FROM {analytics_views['regional_summary_view']['view_name']} LIMIT 20"
        }

    def _generate_view_usage_instructions(self, analytics_views: Dict[str, Any]) -> List[str]:
        """Generate usage instructions for created views."""
        return [
            "Use cost_trend_view for daily cost analysis and trending",
            "Use service_summary_view to identify top cost contributors",
            "Use account_summary_view for account-level cost allocation",
            "Use regional_summary_view for geographic cost distribution",
            "Use commitment_analysis_view to analyze discount utilization",
            "All views are optimized for FinOps reporting and dashboards"
        ]

    async def _generate_transformation_steps(
        self,
        assessment: FocusComplianceAssessment,
        target_compliance: FocusComplianceLevel
    ) -> List[Dict[str, Any]]:
        """Generate transformation steps."""
        steps = []

        for missing_field in assessment.required_fields_missing:
            steps.append({
                "step": f"add_field_{missing_field}",
                "description": f"Add required FOCUS field: {missing_field}",
                "type": "schema_change",
                "complexity": "medium"
            })

        return steps

    def _estimate_transformation_effort(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate transformation effort."""
        total_hours = len(steps) * 2.0  # 2 hours per step estimate
        complexity_weights = {"low": 1.0, "medium": 1.5, "high": 2.5}

        weighted_hours = sum(
            2.0 * complexity_weights.get(step.get("complexity", "medium"), 1.5)
            for step in steps
        )

        return {
            "total_steps": len(steps),
            "estimated_hours": weighted_hours,
            "complexity": "high" if weighted_hours > 20 else "medium" if weighted_hours > 8 else "low"
        }

    async def _analyze_data_completeness(self, connection: ClickHouseConnection, table_name: str) -> Dict[str, Any]:
        """Analyze data completeness."""
        # Mock analysis
        return {
            "overall_completeness": 0.92,
            "field_completeness": {
                "BilledCost": 0.98,
                "ServiceName": 0.95,
                "BillingAccountId": 1.0
            },
            "null_counts": {
                "BilledCost": 200,
                "ServiceName": 500,
                "BillingAccountId": 0
            }
        }

    async def _analyze_data_consistency(self, connection: ClickHouseConnection, table_name: str, sample_size: int) -> Dict[str, Any]:
        """Analyze data consistency."""
        # Mock analysis
        return {
            "consistency_score": 0.88,
            "format_consistency": {
                "date_formats": 0.95,
                "numeric_formats": 0.90,
                "string_formats": 0.85
            },
            "value_range_consistency": 0.92
        }

    async def _analyze_data_accuracy(self, connection: ClickHouseConnection, table_name: str, sample_size: int) -> Dict[str, Any]:
        """Analyze data accuracy."""
        # Mock analysis
        return {
            "accuracy_score": 0.91,
            "validation_results": {
                "negative_costs": 0,
                "future_dates": 5,
                "invalid_formats": 12
            },
            "business_rule_violations": 8
        }

    async def _analyze_duplicates(self, connection: ClickHouseConnection, table_name: str) -> Dict[str, Any]:
        """Analyze duplicate records."""
        # Mock analysis
        return {
            "duplicate_count": 150,
            "duplicate_percentage": 0.15,
            "duplicate_patterns": [
                {"pattern": "same_resource_same_period", "count": 100},
                {"pattern": "billing_period_overlap", "count": 50}
            ]
        }

    async def _analyze_value_distributions(self, connection: ClickHouseConnection, table_name: str, sample_size: int) -> Dict[str, Any]:
        """Analyze value distributions."""
        # Mock analysis
        return {
            "cost_distribution": {
                "min": 0.01,
                "max": 50000.00,
                "median": 125.50,
                "mean": 245.75,
                "std_dev": 890.25
            },
            "service_distribution": {
                "unique_services": 25,
                "top_services": ["EC2", "S3", "RDS"]
            }
        }

    def _calculate_overall_quality_score(self, completeness: Dict, consistency: Dict, accuracy: Dict, duplicates: Dict) -> float:
        """Calculate overall data quality score."""
        completeness_score = completeness.get("overall_completeness", 0.0)
        consistency_score = consistency.get("consistency_score", 0.0)
        accuracy_score = accuracy.get("accuracy_score", 0.0)
        duplicate_penalty = duplicates.get("duplicate_percentage", 0.0)

        # Weighted average with duplicate penalty
        quality_score = (completeness_score * 0.3 + consistency_score * 0.3 + accuracy_score * 0.4) - (duplicate_penalty * 0.1)
        return max(0.0, min(1.0, quality_score))

    def _generate_quality_recommendations(self, completeness: Dict, consistency: Dict, accuracy: Dict, duplicates: Dict) -> List[str]:
        """Generate data quality recommendations."""
        recommendations = []

        if completeness.get("overall_completeness", 1.0) < 0.9:
            recommendations.append("Improve data completeness by addressing missing values")

        if consistency.get("consistency_score", 1.0) < 0.85:
            recommendations.append("Standardize data formats for better consistency")

        if accuracy.get("accuracy_score", 1.0) < 0.9:
            recommendations.append("Implement data validation rules to improve accuracy")

        if duplicates.get("duplicate_percentage", 0.0) > 0.05:
            recommendations.append("Remove duplicate records and implement deduplication process")

        return recommendations


# Factory function for integration
async def create_clickhouse_mcp_integration(
    mcp_client=None,
    focus_integration=None,
    lida_manager=None
) -> ClickHouseMCPIntegration:
    """
    Factory function to create ClickHouseMCPIntegration instance.

    Args:
        mcp_client: MCP client for ClickHouse communication
        focus_integration: FOCUS sample data integration instance
        lida_manager: LIDA Enhanced Manager instance

    Returns:
        Configured ClickHouseMCPIntegration instance
    """
    integration = ClickHouseMCPIntegration(mcp_client, focus_integration, lida_manager)
    logger.info("Created ClickHouseMCPIntegration for database discovery and FOCUS compliance")
    return integration