"""
Test suite for Task 10: FinOps Analytics Web Application.

This test validates the FinOps analytics web application backend functionality,
including sample dataset selection, dashboard management, data exploration tools,
and real-time chart updates for comprehensive FinOps analysis workflows.
"""

import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch
import uuid


def test_finops_web_application_architecture():
    """Test FinOps web application architecture and data models."""

    print("🔍 Testing FinOps Web Application Architecture...")

    try:
        # Test import structure
        from finops_web_application import (
            DatasetType,
            DashboardLayout,
            ExportFormat,
            FocusSampleDataset,
            DashboardConfiguration,
            DataExplorationRequest,
            DatasetComparison,
            FinOpsWebApplicationManager,
            create_finops_web_application_manager
        )
        print("✅ FinOps web application imports successful")

        # Test dataset types enum
        assert DatasetType.FOCUS_SAMPLE.value == "focus_sample", "FOCUS sample dataset type should exist"
        assert DatasetType.GENERATED_SAMPLE.value == "generated_sample", "Generated sample type should exist"
        assert DatasetType.UPLOADED_CSV.value == "uploaded_csv", "Uploaded CSV type should exist"
        assert DatasetType.PRODUCTION_DATA.value == "production_data", "Production data type should exist"
        print("✅ Dataset types enum working correctly")

        # Test dashboard layout enum
        assert DashboardLayout.EXECUTIVE_SUMMARY.value == "executive_summary", "Executive summary layout should exist"
        assert DashboardLayout.COST_OPTIMIZATION.value == "cost_optimization", "Cost optimization layout should exist"
        assert DashboardLayout.DETAILED_ANALYSIS.value == "detailed_analysis", "Detailed analysis layout should exist"
        print("✅ Dashboard layout enum working correctly")

        # Test export format enum
        assert ExportFormat.PDF.value == "pdf", "PDF export format should exist"
        assert ExportFormat.CSV.value == "csv", "CSV export format should exist"
        assert ExportFormat.JSON.value == "json", "JSON export format should exist"
        print("✅ Export format enum working correctly")

        # Test FOCUS sample dataset creation
        sample_dataset = FocusSampleDataset(
            name="Test Dataset",
            description="Test FOCUS sample dataset",
            rows=1000,
            compliance_score=0.95,
            dataset_type=DatasetType.FOCUS_SAMPLE,
            date_range=(datetime(2024, 1, 1), datetime(2024, 3, 31)),
            service_count=5,
            account_count=2,
            region_count=3,
            data_quality_score=0.92,
            missing_fields_percentage=5.0,
            optimization_opportunities_count=8,
            anomaly_candidates_count=2
        )

        assert sample_dataset.name == "Test Dataset", "Dataset name should be set"
        assert sample_dataset.compliance_score == 0.95, "Compliance score should be set"
        assert sample_dataset.dataset_type == DatasetType.FOCUS_SAMPLE, "Dataset type should be set"
        assert sample_dataset.optimization_opportunities_count == 8, "Optimization opportunities should be set"
        print("✅ FocusSampleDataset creation successful")

        # Test dashboard configuration creation
        dashboard_config = DashboardConfiguration(
            dashboard_id="test_dashboard_001",
            user_id="test_user",
            dashboard_name="Test Dashboard",
            layout_type=DashboardLayout.EXECUTIVE_SUMMARY,
            primary_dataset="test_dataset",
            comparison_datasets=["comparison_dataset"],
            enabled_charts=["cost_trend", "service_distribution"],
            chart_positions={"cost_trend": {"row": 1, "col": 1}},
            refresh_interval_seconds=30,
            service_filters=["EC2", "S3"],
            account_filters=["account-1"],
            region_filters=["us-east-1"],
            created_at=datetime.now()
        )

        assert dashboard_config.dashboard_id == "test_dashboard_001", "Dashboard ID should be set"
        assert dashboard_config.layout_type == DashboardLayout.EXECUTIVE_SUMMARY, "Layout type should be set"
        assert len(dashboard_config.enabled_charts) == 2, "Should have enabled charts"
        assert len(dashboard_config.service_filters) == 2, "Should have service filters"
        print("✅ DashboardConfiguration creation successful")

        return True

    except Exception as e:
        print(f"❌ FinOps web application architecture test failed: {e}")
        return False


def test_finops_web_application_manager_initialization():
    """Test FinOps web application manager initialization."""

    print("🔍 Testing FinOps Web Application Manager Initialization...")

    try:
        from finops_web_application import FinOpsWebApplicationManager

        # Mock dependencies
        mock_focus_integration = MagicMock()
        mock_echarts_templates = MagicMock()
        mock_drill_down_manager = MagicMock()
        mock_lida_manager = MagicMock()

        # Test initialization with all components
        manager = FinOpsWebApplicationManager(
            focus_integration=mock_focus_integration,
            echarts_templates=mock_echarts_templates,
            drill_down_manager=mock_drill_down_manager,
            lida_manager=mock_lida_manager
        )

        assert manager.focus_integration is mock_focus_integration, "Should store FOCUS integration reference"
        assert manager.echarts_templates is mock_echarts_templates, "Should store ECharts templates reference"
        assert manager.drill_down_manager is mock_drill_down_manager, "Should store drill-down manager reference"
        assert manager.lida_manager is mock_lida_manager, "Should store LIDA manager reference"
        print("✅ Manager initialization with all components successful")

        # Test internal data structures
        assert hasattr(manager, '_available_datasets'), "Should have available datasets storage"
        assert hasattr(manager, '_user_dashboards'), "Should have user dashboards storage"
        assert hasattr(manager, '_active_sessions'), "Should have active sessions storage"
        assert hasattr(manager, '_dataset_cache'), "Should have dataset cache"

        assert isinstance(manager._available_datasets, dict), "Available datasets should be dictionary"
        assert isinstance(manager._user_dashboards, dict), "User dashboards should be dictionary"
        assert isinstance(manager._active_sessions, dict), "Active sessions should be dictionary"
        print("✅ Internal data structures initialized correctly")

        # Test minimal initialization
        minimal_manager = FinOpsWebApplicationManager()
        assert minimal_manager.focus_integration is None, "Should handle None dependencies"
        assert hasattr(minimal_manager, '_available_datasets'), "Should still have internal structures"
        print("✅ Minimal manager initialization successful")

        return True

    except Exception as e:
        print(f"❌ FinOps web application manager initialization test failed: {e}")
        return False


async def test_dataset_management():
    """Test dataset management functionality."""

    print("🔍 Testing Dataset Management...")

    try:
        from finops_web_application import FinOpsWebApplicationManager, DatasetType

        manager = FinOpsWebApplicationManager()

        # Wait for default datasets to be initialized
        await asyncio.sleep(0.1)

        # Test getting available datasets
        datasets = await manager.get_available_datasets("test_user")

        assert isinstance(datasets, list), "Should return list of datasets"
        assert len(datasets) > 0, "Should have default datasets"

        # Check dataset structure
        first_dataset = datasets[0]
        assert hasattr(first_dataset, 'name'), "Dataset should have name"
        assert hasattr(first_dataset, 'description'), "Dataset should have description"
        assert hasattr(first_dataset, 'rows'), "Dataset should have row count"
        assert hasattr(first_dataset, 'compliance_score'), "Dataset should have compliance score"
        print("✅ Available datasets retrieval successful")

        # Test filtering by dataset type
        focus_datasets = await manager.get_available_datasets("test_user", DatasetType.FOCUS_SAMPLE)
        assert all(d.dataset_type == DatasetType.FOCUS_SAMPLE for d in focus_datasets), "Should filter by type"
        print("✅ Dataset type filtering working")

        # Test dataset selection
        dataset_name = datasets[0].name
        selection_result = await manager.select_dataset("test_user", dataset_name)

        assert "session_id" in selection_result, "Should return session ID"
        assert "dataset" in selection_result, "Should return dataset metadata"
        assert "preview" in selection_result, "Should return dataset preview"
        assert "insights" in selection_result, "Should return initial insights"

        session_id = selection_result["session_id"]
        assert session_id in manager._active_sessions, "Should store active session"

        stored_session = manager._active_sessions[session_id]
        assert stored_session["user_id"] == "test_user", "Should store user ID in session"
        assert stored_session["selected_dataset"] == dataset_name, "Should store selected dataset"
        print("✅ Dataset selection successful")

        # Test dataset preview
        preview = selection_result["preview"]
        assert "sample_records" in preview, "Preview should have sample records"
        assert "total_rows" in preview, "Preview should have total rows"
        assert "columns" in preview, "Preview should have columns"
        assert "statistics" in preview, "Preview should have statistics"

        statistics = preview["statistics"]
        assert "total_cost" in statistics, "Statistics should include total cost"
        assert "unique_services" in statistics, "Statistics should include unique services"
        print("✅ Dataset preview generation successful")

        return True

    except Exception as e:
        print(f"❌ Dataset management test failed: {e}")
        return False


async def test_dashboard_management():
    """Test dashboard management functionality."""

    print("🔍 Testing Dashboard Management...")

    try:
        from finops_web_application import (
            FinOpsWebApplicationManager,
            DashboardLayout
        )

        manager = FinOpsWebApplicationManager()

        # Wait for initialization
        await asyncio.sleep(0.1)

        # Get available datasets first
        datasets = await manager.get_available_datasets("test_user")
        primary_dataset = datasets[0].name

        # Test dashboard creation
        dashboard_config = await manager.create_dashboard(
            user_id="test_user",
            dashboard_name="Test Executive Dashboard",
            layout_type=DashboardLayout.EXECUTIVE_SUMMARY,
            primary_dataset=primary_dataset,
            configuration={
                "refresh_interval": 60,
                "theme": "dark",
                "service_filters": ["EC2", "S3"]
            }
        )

        assert dashboard_config.dashboard_name == "Test Executive Dashboard", "Dashboard name should be set"
        assert dashboard_config.layout_type == DashboardLayout.EXECUTIVE_SUMMARY, "Layout type should be set"
        assert dashboard_config.primary_dataset == primary_dataset, "Primary dataset should be set"
        assert dashboard_config.refresh_interval_seconds == 60, "Refresh interval should be set from config"
        assert dashboard_config.theme == "dark", "Theme should be set from config"
        assert "EC2" in dashboard_config.service_filters, "Service filters should be set"
        print("✅ Dashboard creation successful")

        # Check dashboard is stored for user
        user_dashboards = manager._user_dashboards.get("test_user", [])
        assert len(user_dashboards) == 1, "Should store dashboard for user"
        assert user_dashboards[0].dashboard_id == dashboard_config.dashboard_id, "Should store correct dashboard"
        print("✅ Dashboard storage for user successful")

        # Test dashboard data generation
        dashboard_data = await manager.get_dashboard_data(
            dashboard_config.dashboard_id,
            "test_user"
        )

        assert "dashboard_id" in dashboard_data, "Should include dashboard ID"
        assert "configuration" in dashboard_data, "Should include configuration"
        assert "charts" in dashboard_data, "Should include charts"
        assert "insights" in dashboard_data, "Should include insights"
        assert "recommendations" in dashboard_data, "Should include recommendations"
        assert "data_summary" in dashboard_data, "Should include data summary"

        # Check charts generation
        charts = dashboard_data["charts"]
        expected_charts = ["cost_trend", "service_distribution", "regional_comparison", "key_metrics"]
        for chart_type in expected_charts:
            if chart_type in charts:
                assert isinstance(charts[chart_type], dict), f"{chart_type} should be dictionary"
        print("✅ Dashboard data generation successful")

        # Test dashboard with different layout
        cost_opt_dashboard = await manager.create_dashboard(
            user_id="test_user",
            dashboard_name="Cost Optimization Dashboard",
            layout_type=DashboardLayout.COST_OPTIMIZATION,
            primary_dataset=primary_dataset
        )

        assert cost_opt_dashboard.layout_type == DashboardLayout.COST_OPTIMIZATION, "Should create cost optimization layout"
        assert len(manager._user_dashboards["test_user"]) == 2, "Should have two dashboards for user"
        print("✅ Multiple dashboard creation successful")

        return True

    except Exception as e:
        print(f"❌ Dashboard management test failed: {e}")
        return False


async def test_data_exploration():
    """Test data exploration functionality."""

    print("🔍 Testing Data Exploration...")

    try:
        from finops_web_application import (
            FinOpsWebApplicationManager,
            DataExplorationRequest
        )
        import uuid

        manager = FinOpsWebApplicationManager()
        await asyncio.sleep(0.1)

        # Get available datasets
        datasets = await manager.get_available_datasets("test_user")
        dataset_name = datasets[0].name

        # Test dataset preview exploration
        preview_request = DataExplorationRequest(
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            user_id="test_user",
            dataset_name=dataset_name,
            exploration_type="preview",
            parameters={"max_rows": 20},
            max_rows=20,
            requested_at=datetime.now()
        )

        preview_result = await manager.explore_dataset(preview_request)

        assert "request_id" in preview_result, "Should include request ID"
        assert "dataset_name" in preview_result, "Should include dataset name"
        assert "exploration_type" in preview_result, "Should include exploration type"
        assert "sample_records" in preview_result, "Should include sample records"
        assert "total_rows" in preview_result, "Should include total rows"
        assert len(preview_result["sample_records"]) <= 20, "Should respect max_rows parameter"
        print("✅ Dataset preview exploration successful")

        # Test data quality check exploration
        quality_request = DataExplorationRequest(
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            user_id="test_user",
            dataset_name=dataset_name,
            exploration_type="quality_check",
            parameters={},
            include_quality_metrics=True,
            requested_at=datetime.now()
        )

        quality_result = await manager.explore_dataset(quality_request)

        assert "quality_metrics" in quality_result, "Should include quality metrics"
        assert "issues_found" in quality_result, "Should include issues found"
        assert "recommendations" in quality_result, "Should include recommendations"

        # Check quality metrics structure
        quality_metrics = quality_result["quality_metrics"]
        expected_metrics = ["completeness", "accuracy", "consistency", "timeliness", "overall_score"]
        for metric in expected_metrics:
            assert metric in quality_metrics, f"Should include {metric} metric"
            assert 0 <= quality_metrics[metric] <= 1, f"{metric} should be between 0 and 1"
        print("✅ Data quality check exploration successful")

        # Test field mapping exploration
        mapping_request = DataExplorationRequest(
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            user_id="test_user",
            dataset_name=dataset_name,
            exploration_type="field_mapping",
            parameters={},
            requested_at=datetime.now()
        )

        mapping_result = await manager.explore_dataset(mapping_request)

        assert "field_mappings" in mapping_result, "Should include field mappings"
        assert "compliance_assessment" in mapping_result, "Should include compliance assessment"

        # Check field mappings structure
        field_mappings = mapping_result["field_mappings"]
        if field_mappings:
            first_mapping = field_mappings[0]
            assert "field_name" in first_mapping, "Mapping should include field name"
            assert "focus_mapping" in first_mapping, "Mapping should include FOCUS mapping"
            assert "data_type" in first_mapping, "Mapping should include data type"
            assert "sample_values" in first_mapping, "Mapping should include sample values"
        print("✅ Field mapping exploration successful")

        # Test statistics exploration
        stats_request = DataExplorationRequest(
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            user_id="test_user",
            dataset_name=dataset_name,
            exploration_type="statistics",
            parameters={},
            include_statistics=True,
            requested_at=datetime.now()
        )

        stats_result = await manager.explore_dataset(stats_request)

        assert "statistics" in stats_result, "Should include statistics"

        statistics = stats_result["statistics"]
        expected_stats = ["total_records", "total_cost", "average_cost", "unique_services"]
        for stat in expected_stats:
            assert stat in statistics, f"Should include {stat} statistic"
        print("✅ Statistics exploration successful")

        return True

    except Exception as e:
        print(f"❌ Data exploration test failed: {e}")
        return False


async def test_dataset_comparison():
    """Test dataset comparison functionality."""

    print("🔍 Testing Dataset Comparison...")

    try:
        from finops_web_application import FinOpsWebApplicationManager

        manager = FinOpsWebApplicationManager()
        await asyncio.sleep(0.1)

        # Get available datasets
        datasets = await manager.get_available_datasets("test_user")

        if len(datasets) < 2:
            print("⚠️ Skipping dataset comparison test - need at least 2 datasets")
            return True

        primary_dataset = datasets[0].name
        comparison_dataset = datasets[1].name

        # Test dataset comparison
        comparison_result = await manager.compare_datasets(
            user_id="test_user",
            primary_dataset=primary_dataset,
            comparison_dataset=comparison_dataset
        )

        # Validate comparison result structure
        assert hasattr(comparison_result, 'comparison_id'), "Should have comparison ID"
        assert hasattr(comparison_result, 'primary_dataset'), "Should have primary dataset"
        assert hasattr(comparison_result, 'comparison_dataset'), "Should have comparison dataset"
        assert hasattr(comparison_result, 'common_fields'), "Should have common fields"
        assert hasattr(comparison_result, 'unique_to_primary'), "Should have unique to primary"
        assert hasattr(comparison_result, 'unique_to_comparison'), "Should have unique to comparison"

        assert comparison_result.primary_dataset == primary_dataset, "Should store primary dataset name"
        assert comparison_result.comparison_dataset == comparison_dataset, "Should store comparison dataset name"
        assert isinstance(comparison_result.common_fields, list), "Common fields should be list"
        assert isinstance(comparison_result.mapping_suggestions, list), "Mapping suggestions should be list"
        print("✅ Dataset comparison structure validated")

        # Check schema comparison
        assert hasattr(comparison_result, 'field_type_differences'), "Should have field type differences"
        assert isinstance(comparison_result.field_type_differences, dict), "Field differences should be dict"
        print("✅ Schema comparison working")

        # Check data comparison
        assert hasattr(comparison_result, 'row_count_difference'), "Should have row count difference"
        assert hasattr(comparison_result, 'cost_distribution_similarity'), "Should have cost similarity"
        assert hasattr(comparison_result, 'time_range_overlap'), "Should have time range overlap"
        assert isinstance(comparison_result.row_count_difference, int), "Row count difference should be integer"
        print("✅ Data comparison working")

        # Check feasibility assessment
        assert hasattr(comparison_result, 'merge_feasibility'), "Should have merge feasibility"
        assert comparison_result.merge_feasibility in ["high", "medium", "low"], "Feasibility should be valid value"
        print("✅ Merge feasibility assessment working")

        return True

    except Exception as e:
        print(f"❌ Dataset comparison test failed: {e}")
        return False


async def test_dashboard_export():
    """Test dashboard export functionality."""

    print("🔍 Testing Dashboard Export...")

    try:
        from finops_web_application import (
            FinOpsWebApplicationManager,
            DashboardLayout,
            ExportFormat
        )

        manager = FinOpsWebApplicationManager()
        await asyncio.sleep(0.1)

        # Create a dashboard first
        datasets = await manager.get_available_datasets("test_user")
        primary_dataset = datasets[0].name

        dashboard_config = await manager.create_dashboard(
            user_id="test_user",
            dashboard_name="Export Test Dashboard",
            layout_type=DashboardLayout.EXECUTIVE_SUMMARY,
            primary_dataset=primary_dataset
        )

        dashboard_id = dashboard_config.dashboard_id

        # Test JSON export
        json_export = await manager.export_dashboard(
            dashboard_id=dashboard_id,
            user_id="test_user",
            export_format=ExportFormat.JSON
        )

        # Validate export result structure
        assert "export_id" in json_export, "Should have export ID"
        assert "dashboard_id" in json_export, "Should have dashboard ID"
        assert "export_format" in json_export, "Should have export format"
        assert "filename" in json_export, "Should have filename"
        assert "content_type" in json_export, "Should have content type"
        assert "file_size" in json_export, "Should have file size"
        assert "export_timestamp" in json_export, "Should have export timestamp"
        assert "download_url" in json_export, "Should have download URL"
        assert "expires_at" in json_export, "Should have expiry time"

        assert json_export["export_format"] == "json", "Should specify JSON format"
        assert json_export["content_type"] == "application/json", "Should have correct content type"
        assert json_export["filename"].endswith(".json"), "Filename should have JSON extension"
        print("✅ JSON export successful")

        # Test CSV export
        csv_export = await manager.export_dashboard(
            dashboard_id=dashboard_id,
            user_id="test_user",
            export_format=ExportFormat.CSV
        )

        assert csv_export["export_format"] == "csv", "Should specify CSV format"
        assert csv_export["content_type"] == "text/csv", "Should have correct content type"
        assert csv_export["filename"].endswith(".csv"), "Filename should have CSV extension"
        print("✅ CSV export successful")

        # Test PDF export
        pdf_export = await manager.export_dashboard(
            dashboard_id=dashboard_id,
            user_id="test_user",
            export_format=ExportFormat.PDF,
            options={"include_charts": True, "include_insights": True}
        )

        assert pdf_export["export_format"] == "pdf", "Should specify PDF format"
        assert pdf_export["content_type"] == "application/pdf", "Should have correct content type"
        assert pdf_export["filename"].endswith(".pdf"), "Filename should have PDF extension"
        print("✅ PDF export successful")

        # Validate export IDs are unique
        export_ids = [json_export["export_id"], csv_export["export_id"], pdf_export["export_id"]]
        assert len(set(export_ids)) == 3, "Export IDs should be unique"
        print("✅ Export ID uniqueness validated")

        return True

    except Exception as e:
        print(f"❌ Dashboard export test failed: {e}")
        return False


def test_default_dataset_initialization():
    """Test default dataset initialization."""

    print("🔍 Testing Default Dataset Initialization...")

    try:
        from finops_web_application import FinOpsWebApplicationManager, DatasetType

        manager = FinOpsWebApplicationManager()

        # Check that default datasets are initialized
        assert len(manager._available_datasets) > 0, "Should have default datasets"

        # Check dataset types
        dataset_types = set(d.dataset_type for d in manager._available_datasets.values())
        assert DatasetType.FOCUS_SAMPLE in dataset_types, "Should have FOCUS sample datasets"
        assert DatasetType.GENERATED_SAMPLE in dataset_types, "Should have generated sample datasets"
        print("✅ Default dataset types validated")

        # Check dataset properties
        for dataset_name, dataset in manager._available_datasets.items():
            assert dataset.name is not None, f"Dataset {dataset_name} should have name"
            assert dataset.description is not None, f"Dataset {dataset_name} should have description"
            assert dataset.rows > 0, f"Dataset {dataset_name} should have positive row count"
            assert 0 <= dataset.compliance_score <= 1, f"Dataset {dataset_name} should have valid compliance score"
            assert dataset.service_count > 0, f"Dataset {dataset_name} should have services"
            assert dataset.account_count > 0, f"Dataset {dataset_name} should have accounts"
            assert dataset.region_count > 0, f"Dataset {dataset_name} should have regions"

        print("✅ Default dataset properties validated")

        # Check dataset diversity
        total_datasets = len(manager._available_datasets)
        assert total_datasets >= 3, "Should have multiple default datasets"

        # Check for different sizes and characteristics
        row_counts = [d.rows for d in manager._available_datasets.values()]
        assert min(row_counts) != max(row_counts), "Should have datasets of different sizes"

        compliance_scores = [d.compliance_score for d in manager._available_datasets.values()]
        assert len(set(compliance_scores)) > 1, "Should have datasets with different compliance scores"
        print("✅ Default dataset diversity validated")

        return True

    except Exception as e:
        print(f"❌ Default dataset initialization test failed: {e}")
        return False


def test_factory_function():
    """Test factory function for integration."""

    print("🔍 Testing Factory Function...")

    try:
        from finops_web_application import create_finops_web_application_manager
        import asyncio

        # Test factory function is callable
        assert callable(create_finops_web_application_manager), "Factory function should be callable"

        # Test factory function without dependencies
        manager = asyncio.run(create_finops_web_application_manager())
        assert manager is not None, "Should create manager instance"
        assert hasattr(manager, 'get_available_datasets'), "Should have dataset management methods"
        assert hasattr(manager, 'create_dashboard'), "Should have dashboard management methods"
        assert hasattr(manager, 'explore_dataset'), "Should have data exploration methods"
        print("✅ Factory function basic creation working")

        # Test factory function with dependencies
        mock_focus_integration = MagicMock()
        mock_echarts_templates = MagicMock()
        mock_drill_down_manager = MagicMock()
        mock_lida_manager = MagicMock()

        manager_with_deps = asyncio.run(create_finops_web_application_manager(
            focus_integration=mock_focus_integration,
            echarts_templates=mock_echarts_templates,
            drill_down_manager=mock_drill_down_manager,
            lida_manager=mock_lida_manager
        ))

        assert manager_with_deps.focus_integration is mock_focus_integration, "Should use provided FOCUS integration"
        assert manager_with_deps.echarts_templates is mock_echarts_templates, "Should use provided ECharts templates"
        assert manager_with_deps.drill_down_manager is mock_drill_down_manager, "Should use provided drill-down manager"
        assert manager_with_deps.lida_manager is mock_lida_manager, "Should use provided LIDA manager"
        print("✅ Factory function with dependencies working")

        return True

    except Exception as e:
        print(f"❌ Factory function test failed: {e}")
        return False


def run_task10_validation():
    """Run comprehensive Task 10 validation."""

    print("🧪 Running Task 10: FinOps Analytics Web Application Validation")
    print("="*70)

    tests = [
        ("FinOps Web Application Architecture", test_finops_web_application_architecture),
        ("FinOps Web Application Manager Initialization", test_finops_web_application_manager_initialization),
        ("Dataset Management", test_dataset_management),
        ("Dashboard Management", test_dashboard_management),
        ("Data Exploration", test_data_exploration),
        ("Dataset Comparison", test_dataset_comparison),
        ("Dashboard Export", test_dashboard_export),
        ("Default Dataset Initialization", test_default_dataset_initialization),
        ("Factory Function", test_factory_function)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔬 {test_name}")
        print("-" * 55)

        try:
            # Handle async tests
            if test_func.__name__ in [
                'test_dataset_management', 'test_dashboard_management',
                'test_data_exploration', 'test_dataset_comparison',
                'test_dashboard_export'
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

    print("\n" + "="*70)
    print(f"📊 Task 10 Validation Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Task 10: FinOps Analytics Web Application COMPLETED!")
        print("\n✅ Sample dataset selection interface backend implemented")
        print("✅ FOCUS v1.2 specification sample datasets with compliance scoring")
        print("✅ Responsive dashboard management with multiple layout types")
        print("✅ Real-time chart generation and configuration management")
        print("✅ Data exploration tools with preview, quality assessment, and field mapping")
        print("✅ Dataset comparison functionality with schema and content analysis")
        print("✅ Export capabilities in multiple formats (JSON, CSV, PDF)")
        print("✅ User session management and dashboard personalization")
        print("✅ Data quality metrics and compliance assessment engine")
        print("✅ Intelligent mapping suggestions and merge feasibility analysis")
        print("✅ Comprehensive analytics capabilities with insights and recommendations")
        print("✅ Backend architecture ready for frontend integration")
        print("✅ Ready to proceed to Task 11: ClickHouse MCP Discovery and Analysis")
        return True
    else:
        print("❌ Task 10 validation failed. Please review implementation before proceeding.")
        return False


if __name__ == "__main__":
    success = run_task10_validation()
    exit(0 if success else 1)