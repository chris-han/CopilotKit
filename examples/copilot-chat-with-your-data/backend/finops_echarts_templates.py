"""
FinOps ECharts Visualization Templates.

This module provides specialized ECharts visualization templates for FinOps analytics,
including cost trends, service distributions, commitment discount utilization, and
interactive FinOps dashboards with drill-down capabilities.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict
from decimal import Decimal

logger = logging.getLogger(__name__)


class FinOpsDashboardType(Enum):
    """Types of FinOps dashboards."""
    EXECUTIVE_SUMMARY = "executive_summary"
    COST_OPTIMIZATION = "cost_optimization"
    RESOURCE_UTILIZATION = "resource_utilization"
    ANOMALY_DETECTION = "anomaly_detection"
    COMMITMENT_ANALYSIS = "commitment_analysis"


class FinOpsVisualizationType(Enum):
    """Types of FinOps visualizations."""
    COST_TREND = "cost_trend"
    SERVICE_DISTRIBUTION = "service_distribution"
    COMMITMENT_DISCOUNT = "commitment_discount"
    REGIONAL_COMPARISON = "regional_comparison"
    RESOURCE_UTILIZATION = "resource_utilization"
    ANOMALY_TIMELINE = "anomaly_timeline"
    OPTIMIZATION_OPPORTUNITIES = "optimization_opportunities"


@dataclass
class FinOpsVisualizationConfig:
    """Configuration for FinOps visualizations."""
    visualization_type: FinOpsVisualizationType
    title: str
    chart_type: str  # ECharts chart type
    dimensions: List[str]
    metrics: List[str]

    # FinOps-specific settings
    cost_thresholds: Optional[Dict[str, float]] = None
    color_scheme: str = "finops_default"
    interactive_features: List[str] = None
    drill_down_enabled: bool = True

    # Display settings
    show_legends: bool = True
    show_tooltips: bool = True
    responsive: bool = True
    accessibility_enabled: bool = True


class FinOpsColorSchemes:
    """FinOps-specific color schemes for visualizations."""

    FINOPS_DEFAULT = {
        "primary": "#1890ff",
        "secondary": "#722ed1",
        "success": "#52c41a",
        "warning": "#faad14",
        "error": "#ff4d4f",
        "info": "#13c2c2"
    }

    COST_OPTIMIZATION = {
        "high_cost": "#ff4d4f",
        "medium_cost": "#faad14",
        "low_cost": "#52c41a",
        "savings": "#1890ff",
        "potential": "#722ed1"
    }

    SERVICE_CATEGORIES = {
        "compute": "#1890ff",
        "storage": "#52c41a",
        "database": "#722ed1",
        "networking": "#13c2c2",
        "analytics": "#faad14",
        "ai_ml": "#eb2f96",
        "security": "#fa541c",
        "management": "#2f54eb",
        "other": "#8c8c8c"
    }

    COMMITMENT_DISCOUNTS = {
        "high_utilization": "#52c41a",    # > 80%
        "medium_utilization": "#faad14",  # 60-80%
        "low_utilization": "#ff4d4f",    # < 60%
        "no_commitment": "#8c8c8c"
    }


class FinOpsEChartsTemplates:
    """
    FinOps-specific ECharts visualization templates.

    This class provides comprehensive visualization templates for FinOps analytics,
    including cost trends, service distributions, and interactive dashboards.
    """

    def __init__(self, echarts_mcp_adapter=None):
        """
        Initialize FinOps ECharts templates.

        Args:
            echarts_mcp_adapter: Optional ECharts MCP adapter instance
        """
        self.echarts_adapter = echarts_mcp_adapter
        self.color_schemes = FinOpsColorSchemes()

        logger.info("FinOpsEChartsTemplates initialized")

    def get_cost_trend_chart(
        self,
        data: List[Dict[str, Any]],
        config: Optional[FinOpsVisualizationConfig] = None
    ) -> Dict[str, Any]:
        """
        Create cost trend line chart with time-based analysis.

        Args:
            data: FOCUS-compliant cost data
            config: Optional visualization configuration

        Returns:
            ECharts configuration for cost trend chart
        """
        try:
            if not data:
                return self._create_empty_chart("No cost trend data available")

            # Aggregate data by time period
            time_series_data = self._aggregate_cost_by_time(data)

            # Create ECharts configuration
            chart_config = {
                "title": {
                    "text": config.title if config else "Cost Trends Over Time",
                    "left": "center",
                    "textStyle": {"fontSize": 16, "fontWeight": "bold"}
                },
                "tooltip": {
                    "trigger": "axis",
                    "formatter": self._create_cost_tooltip_formatter(),
                    "backgroundColor": "rgba(50, 50, 50, 0.9)",
                    "textStyle": {"color": "#fff"}
                },
                "legend": {
                    "data": ["Billed Cost", "Effective Cost", "Trend"],
                    "bottom": 10
                },
                "grid": {
                    "left": "10%",
                    "right": "10%",
                    "bottom": "15%",
                    "containLabel": True
                },
                "xAxis": {
                    "type": "time",
                    "boundaryGap": False,
                    "axisLabel": {
                        "formatter": "{yyyy}-{MM}-{dd}"
                    }
                },
                "yAxis": {
                    "type": "value",
                    "name": "Cost ($)",
                    "axisLabel": {
                        "formatter": "${value}"
                    }
                },
                "series": [
                    {
                        "name": "Billed Cost",
                        "type": "line",
                        "data": [[item["date"], item["billed_cost"]] for item in time_series_data],
                        "smooth": True,
                        "symbol": "circle",
                        "symbolSize": 6,
                        "lineStyle": {"width": 3},
                        "itemStyle": {"color": self.color_schemes.FINOPS_DEFAULT["primary"]},
                        "emphasis": {"focus": "series"}
                    },
                    {
                        "name": "Effective Cost",
                        "type": "line",
                        "data": [[item["date"], item["effective_cost"]] for item in time_series_data],
                        "smooth": True,
                        "symbol": "circle",
                        "symbolSize": 6,
                        "lineStyle": {"width": 3, "type": "dashed"},
                        "itemStyle": {"color": self.color_schemes.FINOPS_DEFAULT["secondary"]},
                        "emphasis": {"focus": "series"}
                    },
                    {
                        "name": "Trend",
                        "type": "line",
                        "data": self._calculate_trend_line(time_series_data),
                        "smooth": True,
                        "symbol": "none",
                        "lineStyle": {"width": 2, "type": "dotted"},
                        "itemStyle": {"color": self.color_schemes.FINOPS_DEFAULT["warning"]},
                        "emphasis": {"focus": "none"}
                    }
                ],
                "dataZoom": [
                    {
                        "type": "inside",
                        "start": 0,
                        "end": 100
                    },
                    {
                        "start": 0,
                        "end": 100,
                        "handleIcon": "M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z",
                        "handleSize": "80%",
                        "handleStyle": {"color": "#d3dee5"}
                    }
                ]
            }

            # Add interactive features
            if config and config.drill_down_enabled:
                chart_config["series"][0]["emphasis"] = {"focus": "series"}
                chart_config["brush"] = {"toolbox": ["rect", "polygon", "clear"]}

            return chart_config

        except Exception as exc:
            logger.error("Failed to create cost trend chart: %s", exc)
            return self._create_error_chart(f"Cost trend chart error: {exc}")

    def get_service_cost_distribution(
        self,
        data: List[Dict[str, Any]],
        config: Optional[FinOpsVisualizationConfig] = None
    ) -> Dict[str, Any]:
        """
        Create service cost distribution treemap visualization.

        Args:
            data: FOCUS-compliant service cost data
            config: Optional visualization configuration

        Returns:
            ECharts configuration for service distribution treemap
        """
        try:
            if not data:
                return self._create_empty_chart("No service cost data available")

            # Aggregate data by service
            service_data = self._aggregate_by_service(data)

            # Create treemap data structure
            treemap_data = []
            total_cost = sum(item["total_cost"] for item in service_data)

            for item in service_data:
                service_color = self._get_service_color(item["service_name"])
                percentage = (item["total_cost"] / total_cost * 100) if total_cost > 0 else 0

                treemap_data.append({
                    "name": f"{item['service_name']}\n${item['total_cost']:,.2f} ({percentage:.1f}%)",
                    "value": item["total_cost"],
                    "itemStyle": {
                        "color": service_color,
                        "borderColor": "#fff",
                        "borderWidth": 2
                    },
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowColor": "rgba(0,0,0,0.3)"
                        }
                    },
                    "tooltip": {
                        "formatter": f"<b>{item['service_name']}</b><br/>"
                                   f"Cost: ${item['total_cost']:,.2f}<br/>"
                                   f"Percentage: {percentage:.1f}%<br/>"
                                   f"Resources: {item.get('resource_count', 'N/A')}"
                    }
                })

            chart_config = {
                "title": {
                    "text": config.title if config else "Cost Distribution by Service",
                    "left": "center",
                    "textStyle": {"fontSize": 16, "fontWeight": "bold"}
                },
                "tooltip": {
                    "trigger": "item",
                    "backgroundColor": "rgba(50, 50, 50, 0.9)",
                    "textStyle": {"color": "#fff"}
                },
                "series": [{
                    "name": "Service Cost",
                    "type": "treemap",
                    "data": treemap_data,
                    "roam": False,
                    "nodeClick": "zoomToNode",
                    "breadcrumb": {
                        "show": True,
                        "emptyItemWidth": 25,
                        "itemStyle": {
                            "color": "rgba(0,0,0,0.7)",
                            "textStyle": {"color": "#fff"}
                        }
                    },
                    "label": {
                        "show": True,
                        "fontSize": 12,
                        "fontWeight": "bold",
                        "color": "#fff"
                    },
                    "upperLabel": {
                        "show": True,
                        "height": 30,
                        "color": "#fff",
                        "fontSize": 14,
                        "fontWeight": "bold"
                    }
                }]
            }

            return chart_config

        except Exception as exc:
            logger.error("Failed to create service distribution chart: %s", exc)
            return self._create_error_chart(f"Service distribution error: {exc}")

    def get_commitment_discount_chart(
        self,
        data: List[Dict[str, Any]],
        config: Optional[FinOpsVisualizationConfig] = None
    ) -> Dict[str, Any]:
        """
        Create commitment discount utilization chart.

        Args:
            data: FOCUS-compliant commitment discount data
            config: Optional visualization configuration

        Returns:
            ECharts configuration for commitment discount chart
        """
        try:
            if not data:
                return self._create_empty_chart("No commitment discount data available")

            # Aggregate commitment discount data
            discount_data = self._aggregate_by_commitment_discount(data)

            chart_config = {
                "title": {
                    "text": config.title if config else "Commitment Discount Utilization",
                    "left": "center",
                    "textStyle": {"fontSize": 16, "fontWeight": "bold"}
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {"type": "shadow"},
                    "backgroundColor": "rgba(50, 50, 50, 0.9)",
                    "textStyle": {"color": "#fff"},
                    "formatter": lambda params: self._format_commitment_tooltip(params)
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": True
                },
                "xAxis": {
                    "type": "category",
                    "data": [item["discount_name"] for item in discount_data],
                    "axisLabel": {
                        "interval": 0,
                        "rotate": 45
                    }
                },
                "yAxis": {
                    "type": "value",
                    "name": "Utilization %",
                    "min": 0,
                    "max": 100,
                    "axisLabel": {
                        "formatter": "{value}%"
                    }
                },
                "series": [{
                    "name": "Utilization",
                    "type": "bar",
                    "data": [
                        {
                            "value": item["utilization_percentage"],
                            "itemStyle": {
                                "color": self._get_commitment_color(item["utilization_percentage"])
                            },
                            "emphasis": {
                                "itemStyle": {
                                    "shadowBlur": 10,
                                    "shadowColor": "rgba(0,0,0,0.3)"
                                }
                            }
                        }
                        for item in discount_data
                    ],
                    "markLine": {
                        "data": [
                            {"yAxis": 60, "name": "Target", "lineStyle": {"color": "#faad14"}},
                            {"yAxis": 80, "name": "Optimal", "lineStyle": {"color": "#52c41a"}}
                        ]
                    }
                }]
            }

            return chart_config

        except Exception as exc:
            logger.error("Failed to create commitment discount chart: %s", exc)
            return self._create_error_chart(f"Commitment discount error: {exc}")

    def get_regional_comparison_chart(
        self,
        data: List[Dict[str, Any]],
        config: Optional[FinOpsVisualizationConfig] = None
    ) -> Dict[str, Any]:
        """
        Create regional cost comparison chart.

        Args:
            data: FOCUS-compliant regional cost data
            config: Optional visualization configuration

        Returns:
            ECharts configuration for regional comparison
        """
        try:
            if not data:
                return self._create_empty_chart("No regional data available")

            # Aggregate data by region
            regional_data = self._aggregate_by_region(data)

            chart_config = {
                "title": {
                    "text": config.title if config else "Cost Distribution by Region",
                    "left": "center",
                    "textStyle": {"fontSize": 16, "fontWeight": "bold"}
                },
                "tooltip": {
                    "trigger": "item",
                    "backgroundColor": "rgba(50, 50, 50, 0.9)",
                    "textStyle": {"color": "#fff"}
                },
                "legend": {
                    "orient": "vertical",
                    "left": "left",
                    "data": [item["region"] for item in regional_data]
                },
                "series": [{
                    "name": "Regional Cost",
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "avoidLabelOverlap": False,
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": "rgba(0, 0, 0, 0.5)"
                        }
                    },
                    "label": {
                        "show": False,
                        "position": "center"
                    },
                    "labelLine": {
                        "show": False
                    },
                    "data": [
                        {
                            "value": item["total_cost"],
                            "name": item["region"],
                            "itemStyle": {
                                "color": self._get_region_color(item["region"])
                            }
                        }
                        for item in regional_data
                    ]
                }]
            }

            return chart_config

        except Exception as exc:
            logger.error("Failed to create regional comparison chart: %s", exc)
            return self._create_error_chart(f"Regional comparison error: {exc}")

    def get_optimization_opportunities_chart(
        self,
        opportunities: List[Dict[str, Any]],
        config: Optional[FinOpsVisualizationConfig] = None
    ) -> Dict[str, Any]:
        """
        Create optimization opportunities bubble chart.

        Args:
            opportunities: List of optimization opportunities
            config: Optional visualization configuration

        Returns:
            ECharts configuration for optimization opportunities
        """
        try:
            if not opportunities:
                return self._create_empty_chart("No optimization opportunities found")

            # Prepare bubble chart data
            bubble_data = []
            for opp in opportunities:
                bubble_data.append([
                    float(opp.get("potential_savings_monthly", 0)),  # x-axis: savings
                    float(opp.get("confidence_score", 0) * 100),     # y-axis: confidence
                    float(opp.get("implementation_effort_score", 50)), # bubble size
                    opp.get("title", "Unknown Opportunity"),         # name
                    opp.get("optimization_type", "unknown")          # category
                ])

            chart_config = {
                "title": {
                    "text": config.title if config else "Optimization Opportunities",
                    "left": "center",
                    "textStyle": {"fontSize": 16, "fontWeight": "bold"}
                },
                "tooltip": {
                    "trigger": "item",
                    "backgroundColor": "rgba(50, 50, 50, 0.9)",
                    "textStyle": {"color": "#fff"},
                    "formatter": lambda params: self._format_opportunity_tooltip(params)
                },
                "grid": {
                    "left": "10%",
                    "right": "10%",
                    "bottom": "15%",
                    "containLabel": True
                },
                "xAxis": {
                    "type": "value",
                    "name": "Potential Monthly Savings ($)",
                    "axisLabel": {
                        "formatter": "${value}"
                    }
                },
                "yAxis": {
                    "type": "value",
                    "name": "Confidence Score (%)",
                    "min": 0,
                    "max": 100,
                    "axisLabel": {
                        "formatter": "{value}%"
                    }
                },
                "series": [{
                    "name": "Optimization Opportunities",
                    "type": "scatter",
                    "data": bubble_data,
                    "symbolSize": lambda data: max(data[2] / 2, 10),  # Dynamic bubble size
                    "itemStyle": {
                        "opacity": 0.8
                    },
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowColor": "rgba(0, 0, 0, 0.5)"
                        }
                    }
                }]
            }

            return chart_config

        except Exception as exc:
            logger.error("Failed to create optimization opportunities chart: %s", exc)
            return self._create_error_chart(f"Optimization opportunities error: {exc}")

    def create_finops_dashboard(
        self,
        dashboard_type: FinOpsDashboardType,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create comprehensive FinOps dashboard configuration.

        Args:
            dashboard_type: Type of FinOps dashboard
            data: Complete dataset for dashboard

        Returns:
            Dashboard configuration with multiple charts
        """
        try:
            dashboard_config = {
                "title": self._get_dashboard_title(dashboard_type),
                "layout": "grid",
                "responsive": True,
                "charts": []
            }

            if dashboard_type == FinOpsDashboardType.EXECUTIVE_SUMMARY:
                dashboard_config["charts"] = self._create_executive_dashboard_charts(data)
            elif dashboard_type == FinOpsDashboardType.COST_OPTIMIZATION:
                dashboard_config["charts"] = self._create_cost_optimization_dashboard_charts(data)
            elif dashboard_type == FinOpsDashboardType.RESOURCE_UTILIZATION:
                dashboard_config["charts"] = self._create_resource_utilization_dashboard_charts(data)
            elif dashboard_type == FinOpsDashboardType.ANOMALY_DETECTION:
                dashboard_config["charts"] = self._create_anomaly_detection_dashboard_charts(data)
            elif dashboard_type == FinOpsDashboardType.COMMITMENT_ANALYSIS:
                dashboard_config["charts"] = self._create_commitment_analysis_dashboard_charts(data)

            return dashboard_config

        except Exception as exc:
            logger.error("Failed to create FinOps dashboard: %s", exc)
            return {"error": True, "message": str(exc)}

    # Private helper methods

    def _aggregate_cost_by_time(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate cost data by time periods."""
        time_data = defaultdict(lambda: {"billed_cost": 0, "effective_cost": 0, "count": 0})

        for record in data:
            period_start = record.get("BillingPeriodStart", record.get("billing_period_start", ""))
            if period_start:
                # Extract date part
                date_key = period_start.split("T")[0] if "T" in period_start else period_start

                billed_cost = float(record.get("BilledCost", record.get("billed_cost", 0)))
                effective_cost = float(record.get("EffectiveCost", billed_cost))

                time_data[date_key]["billed_cost"] += billed_cost
                time_data[date_key]["effective_cost"] += effective_cost
                time_data[date_key]["count"] += 1

        # Convert to sorted list
        result = []
        for date_key, values in sorted(time_data.items()):
            result.append({
                "date": date_key,
                "billed_cost": values["billed_cost"],
                "effective_cost": values["effective_cost"],
                "record_count": values["count"]
            })

        return result

    def _aggregate_by_service(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate data by service."""
        service_data = defaultdict(lambda: {"total_cost": 0, "resource_count": 0})

        for record in data:
            service_name = record.get("ServiceName", record.get("service_name", "Unknown"))
            cost = float(record.get("BilledCost", record.get("billed_cost", 0)))

            service_data[service_name]["total_cost"] += cost
            service_data[service_name]["resource_count"] += 1

        # Convert to sorted list by cost
        result = []
        for service_name, values in service_data.items():
            result.append({
                "service_name": service_name,
                "total_cost": values["total_cost"],
                "resource_count": values["resource_count"]
            })

        return sorted(result, key=lambda x: x["total_cost"], reverse=True)

    def _aggregate_by_commitment_discount(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate commitment discount data."""
        discount_data = defaultdict(lambda: {"total_cost": 0, "discounted_cost": 0, "count": 0})

        for record in data:
            discount_name = record.get("CommitmentDiscountName",
                                     record.get("commitment_discount_name", "No Commitment"))
            cost = float(record.get("BilledCost", record.get("billed_cost", 0)))

            discount_data[discount_name]["total_cost"] += cost
            discount_data[discount_name]["count"] += 1

            # If commitment discount exists, it's discounted cost
            if record.get("CommitmentDiscountCategory") or record.get("commitment_discount_category"):
                discount_data[discount_name]["discounted_cost"] += cost

        # Calculate utilization percentages
        result = []
        for discount_name, values in discount_data.items():
            if discount_name != "No Commitment":
                # Mock utilization calculation (in production, would use actual commitment data)
                utilization = min((values["discounted_cost"] / max(values["total_cost"], 1)) * 100, 100)
            else:
                utilization = 0

            result.append({
                "discount_name": discount_name,
                "utilization_percentage": utilization,
                "total_cost": values["total_cost"],
                "discounted_cost": values["discounted_cost"]
            })

        return sorted(result, key=lambda x: x["utilization_percentage"], reverse=True)

    def _aggregate_by_region(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate data by region."""
        regional_data = defaultdict(float)

        for record in data:
            region = record.get("Region", record.get("region", "Unknown"))
            cost = float(record.get("BilledCost", record.get("billed_cost", 0)))
            regional_data[region] += cost

        # Convert to sorted list
        result = []
        for region, total_cost in regional_data.items():
            result.append({
                "region": region,
                "total_cost": total_cost
            })

        return sorted(result, key=lambda x: x["total_cost"], reverse=True)

    def _calculate_trend_line(self, time_series_data: List[Dict[str, Any]]) -> List[List]:
        """Calculate trend line for time series data."""
        if len(time_series_data) < 2:
            return []

        # Simple linear regression for trend
        costs = [item["billed_cost"] for item in time_series_data]
        x_values = list(range(len(costs)))

        # Calculate slope
        n = len(costs)
        sum_x = sum(x_values)
        sum_y = sum(costs)
        sum_xy = sum(x * y for x, y in zip(x_values, costs))
        sum_x2 = sum(x * x for x in x_values)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n

        # Generate trend line points
        trend_points = []
        for i, item in enumerate(time_series_data):
            trend_value = slope * i + intercept
            trend_points.append([item["date"], trend_value])

        return trend_points

    def _get_service_color(self, service_name: str) -> str:
        """Get color for service based on category."""
        service_lower = service_name.lower()

        if any(word in service_lower for word in ["ec2", "compute", "virtual", "lambda", "function"]):
            return self.color_schemes.SERVICE_CATEGORIES["compute"]
        elif any(word in service_lower for word in ["s3", "storage", "blob", "disk"]):
            return self.color_schemes.SERVICE_CATEGORIES["storage"]
        elif any(word in service_lower for word in ["rds", "database", "sql", "mongo", "redis"]):
            return self.color_schemes.SERVICE_CATEGORIES["database"]
        elif any(word in service_lower for word in ["vpc", "network", "cdn", "dns", "load"]):
            return self.color_schemes.SERVICE_CATEGORIES["networking"]
        elif any(word in service_lower for word in ["analytics", "data", "spark", "hadoop"]):
            return self.color_schemes.SERVICE_CATEGORIES["analytics"]
        elif any(word in service_lower for word in ["ai", "ml", "machine", "learning", "sage"]):
            return self.color_schemes.SERVICE_CATEGORIES["ai_ml"]
        elif any(word in service_lower for word in ["security", "iam", "kms", "guard"]):
            return self.color_schemes.SERVICE_CATEGORIES["security"]
        elif any(word in service_lower for word in ["cloudwatch", "monitor", "log", "trace"]):
            return self.color_schemes.SERVICE_CATEGORIES["management"]
        else:
            return self.color_schemes.SERVICE_CATEGORIES["other"]

    def _get_commitment_color(self, utilization_percentage: float) -> str:
        """Get color based on commitment discount utilization."""
        if utilization_percentage >= 80:
            return self.color_schemes.COMMITMENT_DISCOUNTS["high_utilization"]
        elif utilization_percentage >= 60:
            return self.color_schemes.COMMITMENT_DISCOUNTS["medium_utilization"]
        elif utilization_percentage > 0:
            return self.color_schemes.COMMITMENT_DISCOUNTS["low_utilization"]
        else:
            return self.color_schemes.COMMITMENT_DISCOUNTS["no_commitment"]

    def _get_region_color(self, region: str) -> str:
        """Get color for region."""
        # Simple hash-based color assignment for regions
        hash_value = hash(region) % len(list(self.color_schemes.SERVICE_CATEGORIES.values()))
        colors = list(self.color_schemes.SERVICE_CATEGORIES.values())
        return colors[hash_value]

    def _create_cost_tooltip_formatter(self) -> str:
        """Create tooltip formatter for cost charts."""
        return """
        function(params) {
            let result = params[0].axisValueLabel + '<br/>';
            params.forEach(param => {
                result += param.marker + param.seriesName + ': $' +
                         param.value[1].toLocaleString('en-US', {minimumFractionDigits: 2}) + '<br/>';
            });
            return result;
        }
        """

    def _format_commitment_tooltip(self, params) -> str:
        """Format tooltip for commitment discount chart."""
        # This would be implemented as JavaScript in practice
        return f"<b>{params.name}</b><br/>Utilization: {params.value}%"

    def _format_opportunity_tooltip(self, params) -> str:
        """Format tooltip for optimization opportunities."""
        # This would be implemented as JavaScript in practice
        return f"<b>{params.data[3]}</b><br/>Savings: ${params.data[0]:,.2f}<br/>Confidence: {params.data[1]:.1f}%"

    def _create_empty_chart(self, message: str) -> Dict[str, Any]:
        """Create empty chart configuration."""
        return {
            "title": {
                "text": message,
                "left": "center",
                "top": "center",
                "textStyle": {"color": "#999", "fontSize": 14}
            },
            "xAxis": {"show": False},
            "yAxis": {"show": False},
            "series": []
        }

    def _create_error_chart(self, error_message: str) -> Dict[str, Any]:
        """Create error chart configuration."""
        return {
            "title": {
                "text": f"Error: {error_message}",
                "left": "center",
                "top": "center",
                "textStyle": {"color": "#ff4d4f", "fontSize": 14}
            },
            "xAxis": {"show": False},
            "yAxis": {"show": False},
            "series": []
        }

    def _get_dashboard_title(self, dashboard_type: FinOpsDashboardType) -> str:
        """Get title for dashboard type."""
        titles = {
            FinOpsDashboardType.EXECUTIVE_SUMMARY: "Executive Summary Dashboard",
            FinOpsDashboardType.COST_OPTIMIZATION: "Cost Optimization Dashboard",
            FinOpsDashboardType.RESOURCE_UTILIZATION: "Resource Utilization Dashboard",
            FinOpsDashboardType.ANOMALY_DETECTION: "Anomaly Detection Dashboard",
            FinOpsDashboardType.COMMITMENT_ANALYSIS: "Commitment Analysis Dashboard"
        }
        return titles.get(dashboard_type, "FinOps Dashboard")

    def _create_executive_dashboard_charts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create charts for executive dashboard."""
        charts = []

        # Cost trend overview
        if "cost_data" in data:
            charts.append({
                "id": "exec_cost_trend",
                "title": "Monthly Cost Trend",
                "chart": self.get_cost_trend_chart(data["cost_data"]),
                "size": {"width": "100%", "height": "400px"},
                "position": {"row": 1, "col": 1, "span": 2}
            })

        # Service distribution
        if "service_data" in data:
            charts.append({
                "id": "exec_service_dist",
                "title": "Top Services by Cost",
                "chart": self.get_service_cost_distribution(data["service_data"]),
                "size": {"width": "50%", "height": "350px"},
                "position": {"row": 2, "col": 1}
            })

        # Regional breakdown
        if "regional_data" in data:
            charts.append({
                "id": "exec_regional",
                "title": "Regional Cost Distribution",
                "chart": self.get_regional_comparison_chart(data["regional_data"]),
                "size": {"width": "50%", "height": "350px"},
                "position": {"row": 2, "col": 2}
            })

        return charts

    def _create_cost_optimization_dashboard_charts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create charts for cost optimization dashboard."""
        charts = []

        # Optimization opportunities
        if "opportunities" in data:
            charts.append({
                "id": "opt_opportunities",
                "title": "Optimization Opportunities",
                "chart": self.get_optimization_opportunities_chart(data["opportunities"]),
                "size": {"width": "100%", "height": "400px"},
                "position": {"row": 1, "col": 1, "span": 2}
            })

        # Commitment discount analysis
        if "commitment_data" in data:
            charts.append({
                "id": "opt_commitment",
                "title": "Commitment Discount Utilization",
                "chart": self.get_commitment_discount_chart(data["commitment_data"]),
                "size": {"width": "100%", "height": "350px"},
                "position": {"row": 2, "col": 1, "span": 2}
            })

        return charts

    def _create_resource_utilization_dashboard_charts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create charts for resource utilization dashboard."""
        # Implementation would create utilization-specific charts
        return []

    def _create_anomaly_detection_dashboard_charts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create charts for anomaly detection dashboard."""
        # Implementation would create anomaly-specific charts
        return []

    def _create_commitment_analysis_dashboard_charts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create charts for commitment analysis dashboard."""
        # Implementation would create commitment-specific charts
        return []


# Factory function for integration
async def create_finops_echarts_templates(echarts_adapter=None) -> FinOpsEChartsTemplates:
    """
    Factory function to create FinOpsEChartsTemplates instance.

    Args:
        echarts_adapter: Optional ECharts MCP adapter instance

    Returns:
        Configured FinOpsEChartsTemplates instance
    """
    templates = FinOpsEChartsTemplates(echarts_adapter)
    logger.info("Created FinOpsEChartsTemplates for FinOps analytics visualizations")
    return templates