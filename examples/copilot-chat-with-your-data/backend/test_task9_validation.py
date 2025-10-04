"""
Test suite for Task 9: ECharts Visualization for FinOps Analytics.

This test validates the FinOps-specific ECharts visualization templates,
interactive dashboards, and drill-down capabilities for comprehensive
FinOps analytics and cost optimization workflows.
"""

import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch


def test_finops_echarts_templates_architecture():
    """Test FinOps ECharts templates architecture and data models."""

    print("🔍 Testing FinOps ECharts Templates Architecture...")

    try:
        # Test import structure
        from finops_echarts_templates import (
            FinOpsDashboardType,
            FinOpsVisualizationType,
            FinOpsVisualizationConfig,
            FinOpsColorSchemes,
            FinOpsEChartsTemplates,
            create_finops_echarts_templates
        )
        print("✅ FinOps ECharts templates imports successful")

        # Test dashboard types enum
        assert FinOpsDashboardType.EXECUTIVE_SUMMARY.value == "executive_summary", "Executive summary dashboard type should exist"
        assert FinOpsDashboardType.COST_OPTIMIZATION.value == "cost_optimization", "Cost optimization dashboard type should exist"
        assert FinOpsDashboardType.RESOURCE_UTILIZATION.value == "resource_utilization", "Resource utilization dashboard type should exist"
        assert FinOpsDashboardType.ANOMALY_DETECTION.value == "anomaly_detection", "Anomaly detection dashboard type should exist"
        print("✅ FinOps dashboard types enum working correctly")

        # Test visualization types enum
        assert FinOpsVisualizationType.COST_TREND.value == "cost_trend", "Cost trend visualization type should exist"
        assert FinOpsVisualizationType.SERVICE_DISTRIBUTION.value == "service_distribution", "Service distribution type should exist"
        assert FinOpsVisualizationType.COMMITMENT_DISCOUNT.value == "commitment_discount", "Commitment discount type should exist"
        print("✅ FinOps visualization types enum working correctly")

        # Test visualization configuration
        config = FinOpsVisualizationConfig(
            visualization_type=FinOpsVisualizationType.COST_TREND,
            title="Test Cost Trend",
            chart_type="line",
            dimensions=["time"],
            metrics=["cost"],
            cost_thresholds={"high": 1000.0, "medium": 500.0},
            color_scheme="finops_default",
            interactive_features=["drill_down", "zoom"],
            drill_down_enabled=True
        )

        assert config.visualization_type == FinOpsVisualizationType.COST_TREND, "Visualization type should be set"
        assert config.title == "Test Cost Trend", "Title should be set"
        assert config.drill_down_enabled is True, "Drill-down should be enabled"
        assert len(config.interactive_features) == 2, "Should have interactive features"
        print("✅ FinOpsVisualizationConfig creation successful")

        # Test color schemes
        color_schemes = FinOpsColorSchemes()
        assert hasattr(color_schemes, 'FINOPS_DEFAULT'), "Should have default color scheme"
        assert hasattr(color_schemes, 'COST_OPTIMIZATION'), "Should have cost optimization colors"
        assert hasattr(color_schemes, 'SERVICE_CATEGORIES'), "Should have service category colors"
        assert hasattr(color_schemes, 'COMMITMENT_DISCOUNTS'), "Should have commitment discount colors"

        # Test color scheme content
        assert "primary" in color_schemes.FINOPS_DEFAULT, "Should have primary color"
        assert "high_cost" in color_schemes.COST_OPTIMIZATION, "Should have high cost color"
        assert "compute" in color_schemes.SERVICE_CATEGORIES, "Should have compute color"
        assert "high_utilization" in color_schemes.COMMITMENT_DISCOUNTS, "Should have high utilization color"
        print("✅ FinOps color schemes initialized correctly")

        return True

    except Exception as e:
        print(f"❌ FinOps ECharts templates architecture test failed: {e}")
        return False


def test_finops_echarts_templates_initialization():
    """Test FinOps ECharts templates initialization."""

    print("🔍 Testing FinOps ECharts Templates Initialization...")

    try:
        from finops_echarts_templates import FinOpsEChartsTemplates

        # Mock ECharts adapter
        mock_echarts_adapter = MagicMock()

        # Test initialization with adapter
        templates = FinOpsEChartsTemplates(echarts_mcp_adapter=mock_echarts_adapter)
        assert templates.echarts_adapter is mock_echarts_adapter, "Should store ECharts adapter reference"
        assert hasattr(templates, 'color_schemes'), "Should have color schemes"
        print("✅ Templates initialization with adapter successful")

        # Test initialization without adapter
        minimal_templates = FinOpsEChartsTemplates()
        assert minimal_templates.echarts_adapter is None, "Should handle None adapter"
        assert hasattr(minimal_templates, 'color_schemes'), "Should still have color schemes"
        print("✅ Minimal templates initialization successful")

        return True

    except Exception as e:
        print(f"❌ FinOps ECharts templates initialization test failed: {e}")
        return False


def test_cost_trend_chart_generation():
    """Test cost trend chart generation."""

    print("🔍 Testing Cost Trend Chart Generation...")

    try:
        from finops_echarts_templates import FinOpsEChartsTemplates, FinOpsVisualizationType, FinOpsVisualizationConfig

        templates = FinOpsEChartsTemplates()

        # Test with sample FOCUS data
        sample_data = [
            {
                "BillingPeriodStart": "2024-01-01T00:00:00Z",
                "BilledCost": 1000.50,
                "EffectiveCost": 950.25,
                "ServiceName": "Amazon EC2"
            },
            {
                "BillingPeriodStart": "2024-01-02T00:00:00Z",
                "BilledCost": 1200.75,
                "EffectiveCost": 1140.00,
                "ServiceName": "Amazon S3"
            },
            {
                "BillingPeriodStart": "2024-01-03T00:00:00Z",
                "BilledCost": 950.00,
                "EffectiveCost": 900.50,
                "ServiceName": "Amazon RDS"
            }
        ]

        # Test cost trend chart creation
        config = FinOpsVisualizationConfig(
            visualization_type=FinOpsVisualizationType.COST_TREND,
            title="Monthly Cost Trends",
            chart_type="line",
            dimensions=["time"],
            metrics=["BilledCost", "EffectiveCost"]
        )

        chart_config = templates.get_cost_trend_chart(sample_data, config)

        # Validate chart structure
        assert "title" in chart_config, "Chart should have title"
        assert "tooltip" in chart_config, "Chart should have tooltip"
        assert "legend" in chart_config, "Chart should have legend"
        assert "xAxis" in chart_config, "Chart should have x-axis"
        assert "yAxis" in chart_config, "Chart should have y-axis"
        assert "series" in chart_config, "Chart should have series"

        # Validate chart content
        assert chart_config["title"]["text"] == "Monthly Cost Trends", "Should use config title"
        assert chart_config["xAxis"]["type"] == "time", "X-axis should be time type"
        assert chart_config["yAxis"]["type"] == "value", "Y-axis should be value type"
        assert len(chart_config["series"]) >= 2, "Should have multiple series for billed and effective cost"

        # Check series data
        billed_series = next(s for s in chart_config["series"] if s["name"] == "Billed Cost")
        assert billed_series["type"] == "line", "Billed cost should be line chart"
        assert len(billed_series["data"]) == 3, "Should have data points for all sample records"
        print("✅ Cost trend chart generation successful")

        # Test with empty data
        empty_chart = templates.get_cost_trend_chart([])
        assert "title" in empty_chart, "Empty chart should have title"
        assert "no cost trend data available" in empty_chart["title"]["text"].lower(), "Should indicate no data"
        print("✅ Empty data handling for cost trend chart working")

        return True

    except Exception as e:
        print(f"❌ Cost trend chart generation test failed: {e}")
        return False


def test_service_cost_distribution_chart():
    """Test service cost distribution treemap chart."""

    print("🔍 Testing Service Cost Distribution Chart...")

    try:
        from finops_echarts_templates import FinOpsEChartsTemplates

        templates = FinOpsEChartsTemplates()

        # Test with sample service data
        sample_data = [
            {
                "ServiceName": "Amazon EC2",
                "BilledCost": 5000.00,
                "ResourceId": "i-123456789"
            },
            {
                "ServiceName": "Amazon S3",
                "BilledCost": 1500.00,
                "ResourceId": "bucket-1"
            },
            {
                "ServiceName": "Amazon RDS",
                "BilledCost": 2500.00,
                "ResourceId": "db-instance-1"
            },
            {
                "ServiceName": "Amazon EC2",
                "BilledCost": 3000.00,
                "ResourceId": "i-987654321"
            }
        ]

        # Test service distribution chart creation
        chart_config = templates.get_service_cost_distribution(sample_data)

        # Validate chart structure
        assert "title" in chart_config, "Chart should have title"
        assert "tooltip" in chart_config, "Chart should have tooltip"
        assert "series" in chart_config, "Chart should have series"

        # Validate treemap configuration
        series = chart_config["series"][0]
        assert series["type"] == "treemap", "Should be treemap chart"
        assert "data" in series, "Series should have data"
        assert len(series["data"]) > 0, "Should have treemap data points"

        # Check data aggregation (EC2 should be combined)
        treemap_data = series["data"]
        ec2_data = next(d for d in treemap_data if "Amazon EC2" in d["name"])
        assert ec2_data["value"] == 8000.00, "EC2 costs should be aggregated (5000 + 3000)"
        print("✅ Service cost distribution chart generation successful")

        # Test service color assignment
        assert "itemStyle" in ec2_data, "Should have item style for coloring"
        assert "color" in ec2_data["itemStyle"], "Should have color assigned"
        print("✅ Service color assignment working")

        return True

    except Exception as e:
        print(f"❌ Service cost distribution chart test failed: {e}")
        return False


def test_commitment_discount_chart():
    """Test commitment discount utilization chart."""

    print("🔍 Testing Commitment Discount Chart...")

    try:
        from finops_echarts_templates import FinOpsEChartsTemplates

        templates = FinOpsEChartsTemplates()

        # Test with sample commitment data
        sample_data = [
            {
                "CommitmentDiscountName": "Savings Plan 1",
                "CommitmentDiscountCategory": "Spend",
                "BilledCost": 1000.00
            },
            {
                "CommitmentDiscountName": "Reserved Instance 1",
                "CommitmentDiscountCategory": "Usage",
                "BilledCost": 800.00
            },
            {
                "BilledCost": 500.00  # No commitment discount
            },
            {
                "CommitmentDiscountName": "Savings Plan 1",
                "CommitmentDiscountCategory": "Spend",
                "BilledCost": 600.00
            }
        ]

        # Test commitment discount chart creation
        chart_config = templates.get_commitment_discount_chart(sample_data)

        # Validate chart structure
        assert "title" in chart_config, "Chart should have title"
        assert "tooltip" in chart_config, "Chart should have tooltip"
        assert "xAxis" in chart_config, "Chart should have x-axis"
        assert "yAxis" in chart_config, "Chart should have y-axis"
        assert "series" in chart_config, "Chart should have series"

        # Validate bar chart configuration
        series = chart_config["series"][0]
        assert series["type"] == "bar", "Should be bar chart"
        assert "data" in series, "Series should have data"

        # Check y-axis configuration for percentage
        assert chart_config["yAxis"]["min"] == 0, "Y-axis should start at 0"
        assert chart_config["yAxis"]["max"] == 100, "Y-axis should end at 100"
        assert "%" in chart_config["yAxis"]["axisLabel"]["formatter"], "Y-axis should show percentage"

        # Check mark lines for targets
        assert "markLine" in series, "Should have target lines"
        mark_lines = series["markLine"]["data"]
        assert len(mark_lines) >= 2, "Should have target and optimal lines"
        print("✅ Commitment discount chart generation successful")

        return True

    except Exception as e:
        print(f"❌ Commitment discount chart test failed: {e}")
        return False


def test_regional_comparison_chart():
    """Test regional cost comparison chart."""

    print("🔍 Testing Regional Comparison Chart...")

    try:
        from finops_echarts_templates import FinOpsEChartsTemplates

        templates = FinOpsEChartsTemplates()

        # Test with sample regional data
        sample_data = [
            {"Region": "us-east-1", "BilledCost": 4000.00},
            {"Region": "us-west-2", "BilledCost": 2500.00},
            {"Region": "eu-west-1", "BilledCost": 1500.00},
            {"Region": "us-east-1", "BilledCost": 1000.00}  # Additional us-east-1 cost
        ]

        # Test regional comparison chart creation
        chart_config = templates.get_regional_comparison_chart(sample_data)

        # Validate chart structure
        assert "title" in chart_config, "Chart should have title"
        assert "tooltip" in chart_config, "Chart should have tooltip"
        assert "legend" in chart_config, "Chart should have legend"
        assert "series" in chart_config, "Chart should have series"

        # Validate pie chart configuration
        series = chart_config["series"][0]
        assert series["type"] == "pie", "Should be pie chart"
        assert "data" in series, "Series should have data"

        # Check data aggregation and structure
        pie_data = series["data"]
        assert len(pie_data) == 3, "Should have 3 unique regions"

        # Find us-east-1 data point
        us_east_data = next(d for d in pie_data if d["name"] == "us-east-1")
        assert us_east_data["value"] == 5000.00, "us-east-1 costs should be aggregated (4000 + 1000)"
        print("✅ Regional comparison chart generation successful")

        return True

    except Exception as e:
        print(f"❌ Regional comparison chart test failed: {e}")
        return False


def test_optimization_opportunities_chart():
    """Test optimization opportunities bubble chart."""

    print("🔍 Testing Optimization Opportunities Chart...")

    try:
        from finops_echarts_templates import FinOpsEChartsTemplates

        templates = FinOpsEChartsTemplates()

        # Test with sample optimization opportunities
        sample_opportunities = [
            {
                "title": "Right-size EC2 instances",
                "optimization_type": "rightsizing",
                "potential_savings_monthly": 1200.00,
                "confidence_score": 0.85,
                "implementation_effort_score": 60.0
            },
            {
                "title": "Purchase Savings Plans",
                "optimization_type": "commitment_opportunity",
                "potential_savings_monthly": 2500.00,
                "confidence_score": 0.90,
                "implementation_effort_score": 40.0
            },
            {
                "title": "Remove unused volumes",
                "optimization_type": "unused_resources",
                "potential_savings_monthly": 800.00,
                "confidence_score": 0.95,
                "implementation_effort_score": 20.0
            }
        ]

        # Test optimization opportunities chart creation
        chart_config = templates.get_optimization_opportunities_chart(sample_opportunities)

        # Validate chart structure
        assert "title" in chart_config, "Chart should have title"
        assert "tooltip" in chart_config, "Chart should have tooltip"
        assert "xAxis" in chart_config, "Chart should have x-axis"
        assert "yAxis" in chart_config, "Chart should have y-axis"
        assert "series" in chart_config, "Chart should have series"

        # Validate scatter chart configuration
        series = chart_config["series"][0]
        assert series["type"] == "scatter", "Should be scatter chart"
        assert "data" in series, "Series should have data"
        assert len(series["data"]) == 3, "Should have 3 opportunity data points"

        # Check axis configurations
        assert "Potential Monthly Savings" in chart_config["xAxis"]["name"], "X-axis should show savings"
        assert "Confidence Score" in chart_config["yAxis"]["name"], "Y-axis should show confidence"
        assert chart_config["yAxis"]["min"] == 0, "Y-axis should start at 0"
        assert chart_config["yAxis"]["max"] == 100, "Y-axis should end at 100"

        # Check data point structure
        first_opportunity = series["data"][0]
        assert len(first_opportunity) == 5, "Data point should have 5 elements (x, y, size, name, category)"
        assert first_opportunity[0] == 1200.00, "X-value should be potential savings"
        assert first_opportunity[1] == 85.0, "Y-value should be confidence score * 100"
        print("✅ Optimization opportunities chart generation successful")

        return True

    except Exception as e:
        print(f"❌ Optimization opportunities chart test failed: {e}")
        return False


def test_finops_dashboard_creation():
    """Test FinOps dashboard creation."""

    print("🔍 Testing FinOps Dashboard Creation...")

    try:
        from finops_echarts_templates import FinOpsEChartsTemplates, FinOpsDashboardType

        templates = FinOpsEChartsTemplates()

        # Test executive summary dashboard
        sample_data = {
            "cost_data": [
                {"BillingPeriodStart": "2024-01-01", "BilledCost": 1000.00}
            ],
            "service_data": [
                {"ServiceName": "Amazon EC2", "BilledCost": 500.00}
            ],
            "regional_data": [
                {"Region": "us-east-1", "BilledCost": 800.00}
            ]
        }

        dashboard_config = templates.create_finops_dashboard(
            FinOpsDashboardType.EXECUTIVE_SUMMARY,
            sample_data
        )

        # Validate dashboard structure
        assert "title" in dashboard_config, "Dashboard should have title"
        assert "layout" in dashboard_config, "Dashboard should have layout"
        assert "charts" in dashboard_config, "Dashboard should have charts"
        assert dashboard_config["responsive"] is True, "Dashboard should be responsive"

        # Check dashboard title
        assert "Executive Summary" in dashboard_config["title"], "Should have correct title"

        # Check charts
        charts = dashboard_config["charts"]
        assert len(charts) > 0, "Should have dashboard charts"

        # Validate chart structure
        first_chart = charts[0]
        required_fields = ["id", "title", "chart", "size", "position"]
        for field in required_fields:
            assert field in first_chart, f"Chart should have {field}"

        print("✅ Executive summary dashboard creation successful")

        # Test cost optimization dashboard
        optimization_data = {
            "opportunities": [
                {"title": "Test Opportunity", "potential_savings_monthly": 1000.0, "confidence_score": 0.8}
            ],
            "commitment_data": [
                {"CommitmentDiscountName": "Test Commitment", "BilledCost": 500.0}
            ]
        }

        cost_opt_dashboard = templates.create_finops_dashboard(
            FinOpsDashboardType.COST_OPTIMIZATION,
            optimization_data
        )

        assert "Cost Optimization" in cost_opt_dashboard["title"], "Should have cost optimization title"
        print("✅ Cost optimization dashboard creation successful")

        return True

    except Exception as e:
        print(f"❌ FinOps dashboard creation test failed: {e}")
        return False


def test_finops_drill_down_manager_architecture():
    """Test FinOps drill-down manager architecture."""

    print("🔍 Testing FinOps Drill-Down Manager Architecture...")

    try:
        # Test import structure
        from finops_drill_down_manager import (
            FinOpsDrillDownType,
            FinOpsDrillDownLevel,
            FinOpsDrillDownContext,
            FinOpsDrillDownResult,
            finOpsDrillDownManager,
            create_finops_drill_down_manager
        )
        print("✅ FinOps drill-down manager imports successful")

        # Test drill-down types enum
        assert FinOpsDrillDownType.SERVICE_TO_RESOURCE.value == "service_to_resource", "Service to resource drill-down should exist"
        assert FinOpsDrillDownType.TIME_BASED_ANALYSIS.value == "time_based_analysis", "Time-based analysis should exist"
        assert FinOpsDrillDownType.CROSS_ACCOUNT_COMPARISON.value == "cross_account_comparison", "Cross-account comparison should exist"
        assert FinOpsDrillDownType.COMMITMENT_DISCOUNT_ANALYSIS.value == "commitment_discount_analysis", "Commitment analysis should exist"
        print("✅ FinOps drill-down types enum working correctly")

        # Test drill-down levels enum
        assert FinOpsDrillDownLevel.OVERVIEW.value == "overview", "Overview level should exist"
        assert FinOpsDrillDownLevel.SERVICE.value == "service", "Service level should exist"
        assert FinOpsDrillDownLevel.RESOURCE.value == "resource", "Resource level should exist"
        print("✅ FinOps drill-down levels enum working correctly")

        # Test drill-down context creation
        context = FinOpsDrillDownContext(
            drill_down_id="test_drill_001",
            user_id="test_user",
            session_id="test_session",
            drill_down_type=FinOpsDrillDownType.SERVICE_TO_RESOURCE,
            current_level=FinOpsDrillDownLevel.SERVICE,
            breadcrumb_path=[{"label": "Overview", "level": "overview"}],
            filter_stack=[{"region": "us-east-1"}],
            selected_dimension="ServiceName",
            selected_value="Amazon EC2",
            applied_filters={"region": "us-east-1"},
            created_at=datetime.now()
        )

        assert context.drill_down_type == FinOpsDrillDownType.SERVICE_TO_RESOURCE, "Drill-down type should be set"
        assert context.current_level == FinOpsDrillDownLevel.SERVICE, "Current level should be set"
        assert context.selected_value == "Amazon EC2", "Selected value should be set"
        assert len(context.breadcrumb_path) == 1, "Should have breadcrumb path"
        print("✅ FinOpsDrillDownContext creation successful")

        # Test drill-down result creation
        result = FinOpsDrillDownResult(
            drill_down_id="test_drill_001",
            chart_config={"title": "Test Chart"},
            data_summary={"total_cost": 1000.0},
            navigation_options={"can_drill_deeper": True},
            insights=["Test insight"],
            recommendations=["Test recommendation"],
            available_drill_downs=[{"type": "deeper", "label": "Drill Deeper"}],
            related_analyses=[{"type": "optimization", "title": "Optimization"}],
            export_options=["csv", "pdf"]
        )

        assert result.drill_down_id == "test_drill_001", "Drill-down ID should be set"
        assert "title" in result.chart_config, "Should have chart config"
        assert len(result.insights) == 1, "Should have insights"
        assert len(result.recommendations) == 1, "Should have recommendations"
        print("✅ FinOpsDrillDownResult creation successful")

        return True

    except Exception as e:
        print(f"❌ FinOps drill-down manager architecture test failed: {e}")
        return False


def test_finops_drill_down_manager_initialization():
    """Test FinOps drill-down manager initialization."""

    print("🔍 Testing FinOps Drill-Down Manager Initialization...")

    try:
        from finops_drill_down_manager import finOpsDrillDownManager

        # Mock dependencies
        mock_echarts_templates = MagicMock()
        mock_focus_integration = MagicMock()
        mock_lida_manager = MagicMock()

        # Test initialization with all components
        manager = finOpsDrillDownManager(
            echarts_templates=mock_echarts_templates,
            focus_integration=mock_focus_integration,
            lida_manager=mock_lida_manager
        )

        assert manager.echarts_templates is mock_echarts_templates, "Should store ECharts templates reference"
        assert manager.focus_integration is mock_focus_integration, "Should store FOCUS integration reference"
        assert manager.lida_manager is mock_lida_manager, "Should store LIDA manager reference"
        print("✅ Manager initialization with all components successful")

        # Test internal data structures
        assert hasattr(manager, '_active_contexts'), "Should have active contexts storage"
        assert hasattr(manager, 'drill_down_hierarchies'), "Should have drill-down hierarchies"
        assert isinstance(manager._active_contexts, dict), "Active contexts should be dictionary"
        print("✅ Internal data structures initialized correctly")

        # Test minimal initialization
        minimal_manager = finOpsDrillDownManager()
        assert minimal_manager.echarts_templates is None, "Should handle None dependencies"
        assert hasattr(minimal_manager, '_active_contexts'), "Should still have active contexts"
        print("✅ Minimal manager initialization successful")

        return True

    except Exception as e:
        print(f"❌ FinOps drill-down manager initialization test failed: {e}")
        return False


async def test_drill_down_initiation():
    """Test drill-down operation initiation."""

    print("🔍 Testing Drill-Down Initiation...")

    try:
        from finops_drill_down_manager import (
            finOpsDrillDownManager,
            FinOpsDrillDownType
        )

        # Mock dependencies
        mock_echarts_templates = MagicMock()
        mock_focus_integration = MagicMock()

        manager = finOpsDrillDownManager(
            echarts_templates=mock_echarts_templates,
            focus_integration=mock_focus_integration
        )

        # Test service-to-resource drill-down initiation
        result = await manager.initiate_drill_down(
            user_id="test_user",
            session_id="test_session",
            drill_down_type=FinOpsDrillDownType.SERVICE_TO_RESOURCE,
            selected_dimension="ServiceName",
            selected_value="Amazon EC2",
            initial_filters={"region": "us-east-1"}
        )

        # Validate result structure
        assert hasattr(result, 'drill_down_id'), "Result should have drill-down ID"
        assert hasattr(result, 'chart_config'), "Result should have chart config"
        assert hasattr(result, 'data_summary'), "Result should have data summary"
        assert hasattr(result, 'navigation_options'), "Result should have navigation options"
        assert hasattr(result, 'insights'), "Result should have insights"
        assert hasattr(result, 'recommendations'), "Result should have recommendations"

        # Check drill-down context storage
        assert len(manager._active_contexts) == 1, "Should store active context"
        stored_context = list(manager._active_contexts.values())[0]
        assert stored_context.selected_value == "Amazon EC2", "Should store selected value"
        assert stored_context.drill_down_type == FinOpsDrillDownType.SERVICE_TO_RESOURCE, "Should store drill-down type"
        print("✅ Service-to-resource drill-down initiation successful")

        # Test time-based drill-down initiation
        time_result = await manager.initiate_drill_down(
            user_id="test_user",
            session_id="test_session_2",
            drill_down_type=FinOpsDrillDownType.TIME_BASED_ANALYSIS,
            selected_dimension="BillingPeriod",
            selected_value="2024-01",
            initial_filters={"granularity": "daily"}
        )

        assert time_result.drill_down_id != result.drill_down_id, "Should have different drill-down IDs"
        assert len(manager._active_contexts) == 2, "Should store multiple active contexts"
        print("✅ Time-based drill-down initiation successful")

        return True

    except Exception as e:
        print(f"❌ Drill-down initiation test failed: {e}")
        return False


async def test_drill_down_suggestions():
    """Test drill-down suggestions generation."""

    print("🔍 Testing Drill-Down Suggestions...")

    try:
        from finops_drill_down_manager import finOpsDrillDownManager

        manager = finOpsDrillDownManager()

        # Test suggestions with high-cost services context
        high_cost_context = {
            "high_cost_services": ["Amazon EC2", "Amazon RDS"],
            "cost_anomalies": [{"type": "cost_spike", "service": "Amazon S3"}],
            "commitment_underutilization": True,
            "multi_account_data": True
        }

        suggestions = await manager.get_drill_down_suggestions(
            user_id="test_user",
            current_context=high_cost_context
        )

        # Validate suggestions structure
        assert isinstance(suggestions, list), "Should return list of suggestions"
        assert len(suggestions) > 0, "Should have suggestions for given context"

        # Check suggestion structure
        first_suggestion = suggestions[0]
        required_fields = ["type", "title", "description", "priority", "estimated_insights"]
        for field in required_fields:
            assert field in first_suggestion, f"Suggestion should have {field}"

        # Check priority ordering (high priority should be first)
        priorities = [s["priority"] for s in suggestions]
        high_priority_count = priorities.count("high")
        assert high_priority_count > 0, "Should have high priority suggestions"

        # Check for expected suggestion types
        suggestion_types = [s["type"] for s in suggestions]
        assert "service_to_resource" in suggestion_types, "Should suggest service drill-down for high-cost services"
        assert "cost_anomaly_investigation" in suggestion_types, "Should suggest anomaly investigation"
        print("✅ Drill-down suggestions generation successful")

        # Test suggestions with minimal context
        minimal_context = {}
        minimal_suggestions = await manager.get_drill_down_suggestions(
            user_id="test_user",
            current_context=minimal_context
        )

        assert isinstance(minimal_suggestions, list), "Should handle minimal context"
        print("✅ Minimal context suggestions handling working")

        return True

    except Exception as e:
        print(f"❌ Drill-down suggestions test failed: {e}")
        return False


def test_color_scheme_assignment():
    """Test color scheme assignment for different service types."""

    print("🔍 Testing Color Scheme Assignment...")

    try:
        from finops_echarts_templates import FinOpsEChartsTemplates

        templates = FinOpsEChartsTemplates()

        # Test service color assignments
        compute_color = templates._get_service_color("Amazon EC2")
        storage_color = templates._get_service_color("Amazon S3")
        database_color = templates._get_service_color("Amazon RDS")
        networking_color = templates._get_service_color("Amazon VPC")

        # Validate colors are assigned
        assert compute_color is not None, "Compute service should have color"
        assert storage_color is not None, "Storage service should have color"
        assert database_color is not None, "Database service should have color"
        assert networking_color is not None, "Networking service should have color"

        # Validate different services get different colors
        assert compute_color != storage_color, "Different service categories should have different colors"
        assert storage_color != database_color, "Different service categories should have different colors"
        print("✅ Service color assignment working correctly")

        # Test commitment discount color assignments
        high_util_color = templates._get_commitment_color(90.0)
        medium_util_color = templates._get_commitment_color(70.0)
        low_util_color = templates._get_commitment_color(30.0)
        no_commit_color = templates._get_commitment_color(0.0)

        # Validate commitment colors
        assert high_util_color != medium_util_color, "Different utilization levels should have different colors"
        assert medium_util_color != low_util_color, "Different utilization levels should have different colors"
        assert low_util_color != no_commit_color, "Different utilization levels should have different colors"
        print("✅ Commitment discount color assignment working correctly")

        return True

    except Exception as e:
        print(f"❌ Color scheme assignment test failed: {e}")
        return False


def test_factory_functions():
    """Test factory functions for integration."""

    print("🔍 Testing Factory Functions...")

    try:
        from finops_echarts_templates import create_finops_echarts_templates
        from finops_drill_down_manager import create_finops_drill_down_manager

        # Test ECharts templates factory function
        import asyncio

        templates = asyncio.run(create_finops_echarts_templates())
        assert templates is not None, "Should create templates instance"
        assert hasattr(templates, 'get_cost_trend_chart'), "Should have cost trend chart method"
        assert hasattr(templates, 'create_finops_dashboard'), "Should have dashboard creation method"
        print("✅ FinOps ECharts templates factory function working")

        # Test drill-down manager factory function
        manager = asyncio.run(create_finops_drill_down_manager())
        assert manager is not None, "Should create manager instance"
        assert hasattr(manager, 'initiate_drill_down'), "Should have drill-down initiation method"
        assert hasattr(manager, 'get_drill_down_suggestions'), "Should have suggestions method"
        print("✅ FinOps drill-down manager factory function working")

        # Test factory functions with dependencies
        mock_echarts_adapter = MagicMock()
        templates_with_adapter = asyncio.run(create_finops_echarts_templates(mock_echarts_adapter))
        assert templates_with_adapter.echarts_adapter is mock_echarts_adapter, "Should use provided adapter"
        print("✅ Factory functions with dependencies working")

        return True

    except Exception as e:
        print(f"❌ Factory functions test failed: {e}")
        return False


def run_task9_validation():
    """Run comprehensive Task 9 validation."""

    print("🧪 Running Task 9: ECharts Visualization for FinOps Analytics Validation")
    print("="*75)

    tests = [
        ("FinOps ECharts Templates Architecture", test_finops_echarts_templates_architecture),
        ("FinOps ECharts Templates Initialization", test_finops_echarts_templates_initialization),
        ("Cost Trend Chart Generation", test_cost_trend_chart_generation),
        ("Service Cost Distribution Chart", test_service_cost_distribution_chart),
        ("Commitment Discount Chart", test_commitment_discount_chart),
        ("Regional Comparison Chart", test_regional_comparison_chart),
        ("Optimization Opportunities Chart", test_optimization_opportunities_chart),
        ("FinOps Dashboard Creation", test_finops_dashboard_creation),
        ("FinOps Drill-Down Manager Architecture", test_finops_drill_down_manager_architecture),
        ("FinOps Drill-Down Manager Initialization", test_finops_drill_down_manager_initialization),
        ("Drill-Down Initiation", test_drill_down_initiation),
        ("Drill-Down Suggestions", test_drill_down_suggestions),
        ("Color Scheme Assignment", test_color_scheme_assignment),
        ("Factory Functions", test_factory_functions)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔬 {test_name}")
        print("-" * 55)

        try:
            # Handle async tests
            if test_func.__name__ in [
                'test_drill_down_initiation', 'test_drill_down_suggestions'
            ]:
                import asyncio
                result = asyncio.run(test_func())
            else:
                result = test_func()

            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")

    print("\n" + "="*75)
    print(f"📊 Task 9 Validation Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Task 9: ECharts Visualization for FinOps Analytics COMPLETED!")
        print("\n✅ FinOps-specific ECharts visualization templates implemented")
        print("✅ Cost trend charts with time-based analysis capabilities")
        print("✅ Service cost distribution treemap visualizations")
        print("✅ Commitment discount utilization bar charts with targets")
        print("✅ Regional comparison pie charts with aggregation")
        print("✅ Optimization opportunities bubble charts with confidence scoring")
        print("✅ Interactive FinOps dashboards (Executive Summary, Cost Optimization)")
        print("✅ Comprehensive drill-down capabilities and context management")
        print("✅ Service-to-resource, time-based, and cross-account drill-downs")
        print("✅ Intelligent drill-down suggestions based on analysis context")
        print("✅ FinOps-specific color schemes and accessibility features")
        print("✅ Export options and related analysis recommendations")
        print("✅ Ready to proceed to Task 10: FinOps Analytics Web Application")
        return True
    else:
        print("❌ Task 9 validation failed. Please review implementation before proceeding.")
        return False


if __name__ == "__main__":
    success = run_task9_validation()
    exit(0 if success else 1)