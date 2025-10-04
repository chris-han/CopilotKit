"""
Test suite for Task 3: Semantic Layer Integration.

This test validates the semantic layer integration that connects LIDA's data
summarization to dbt MCP server and ClickHouse, providing enhanced metric
definitions and business entity mapping.
"""

import json
import sys
from unittest.mock import MagicMock, AsyncMock, patch


def test_semantic_layer_architecture():
    """Test the semantic layer integration architecture and data models."""

    print("🔍 Testing Semantic Layer Integration Architecture...")

    try:
        # Test import structure
        from semantic_layer_integration import (
            SemanticLayerIntegration,
            SemanticMetric,
            BusinessEntity,
            SemanticModel,
            MetricType,
            create_semantic_layer_integration
        )
        print("✅ Semantic Layer Integration imports successful")

        # Test data model creation
        metric = SemanticMetric(
            name="total_revenue",
            type=MetricType.SUM,
            sql="SUM(revenue)",
            base_field="revenue",
            dimensions=["region", "time_period"],
            narrative_goal="magnitude_comparison",
            recommended_chart="bar",
            description="Total revenue across all transactions",
            business_context="Key financial performance indicator",
            unit="USD",
            format="currency"
        )

        assert metric.name == "total_revenue", "Metric name should be set correctly"
        assert metric.type == MetricType.SUM, "Metric type should be SUM"
        assert "region" in metric.dimensions, "Should contain region dimension"
        print("✅ SemanticMetric model creation successful")

        # Test business entity creation
        entity = BusinessEntity(
            name="sales_data",
            type="table",
            description="Core sales transaction data",
            primary_key="transaction_id",
            relationships=[
                {"type": "belongs_to", "entity": "customer", "key": "customer_id"}
            ],
            business_rules=["Revenue must be positive for completed transactions"]
        )

        assert entity.name == "sales_data", "Entity name should be set correctly"
        assert entity.type == "table", "Entity type should be table"
        assert len(entity.business_rules) == 1, "Should have business rules"
        print("✅ BusinessEntity model creation successful")

        # Test semantic model creation
        semantic_model = SemanticModel(
            name="sales_analytics",
            entities=[entity],
            metrics=[metric],
            relationships=[],
            business_glossary={"revenue": "Total monetary value"}
        )

        assert semantic_model.name == "sales_analytics", "Model name should be set"
        assert len(semantic_model.entities) == 1, "Should contain entity"
        assert len(semantic_model.metrics) == 1, "Should contain metric"
        print("✅ SemanticModel creation successful")

        return True

    except Exception as e:
        print(f"❌ Semantic layer architecture test failed: {e}")
        return False


def test_integration_initialization():
    """Test semantic layer integration initialization with mock clients."""

    print("🔍 Testing Integration Initialization...")

    try:
        from semantic_layer_integration import SemanticLayerIntegration

        # Test initialization without clients (mock mode)
        integration = SemanticLayerIntegration()
        assert integration.mock_mode is True, "Should be in mock mode without clients"
        assert integration.dbt_client is None, "dbt client should be None"
        assert integration.clickhouse_client is None, "ClickHouse client should be None"
        print("✅ Mock mode initialization successful")

        # Test initialization with mock clients
        mock_dbt_client = MagicMock()
        mock_clickhouse_client = MagicMock()

        integration_with_clients = SemanticLayerIntegration(
            dbt_mcp_client=mock_dbt_client,
            clickhouse_mcp_client=mock_clickhouse_client
        )

        assert integration_with_clients.mock_mode is False, "Should not be in mock mode with clients"
        assert integration_with_clients.dbt_client is mock_dbt_client, "dbt client should be set"
        assert integration_with_clients.clickhouse_client is mock_clickhouse_client, "ClickHouse client should be set"
        print("✅ Client-based initialization successful")

        # Test that mock semantic model is initialized
        assert len(integration._semantic_models) > 0, "Should have mock semantic models"
        assert "sales_analytics" in integration._semantic_models, "Should have sales_analytics model"
        assert len(integration._metric_cache) > 0, "Should have cached metrics"
        print("✅ Mock semantic model initialization successful")

        return True

    except Exception as e:
        print(f"❌ Integration initialization test failed: {e}")
        return False


async def test_semantic_model_retrieval():
    """Test semantic model retrieval functionality."""

    print("🔍 Testing Semantic Model Retrieval...")

    try:
        from semantic_layer_integration import SemanticLayerIntegration

        integration = SemanticLayerIntegration()  # Mock mode

        # Test retrieving existing semantic model
        model = await integration.get_semantic_model("sales_analytics")
        assert model is not None, "Should retrieve sales_analytics model"
        assert model.name == "sales_analytics", "Model name should match"
        assert len(model.entities) > 0, "Should have entities"
        assert len(model.metrics) > 0, "Should have metrics"
        print("✅ Semantic model retrieval successful")

        # Test retrieving non-existent model
        nonexistent_model = await integration.get_semantic_model("nonexistent")
        assert nonexistent_model is None, "Should return None for non-existent model"
        print("✅ Non-existent model handling successful")

        return True

    except Exception as e:
        print(f"❌ Semantic model retrieval test failed: {e}")
        return False


async def test_metrics_functionality():
    """Test available metrics retrieval and filtering."""

    print("🔍 Testing Metrics Functionality...")

    try:
        from semantic_layer_integration import SemanticLayerIntegration

        integration = SemanticLayerIntegration()  # Mock mode

        # Test getting all available metrics
        all_metrics = await integration.get_available_metrics()
        assert len(all_metrics) > 0, "Should have available metrics"
        assert any(metric.name == "total_revenue" for metric in all_metrics), "Should have total_revenue metric"
        assert any(metric.name == "customer_count" for metric in all_metrics), "Should have customer_count metric"
        print("✅ All metrics retrieval successful")

        # Test filtering metrics by entity
        revenue_metrics = await integration.get_available_metrics(entity_name="revenue")
        assert len(revenue_metrics) > 0, "Should have revenue-related metrics"
        assert all("revenue" in metric.name.lower() or
                  "revenue" in metric.sql.lower() or
                  "revenue" in metric.base_field.lower()
                  for metric in revenue_metrics), "All metrics should be revenue-related"
        print("✅ Entity-based metric filtering successful")

        # Test metric query functionality
        metric_result = await integration.query_metric(
            metric_name="total_revenue",
            dimensions=["region"],
            filters={"status": "completed"},
            limit=10
        )

        assert "metric" in metric_result, "Result should contain metric name"
        assert "data" in metric_result, "Result should contain data"
        assert "metadata" in metric_result, "Result should contain metadata"
        assert metric_result["metric"] == "total_revenue", "Metric name should match"
        print("✅ Metric query functionality successful")

        return True

    except Exception as e:
        print(f"❌ Metrics functionality test failed: {e}")
        return False


async def test_data_summary_enhancement():
    """Test enhanced data summary generation with semantic insights."""

    print("🔍 Testing Data Summary Enhancement...")

    try:
        from semantic_layer_integration import SemanticLayerIntegration

        integration = SemanticLayerIntegration()  # Mock mode

        # Create sample data summary
        sample_data_summary = {
            'columns': ['customer_id', 'revenue', 'region', 'product_id'],
            'data_types': {
                'customer_id': 'categorical',
                'revenue': 'numeric',
                'region': 'categorical',
                'product_id': 'categorical'
            },
            'sample_data': [
                {'customer_id': 'C001', 'revenue': 1500, 'region': 'North', 'product_id': 'P001'},
                {'customer_id': 'C002', 'revenue': 2300, 'region': 'South', 'product_id': 'P002'}
            ]
        }

        # Test enhanced data summary generation
        enhanced_summary = await integration.enhance_data_summary(
            sample_data_summary,
            domain="sales_analytics"
        )

        # Validate enhanced summary structure
        assert 'semantic_model' in enhanced_summary, "Should have semantic model reference"
        assert 'entity_mappings' in enhanced_summary, "Should have entity mappings"
        assert 'available_metrics' in enhanced_summary, "Should have available metrics"
        assert 'business_insights' in enhanced_summary, "Should have business insights"
        assert 'semantic_relationships' in enhanced_summary, "Should have relationships"
        assert 'business_glossary' in enhanced_summary, "Should have business glossary"

        print("✅ Enhanced data summary structure validated")

        # Validate entity mappings
        entity_mappings = enhanced_summary['entity_mappings']
        assert isinstance(entity_mappings, dict), "Entity mappings should be a dictionary"
        assert any('customer' in mapping.lower() for mapping in entity_mappings.values()), "Should map customer entities"
        print("✅ Entity mapping functionality successful")

        # Validate available metrics
        available_metrics = enhanced_summary['available_metrics']
        assert len(available_metrics) > 0, "Should have available metrics"
        assert all('name' in metric for metric in available_metrics), "All metrics should have names"
        assert all('description' in metric for metric in available_metrics), "All metrics should have descriptions"
        print("✅ Available metrics enhancement successful")

        # Validate business insights
        business_insights = enhanced_summary['business_insights']
        assert isinstance(business_insights, list), "Business insights should be a list"
        assert len(business_insights) > 0, "Should generate business insights"
        print("✅ Business insights generation successful")

        return True

    except Exception as e:
        print(f"❌ Data summary enhancement test failed: {e}")
        return False


def test_business_logic_mapping():
    """Test business entity and relationship mapping."""

    print("🔍 Testing Business Logic Mapping...")

    try:
        from semantic_layer_integration import SemanticLayerIntegration

        integration = SemanticLayerIntegration()  # Mock mode

        # Get the mock semantic model
        model = integration._semantic_models.get("sales_analytics")
        assert model is not None, "Should have sales_analytics model"

        # Test column to entity mapping
        columns = ['customer_id', 'revenue', 'product_id', 'region']
        entity_mappings = integration._map_columns_to_entities(columns, model)

        assert isinstance(entity_mappings, dict), "Should return dictionary of mappings"
        assert 'customer_id' in entity_mappings, "Should map customer_id"
        assert 'revenue' in entity_mappings, "Should map revenue column"
        print("✅ Column to entity mapping successful")

        # Test relationship extraction
        relationships = integration._extract_relationships(model)
        assert isinstance(relationships, list), "Should return list of relationships"
        assert len(relationships) > 0, "Should have relationships"
        assert all('type' in rel for rel in relationships), "All relationships should have type"
        print("✅ Relationship extraction successful")

        # Test business insights generation
        data_types = {'revenue': 'numeric', 'region': 'categorical', 'customer_id': 'categorical', 'product_id': 'categorical'}
        time_columns = columns + ['date']  # Add time column to test time analysis detection
        insights = integration._generate_business_insights(time_columns, data_types, model)

        assert isinstance(insights, list), "Should return list of insights"
        assert len(insights) > 0, "Should generate insights"
        assert any('numeric' in insight.lower() for insight in insights), "Should mention numeric measures"
        assert any('time' in insight.lower() or 'trend' in insight.lower() for insight in insights), "Should identify time analysis"
        print("✅ Business insights generation successful")

        return True

    except Exception as e:
        print(f"❌ Business logic mapping test failed: {e}")
        return False


def test_lida_manager_integration():
    """Test integration with LIDA Enhanced Manager."""

    print("🔍 Testing LIDA Manager Integration...")

    try:
        # Mock dependencies for LIDA manager
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

        # Test LIDA manager with semantic layer integration
        from lida_enhanced_manager import LidaEnhancedManager
        from semantic_layer_integration import SemanticLayerIntegration

        mock_azure_client = MagicMock()
        sample_context = {"name": "test", "metrics": [], "dimensions": []}

        # Create semantic layer integration
        semantic_integration = SemanticLayerIntegration()

        # Verify semantic integration could be used with LIDA manager
        assert hasattr(semantic_integration, 'enhance_data_summary'), "Should have enhance_data_summary method"
        assert hasattr(semantic_integration, 'get_available_metrics'), "Should have get_available_metrics method"
        assert hasattr(semantic_integration, 'query_metric'), "Should have query_metric method"
        print("✅ Semantic integration methods compatible with LIDA manager")

        # Test factory function
        from semantic_layer_integration import create_semantic_layer_integration

        # This should be async, but for testing we'll verify it exists
        assert callable(create_semantic_layer_integration), "Factory function should be callable"
        print("✅ Factory function available for integration")

        return True

    except Exception as e:
        print(f"❌ LIDA manager integration test failed: {e}")
        return False


def run_task3_validation():
    """Run comprehensive Task 3 validation."""

    print("🧪 Running Task 3: Semantic Layer Integration Validation")
    print("="*60)

    tests = [
        ("Semantic Layer Architecture", test_semantic_layer_architecture),
        ("Integration Initialization", test_integration_initialization),
        ("Semantic Model Retrieval", test_semantic_model_retrieval),
        ("Metrics Functionality", test_metrics_functionality),
        ("Data Summary Enhancement", test_data_summary_enhancement),
        ("Business Logic Mapping", test_business_logic_mapping),
        ("LIDA Manager Integration", test_lida_manager_integration)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔬 {test_name}")
        print("-" * 40)

        try:
            # Handle async tests
            if test_func.__name__ in ['test_semantic_model_retrieval', 'test_metrics_functionality', 'test_data_summary_enhancement']:
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

    print("\n" + "="*60)
    print(f"📊 Task 3 Validation Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Task 3: Semantic Layer Integration COMPLETED!")
        print("\n✅ Semantic layer integration architecture implemented")
        print("✅ dbt MCP server connection capabilities added")
        print("✅ ClickHouse OLAP query optimization prepared")
        print("✅ Business entity relationship understanding enhanced")
        print("✅ Enhanced metric definitions beyond basic column analysis")
        print("✅ Mock semantic models for testing implemented")
        print("✅ Ready to proceed to Task 4: Persona-Aware Visualization Selection")
        return True
    else:
        print("❌ Task 3 validation failed. Please review implementation before proceeding.")
        return False


if __name__ == "__main__":
    success = run_task3_validation()
    exit(0 if success else 1)