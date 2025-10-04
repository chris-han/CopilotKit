"""
FinOps Drill-Down Manager.

This module provides FinOps-specific drill-down capabilities for interactive
chart navigation, including service-to-resource breakdowns, time-based analysis,
cross-account comparisons, and commitment discount analysis flows.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class FinOpsDrillDownType(Enum):
    """Types of FinOps drill-down operations."""
    SERVICE_TO_RESOURCE = "service_to_resource"
    TIME_BASED_ANALYSIS = "time_based_analysis"
    CROSS_ACCOUNT_COMPARISON = "cross_account_comparison"
    COMMITMENT_DISCOUNT_ANALYSIS = "commitment_discount_analysis"
    REGIONAL_BREAKDOWN = "regional_breakdown"
    COST_ANOMALY_INVESTIGATION = "cost_anomaly_investigation"
    OPTIMIZATION_DETAIL = "optimization_detail"


class FinOpsDrillDownLevel(Enum):
    """Drill-down hierarchy levels."""
    OVERVIEW = "overview"
    SERVICE_CATEGORY = "service_category"
    SERVICE = "service"
    RESOURCE_TYPE = "resource_type"
    RESOURCE = "resource"
    BILLING_PERIOD = "billing_period"
    DAILY = "daily"
    HOURLY = "hourly"


@dataclass
class FinOpsDrillDownContext:
    """Context for FinOps drill-down operations."""
    drill_down_id: str
    user_id: str
    session_id: str
    drill_down_type: FinOpsDrillDownType
    current_level: FinOpsDrillDownLevel

    # Navigation state
    breadcrumb_path: List[Dict[str, str]]
    filter_stack: List[Dict[str, Any]]
    parent_context: Optional[str] = None

    # Current selection
    selected_dimension: str = ""
    selected_value: str = ""
    applied_filters: Dict[str, Any] = None

    # FinOps-specific context
    cost_period: Tuple[datetime, datetime] = None
    account_scope: List[str] = None
    service_scope: List[str] = None
    region_scope: List[str] = None

    # Analysis preferences
    currency: str = "USD"
    cost_metric: str = "BilledCost"  # BilledCost, EffectiveCost, etc.
    aggregation_level: str = "daily"

    # Metadata
    created_at: datetime = None
    last_updated: datetime = None


@dataclass
class FinOpsDrillDownResult:
    """Result of a FinOps drill-down operation."""
    drill_down_id: str
    chart_config: Dict[str, Any]
    data_summary: Dict[str, Any]
    navigation_options: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]

    # Interactive features
    available_drill_downs: List[Dict[str, str]]
    related_analyses: List[Dict[str, Any]]
    export_options: List[str]


class finOpsDrillDownManager:
    """
    Manager for FinOps-specific drill-down capabilities.

    This class provides comprehensive drill-down functionality for FinOps analytics,
    including hierarchical navigation, context preservation, and specialized analysis flows.
    """

    def __init__(
        self,
        echarts_templates=None,
        focus_integration=None,
        lida_manager=None
    ):
        """
        Initialize FinOps drill-down manager.

        Args:
            echarts_templates: FinOps ECharts templates instance
            focus_integration: FOCUS data integration instance
            lida_manager: LIDA Enhanced Manager instance
        """
        self.echarts_templates = echarts_templates
        self.focus_integration = focus_integration
        self.lida_manager = lida_manager

        # Active drill-down contexts
        self._active_contexts: Dict[str, FinOpsDrillDownContext] = {}

        # Drill-down hierarchy definitions
        self.drill_down_hierarchies = self._define_drill_down_hierarchies()

        logger.info("FinOpsDrillDownManager initialized")

    async def initiate_drill_down(
        self,
        user_id: str,
        session_id: str,
        drill_down_type: FinOpsDrillDownType,
        selected_dimension: str,
        selected_value: str,
        parent_context: Optional[str] = None,
        initial_filters: Optional[Dict[str, Any]] = None
    ) -> FinOpsDrillDownResult:
        """
        Initiate a new drill-down operation.

        Args:
            user_id: User identifier
            session_id: Session identifier
            drill_down_type: Type of drill-down operation
            selected_dimension: Dimension being drilled into
            selected_value: Value being selected for drill-down
            parent_context: Optional parent drill-down context ID
            initial_filters: Optional initial filters

        Returns:
            Drill-down result with chart and navigation options
        """
        try:
            drill_down_id = f"drill_{user_id}_{datetime.now().timestamp()}"

            # Create drill-down context
            context = FinOpsDrillDownContext(
                drill_down_id=drill_down_id,
                user_id=user_id,
                session_id=session_id,
                drill_down_type=drill_down_type,
                current_level=self._get_initial_level(drill_down_type),
                breadcrumb_path=self._build_initial_breadcrumb(parent_context),
                filter_stack=[initial_filters or {}],
                parent_context=parent_context,
                selected_dimension=selected_dimension,
                selected_value=selected_value,
                applied_filters=initial_filters or {},
                created_at=datetime.now(),
                last_updated=datetime.now()
            )

            # Store context
            self._active_contexts[drill_down_id] = context

            # Execute drill-down based on type
            if drill_down_type == FinOpsDrillDownType.SERVICE_TO_RESOURCE:
                result = await self._execute_service_to_resource_drill_down(context)
            elif drill_down_type == FinOpsDrillDownType.TIME_BASED_ANALYSIS:
                result = await self._execute_time_based_drill_down(context)
            elif drill_down_type == FinOpsDrillDownType.CROSS_ACCOUNT_COMPARISON:
                result = await self._execute_cross_account_drill_down(context)
            elif drill_down_type == FinOpsDrillDownType.COMMITMENT_DISCOUNT_ANALYSIS:
                result = await self._execute_commitment_drill_down(context)
            elif drill_down_type == FinOpsDrillDownType.REGIONAL_BREAKDOWN:
                result = await self._execute_regional_drill_down(context)
            elif drill_down_type == FinOpsDrillDownType.COST_ANOMALY_INVESTIGATION:
                result = await self._execute_anomaly_investigation_drill_down(context)
            elif drill_down_type == FinOpsDrillDownType.OPTIMIZATION_DETAIL:
                result = await self._execute_optimization_detail_drill_down(context)
            else:
                raise ValueError(f"Unsupported drill-down type: {drill_down_type}")

            logger.info("Initiated drill-down %s for user %s", drill_down_id, user_id)
            return result

        except Exception as exc:
            logger.error("Failed to initiate drill-down: %s", exc)
            raise

    async def navigate_drill_down(
        self,
        drill_down_id: str,
        navigation_action: str,
        target_dimension: Optional[str] = None,
        target_value: Optional[str] = None,
        additional_filters: Optional[Dict[str, Any]] = None
    ) -> FinOpsDrillDownResult:
        """
        Navigate within an existing drill-down context.

        Args:
            drill_down_id: Drill-down context identifier
            navigation_action: Navigation action (drill_deeper, go_back, filter, etc.)
            target_dimension: Optional target dimension for navigation
            target_value: Optional target value for navigation
            additional_filters: Optional additional filters to apply

        Returns:
            Updated drill-down result
        """
        try:
            if drill_down_id not in self._active_contexts:
                raise ValueError(f"Drill-down context {drill_down_id} not found")

            context = self._active_contexts[drill_down_id]
            context.last_updated = datetime.now()

            if navigation_action == "drill_deeper":
                result = await self._navigate_deeper(context, target_dimension, target_value)
            elif navigation_action == "go_back":
                result = await self._navigate_back(context)
            elif navigation_action == "apply_filter":
                result = await self._apply_additional_filter(context, additional_filters)
            elif navigation_action == "change_aggregation":
                result = await self._change_aggregation_level(context, target_value)
            elif navigation_action == "switch_metric":
                result = await self._switch_cost_metric(context, target_value)
            else:
                raise ValueError(f"Unsupported navigation action: {navigation_action}")

            logger.info("Navigated drill-down %s with action %s", drill_down_id, navigation_action)
            return result

        except Exception as exc:
            logger.error("Failed to navigate drill-down: %s", exc)
            raise

    async def get_drill_down_suggestions(
        self,
        user_id: str,
        current_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get intelligent drill-down suggestions based on current context.

        Args:
            user_id: User identifier
            current_context: Current analysis context

        Returns:
            List of suggested drill-down operations
        """
        try:
            suggestions = []

            # Analyze current context
            if "high_cost_services" in current_context:
                suggestions.append({
                    "type": "service_to_resource",
                    "title": "Drill into High-Cost Services",
                    "description": "Analyze resource-level costs for expensive services",
                    "priority": "high",
                    "estimated_insights": ["Resource optimization opportunities", "Usage patterns"]
                })

            if "cost_anomalies" in current_context:
                suggestions.append({
                    "type": "cost_anomaly_investigation",
                    "title": "Investigate Cost Anomalies",
                    "description": "Deep dive into detected cost spikes or unusual patterns",
                    "priority": "high",
                    "estimated_insights": ["Root cause analysis", "Impact assessment"]
                })

            if "commitment_underutilization" in current_context:
                suggestions.append({
                    "type": "commitment_discount_analysis",
                    "title": "Analyze Commitment Discounts",
                    "description": "Review commitment discount utilization and opportunities",
                    "priority": "medium",
                    "estimated_insights": ["Utilization gaps", "Optimization recommendations"]
                })

            if "multi_account_data" in current_context:
                suggestions.append({
                    "type": "cross_account_comparison",
                    "title": "Compare Account Costs",
                    "description": "Analyze cost patterns across different accounts",
                    "priority": "medium",
                    "estimated_insights": ["Account optimization", "Resource allocation"]
                })

            if "time_series_data" in current_context:
                suggestions.append({
                    "type": "time_based_analysis",
                    "title": "Time-Based Cost Analysis",
                    "description": "Examine cost trends and seasonal patterns",
                    "priority": "low",
                    "estimated_insights": ["Trend analysis", "Forecasting insights"]
                })

            return sorted(suggestions, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]], reverse=True)

        except Exception as exc:
            logger.error("Failed to get drill-down suggestions: %s", exc)
            return []

    # Private drill-down execution methods

    async def _execute_service_to_resource_drill_down(
        self,
        context: FinOpsDrillDownContext
    ) -> FinOpsDrillDownResult:
        """Execute service-to-resource drill-down."""
        try:
            # Get data for selected service
            service_data = await self._get_service_resource_data(
                context.selected_value, context.applied_filters
            )

            # Create resource-level visualization
            chart_config = None
            if self.echarts_templates:
                chart_config = self.echarts_templates.get_service_cost_distribution(
                    service_data["resources"]
                )

            # Generate insights
            insights = self._generate_service_resource_insights(service_data)

            # Create navigation options
            navigation_options = {
                "can_drill_deeper": len(service_data["resources"]) > 0,
                "available_dimensions": ["ResourceType", "AvailabilityZone", "PricingCategory"],
                "current_level": "resource",
                "breadcrumb": context.breadcrumb_path + [
                    {"label": context.selected_value, "level": "service"}
                ]
            }

            return FinOpsDrillDownResult(
                drill_down_id=context.drill_down_id,
                chart_config=chart_config or {},
                data_summary=service_data["summary"],
                navigation_options=navigation_options,
                insights=insights,
                recommendations=self._generate_service_recommendations(service_data),
                available_drill_downs=self._get_available_drill_downs(context),
                related_analyses=self._get_related_analyses(context),
                export_options=["csv", "pdf", "excel"]
            )

        except Exception as exc:
            logger.error("Failed to execute service-to-resource drill-down: %s", exc)
            raise

    async def _execute_time_based_drill_down(
        self,
        context: FinOpsDrillDownContext
    ) -> FinOpsDrillDownResult:
        """Execute time-based analysis drill-down."""
        try:
            # Get time-series data with higher granularity
            time_data = await self._get_time_based_data(
                context.selected_value, context.applied_filters, "daily"
            )

            # Create time-based visualization
            chart_config = None
            if self.echarts_templates:
                chart_config = self.echarts_templates.get_cost_trend_chart(
                    time_data["time_series"]
                )

            # Generate time-based insights
            insights = self._generate_time_based_insights(time_data)

            navigation_options = {
                "can_drill_deeper": True,
                "available_dimensions": ["Hour", "DayOfWeek", "Month"],
                "time_granularities": ["hourly", "daily", "weekly", "monthly"],
                "current_granularity": "daily",
                "date_range": time_data.get("date_range", {})
            }

            return FinOpsDrillDownResult(
                drill_down_id=context.drill_down_id,
                chart_config=chart_config or {},
                data_summary=time_data["summary"],
                navigation_options=navigation_options,
                insights=insights,
                recommendations=self._generate_time_based_recommendations(time_data),
                available_drill_downs=self._get_available_drill_downs(context),
                related_analyses=self._get_related_analyses(context),
                export_options=["csv", "pdf", "time_series_data"]
            )

        except Exception as exc:
            logger.error("Failed to execute time-based drill-down: %s", exc)
            raise

    async def _execute_cross_account_drill_down(
        self,
        context: FinOpsDrillDownContext
    ) -> FinOpsDrillDownResult:
        """Execute cross-account comparison drill-down."""
        try:
            # Get cross-account comparison data
            account_data = await self._get_cross_account_data(
                context.applied_filters
            )

            # Create account comparison visualization
            chart_config = None
            if self.echarts_templates:
                chart_config = self.echarts_templates.get_regional_comparison_chart(
                    account_data["accounts"]  # Reuse regional chart for account comparison
                )

            # Generate account insights
            insights = self._generate_cross_account_insights(account_data)

            navigation_options = {
                "can_drill_deeper": True,
                "available_dimensions": ["ServiceCategory", "Region", "ChargeCategory"],
                "account_scope": list(account_data["accounts"].keys()),
                "comparison_metrics": ["cost", "growth_rate", "efficiency"]
            }

            return FinOpsDrillDownResult(
                drill_down_id=context.drill_down_id,
                chart_config=chart_config or {},
                data_summary=account_data["summary"],
                navigation_options=navigation_options,
                insights=insights,
                recommendations=self._generate_account_recommendations(account_data),
                available_drill_downs=self._get_available_drill_downs(context),
                related_analyses=self._get_related_analyses(context),
                export_options=["csv", "pdf", "account_comparison"]
            )

        except Exception as exc:
            logger.error("Failed to execute cross-account drill-down: %s", exc)
            raise

    async def _execute_commitment_drill_down(
        self,
        context: FinOpsDrillDownContext
    ) -> FinOpsDrillDownResult:
        """Execute commitment discount analysis drill-down."""
        try:
            # Get commitment discount data
            commitment_data = await self._get_commitment_discount_data(
                context.selected_value, context.applied_filters
            )

            # Create commitment analysis visualization
            chart_config = None
            if self.echarts_templates:
                chart_config = self.echarts_templates.get_commitment_discount_chart(
                    commitment_data["commitments"]
                )

            # Generate commitment insights
            insights = self._generate_commitment_insights(commitment_data)

            navigation_options = {
                "can_drill_deeper": True,
                "available_dimensions": ["CommitmentType", "ServiceCategory", "Region"],
                "commitment_types": ["Savings Plans", "Reserved Instances", "Compute Savings Plans"],
                "utilization_thresholds": {"high": 80, "medium": 60, "low": 40}
            }

            return FinOpsDrillDownResult(
                drill_down_id=context.drill_down_id,
                chart_config=chart_config or {},
                data_summary=commitment_data["summary"],
                navigation_options=navigation_options,
                insights=insights,
                recommendations=self._generate_commitment_recommendations(commitment_data),
                available_drill_downs=self._get_available_drill_downs(context),
                related_analyses=self._get_related_analyses(context),
                export_options=["csv", "pdf", "commitment_analysis"]
            )

        except Exception as exc:
            logger.error("Failed to execute commitment drill-down: %s", exc)
            raise

    async def _execute_regional_drill_down(
        self,
        context: FinOpsDrillDownContext
    ) -> FinOpsDrillDownResult:
        """Execute regional breakdown drill-down."""
        try:
            # Get regional data
            regional_data = await self._get_regional_breakdown_data(
                context.selected_value, context.applied_filters
            )

            # Create regional visualization
            chart_config = None
            if self.echarts_templates:
                chart_config = self.echarts_templates.get_regional_comparison_chart(
                    regional_data["regions"]
                )

            # Generate regional insights
            insights = self._generate_regional_insights(regional_data)

            navigation_options = {
                "can_drill_deeper": True,
                "available_dimensions": ["AvailabilityZone", "ServiceCategory", "ResourceType"],
                "regions": list(regional_data["regions"].keys()),
                "cost_comparison": "enabled"
            }

            return FinOpsDrillDownResult(
                drill_down_id=context.drill_down_id,
                chart_config=chart_config or {},
                data_summary=regional_data["summary"],
                navigation_options=navigation_options,
                insights=insights,
                recommendations=self._generate_regional_recommendations(regional_data),
                available_drill_downs=self._get_available_drill_downs(context),
                related_analyses=self._get_related_analyses(context),
                export_options=["csv", "pdf", "regional_analysis"]
            )

        except Exception as exc:
            logger.error("Failed to execute regional drill-down: %s", exc)
            raise

    async def _execute_anomaly_investigation_drill_down(
        self,
        context: FinOpsDrillDownContext
    ) -> FinOpsDrillDownResult:
        """Execute cost anomaly investigation drill-down."""
        try:
            # Get anomaly investigation data
            anomaly_data = await self._get_anomaly_investigation_data(
                context.selected_value, context.applied_filters
            )

            # Create anomaly investigation visualization
            chart_config = None
            if self.echarts_templates:
                chart_config = self.echarts_templates.get_cost_trend_chart(
                    anomaly_data["timeline"]
                )

            # Generate anomaly insights
            insights = self._generate_anomaly_investigation_insights(anomaly_data)

            navigation_options = {
                "can_drill_deeper": True,
                "available_dimensions": ["CauseAnalysis", "ImpactedResources", "TimeRange"],
                "anomaly_types": ["cost_spike", "unusual_pattern", "missing_discounts"],
                "investigation_tools": ["correlation_analysis", "impact_assessment", "root_cause"]
            }

            return FinOpsDrillDownResult(
                drill_down_id=context.drill_down_id,
                chart_config=chart_config or {},
                data_summary=anomaly_data["summary"],
                navigation_options=navigation_options,
                insights=insights,
                recommendations=self._generate_anomaly_recommendations(anomaly_data),
                available_drill_downs=self._get_available_drill_downs(context),
                related_analyses=self._get_related_analyses(context),
                export_options=["csv", "pdf", "anomaly_report"]
            )

        except Exception as exc:
            logger.error("Failed to execute anomaly investigation drill-down: %s", exc)
            raise

    async def _execute_optimization_detail_drill_down(
        self,
        context: FinOpsDrillDownContext
    ) -> FinOpsDrillDownResult:
        """Execute optimization detail drill-down."""
        try:
            # Get optimization detail data
            optimization_data = await self._get_optimization_detail_data(
                context.selected_value, context.applied_filters
            )

            # Create optimization visualization
            chart_config = None
            if self.echarts_templates:
                chart_config = self.echarts_templates.get_optimization_opportunities_chart(
                    optimization_data["opportunities"]
                )

            # Generate optimization insights
            insights = self._generate_optimization_detail_insights(optimization_data)

            navigation_options = {
                "can_drill_deeper": True,
                "available_dimensions": ["OptimizationType", "AffectedServices", "Implementation"],
                "optimization_types": ["rightsizing", "commitment_opportunity", "unused_resources"],
                "implementation_phases": ["quick_wins", "medium_term", "strategic"]
            }

            return FinOpsDrillDownResult(
                drill_down_id=context.drill_down_id,
                chart_config=chart_config or {},
                data_summary=optimization_data["summary"],
                navigation_options=navigation_options,
                insights=insights,
                recommendations=self._generate_optimization_recommendations(optimization_data),
                available_drill_downs=self._get_available_drill_downs(context),
                related_analyses=self._get_related_analyses(context),
                export_options=["csv", "pdf", "optimization_plan"]
            )

        except Exception as exc:
            logger.error("Failed to execute optimization detail drill-down: %s", exc)
            raise

    # Private helper methods for data retrieval

    async def _get_service_resource_data(
        self,
        service_name: str,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get service resource data."""
        # Mock implementation - would integrate with actual data source
        return {
            "resources": [
                {"ResourceId": "r-123", "ResourceType": "Instance", "BilledCost": 500.0},
                {"ResourceId": "r-456", "ResourceType": "Volume", "BilledCost": 100.0}
            ],
            "summary": {
                "total_cost": 600.0,
                "resource_count": 2,
                "avg_cost_per_resource": 300.0
            }
        }

    async def _get_time_based_data(
        self,
        dimension: str,
        filters: Dict[str, Any],
        granularity: str
    ) -> Dict[str, Any]:
        """Get time-based data."""
        # Mock implementation
        return {
            "time_series": [
                {"date": "2024-01-01", "billed_cost": 1000.0, "effective_cost": 950.0},
                {"date": "2024-01-02", "billed_cost": 1100.0, "effective_cost": 1050.0}
            ],
            "summary": {
                "total_cost": 2100.0,
                "avg_daily_cost": 1050.0,
                "trend": "increasing"
            },
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-01-02"
            }
        }

    async def _get_cross_account_data(
        self,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get cross-account comparison data."""
        # Mock implementation
        return {
            "accounts": {
                "account-1": {"total_cost": 5000.0, "region": "us-east-1"},
                "account-2": {"total_cost": 3000.0, "region": "us-west-2"}
            },
            "summary": {
                "total_cost": 8000.0,
                "account_count": 2,
                "cost_distribution": "uneven"
            }
        }

    async def _get_commitment_discount_data(
        self,
        commitment_name: str,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get commitment discount data."""
        # Mock implementation
        return {
            "commitments": [
                {"discount_name": "Savings Plan 1", "utilization_percentage": 85.0},
                {"discount_name": "Reserved Instance 1", "utilization_percentage": 60.0}
            ],
            "summary": {
                "total_commitment_value": 10000.0,
                "avg_utilization": 72.5,
                "potential_savings": 1500.0
            }
        }

    async def _get_regional_breakdown_data(
        self,
        region: str,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get regional breakdown data."""
        # Mock implementation
        return {
            "regions": [
                {"region": "us-east-1", "total_cost": 4000.0},
                {"region": "us-west-2", "total_cost": 2000.0}
            ],
            "summary": {
                "total_cost": 6000.0,
                "region_count": 2,
                "dominant_region": "us-east-1"
            }
        }

    async def _get_anomaly_investigation_data(
        self,
        anomaly_id: str,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get anomaly investigation data."""
        # Mock implementation
        return {
            "timeline": [
                {"date": "2024-01-01", "billed_cost": 1000.0, "baseline": 800.0},
                {"date": "2024-01-02", "billed_cost": 2000.0, "baseline": 800.0}
            ],
            "summary": {
                "anomaly_type": "cost_spike",
                "deviation_percentage": 150.0,
                "impact_cost": 1200.0
            }
        }

    async def _get_optimization_detail_data(
        self,
        opportunity_id: str,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get optimization detail data."""
        # Mock implementation
        return {
            "opportunities": [
                {
                    "opportunity_id": opportunity_id,
                    "potential_savings_monthly": 1000.0,
                    "confidence_score": 0.8,
                    "implementation_effort_score": 60.0,
                    "title": "Right-size EC2 instances"
                }
            ],
            "summary": {
                "total_opportunities": 1,
                "total_potential_savings": 1000.0,
                "avg_confidence": 0.8
            }
        }

    # Helper methods for navigation and insights

    def _get_initial_level(self, drill_down_type: FinOpsDrillDownType) -> FinOpsDrillDownLevel:
        """Get initial drill-down level for type."""
        level_mapping = {
            FinOpsDrillDownType.SERVICE_TO_RESOURCE: FinOpsDrillDownLevel.SERVICE,
            FinOpsDrillDownType.TIME_BASED_ANALYSIS: FinOpsDrillDownLevel.BILLING_PERIOD,
            FinOpsDrillDownType.CROSS_ACCOUNT_COMPARISON: FinOpsDrillDownLevel.OVERVIEW,
            FinOpsDrillDownType.COMMITMENT_DISCOUNT_ANALYSIS: FinOpsDrillDownLevel.OVERVIEW,
            FinOpsDrillDownType.REGIONAL_BREAKDOWN: FinOpsDrillDownLevel.OVERVIEW,
            FinOpsDrillDownType.COST_ANOMALY_INVESTIGATION: FinOpsDrillDownLevel.OVERVIEW,
            FinOpsDrillDownType.OPTIMIZATION_DETAIL: FinOpsDrillDownLevel.OVERVIEW
        }
        return level_mapping.get(drill_down_type, FinOpsDrillDownLevel.OVERVIEW)

    def _build_initial_breadcrumb(self, parent_context: Optional[str]) -> List[Dict[str, str]]:
        """Build initial breadcrumb path."""
        if parent_context:
            # Would retrieve parent breadcrumb in practice
            return [{"label": "Overview", "level": "overview"}]
        else:
            return [{"label": "Dashboard", "level": "root"}]

    def _define_drill_down_hierarchies(self) -> Dict[str, List[str]]:
        """Define drill-down hierarchies for different analysis types."""
        return {
            "service_hierarchy": ["overview", "service_category", "service", "resource_type", "resource"],
            "time_hierarchy": ["overview", "yearly", "monthly", "daily", "hourly"],
            "account_hierarchy": ["overview", "organization", "account", "service", "resource"],
            "regional_hierarchy": ["overview", "region", "availability_zone", "service", "resource"]
        }

    def _generate_service_resource_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights for service resource drill-down."""
        insights = []
        if data["summary"]["resource_count"] > 0:
            insights.append(f"Service contains {data['summary']['resource_count']} resources")
            insights.append(f"Average cost per resource: ${data['summary']['avg_cost_per_resource']:,.2f}")
        return insights

    def _generate_service_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate recommendations for service analysis."""
        return [
            "Review high-cost resources for optimization opportunities",
            "Consider right-sizing underutilized resources"
        ]

    # Similar methods for other drill-down types...
    def _generate_time_based_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate time-based insights."""
        return [f"Cost trend: {data['summary']['trend']}", f"Average daily cost: ${data['summary']['avg_daily_cost']:,.2f}"]

    def _generate_time_based_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate time-based recommendations."""
        return ["Monitor for seasonal patterns", "Consider scheduling optimizations"]

    def _generate_cross_account_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate cross-account insights."""
        return [f"Total accounts analyzed: {data['summary']['account_count']}", f"Cost distribution: {data['summary']['cost_distribution']}"]

    def _generate_account_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate account recommendations."""
        return ["Balance costs across accounts", "Review account-level policies"]

    def _generate_commitment_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate commitment insights."""
        return [f"Average utilization: {data['summary']['avg_utilization']:.1f}%", f"Potential savings: ${data['summary']['potential_savings']:,.2f}"]

    def _generate_commitment_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate commitment recommendations."""
        return ["Increase commitment utilization", "Consider additional commitments"]

    def _generate_regional_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate regional insights."""
        return [f"Dominant region: {data['summary']['dominant_region']}", f"Regional distribution across {data['summary']['region_count']} regions"]

    def _generate_regional_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate regional recommendations."""
        return ["Consider regional cost optimization", "Review data transfer costs"]

    def _generate_anomaly_investigation_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate anomaly investigation insights."""
        return [f"Anomaly type: {data['summary']['anomaly_type']}", f"Cost deviation: {data['summary']['deviation_percentage']:.1f}%"]

    def _generate_anomaly_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate anomaly recommendations."""
        return ["Investigate root causes", "Implement cost alerts"]

    def _generate_optimization_detail_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate optimization detail insights."""
        return [f"Total optimization opportunities: {data['summary']['total_opportunities']}", f"Potential monthly savings: ${data['summary']['total_potential_savings']:,.2f}"]

    def _generate_optimization_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations."""
        return ["Prioritize high-confidence opportunities", "Implement quick wins first"]

    def _get_available_drill_downs(self, context: FinOpsDrillDownContext) -> List[Dict[str, str]]:
        """Get available drill-down options for context."""
        return [
            {"type": "deeper", "label": "Drill Deeper", "enabled": True},
            {"type": "parallel", "label": "Switch Dimension", "enabled": True},
            {"type": "related", "label": "Related Analysis", "enabled": True}
        ]

    def _get_related_analyses(self, context: FinOpsDrillDownContext) -> List[Dict[str, Any]]:
        """Get related analysis suggestions."""
        return [
            {"type": "optimization", "title": "Optimization Opportunities", "description": "Find cost optimization opportunities"},
            {"type": "forecasting", "title": "Cost Forecasting", "description": "Predict future costs"}
        ]

    # Navigation methods

    async def _navigate_deeper(
        self,
        context: FinOpsDrillDownContext,
        target_dimension: str,
        target_value: str
    ) -> FinOpsDrillDownResult:
        """Navigate deeper into drill-down hierarchy."""
        # Implementation would handle deeper navigation
        pass

    async def _navigate_back(self, context: FinOpsDrillDownContext) -> FinOpsDrillDownResult:
        """Navigate back in drill-down hierarchy."""
        # Implementation would handle back navigation
        pass

    async def _apply_additional_filter(
        self,
        context: FinOpsDrillDownContext,
        additional_filters: Dict[str, Any]
    ) -> FinOpsDrillDownResult:
        """Apply additional filters to current drill-down."""
        # Implementation would handle filter application
        pass

    async def _change_aggregation_level(
        self,
        context: FinOpsDrillDownContext,
        new_level: str
    ) -> FinOpsDrillDownResult:
        """Change aggregation level for current drill-down."""
        # Implementation would handle aggregation changes
        pass

    async def _switch_cost_metric(
        self,
        context: FinOpsDrillDownContext,
        new_metric: str
    ) -> FinOpsDrillDownResult:
        """Switch cost metric for current drill-down."""
        # Implementation would handle metric switching
        pass


# Factory function for integration
async def create_finops_drill_down_manager(
    echarts_templates=None,
    focus_integration=None,
    lida_manager=None
) -> finOpsDrillDownManager:
    """
    Factory function to create FinOpsDrillDownManager instance.

    Args:
        echarts_templates: FinOps ECharts templates instance
        focus_integration: FOCUS data integration instance
        lida_manager: LIDA Enhanced Manager instance

    Returns:
        Configured FinOpsDrillDownManager instance
    """
    manager = finOpsDrillDownManager(echarts_templates, focus_integration, lida_manager)
    logger.info("Created FinOpsDrillDownManager for interactive FinOps analytics")
    return manager