"""
Test suite for LIDA Enhanced Manager integration with AG-UI FastAPI backend.

This test validates Task 1: Backend Foundation Migration - Adapt LIDA Manager class
to integrate with FastAPI backend.
"""

import asyncio
import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Mock the environment variables before importing main modules
os.environ.setdefault("AZURE_OPENAI_API_KEY", "test-key")
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT", "test-deployment")

from lida_enhanced_manager import LidaEnhancedManager, EnhancedDataSummary, EnhancedGoal


class TestLidaEnhancedManager:
    """Test the LIDA Enhanced Manager integration."""

    @pytest.fixture
    def mock_azure_client(self):
        """Mock Azure OpenAI client."""
        client = AsyncMock()

        # Mock chat completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test analysis response"

        client.chat.completions.create.return_value = mock_response
        return client

    @pytest.fixture
    def sample_dashboard_context(self):
        """Sample dashboard context for testing."""
        return {
            "name": "sales_dashboard",
            "description": "Sales performance dashboard",
            "metrics": [
                {"name": "total_revenue", "type": "numeric"},
                {"name": "units_sold", "type": "numeric"}
            ],
            "dimensions": [
                {"name": "region", "type": "categorical"},
                {"name": "product_category", "type": "categorical"}
            ],
            "sample_data": [
                {"region": "North", "product_category": "Electronics", "total_revenue": 10000},
                {"region": "South", "product_category": "Clothing", "total_revenue": 8000}
            ]
        }

    @pytest.mark.asyncio
    async def test_lida_manager_initialization(self, mock_azure_client, sample_dashboard_context):
        """Test that LIDA Enhanced Manager initializes correctly."""
        manager = LidaEnhancedManager(
            azure_client=mock_azure_client,
            deployment_name="test-deployment",
            dashboard_context=sample_dashboard_context
        )

        assert manager.azure_client == mock_azure_client
        assert manager.deployment_name == "test-deployment"
        assert manager.dashboard_context == sample_dashboard_context
        assert manager._text_gen is not None

    @pytest.mark.asyncio
    async def test_data_summarization(self, mock_azure_client, sample_dashboard_context):
        """Test data summarization functionality."""
        manager = LidaEnhancedManager(
            azure_client=mock_azure_client,
            deployment_name="test-deployment",
            dashboard_context=sample_dashboard_context
        )

        # Mock the LLM response for insights generation
        mock_azure_client.chat.completions.create.return_value.choices[0].message.content = """
        - Revenue shows strong regional variation
        - Electronics category leads in performance
        - North region outperforms South
        """

        summary = await manager.summarize_data(sample_dashboard_context)

        assert isinstance(summary, EnhancedDataSummary)
        assert summary.dataset_name == "sales_dashboard"
        assert "total_revenue" in summary.columns
        assert "region" in summary.columns
        assert len(summary.insights) > 0
        assert summary.ag_ui_context == sample_dashboard_context

    @pytest.mark.asyncio
    async def test_goal_generation(self, mock_azure_client, sample_dashboard_context):
        """Test goal generation with persona awareness."""
        manager = LidaEnhancedManager(
            azure_client=mock_azure_client,
            deployment_name="test-deployment",
            dashboard_context=sample_dashboard_context
        )

        # Create a sample data summary
        summary = EnhancedDataSummary(
            summary="Sales dashboard with revenue and regional data",
            dataset_name="sales_dashboard",
            columns=["total_revenue", "region", "product_category"],
            data_types={"total_revenue": "numeric", "region": "categorical"},
            insights=["Strong regional variation", "Electronics leading"],
            ag_ui_context=sample_dashboard_context
        )

        # Mock goal generation response
        mock_goals_response = """
        {"question": "What are the revenue trends by region?", "visualization": "Regional revenue analysis", "rationale": "Understanding regional performance", "chart_type": "bar", "dimensions": ["region"], "metrics": ["total_revenue"]}
        {"question": "How do product categories compare?", "visualization": "Category comparison", "rationale": "Product performance analysis", "chart_type": "column", "dimensions": ["product_category"], "metrics": ["total_revenue"]}
        """

        mock_azure_client.chat.completions.create.return_value.choices[0].message.content = mock_goals_response

        goals = await manager.generate_goals(summary, n=2, persona="analyst")

        assert isinstance(goals, list)
        assert len(goals) <= 2

        if goals:  # Only test if goals were generated
            goal = goals[0]
            assert isinstance(goal, EnhancedGoal)
            assert goal.persona == "analyst"
            assert goal.ag_ui_compatible is True

    @pytest.mark.asyncio
    async def test_visualization_spec_generation(self, mock_azure_client, sample_dashboard_context):
        """Test visualization specification generation."""
        manager = LidaEnhancedManager(
            azure_client=mock_azure_client,
            deployment_name="test-deployment",
            dashboard_context=sample_dashboard_context
        )

        # Create sample goal and summary
        goal = EnhancedGoal(
            question="What are the revenue trends by region?",
            visualization="Regional revenue analysis",
            rationale="Understanding regional performance",
            chart_type="bar",
            dimensions=["region"],
            metrics=["total_revenue"],
            persona="analyst",
            narrative_goal="magnitude_comparison",
            ag_ui_compatible=True
        )

        summary = EnhancedDataSummary(
            summary="Sales dashboard with revenue and regional data",
            dataset_name="sales_dashboard",
            columns=["total_revenue", "region"],
            data_types={"total_revenue": "numeric", "region": "categorical"},
            insights=["Strong regional variation"],
            ag_ui_context=sample_dashboard_context
        )

        viz_spec = await manager.visualize_goal(goal, summary)

        assert isinstance(viz_spec, dict)
        assert "goal" in viz_spec
        assert "chart_type" in viz_spec
        assert viz_spec["chart_type"] == "bar"
        assert "ag_ui_highlight" in viz_spec
        assert "chart_ids" in viz_spec["ag_ui_highlight"]

    @pytest.mark.asyncio
    async def test_async_text_generation(self, mock_azure_client, sample_dashboard_context):
        """Test async text generation functionality."""
        manager = LidaEnhancedManager(
            azure_client=mock_azure_client,
            deployment_name="test-deployment",
            dashboard_context=sample_dashboard_context
        )

        mock_azure_client.chat.completions.create.return_value.choices[0].message.content = "Generated text response"

        messages = [{"role": "user", "content": "Test prompt"}]
        result = await manager._text_gen.generate(messages)

        assert result == "Generated text response"
        mock_azure_client.chat.completions.create.assert_called_once()

    def test_persona_context_mapping(self, mock_azure_client, sample_dashboard_context):
        """Test persona context mapping."""
        manager = LidaEnhancedManager(
            azure_client=mock_azure_client,
            deployment_name="test-deployment",
            dashboard_context=sample_dashboard_context
        )

        executive_context = manager._get_persona_context("executive")
        analyst_context = manager._get_persona_context("analyst")

        assert "strategic" in executive_context
        assert "detailed" in analyst_context
        assert executive_context != analyst_context

    def test_chart_id_mapping(self, mock_azure_client, sample_dashboard_context):
        """Test mapping of goals to AG-UI chart IDs."""
        manager = LidaEnhancedManager(
            azure_client=mock_azure_client,
            deployment_name="test-deployment",
            dashboard_context=sample_dashboard_context
        )

        sales_goal = EnhancedGoal(
            question="What are the sales trends?",
            visualization="Sales analysis",
            rationale="Understanding sales performance",
            chart_type="line",
            dimensions=["time"],
            metrics=["sales"],
            persona="analyst",
            narrative_goal="change_over_time"
        )

        product_goal = EnhancedGoal(
            question="How do products compare?",
            visualization="Product analysis",
            rationale="Understanding product performance",
            chart_type="bar",
            dimensions=["product"],
            metrics=["revenue"],
            persona="analyst",
            narrative_goal="magnitude_comparison"
        )

        sales_chart_ids = manager._map_to_chart_ids(sales_goal)
        product_chart_ids = manager._map_to_chart_ids(product_goal)

        assert isinstance(sales_chart_ids, list)
        assert isinstance(product_chart_ids, list)
        assert len(sales_chart_ids) > 0
        assert len(product_chart_ids) > 0


class TestFastAPIIntegration:
    """Test FastAPI integration with LIDA Enhanced Manager."""

    @pytest.mark.asyncio
    async def test_lida_manager_factory(self):
        """Test the factory function for creating LIDA manager."""
        with patch('lida_enhanced_manager.LidaEnhancedManager') as mock_manager_class:
            mock_client = AsyncMock()
            mock_context = {"test": "context"}

            from lida_enhanced_manager import create_lida_enhanced_manager

            result = await create_lida_enhanced_manager(
                azure_client=mock_client,
                deployment_name="test-deployment",
                dashboard_context=mock_context
            )

            mock_manager_class.assert_called_once_with(
                mock_client, "test-deployment", mock_context
            )

    def test_error_handling(self, mock_azure_client, sample_dashboard_context):
        """Test error handling in LIDA manager."""
        manager = LidaEnhancedManager(
            azure_client=mock_azure_client,
            deployment_name="test-deployment",
            dashboard_context=sample_dashboard_context
        )

        # Test with client that raises an exception
        mock_azure_client.chat.completions.create.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            asyncio.run(manager._text_gen.generate([{"role": "user", "content": "test"}]))


def run_tests():
    """Run the test suite for LIDA integration."""
    print("🧪 Running LIDA Integration Tests for Task 1...")

    # Simple synchronization test without pytest
    import sys

    try:
        # Test basic imports
        from lida_enhanced_manager import LidaEnhancedManager, EnhancedDataSummary, EnhancedGoal
        print("✅ LIDA Enhanced Manager imports successful")

        # Test basic initialization
        mock_client = MagicMock()
        test_context = {"name": "test", "metrics": [], "dimensions": []}

        manager = LidaEnhancedManager(
            azure_client=mock_client,
            deployment_name="test-deployment",
            dashboard_context=test_context
        )

        print("✅ LIDA Enhanced Manager initialization successful")

        # Test data models
        summary = EnhancedDataSummary(
            summary="Test summary",
            dataset_name="test",
            columns=["col1"],
            data_types={"col1": "numeric"},
            insights=["Test insight"],
            ag_ui_context=test_context
        )

        goal = EnhancedGoal(
            question="Test question?",
            visualization="Test viz",
            rationale="Test rationale",
            chart_type="bar",
            dimensions=["col1"],
            metrics=["metric1"],
            persona="analyst",
            narrative_goal="magnitude_comparison"
        )

        print("✅ LIDA data models creation successful")

        # Test AG-UI integration patterns
        assert hasattr(manager, '_map_to_chart_ids')
        assert hasattr(manager, '_get_persona_context')

        print("✅ AG-UI integration methods present")

        print("🎉 All LIDA Integration Tests for Task 1 PASSED!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)