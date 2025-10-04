"""
Test suite for Task 2: ECharts Integration Layer.

This test validates the ECharts MCP adapter that replaces LIDA's code generation
with interactive ECharts configurations.
"""

import json
import sys
from unittest.mock import MagicMock, AsyncMock, patch


def test_echarts_adapter_architecture():
    """Test the ECharts LIDA adapter architecture and chart type mapping."""

    print("🔍 Testing ECharts LIDA Adapter Architecture...")

    try:
        # Test import structure
        from echarts_lida_adapter import EChartsLidaAdapter, create_echarts_lida_adapter
        print("✅ ECharts LIDA Adapter imports successful")

        # Test adapter initialization
        adapter = EChartsLidaAdapter()
        assert adapter.mock_mode is True, "Should be in mock mode without MCP client"
        print("✅ ECharts adapter initialization successful")

        # Test chart type mapping
        chart_types = adapter.get_supported_chart_types()
        assert isinstance(chart_types, list), "Chart types should be a list"
        assert len(chart_types) > 0, "Should support multiple chart types"
        assert 'bar' in chart_types, "Should support bar charts"
        assert 'line' in chart_types, "Should support line charts"
        assert 'pie' in chart_types, "Should support pie charts"
        print("✅ Chart type mapping functional")

        # Test narrative goal to chart mapping
        assert hasattr(adapter, 'narrative_to_chart_mapping'), "Missing narrative mapping"
        narrative_mapping = adapter.narrative_to_chart_mapping
        assert 'magnitude_comparison' in narrative_mapping, "Missing magnitude comparison"
        assert 'change_over_time' in narrative_mapping, "Missing time series mapping"
        assert 'correlation' in narrative_mapping, "Missing correlation mapping"
        print("✅ Narrative goal to chart mapping present")

        # Test persona constraints
        executive_constraints = adapter.get_persona_constraints('executive')
        analyst_constraints = adapter.get_persona_constraints('analyst')

        assert 'allowed' in executive_constraints, "Missing allowed charts for executive"
        assert 'forbidden' in executive_constraints, "Missing forbidden charts for executive"
        assert len(executive_constraints['allowed']) < len(analyst_constraints['allowed']), \
            "Executive should have fewer allowed chart types than analyst"
        print("✅ Persona constraint system functional")

        return True

    except Exception as e:
        print(f"❌ ECharts adapter architecture test failed: {e}")
        return False


def test_chart_type_selection():
    """Test optimal chart type selection based on goals and personas."""

    print("🔍 Testing Chart Type Selection Logic...")

    try:
        from echarts_lida_adapter import EChartsLidaAdapter

        adapter = EChartsLidaAdapter()

        # Test executive persona constraints
        executive_goal = {
            'chart_type': 'heatmap',  # Complex chart type
            'narrative_goal': 'magnitude_comparison',
            'question': 'What are the revenue trends?'
        }

        selected_type = adapter.map_goal_to_chart_type(executive_goal, 'executive')
        assert selected_type in ['bar'], "Executive should get simplified chart type"
        print("✅ Executive persona chart simplification working")

        # Test analyst persona flexibility
        analyst_goal = {
            'chart_type': 'scatter',
            'narrative_goal': 'correlation',
            'question': 'How do metrics correlate?'
        }

        selected_type = adapter.map_goal_to_chart_type(analyst_goal, 'analyst')
        assert selected_type == 'scatter', "Analyst should get requested complex chart type"
        print("✅ Analyst persona chart flexibility working")

        # Test narrative goal override
        time_goal = {
            'chart_type': 'bar',  # Different from narrative goal
            'narrative_goal': 'change_over_time',
            'question': 'How have sales changed over time?'
        }

        selected_type = adapter.map_goal_to_chart_type(time_goal, 'analyst')
        assert selected_type in ['line'], "Should select line chart for time series"
        print("✅ Narrative goal-based chart selection working")

        return True

    except Exception as e:
        print(f"❌ Chart type selection test failed: {e}")
        return False


def test_visualization_generation():
    """Test visualization generation with ECharts configurations."""

    print("🔍 Testing Visualization Generation...")

    try:
        from echarts_lida_adapter import EChartsLidaAdapter

        adapter = EChartsLidaAdapter()

        # Test data with sample goal and summary
        sample_goal = {
            'question': 'What are the sales by region?',
            'chart_type': 'bar',
            'dimensions': ['region'],
            'metrics': ['sales'],
            'narrative_goal': 'magnitude_comparison',
            'visualization': 'Sales by region analysis'
        }

        sample_summary = {
            'summary': 'Sales data by region',
            'columns': ['region', 'sales'],
            'data_types': {'region': 'categorical', 'sales': 'numeric'},
            'sample_data': [
                {'region': 'North', 'sales': 10000},
                {'region': 'South', 'sales': 8000},
                {'region': 'East', 'sales': 12000}
            ]
        }

        # Since we can't use async in this context, we'll test the internal methods
        chart_data = adapter._prepare_chart_data(sample_summary, ['region'], ['sales'])
        assert isinstance(chart_data, list), "Chart data should be a list"
        assert len(chart_data) > 0, "Should have chart data points"
        print("✅ Chart data preparation working")

        # Test mock ECharts config generation
        echarts_config = adapter._generate_mock_echarts_config(
            'bar', 'Sales by Region', chart_data, ['region'], ['sales']
        )

        assert isinstance(echarts_config, dict), "ECharts config should be a dictionary"
        assert 'title' in echarts_config, "Should have title"
        assert 'series' in echarts_config, "Should have series"
        assert echarts_config['title']['text'] == 'Sales by Region', "Title should match"
        print("✅ ECharts configuration generation working")

        return True

    except Exception as e:
        print(f"❌ Visualization generation test failed: {e}")
        return False


def test_interactive_features():
    """Test interactive features enhancement."""

    print("🔍 Testing Interactive Features...")

    try:
        from echarts_lida_adapter import EChartsLidaAdapter

        adapter = EChartsLidaAdapter()

        # Test base config
        base_config = {
            "title": {"text": "Test Chart"},
            "series": [{"type": "bar", "data": [1, 2, 3]}]
        }

        sample_goal = {
            'question': 'Test question',
            'visualization': 'Test visualization'
        }

        # Test interactive features for different personas
        executive_config = adapter._add_interactive_features(base_config, sample_goal, 'executive')
        analyst_config = adapter._add_interactive_features(base_config, sample_goal, 'analyst')

        # Executive should have basic features
        assert 'toolbox' in executive_config, "Executive should have toolbox"
        assert 'saveAsImage' in executive_config['toolbox']['feature'], "Should have export"

        # Analyst should have advanced features
        assert 'toolbox' in analyst_config, "Analyst should have toolbox"
        assert 'brush' in analyst_config, "Analyst should have brush selection"
        assert 'dataZoom' in analyst_config, "Analyst should have data zoom"

        print("✅ Interactive features enhancement working")

        # Test accessibility features
        accessible_config = adapter._add_accessibility_features(base_config, sample_goal, 'analyst')
        assert 'aria' in accessible_config, "Should have aria accessibility"
        assert accessible_config['aria']['enabled'] is True, "Aria should be enabled"
        print("✅ Accessibility features working")

        # Test feature lists
        features = adapter._get_interactive_features_list('bar')
        accessibility_features = adapter._get_accessibility_features_list()

        assert isinstance(features, list), "Interactive features should be a list"
        assert isinstance(accessibility_features, list), "Accessibility features should be a list"
        assert 'hover_tooltips' in features, "Should include hover tooltips"
        assert 'aria_labels' in accessibility_features, "Should include aria labels"
        print("✅ Feature listing working")

        return True

    except Exception as e:
        print(f"❌ Interactive features test failed: {e}")
        return False


def test_lida_manager_integration():
    """Test integration with LIDA Enhanced Manager."""

    print("🔍 Testing LIDA Manager Integration...")

    try:
        # Mock dependencies
        sys.modules['openai'] = MagicMock()
        sys.modules['openai'].AsyncAzureOpenAI = MagicMock

        class MockBaseModel:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
            def dict(self):
                return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

        pydantic_mock = MagicMock()
        pydantic_mock.BaseModel = MockBaseModel
        sys.modules['pydantic'] = pydantic_mock

        # Test LIDA manager with ECharts integration
        from lida_enhanced_manager import LidaEnhancedManager, EnhancedGoal, EnhancedDataSummary

        mock_azure_client = MagicMock()
        sample_context = {"name": "test", "metrics": [], "dimensions": []}

        manager = LidaEnhancedManager(
            azure_client=mock_azure_client,
            deployment_name="test",
            dashboard_context=sample_context,
            echarts_mcp_client=None  # This should trigger mock mode
        )

        # Test that ECharts adapter is initialized
        assert hasattr(manager, 'echarts_adapter'), "Should have ECharts adapter"
        print("✅ LIDA manager ECharts integration present")

        # Test fallback visualization creation
        goal = EnhancedGoal(
            question="Test question",
            visualization="Test viz",
            rationale="Test rationale",
            chart_type="bar",
            dimensions=["col1"],
            metrics=["metric1"],
            persona="analyst",
            narrative_goal="magnitude_comparison"
        )

        summary = EnhancedDataSummary(
            summary="Test summary",
            dataset_name="test",
            columns=["col1"],
            data_types={"col1": "numeric"},
            insights=["Test insight"],
            ag_ui_context=sample_context
        )

        fallback_viz = manager._create_fallback_visualization(goal, summary)
        assert isinstance(fallback_viz, dict), "Fallback should be a dictionary"
        assert 'echarts_config' in fallback_viz, "Should have ECharts config"
        print("✅ Fallback visualization creation working")

        return True

    except Exception as e:
        print(f"❌ LIDA manager integration test failed: {e}")
        return False


def test_cleveland_mcgill_compliance():
    """Test Cleveland-McGill perceptual hierarchy compliance."""

    print("🔍 Testing Cleveland-McGill Perceptual Hierarchy...")

    try:
        from echarts_lida_adapter import EChartsLidaAdapter

        adapter = EChartsLidaAdapter()

        # Test that magnitude comparison uses position/length encoding (bar charts)
        magnitude_goal = {
            'chart_type': 'pie',  # Less accurate encoding
            'narrative_goal': 'magnitude_comparison',
            'question': 'Compare values'
        }

        selected_type = adapter.map_goal_to_chart_type(magnitude_goal, 'analyst')
        assert selected_type in ['bar'], "Should prefer bar charts for magnitude comparison"
        print("✅ Magnitude comparison uses optimal encoding")

        # Test that time series uses position encoding (line charts)
        time_goal = {
            'chart_type': 'pie',
            'narrative_goal': 'change_over_time',
            'question': 'Show trends over time'
        }

        selected_type = adapter.map_goal_to_chart_type(time_goal, 'analyst')
        assert selected_type in ['line'], "Should prefer line charts for time series"
        print("✅ Time series uses optimal encoding")

        # Test correlation uses position encoding (scatter plots)
        correlation_goal = {
            'chart_type': 'bar',
            'narrative_goal': 'correlation',
            'question': 'Show correlation between variables'
        }

        selected_type = adapter.map_goal_to_chart_type(correlation_goal, 'analyst')
        assert selected_type in ['scatter'], "Should prefer scatter plots for correlation"
        print("✅ Correlation uses optimal encoding")

        return True

    except Exception as e:
        print(f"❌ Cleveland-McGill compliance test failed: {e}")
        return False


def run_task2_validation():
    """Run comprehensive Task 2 validation."""

    print("🧪 Running Task 2: ECharts Integration Layer Validation")
    print("="*60)

    tests = [
        ("ECharts Adapter Architecture", test_echarts_adapter_architecture),
        ("Chart Type Selection", test_chart_type_selection),
        ("Visualization Generation", test_visualization_generation),
        ("Interactive Features", test_interactive_features),
        ("LIDA Manager Integration", test_lida_manager_integration),
        ("Cleveland-McGill Compliance", test_cleveland_mcgill_compliance)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔬 {test_name}")
        print("-" * 40)

        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")

    print("\n" + "="*60)
    print(f"📊 Task 2 Validation Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Task 2: ECharts Integration Layer COMPLETED!")
        print("\n✅ ECharts MCP adapter successfully created")
        print("✅ LIDA visualization intents mapped to ECharts types")
        print("✅ Chart configuration translator implemented")
        print("✅ Interactive features added beyond LIDA static output")
        print("✅ Cleveland-McGill perceptual hierarchy enforced")
        print("✅ Persona-aware complexity filtering implemented")
        print("✅ WCAG 2.1 accessibility features included")
        print("✅ Ready to proceed to Task 3: Semantic Layer Integration")
        return True
    else:
        print("❌ Task 2 validation failed. Please review implementation before proceeding.")
        return False


if __name__ == "__main__":
    success = run_task2_validation()
    exit(0 if success else 1)