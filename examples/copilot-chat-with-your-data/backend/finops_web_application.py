"""
FinOps Analytics Web Application Backend.

This module provides backend support for the FinOps analytics web application,
including sample dataset selection, dashboard management, data exploration tools,
and real-time chart updates for comprehensive FinOps analysis workflows.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)


class DatasetType(Enum):
    """Types of datasets available in the application."""
    FOCUS_SAMPLE = "focus_sample"
    GENERATED_SAMPLE = "generated_sample"
    UPLOADED_CSV = "uploaded_csv"
    PRODUCTION_DATA = "production_data"


class DashboardLayout(Enum):
    """Dashboard layout types."""
    EXECUTIVE_SUMMARY = "executive_summary"
    COST_OPTIMIZATION = "cost_optimization"
    DETAILED_ANALYSIS = "detailed_analysis"
    COMPARISON_VIEW = "comparison_view"


class ExportFormat(Enum):
    """Export format options."""
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PNG = "png"
    SVG = "svg"


@dataclass
class FocusSampleDataset:
    """FOCUS sample dataset metadata."""
    name: str
    description: str
    rows: int
    compliance_score: float
    dataset_type: DatasetType

    # Dataset characteristics
    date_range: Tuple[datetime, datetime]
    service_count: int
    account_count: int
    region_count: int

    # File information
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    last_updated: Optional[datetime] = None

    # Quality metrics
    data_quality_score: float = 0.0
    missing_fields_percentage: float = 0.0
    focus_version: str = "1.2"

    # Analytics readiness
    analytics_ready: bool = True
    optimization_opportunities_count: int = 0
    anomaly_candidates_count: int = 0


@dataclass
class DashboardConfiguration:
    """Dashboard configuration and layout."""
    dashboard_id: str
    user_id: str
    dashboard_name: str
    layout_type: DashboardLayout

    # Dataset configuration
    primary_dataset: str
    comparison_datasets: List[str]

    # Chart configuration
    enabled_charts: List[str]
    chart_positions: Dict[str, Dict[str, Any]]
    refresh_interval_seconds: int

    # Filters and preferences
    date_range_filter: Optional[Tuple[datetime, datetime]] = None
    service_filters: List[str] = None
    account_filters: List[str] = None
    region_filters: List[str] = None

    # Display preferences
    theme: str = "light"
    color_scheme: str = "finops_default"
    show_insights: bool = True
    show_recommendations: bool = True

    # Metadata
    created_at: datetime = None
    last_modified: datetime = None
    is_shared: bool = False


@dataclass
class DataExplorationRequest:
    """Data exploration request parameters."""
    request_id: str
    user_id: str
    dataset_name: str
    exploration_type: str  # preview, comparison, quality_check, field_mapping

    # Request parameters
    parameters: Dict[str, Any]

    # Response preferences
    max_rows: int = 100
    include_statistics: bool = True
    include_quality_metrics: bool = True

    # Timestamp
    requested_at: datetime = None


@dataclass
class DatasetComparison:
    """Dataset comparison results."""
    comparison_id: str
    primary_dataset: str
    comparison_dataset: str

    # Schema comparison
    common_fields: List[str]
    unique_to_primary: List[str]
    unique_to_comparison: List[str]
    field_type_differences: Dict[str, Tuple[str, str]]

    # Data comparison
    row_count_difference: int
    cost_distribution_similarity: float
    time_range_overlap: Tuple[datetime, datetime]

    # Quality comparison
    quality_score_difference: float
    compliance_score_difference: float

    # Recommendations
    mapping_suggestions: List[Dict[str, Any]]
    merge_feasibility: str  # high, medium, low

    # Metadata
    compared_at: datetime = None


class FinOpsWebApplicationManager:
    """
    Manager for FinOps Analytics Web Application backend functionality.

    This class provides comprehensive backend support for the web application,
    including dataset management, dashboard configuration, and data exploration tools.
    """

    def __init__(
        self,
        focus_integration=None,
        echarts_templates=None,
        drill_down_manager=None,
        lida_manager=None
    ):
        """
        Initialize FinOps web application manager.

        Args:
            focus_integration: FOCUS sample data integration instance
            echarts_templates: FinOps ECharts templates instance
            drill_down_manager: FinOps drill-down manager instance
            lida_manager: LIDA Enhanced Manager instance
        """
        self.focus_integration = focus_integration
        self.echarts_templates = echarts_templates
        self.drill_down_manager = drill_down_manager
        self.lida_manager = lida_manager

        # Application state
        self._available_datasets: Dict[str, FocusSampleDataset] = {}
        self._user_dashboards: Dict[str, List[DashboardConfiguration]] = {}
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._dataset_cache: Dict[str, Dict[str, Any]] = {}

        # Initialize with default datasets
        asyncio.create_task(self._initialize_default_datasets())

        logger.info("FinOpsWebApplicationManager initialized")

    async def get_available_datasets(
        self,
        user_id: str,
        dataset_type: Optional[DatasetType] = None
    ) -> List[FocusSampleDataset]:
        """
        Get list of available datasets for user.

        Args:
            user_id: User identifier
            dataset_type: Optional filter by dataset type

        Returns:
            List of available datasets
        """
        try:
            datasets = list(self._available_datasets.values())

            # Filter by dataset type if specified
            if dataset_type:
                datasets = [d for d in datasets if d.dataset_type == dataset_type]

            # Sort by compliance score and analytics readiness
            datasets.sort(
                key=lambda d: (d.analytics_ready, d.compliance_score, d.rows),
                reverse=True
            )

            logger.info("Retrieved %d available datasets for user %s", len(datasets), user_id)
            return datasets

        except Exception as exc:
            logger.error("Failed to get available datasets: %s", exc)
            raise

    async def select_dataset(
        self,
        user_id: str,
        dataset_name: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Select a dataset for analysis.

        Args:
            user_id: User identifier
            dataset_name: Name of dataset to select
            session_id: Optional session identifier

        Returns:
            Dataset selection result with metadata and preview
        """
        try:
            if dataset_name not in self._available_datasets:
                raise ValueError(f"Dataset '{dataset_name}' not found")

            dataset = self._available_datasets[dataset_name]
            session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"

            # Load dataset data if not cached
            if dataset_name not in self._dataset_cache:
                dataset_data = await self._load_dataset_data(dataset_name)
                self._dataset_cache[dataset_name] = dataset_data

            # Create session
            self._active_sessions[session_id] = {
                "user_id": user_id,
                "selected_dataset": dataset_name,
                "dataset_metadata": asdict(dataset),
                "session_start": datetime.now(),
                "last_activity": datetime.now()
            }

            # Generate dataset preview
            preview_data = await self._generate_dataset_preview(dataset_name)

            # Generate initial insights
            initial_insights = await self._generate_initial_insights(dataset_name)

            result = {
                "session_id": session_id,
                "dataset": asdict(dataset),
                "preview": preview_data,
                "insights": initial_insights,
                "analytics_ready": dataset.analytics_ready,
                "optimization_opportunities": dataset.optimization_opportunities_count,
                "anomaly_candidates": dataset.anomaly_candidates_count
            }

            logger.info("Selected dataset '%s' for user %s in session %s", dataset_name, user_id, session_id)
            return result

        except Exception as exc:
            logger.error("Failed to select dataset: %s", exc)
            raise

    async def create_dashboard(
        self,
        user_id: str,
        dashboard_name: str,
        layout_type: DashboardLayout,
        primary_dataset: str,
        configuration: Optional[Dict[str, Any]] = None
    ) -> DashboardConfiguration:
        """
        Create a new dashboard configuration.

        Args:
            user_id: User identifier
            dashboard_name: Name for the dashboard
            layout_type: Dashboard layout type
            primary_dataset: Primary dataset for dashboard
            configuration: Optional additional configuration

        Returns:
            Created dashboard configuration
        """
        try:
            dashboard_id = f"dashboard_{uuid.uuid4().hex[:8]}"

            # Validate dataset exists
            if primary_dataset not in self._available_datasets:
                raise ValueError(f"Dataset '{primary_dataset}' not found")

            # Create dashboard configuration
            dashboard_config = DashboardConfiguration(
                dashboard_id=dashboard_id,
                user_id=user_id,
                dashboard_name=dashboard_name,
                layout_type=layout_type,
                primary_dataset=primary_dataset,
                comparison_datasets=configuration.get("comparison_datasets", []) if configuration else [],
                enabled_charts=self._get_default_charts_for_layout(layout_type),
                chart_positions=self._get_default_chart_positions(layout_type),
                refresh_interval_seconds=configuration.get("refresh_interval", 30) if configuration else 30,
                service_filters=configuration.get("service_filters", []) if configuration else [],
                account_filters=configuration.get("account_filters", []) if configuration else [],
                region_filters=configuration.get("region_filters", []) if configuration else [],
                theme=configuration.get("theme", "light") if configuration else "light",
                color_scheme=configuration.get("color_scheme", "finops_default") if configuration else "finops_default",
                created_at=datetime.now(),
                last_modified=datetime.now()
            )

            # Store dashboard for user
            if user_id not in self._user_dashboards:
                self._user_dashboards[user_id] = []
            self._user_dashboards[user_id].append(dashboard_config)

            logger.info("Created dashboard '%s' for user %s", dashboard_name, user_id)
            return dashboard_config

        except Exception as exc:
            logger.error("Failed to create dashboard: %s", exc)
            raise

    async def get_dashboard_data(
        self,
        dashboard_id: str,
        user_id: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get dashboard data with charts and insights.

        Args:
            dashboard_id: Dashboard identifier
            user_id: User identifier
            force_refresh: Force refresh of cached data

        Returns:
            Complete dashboard data with charts
        """
        try:
            # Find dashboard configuration
            dashboard_config = None
            for user_dashboards in self._user_dashboards.get(user_id, []):
                if user_dashboards.dashboard_id == dashboard_id:
                    dashboard_config = user_dashboards
                    break

            if not dashboard_config:
                raise ValueError(f"Dashboard '{dashboard_id}' not found for user")

            # Load primary dataset
            primary_data = await self._load_dataset_data(dashboard_config.primary_dataset)

            # Generate charts based on dashboard configuration
            charts = await self._generate_dashboard_charts(dashboard_config, primary_data)

            # Generate insights and recommendations
            insights = await self._generate_dashboard_insights(dashboard_config, primary_data)
            recommendations = await self._generate_dashboard_recommendations(dashboard_config, primary_data)

            # Load comparison data if configured
            comparison_data = {}
            for comparison_dataset in dashboard_config.comparison_datasets:
                comparison_data[comparison_dataset] = await self._load_dataset_data(comparison_dataset)

            dashboard_data = {
                "dashboard_id": dashboard_id,
                "configuration": asdict(dashboard_config),
                "charts": charts,
                "insights": insights,
                "recommendations": recommendations,
                "data_summary": {
                    "primary_dataset": dashboard_config.primary_dataset,
                    "total_cost": sum(float(r.get("BilledCost", 0)) for r in primary_data.get("records", [])),
                    "record_count": len(primary_data.get("records", [])),
                    "date_range": primary_data.get("date_range", {}),
                    "last_updated": datetime.now().isoformat()
                },
                "comparison_data": comparison_data if comparison_data else None,
                "export_options": [format.value for format in ExportFormat]
            }

            logger.info("Generated dashboard data for dashboard %s", dashboard_id)
            return dashboard_data

        except Exception as exc:
            logger.error("Failed to get dashboard data: %s", exc)
            raise

    async def explore_dataset(
        self,
        exploration_request: DataExplorationRequest
    ) -> Dict[str, Any]:
        """
        Perform dataset exploration based on request.

        Args:
            exploration_request: Exploration request parameters

        Returns:
            Exploration results
        """
        try:
            dataset_name = exploration_request.dataset_name

            if dataset_name not in self._available_datasets:
                raise ValueError(f"Dataset '{dataset_name}' not found")

            # Load dataset data
            dataset_data = await self._load_dataset_data(dataset_name)

            exploration_type = exploration_request.exploration_type

            if exploration_type == "preview":
                result = await self._generate_dataset_preview(
                    dataset_name,
                    max_rows=exploration_request.max_rows
                )
            elif exploration_type == "quality_check":
                result = await self._perform_data_quality_assessment(dataset_data)
            elif exploration_type == "field_mapping":
                result = await self._generate_field_mapping_analysis(dataset_data)
            elif exploration_type == "statistics":
                result = await self._generate_dataset_statistics(dataset_data)
            else:
                raise ValueError(f"Unsupported exploration type: {exploration_type}")

            # Add metadata
            result["request_id"] = exploration_request.request_id
            result["dataset_name"] = dataset_name
            result["exploration_type"] = exploration_type
            result["generated_at"] = datetime.now().isoformat()

            logger.info("Completed dataset exploration '%s' for dataset '%s'", exploration_type, dataset_name)
            return result

        except Exception as exc:
            logger.error("Failed to explore dataset: %s", exc)
            raise

    async def compare_datasets(
        self,
        user_id: str,
        primary_dataset: str,
        comparison_dataset: str
    ) -> DatasetComparison:
        """
        Compare two datasets for compatibility and differences.

        Args:
            user_id: User identifier
            primary_dataset: Primary dataset name
            comparison_dataset: Comparison dataset name

        Returns:
            Dataset comparison results
        """
        try:
            # Validate datasets exist
            if primary_dataset not in self._available_datasets:
                raise ValueError(f"Primary dataset '{primary_dataset}' not found")
            if comparison_dataset not in self._available_datasets:
                raise ValueError(f"Comparison dataset '{comparison_dataset}' not found")

            # Load dataset data
            primary_data = await self._load_dataset_data(primary_dataset)
            comparison_data = await self._load_dataset_data(comparison_dataset)

            # Perform schema comparison
            schema_comparison = await self._compare_dataset_schemas(primary_data, comparison_data)

            # Perform data comparison
            data_comparison = await self._compare_dataset_content(primary_data, comparison_data)

            # Generate mapping suggestions
            mapping_suggestions = await self._generate_mapping_suggestions(
                primary_data, comparison_data, schema_comparison
            )

            comparison_id = f"comparison_{uuid.uuid4().hex[:8]}"

            comparison_result = DatasetComparison(
                comparison_id=comparison_id,
                primary_dataset=primary_dataset,
                comparison_dataset=comparison_dataset,
                common_fields=schema_comparison["common_fields"],
                unique_to_primary=schema_comparison["unique_to_primary"],
                unique_to_comparison=schema_comparison["unique_to_comparison"],
                field_type_differences=schema_comparison["field_type_differences"],
                row_count_difference=data_comparison["row_count_difference"],
                cost_distribution_similarity=data_comparison["cost_similarity"],
                time_range_overlap=data_comparison["time_overlap"],
                quality_score_difference=data_comparison["quality_difference"],
                compliance_score_difference=data_comparison["compliance_difference"],
                mapping_suggestions=mapping_suggestions,
                merge_feasibility=self._assess_merge_feasibility(schema_comparison, data_comparison),
                compared_at=datetime.now()
            )

            logger.info("Compared datasets '%s' and '%s'", primary_dataset, comparison_dataset)
            return comparison_result

        except Exception as exc:
            logger.error("Failed to compare datasets: %s", exc)
            raise

    async def export_dashboard(
        self,
        dashboard_id: str,
        user_id: str,
        export_format: ExportFormat,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export dashboard in specified format.

        Args:
            dashboard_id: Dashboard identifier
            user_id: User identifier
            export_format: Export format
            options: Optional export options

        Returns:
            Export result with download information
        """
        try:
            # Get dashboard data
            dashboard_data = await self.get_dashboard_data(dashboard_id, user_id)

            export_id = f"export_{uuid.uuid4().hex[:8]}"
            export_timestamp = datetime.now()

            if export_format == ExportFormat.JSON:
                export_content = json.dumps(dashboard_data, indent=2, default=str)
                file_extension = "json"
                content_type = "application/json"
            elif export_format == ExportFormat.CSV:
                export_content = await self._export_dashboard_to_csv(dashboard_data)
                file_extension = "csv"
                content_type = "text/csv"
            elif export_format == ExportFormat.PDF:
                export_content = await self._export_dashboard_to_pdf(dashboard_data, options)
                file_extension = "pdf"
                content_type = "application/pdf"
            else:
                raise ValueError(f"Unsupported export format: {export_format}")

            # Generate filename
            dashboard_name = dashboard_data["configuration"]["dashboard_name"]
            filename = f"{dashboard_name}_{export_timestamp.strftime('%Y%m%d_%H%M%S')}.{file_extension}"

            export_result = {
                "export_id": export_id,
                "dashboard_id": dashboard_id,
                "export_format": export_format.value,
                "filename": filename,
                "content_type": content_type,
                "file_size": len(export_content.encode() if isinstance(export_content, str) else export_content),
                "export_timestamp": export_timestamp.isoformat(),
                "download_url": f"/api/exports/{export_id}/download",
                "expires_at": (export_timestamp + timedelta(hours=24)).isoformat()
            }

            # Store export content (in production, would store in file system or cloud storage)
            # For now, just return the result
            logger.info("Exported dashboard %s in %s format", dashboard_id, export_format.value)
            return export_result

        except Exception as exc:
            logger.error("Failed to export dashboard: %s", exc)
            raise

    # Private helper methods

    async def _initialize_default_datasets(self):
        """Initialize default FOCUS sample datasets."""
        try:
            # Create default sample datasets
            default_datasets = [
                FocusSampleDataset(
                    name="AWS Multi-Account Sample",
                    description="Sample AWS multi-account cost data with EC2, S3, and RDS usage",
                    rows=2500,
                    compliance_score=0.95,
                    dataset_type=DatasetType.FOCUS_SAMPLE,
                    date_range=(datetime(2024, 1, 1), datetime(2024, 3, 31)),
                    service_count=8,
                    account_count=3,
                    region_count=4,
                    data_quality_score=0.92,
                    missing_fields_percentage=5.0,
                    optimization_opportunities_count=12,
                    anomaly_candidates_count=3
                ),
                FocusSampleDataset(
                    name="Azure Enterprise Sample",
                    description="Enterprise Azure cost data with commitment discounts and reserved instances",
                    rows=1800,
                    compliance_score=0.88,
                    dataset_type=DatasetType.FOCUS_SAMPLE,
                    date_range=(datetime(2024, 2, 1), datetime(2024, 4, 30)),
                    service_count=6,
                    account_count=2,
                    region_count=3,
                    data_quality_score=0.89,
                    missing_fields_percentage=8.0,
                    optimization_opportunities_count=8,
                    anomaly_candidates_count=1
                ),
                FocusSampleDataset(
                    name="GCP Startup Sample",
                    description="Small-scale GCP usage with compute and storage focus",
                    rows=800,
                    compliance_score=0.82,
                    dataset_type=DatasetType.FOCUS_SAMPLE,
                    date_range=(datetime(2024, 1, 15), datetime(2024, 3, 15)),
                    service_count=4,
                    account_count=1,
                    region_count=2,
                    data_quality_score=0.85,
                    missing_fields_percentage=12.0,
                    optimization_opportunities_count=4,
                    anomaly_candidates_count=0
                ),
                FocusSampleDataset(
                    name="Multi-Cloud Hybrid Sample",
                    description="Hybrid multi-cloud environment with AWS, Azure, and GCP resources",
                    rows=3200,
                    compliance_score=0.91,
                    dataset_type=DatasetType.GENERATED_SAMPLE,
                    date_range=(datetime(2024, 1, 1), datetime(2024, 4, 30)),
                    service_count=15,
                    account_count=5,
                    region_count=8,
                    data_quality_score=0.94,
                    missing_fields_percentage=3.0,
                    optimization_opportunities_count=18,
                    anomaly_candidates_count=5
                )
            ]

            for dataset in default_datasets:
                self._available_datasets[dataset.name] = dataset

            logger.info("Initialized %d default datasets", len(default_datasets))

        except Exception as exc:
            logger.error("Failed to initialize default datasets: %s", exc)

    async def _load_dataset_data(self, dataset_name: str) -> Dict[str, Any]:
        """Load dataset data from storage or generate if needed."""
        if dataset_name in self._dataset_cache:
            return self._dataset_cache[dataset_name]

        dataset = self._available_datasets[dataset_name]

        if dataset.dataset_type == DatasetType.FOCUS_SAMPLE:
            # Use FOCUS integration to generate sample data
            if self.focus_integration:
                records = await self.focus_integration.generate_sample_dataset(
                    dataset_name, dataset.rows
                )
                dataset_data = {
                    "records": [asdict(r) for r in records],
                    "metadata": asdict(dataset),
                    "date_range": {
                        "start": dataset.date_range[0].isoformat(),
                        "end": dataset.date_range[1].isoformat()
                    }
                }
            else:
                # Generate mock data
                dataset_data = await self._generate_mock_dataset_data(dataset)
        else:
            # Generate mock data for other types
            dataset_data = await self._generate_mock_dataset_data(dataset)

        self._dataset_cache[dataset_name] = dataset_data
        return dataset_data

    async def _generate_mock_dataset_data(self, dataset: FocusSampleDataset) -> Dict[str, Any]:
        """Generate mock dataset data for testing."""
        records = []
        base_date = dataset.date_range[0]

        for i in range(dataset.rows):
            record = {
                "BillingPeriodStart": (base_date + timedelta(days=i % 90)).isoformat(),
                "BillingPeriodEnd": (base_date + timedelta(days=(i % 90) + 1)).isoformat(),
                "BillingAccountId": f"account-{(i % dataset.account_count) + 1:03d}",
                "BillingAccountName": f"Account {(i % dataset.account_count) + 1}",
                "BilledCost": round(100 + (i * 1.5) % 1000, 2),
                "ChargeCategory": ["Usage", "Purchase", "Credit"][i % 3],
                "ServiceName": f"Service-{(i % dataset.service_count) + 1}",
                "Region": f"region-{(i % dataset.region_count) + 1}",
                "ResourceId": f"resource-{i:06d}"
            }
            records.append(record)

        return {
            "records": records,
            "metadata": asdict(dataset),
            "date_range": {
                "start": dataset.date_range[0].isoformat(),
                "end": dataset.date_range[1].isoformat()
            }
        }

    async def _generate_dataset_preview(self, dataset_name: str, max_rows: int = 10) -> Dict[str, Any]:
        """Generate dataset preview with sample records and statistics."""
        dataset_data = await self._load_dataset_data(dataset_name)
        records = dataset_data["records"]

        preview = {
            "sample_records": records[:max_rows],
            "total_rows": len(records),
            "columns": list(records[0].keys()) if records else [],
            "statistics": {
                "total_cost": sum(float(r.get("BilledCost", 0)) for r in records),
                "unique_services": len(set(r.get("ServiceName", "Unknown") for r in records)),
                "unique_accounts": len(set(r.get("BillingAccountId", "Unknown") for r in records)),
                "unique_regions": len(set(r.get("Region", "Unknown") for r in records)),
                "date_range": dataset_data["date_range"]
            }
        }

        return preview

    async def _generate_initial_insights(self, dataset_name: str) -> List[str]:
        """Generate initial insights for selected dataset."""
        dataset_data = await self._load_dataset_data(dataset_name)
        dataset = self._available_datasets[dataset_name]
        records = dataset_data["records"]

        insights = []

        # Cost insights
        total_cost = sum(float(r.get("BilledCost", 0)) for r in records)
        insights.append(f"Total cost: ${total_cost:,.2f} across {len(records):,} line items")

        # Service insights
        service_costs = defaultdict(float)
        for record in records:
            service_costs[record.get("ServiceName", "Unknown")] += float(record.get("BilledCost", 0))

        if service_costs:
            top_service = max(service_costs.items(), key=lambda x: x[1])
            insights.append(f"Top service by cost: {top_service[0]} (${top_service[1]:,.2f})")

        # Optimization insights
        if dataset.optimization_opportunities_count > 0:
            insights.append(f"{dataset.optimization_opportunities_count} optimization opportunities identified")

        # Anomaly insights
        if dataset.anomaly_candidates_count > 0:
            insights.append(f"{dataset.anomaly_candidates_count} potential cost anomalies detected")

        return insights

    def _get_default_charts_for_layout(self, layout_type: DashboardLayout) -> List[str]:
        """Get default charts for dashboard layout type."""
        if layout_type == DashboardLayout.EXECUTIVE_SUMMARY:
            return ["cost_trend", "service_distribution", "regional_comparison", "key_metrics"]
        elif layout_type == DashboardLayout.COST_OPTIMIZATION:
            return ["optimization_opportunities", "commitment_discount", "cost_trend", "anomaly_detection"]
        elif layout_type == DashboardLayout.DETAILED_ANALYSIS:
            return ["cost_trend", "service_distribution", "regional_comparison", "optimization_opportunities", "commitment_discount", "resource_utilization"]
        elif layout_type == DashboardLayout.COMPARISON_VIEW:
            return ["comparison_overview", "cost_trend_comparison", "service_comparison"]
        else:
            return ["cost_trend", "service_distribution"]

    def _get_default_chart_positions(self, layout_type: DashboardLayout) -> Dict[str, Dict[str, Any]]:
        """Get default chart positions for layout type."""
        if layout_type == DashboardLayout.EXECUTIVE_SUMMARY:
            return {
                "cost_trend": {"row": 1, "col": 1, "width": 8, "height": 4},
                "key_metrics": {"row": 1, "col": 9, "width": 4, "height": 4},
                "service_distribution": {"row": 2, "col": 1, "width": 6, "height": 4},
                "regional_comparison": {"row": 2, "col": 7, "width": 6, "height": 4}
            }
        else:
            # Default grid layout
            return {
                chart: {"row": i // 2 + 1, "col": (i % 2) * 6 + 1, "width": 6, "height": 4}
                for i, chart in enumerate(self._get_default_charts_for_layout(layout_type))
            }

    async def _generate_dashboard_charts(
        self,
        dashboard_config: DashboardConfiguration,
        dataset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate charts for dashboard."""
        charts = {}

        if not self.echarts_templates:
            return charts

        records = dataset_data["records"]

        for chart_type in dashboard_config.enabled_charts:
            try:
                if chart_type == "cost_trend":
                    charts[chart_type] = self.echarts_templates.get_cost_trend_chart(records)
                elif chart_type == "service_distribution":
                    charts[chart_type] = self.echarts_templates.get_service_cost_distribution(records)
                elif chart_type == "regional_comparison":
                    charts[chart_type] = self.echarts_templates.get_regional_comparison_chart(records)
                elif chart_type == "commitment_discount":
                    charts[chart_type] = self.echarts_templates.get_commitment_discount_chart(records)
                elif chart_type == "optimization_opportunities":
                    # Mock optimization opportunities for now
                    opportunities = [
                        {"title": "Right-size instances", "potential_savings_monthly": 1000, "confidence_score": 0.8}
                    ]
                    charts[chart_type] = self.echarts_templates.get_optimization_opportunities_chart(opportunities)
            except Exception as exc:
                logger.warning("Failed to generate chart %s: %s", chart_type, exc)
                charts[chart_type] = {"error": f"Failed to generate {chart_type}"}

        return charts

    async def _generate_dashboard_insights(
        self,
        dashboard_config: DashboardConfiguration,
        dataset_data: Dict[str, Any]
    ) -> List[str]:
        """Generate insights for dashboard."""
        return await self._generate_initial_insights(dashboard_config.primary_dataset)

    async def _generate_dashboard_recommendations(
        self,
        dashboard_config: DashboardConfiguration,
        dataset_data: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for dashboard."""
        recommendations = [
            "Consider implementing cost allocation tags for better tracking",
            "Review commitment discount opportunities for potential savings",
            "Monitor cost trends for seasonal patterns and optimization timing"
        ]
        return recommendations

    # Additional helper methods for comparison and quality assessment

    async def _compare_dataset_schemas(
        self,
        primary_data: Dict[str, Any],
        comparison_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare schemas of two datasets."""
        primary_fields = set(primary_data["records"][0].keys()) if primary_data["records"] else set()
        comparison_fields = set(comparison_data["records"][0].keys()) if comparison_data["records"] else set()

        return {
            "common_fields": list(primary_fields & comparison_fields),
            "unique_to_primary": list(primary_fields - comparison_fields),
            "unique_to_comparison": list(comparison_fields - primary_fields),
            "field_type_differences": {}  # Would implement type comparison in production
        }

    async def _compare_dataset_content(
        self,
        primary_data: Dict[str, Any],
        comparison_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare content of two datasets."""
        primary_records = primary_data["records"]
        comparison_records = comparison_data["records"]

        return {
            "row_count_difference": len(primary_records) - len(comparison_records),
            "cost_similarity": 0.85,  # Mock similarity score
            "time_overlap": (datetime(2024, 2, 1), datetime(2024, 3, 31)),  # Mock overlap
            "quality_difference": 0.03,  # Mock quality difference
            "compliance_difference": 0.07  # Mock compliance difference
        }

    async def _generate_mapping_suggestions(
        self,
        primary_data: Dict[str, Any],
        comparison_data: Dict[str, Any],
        schema_comparison: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate field mapping suggestions."""
        return [
            {
                "source_field": "BilledCost",
                "target_field": "Cost",
                "confidence": 0.95,
                "transformation_required": False
            }
        ]

    def _assess_merge_feasibility(
        self,
        schema_comparison: Dict[str, Any],
        data_comparison: Dict[str, Any]
    ) -> str:
        """Assess feasibility of merging datasets."""
        common_fields_ratio = len(schema_comparison["common_fields"]) / max(
            len(schema_comparison["common_fields"]) +
            len(schema_comparison["unique_to_primary"]) +
            len(schema_comparison["unique_to_comparison"]), 1
        )

        if common_fields_ratio > 0.8:
            return "high"
        elif common_fields_ratio > 0.6:
            return "medium"
        else:
            return "low"

    async def _perform_data_quality_assessment(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform data quality assessment."""
        records = dataset_data["records"]

        quality_metrics = {
            "completeness": 0.95,  # Mock completeness score
            "accuracy": 0.92,      # Mock accuracy score
            "consistency": 0.88,   # Mock consistency score
            "timeliness": 0.96,    # Mock timeliness score
            "overall_score": 0.93  # Mock overall score
        }

        return {
            "quality_metrics": quality_metrics,
            "issues_found": [
                {"type": "missing_values", "field": "ResourceName", "count": 12},
                {"type": "data_type_mismatch", "field": "BilledCost", "count": 3}
            ],
            "recommendations": [
                "Review data collection process for ResourceName field",
                "Implement data validation for BilledCost field"
            ]
        }

    async def _generate_field_mapping_analysis(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate field mapping analysis."""
        records = dataset_data["records"]

        if not records:
            return {"field_mappings": [], "compliance_assessment": {}}

        field_mappings = []
        for field in records[0].keys():
            field_mappings.append({
                "field_name": field,
                "focus_mapping": self._map_to_focus_field(field),
                "data_type": "string",  # Would analyze actual data types
                "sample_values": [str(r.get(field, ""))[:50] for r in records[:3]],
                "completeness": 0.95  # Mock completeness
            })

        return {
            "field_mappings": field_mappings,
            "compliance_assessment": {
                "focus_version": "1.2",
                "compliance_score": 0.91,
                "missing_required_fields": [],
                "additional_fields": []
            }
        }

    def _map_to_focus_field(self, field_name: str) -> str:
        """Map field name to FOCUS specification field."""
        mapping = {
            "BilledCost": "BilledCost",
            "ServiceName": "ServiceName",
            "Region": "Region",
            "BillingAccountId": "BillingAccountId",
            "ChargeCategory": "ChargeCategory"
        }
        return mapping.get(field_name, "custom_field")

    async def _generate_dataset_statistics(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive dataset statistics."""
        records = dataset_data["records"]

        if not records:
            return {"statistics": {}}

        # Calculate basic statistics
        costs = [float(r.get("BilledCost", 0)) for r in records]

        return {
            "statistics": {
                "total_records": len(records),
                "total_cost": sum(costs),
                "average_cost": sum(costs) / len(costs) if costs else 0,
                "min_cost": min(costs) if costs else 0,
                "max_cost": max(costs) if costs else 0,
                "unique_services": len(set(r.get("ServiceName", "") for r in records)),
                "unique_accounts": len(set(r.get("BillingAccountId", "") for r in records)),
                "unique_regions": len(set(r.get("Region", "") for r in records)),
                "date_coverage": dataset_data.get("date_range", {})
            }
        }

    async def _export_dashboard_to_csv(self, dashboard_data: Dict[str, Any]) -> str:
        """Export dashboard data to CSV format."""
        # Mock CSV export
        return "Dashboard,Chart,Value\nTest Dashboard,Cost Trend,1000.00\n"

    async def _export_dashboard_to_pdf(
        self,
        dashboard_data: Dict[str, Any],
        options: Optional[Dict[str, Any]]
    ) -> bytes:
        """Export dashboard to PDF format."""
        # Mock PDF export
        return b"Mock PDF content"


# Factory function for integration
async def create_finops_web_application_manager(
    focus_integration=None,
    echarts_templates=None,
    drill_down_manager=None,
    lida_manager=None
) -> FinOpsWebApplicationManager:
    """
    Factory function to create FinOpsWebApplicationManager instance.

    Args:
        focus_integration: FOCUS sample data integration instance
        echarts_templates: FinOps ECharts templates instance
        drill_down_manager: FinOps drill-down manager instance
        lida_manager: LIDA Enhanced Manager instance

    Returns:
        Configured FinOpsWebApplicationManager instance
    """
    manager = FinOpsWebApplicationManager(
        focus_integration=focus_integration,
        echarts_templates=echarts_templates,
        drill_down_manager=drill_down_manager,
        lida_manager=lida_manager
    )
    logger.info("Created FinOpsWebApplicationManager for comprehensive FinOps analytics")
    return manager