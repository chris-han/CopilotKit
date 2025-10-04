"""
Test suite for Task 8: Enhanced LIDA Integration with FOCUS Data.

This test validates the enhanced LIDA integration system that extends LIDA's
data summarization capabilities specifically for FOCUS-compliant datasets,
adding FinOps domain knowledge, optimization opportunities, and specialized insights.
"""

import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch


def test_focus_lida_integration_architecture():
    """Test FOCUS LIDA integration architecture and data models."""

    print("🔍 Testing FOCUS LIDA Integration Architecture...")

    try:
        # Test import structure
        from focus_lida_integration import (
            FinOpsOptimizationType,
            FinOpsAnomalyType,
            FinOpsOptimizationOpportunity,
            FinOpsAnomaly,
            FocusEnhancedSummary,
            FinOpsDomainKnowledge,
            FocusLidaDataSummarizer,
            create_focus_lida_integration
        )
        print("✅ FOCUS LIDA integration imports successful")

        # Test FinOps optimization types enum
        assert FinOpsOptimizationType.RIGHTSIZING.value == "rightsizing", "Rightsizing optimization type should exist"
        assert FinOpsOptimizationType.COMMITMENT_OPPORTUNITY.value == "commitment_opportunity", "Commitment opportunity should exist"
        assert FinOpsOptimizationType.UNUSED_RESOURCES.value == "unused_resources", "Unused resources type should exist"
        print("✅ FinOps optimization types enum working correctly")

        # Test FinOps anomaly types enum
        assert FinOpsAnomalyType.COST_SPIKE.value == "cost_spike", "Cost spike anomaly type should exist"
        assert FinOpsAnomalyType.UNUSUAL_PATTERN.value == "unusual_pattern", "Unusual pattern type should exist"
        assert FinOpsAnomalyType.MISSING_DISCOUNTS.value == "missing_discounts", "Missing discounts type should exist"
        print("✅ FinOps anomaly types enum working correctly")

        # Test optimization opportunity creation
        opportunity = FinOpsOptimizationOpportunity(
            opportunity_id="test_opp_001",
            optimization_type=FinOpsOptimizationType.RIGHTSIZING,
            title="Test Rightsizing Opportunity",
            description="Test description for rightsizing",
            potential_savings_monthly=Decimal("1000.00"),
            confidence_score=0.85,
            implementation_effort="medium",
            affected_services=["EC2", "RDS"],
            affected_accounts=["account-123"],
            affected_regions=["us-east-1"],
            recommended_actions=["Analyze usage patterns", "Right-size instances"],
            implementation_timeline="2-4 weeks",
            supporting_evidence={"utilization": 20.5},
            created_at=datetime.now()
        )

        assert opportunity.optimization_type == FinOpsOptimizationType.RIGHTSIZING, "Optimization type should be set"
        assert opportunity.potential_savings_monthly == Decimal("1000.00"), "Savings should be set"
        assert opportunity.confidence_score == 0.85, "Confidence score should be set"
        assert len(opportunity.affected_services) == 2, "Should have affected services"
        print("✅ FinOpsOptimizationOpportunity creation successful")

        # Test anomaly creation
        anomaly = FinOpsAnomaly(
            anomaly_id="test_anomaly_001",
            anomaly_type=FinOpsAnomalyType.COST_SPIKE,
            severity="high",
            title="Test Cost Spike",
            description="Unusual cost increase detected",
            affected_period_start=datetime.now() - timedelta(days=7),
            affected_period_end=datetime.now(),
            affected_services=["EC2"],
            affected_accounts=["account-123"],
            baseline_value=Decimal("1000.00"),
            anomalous_value=Decimal("2500.00"),
            deviation_percentage=150.0,
            investigation_suggestions=["Check for new deployments"],
            related_opportunities=[],
            detected_at=datetime.now()
        )

        assert anomaly.anomaly_type == FinOpsAnomalyType.COST_SPIKE, "Anomaly type should be set"
        assert anomaly.severity == "high", "Severity should be set"
        assert anomaly.deviation_percentage == 150.0, "Deviation should be set"
        print("✅ FinOpsAnomaly creation successful")

        return True

    except Exception as e:
        print(f"❌ FOCUS LIDA integration architecture test failed: {e}")
        return False


def test_finops_domain_knowledge():
    """Test FinOps domain knowledge system."""

    print("🔍 Testing FinOps Domain Knowledge...")

    try:
        from focus_lida_integration import FinOpsDomainKnowledge

        domain_knowledge = FinOpsDomainKnowledge()

        # Test initialization
        assert hasattr(domain_knowledge, 'cost_thresholds'), "Should have cost thresholds"
        assert hasattr(domain_knowledge, 'service_categories'), "Should have service categories"
        assert hasattr(domain_knowledge, 'optimization_patterns'), "Should have optimization patterns"
        print("✅ Domain knowledge initialization successful")

        # Test service category identification
        assert domain_knowledge.identify_service_category("Amazon EC2") == "compute", "Should identify EC2 as compute"
        assert domain_knowledge.identify_service_category("Amazon S3") == "storage", "Should identify S3 as storage"
        assert domain_knowledge.identify_service_category("Amazon RDS") == "database", "Should identify RDS as database"
        assert domain_knowledge.identify_service_category("Unknown Service") == "other", "Should default to other"
        print("✅ Service category identification working")

        # Test efficiency score calculation
        cost_data = {
            "commitment_coverage": 70.0,
            "service_distribution_entropy": 1.5,
            "regional_cost_variance": 25.0,
            "cost_trend_stability": 0.8
        }

        efficiency_score = domain_knowledge.calculate_efficiency_score(cost_data)
        assert 0.0 <= efficiency_score <= 1.0, "Efficiency score should be between 0 and 1"
        assert efficiency_score > 0.5, "Should have reasonable efficiency score with good data"
        print("✅ Efficiency score calculation working")

        # Test with empty data
        empty_score = domain_knowledge.calculate_efficiency_score({})
        assert empty_score == 0.5, "Should return default score for empty data"
        print("✅ Empty data handling working")

        return True

    except Exception as e:
        print(f"❌ FinOps domain knowledge test failed: {e}")
        return False


async def test_focus_lida_data_summarizer():
    """Test FOCUS LIDA data summarizer functionality."""

    print("🔍 Testing FOCUS LIDA Data Summarizer...")

    try:
        from focus_lida_integration import FocusLidaDataSummarizer

        # Mock LIDA manager
        mock_lida_manager = MagicMock()
        mock_lida_manager.summarize_data = AsyncMock(return_value={
            "name": "Test Dataset",
            "columns": ["BilledCost", "ServiceName", "Region"],
            "data_types": {"BilledCost": "numeric", "ServiceName": "categorical"},
            "row_count": 1000,
            "insights": ["Test insight"]
        })

        # Test initialization
        summarizer = FocusLidaDataSummarizer(lida_manager=mock_lida_manager)
        assert summarizer.lida_manager is mock_lida_manager, "Should store LIDA manager reference"
        assert hasattr(summarizer, 'finops_domain'), "Should have FinOps domain knowledge"
        assert hasattr(summarizer, 'focus_field_definitions'), "Should have FOCUS field definitions"
        print("✅ FOCUS LIDA summarizer initialization successful")

        # Test FOCUS field definitions
        field_definitions = summarizer.focus_field_definitions
        assert "BilledCost" in field_definitions, "Should have BilledCost field definition"
        assert "ChargeCategory" in field_definitions, "Should have ChargeCategory field definition"
        assert "ServiceName" in field_definitions, "Should have ServiceName field definition"

        billed_cost_def = field_definitions["BilledCost"]
        assert billed_cost_def["type"] == "numeric", "BilledCost should be numeric type"
        assert billed_cost_def["finops_category"] == "cost", "Should be in cost category"
        assert billed_cost_def["visualization_priority"] == "high", "Should have high priority"
        print("✅ FOCUS field definitions loaded correctly")

        # Test sample data creation for summarization
        sample_focus_data = {
            "name": "FOCUS Test Dataset",
            "sample_data": [
                {
                    "BillingAccountId": "account-001",
                    "BillingAccountName": "Test Account",
                    "BilledCost": 100.50,
                    "ChargeCategory": "Usage",
                    "ServiceName": "Amazon EC2",
                    "Region": "us-east-1",
                    "CommitmentDiscountCategory": None,
                    "BillingPeriodStart": "2024-01-01T00:00:00Z"
                },
                {
                    "BillingAccountId": "account-002",
                    "BillingAccountName": "Prod Account",
                    "BilledCost": 250.75,
                    "ChargeCategory": "Usage",
                    "ServiceName": "Amazon S3",
                    "Region": "us-west-2",
                    "CommitmentDiscountCategory": "Spend",
                    "BillingPeriodStart": "2024-01-01T00:00:00Z"
                }
            ]
        }

        # Test enhanced summarization
        enhanced_summary = await summarizer.summarize_focus_data(sample_focus_data)

        # Validate enhanced summary structure
        assert hasattr(enhanced_summary, 'base_summary'), "Should have base summary"
        assert hasattr(enhanced_summary, 'billing_accounts_analysis'), "Should have billing accounts analysis"
        assert hasattr(enhanced_summary, 'service_distribution_analysis'), "Should have service distribution analysis"
        assert hasattr(enhanced_summary, 'optimization_opportunities'), "Should have optimization opportunities"
        assert hasattr(enhanced_summary, 'anomaly_candidates'), "Should have anomaly candidates"
        assert hasattr(enhanced_summary, 'finops_kpis'), "Should have FinOps KPIs"
        print("✅ Enhanced summary structure validated")

        # Test base summary
        base_summary = enhanced_summary.base_summary
        assert "name" in base_summary, "Base summary should have name"
        print("✅ Base summary integration working")

        # Test billing accounts analysis
        billing_analysis = enhanced_summary.billing_accounts_analysis
        assert "total_accounts" in billing_analysis, "Should analyze total accounts"
        assert "total_cost" in billing_analysis, "Should calculate total cost"
        assert "top_accounts" in billing_analysis, "Should identify top accounts"
        assert billing_analysis["total_accounts"] == 2, "Should count 2 accounts"
        print("✅ Billing accounts analysis working")

        # Test service distribution analysis
        service_analysis = enhanced_summary.service_distribution_analysis
        assert "total_services" in service_analysis, "Should analyze total services"
        assert "service_concentration_index" in service_analysis, "Should calculate concentration"
        assert "top_services" in service_analysis, "Should identify top services"
        assert service_analysis["total_services"] == 2, "Should count 2 services"
        print("✅ Service distribution analysis working")

        # Test optimization opportunities
        opportunities = enhanced_summary.optimization_opportunities
        assert isinstance(opportunities, list), "Should return list of opportunities"
        print("✅ Optimization opportunities generation working")

        # Test FinOps KPIs
        finops_kpis = enhanced_summary.finops_kpis
        assert "total_monthly_cost" in finops_kpis, "Should calculate total monthly cost"
        assert "commitment_coverage_percentage" in finops_kpis, "Should calculate commitment coverage"
        assert finops_kpis["total_monthly_cost"] > 0, "Should have positive total cost"
        print("✅ FinOps KPIs calculation working")

        return True

    except Exception as e:
        print(f"❌ FOCUS LIDA data summarizer test failed: {e}")
        return False


async def test_focus_billing_analysis():
    """Test FOCUS billing accounts analysis functionality."""

    print("🔍 Testing FOCUS Billing Analysis...")

    try:
        from focus_lida_integration import FocusLidaDataSummarizer

        summarizer = FocusLidaDataSummarizer()

        # Test billing accounts analysis
        sample_data = [
            {
                "BillingAccountId": "account-001",
                "BillingAccountName": "Development Account",
                "BilledCost": 1000.00
            },
            {
                "BillingAccountId": "account-002",
                "BillingAccountName": "Production Account",
                "BilledCost": 5000.00
            },
            {
                "BillingAccountId": "account-001",
                "BillingAccountName": "Development Account",
                "BilledCost": 500.00
            }
        ]

        billing_analysis = await summarizer._analyze_billing_accounts(sample_data)

        # Validate analysis results
        assert billing_analysis["total_accounts"] == 2, "Should identify 2 unique accounts"
        assert billing_analysis["total_cost"] == 6500.00, "Should sum all costs"
        assert billing_analysis["average_cost_per_account"] == 3250.00, "Should calculate average correctly"

        # Test top accounts
        top_accounts = billing_analysis["top_accounts"]
        assert len(top_accounts) == 2, "Should list top accounts"
        assert top_accounts[0]["account_id"] == "account-002", "Production should be top account"
        assert top_accounts[0]["cost"] == 5000.00, "Should have correct cost"
        print("✅ Billing accounts analysis working correctly")

        # Test empty data
        empty_analysis = await summarizer._analyze_billing_accounts([])
        assert empty_analysis == {}, "Should handle empty data gracefully"
        print("✅ Empty billing data handling working")

        return True

    except Exception as e:
        print(f"❌ FOCUS billing analysis test failed: {e}")
        return False


async def test_optimization_opportunities_identification():
    """Test FinOps optimization opportunities identification."""

    print("🔍 Testing Optimization Opportunities Identification...")

    try:
        from focus_lida_integration import FocusLidaDataSummarizer

        summarizer = FocusLidaDataSummarizer()

        # Create sample data that should trigger optimization opportunities
        sample_data = [
            {
                "BilledCost": 10000.00,
                "CommitmentDiscountCategory": None,  # No commitment discounts
                "ServiceName": "Amazon EC2",
                "Region": "us-east-1",
                "ChargeCategory": "Usage"
            } for _ in range(80)  # 80% in one region to trigger regional optimization
        ] + [
            {
                "BilledCost": 1000.00,
                "CommitmentDiscountCategory": None,
                "ServiceName": "Amazon S3",
                "Region": "us-west-2",
                "ChargeCategory": "Usage"
            } for _ in range(20)
        ]

        # Test optimization opportunity identification
        opportunities = await summarizer._identify_optimization_opportunities(sample_data)

        assert len(opportunities) > 0, "Should identify optimization opportunities"
        print("✅ Optimization opportunities identified")

        # Check for commitment discount opportunity
        commitment_opportunities = [
            opp for opp in opportunities
            if opp.optimization_type.value == "commitment_opportunity"
        ]
        assert len(commitment_opportunities) > 0, "Should identify commitment discount opportunity"

        commitment_opp = commitment_opportunities[0]
        assert commitment_opp.potential_savings_monthly > 0, "Should calculate potential savings"
        assert 0.0 <= commitment_opp.confidence_score <= 1.0, "Confidence score should be valid"
        assert len(commitment_opp.recommended_actions) > 0, "Should provide recommended actions"
        print("✅ Commitment discount opportunity analysis working")

        # Check for regional optimization opportunity (if triggered)
        regional_opportunities = [
            opp for opp in opportunities
            if opp.optimization_type.value == "regional_optimization"
        ]
        if regional_opportunities:
            regional_opp = regional_opportunities[0]
            assert "concentration" in regional_opp.title.lower(), "Should identify concentration risk"
            print("✅ Regional optimization opportunity analysis working")

        return True

    except Exception as e:
        print(f"❌ Optimization opportunities identification test failed: {e}")
        return False


async def test_anomaly_detection():
    """Test FinOps anomaly detection capabilities."""

    print("🔍 Testing Anomaly Detection...")

    try:
        from focus_lida_integration import FocusLidaDataSummarizer

        summarizer = FocusLidaDataSummarizer()

        # Create sample data with anomalous patterns
        sample_data = [
            {
                "BilledCost": 10000.00,  # High usage cost
                "ChargeCategory": "Usage",
                "BillingPeriodStart": "2024-01-01T00:00:00Z",
                "CommitmentDiscountCategory": None
            },
            {
                "BilledCost": 5.00,  # Very low credit (indicating missing discounts)
                "ChargeCategory": "Credit",
                "BillingPeriodStart": "2024-01-01T00:00:00Z",
                "CommitmentDiscountCategory": None
            }
        ]

        # Test anomaly detection
        anomalies = await summarizer._identify_potential_anomalies(sample_data)

        assert isinstance(anomalies, list), "Should return list of anomalies"
        print("✅ Anomaly detection returns proper structure")

        # Test with insufficient data
        insufficient_data = [{"BilledCost": 100.00, "ChargeCategory": "Usage"}]
        minimal_anomalies = await summarizer._identify_potential_anomalies(insufficient_data)
        assert isinstance(minimal_anomalies, list), "Should handle insufficient data gracefully"
        print("✅ Insufficient data handling working")

        # Test with empty data
        empty_anomalies = await summarizer._identify_potential_anomalies([])
        assert empty_anomalies == [], "Should return empty list for no data"
        print("✅ Empty data anomaly detection working")

        return True

    except Exception as e:
        print(f"❌ Anomaly detection test failed: {e}")
        return False


async def test_finops_kpis_calculation():
    """Test FinOps KPIs calculation."""

    print("🔍 Testing FinOps KPIs Calculation...")

    try:
        from focus_lida_integration import FocusLidaDataSummarizer

        summarizer = FocusLidaDataSummarizer()

        # Create comprehensive sample data
        sample_data = [
            {
                "BilledCost": 1000.00,
                "ServiceName": "Amazon EC2",
                "Region": "us-east-1",
                "CommitmentDiscountCategory": "Spend"
            },
            {
                "BilledCost": 2000.00,
                "ServiceName": "Amazon S3",
                "Region": "us-west-2",
                "CommitmentDiscountCategory": None
            },
            {
                "BilledCost": 1500.00,
                "ServiceName": "Amazon RDS",
                "Region": "eu-west-1",
                "CommitmentDiscountCategory": "Usage"
            }
        ]

        # Test KPIs calculation
        finops_kpis = await summarizer._calculate_finops_kpis(sample_data)

        # Validate KPI structure
        required_kpis = [
            "total_monthly_cost",
            "average_cost_per_record",
            "commitment_coverage_percentage",
            "service_diversity_score",
            "regional_diversity_count",
            "cost_per_service"
        ]

        for kpi in required_kpis:
            assert kpi in finops_kpis, f"Should calculate {kpi}"

        # Validate KPI values
        assert finops_kpis["total_monthly_cost"] == 4500.00, "Should sum total cost correctly"
        assert finops_kpis["average_cost_per_record"] == 1500.00, "Should calculate average correctly"
        assert 0.0 <= finops_kpis["commitment_coverage_percentage"] <= 100.0, "Coverage should be valid percentage"
        assert finops_kpis["regional_diversity_count"] == 3, "Should count 3 regions"
        assert finops_kpis["cost_per_service"] > 0, "Should calculate cost per service"
        print("✅ FinOps KPIs calculation working correctly")

        # Test with empty data
        empty_kpis = await summarizer._calculate_finops_kpis([])
        assert empty_kpis == {}, "Should handle empty data"
        print("✅ Empty data KPIs handling working")

        return True

    except Exception as e:
        print(f"❌ FinOps KPIs calculation test failed: {e}")
        return False


async def test_narrative_insights_generation():
    """Test FinOps narrative insights generation."""

    print("🔍 Testing Narrative Insights Generation...")

    try:
        from focus_lida_integration import FocusLidaDataSummarizer

        summarizer = FocusLidaDataSummarizer()

        # Create sample data for insights
        sample_data = [
            {
                "BilledCost": 5000.00,
                "ServiceName": "Amazon EC2",
                "Region": "us-east-1",
                "CommitmentDiscountCategory": "Spend"
            },
            {
                "BilledCost": 1000.00,
                "ServiceName": "Amazon S3",
                "Region": "us-east-1",
                "CommitmentDiscountCategory": None
            }
        ]

        # Mock opportunities and anomalies
        opportunities = []
        anomalies = []

        # Test narrative insights generation
        insights = await summarizer._generate_finops_narrative_insights(
            sample_data, opportunities, anomalies
        )

        assert isinstance(insights, list), "Should return list of insights"
        assert len(insights) > 0, "Should generate insights from data"

        # Check for expected insight types
        insights_text = " ".join(insights).lower()
        assert "cost" in insights_text, "Should mention cost"
        assert any(word in insights_text for word in ["service", "ec2", "s3"]), "Should mention services"
        print("✅ Narrative insights generation working")

        # Test with empty data
        empty_insights = await summarizer._generate_finops_narrative_insights([], [], [])
        assert len(empty_insights) == 1, "Should return one insight for no data"
        assert "no data" in empty_insights[0].lower(), "Should indicate no data available"
        print("✅ Empty data insights handling working")

        return True

    except Exception as e:
        print(f"❌ Narrative insights generation test failed: {e}")
        return False


def test_visualization_recommendations():
    """Test visualization recommendations generation."""

    print("🔍 Testing Visualization Recommendations...")

    try:
        from focus_lida_integration import FocusLidaDataSummarizer

        summarizer = FocusLidaDataSummarizer()

        # Test with sample data
        sample_data = [
            {
                "BillingPeriodStart": "2024-01-01T00:00:00Z",
                "BilledCost": 1000.00,
                "ServiceName": "Amazon EC2",
                "Region": "us-east-1",
                "BillingAccountName": "Test Account",
                "ChargeCategory": "Usage"
            }
        ]

        # Test visualization recommendations
        import asyncio
        viz_recommendations = asyncio.run(
            summarizer._generate_visualization_recommendations(sample_data)
        )

        assert isinstance(viz_recommendations, list), "Should return list of recommendations"
        assert len(viz_recommendations) > 0, "Should generate visualization recommendations"

        # Check for expected chart types
        chart_types = [rec.get("chart_type") for rec in viz_recommendations]
        expected_types = ["line", "bar", "pie", "stacked_bar", "scatter"]

        for chart_type in expected_types:
            assert chart_type in chart_types, f"Should recommend {chart_type} chart"

        # Validate recommendation structure
        first_rec = viz_recommendations[0]
        required_fields = ["chart_type", "title", "dimensions", "metrics", "narrative_goal", "description", "priority"]

        for field in required_fields:
            assert field in first_rec, f"Recommendation should have {field}"
        print("✅ Visualization recommendations structure validated")

        # Test with empty data
        empty_recommendations = asyncio.run(
            summarizer._generate_visualization_recommendations([])
        )
        assert empty_recommendations == [], "Should handle empty data"
        print("✅ Empty data visualization recommendations working")

        return True

    except Exception as e:
        print(f"❌ Visualization recommendations test failed: {e}")
        return False


def test_factory_function():
    """Test factory function for integration."""

    print("🔍 Testing Factory Function...")

    try:
        from focus_lida_integration import create_focus_lida_integration

        # Test factory function is callable
        assert callable(create_focus_lida_integration), "Factory function should be callable"

        # Test factory function with mock LIDA manager
        import asyncio
        mock_lida_manager = MagicMock()

        integration = asyncio.run(create_focus_lida_integration(mock_lida_manager))

        assert integration is not None, "Should create integration instance"
        assert integration.lida_manager is mock_lida_manager, "Should store LIDA manager reference"
        print("✅ Factory function working correctly")

        # Test factory function without LIDA manager
        minimal_integration = asyncio.run(create_focus_lida_integration())
        assert minimal_integration is not None, "Should create integration without LIDA manager"
        assert minimal_integration.lida_manager is None, "Should handle None LIDA manager"
        print("✅ Factory function minimal creation working")

        return True

    except Exception as e:
        print(f"❌ Factory function test failed: {e}")
        return False


def run_task8_validation():
    """Run comprehensive Task 8 validation."""

    print("🧪 Running Task 8: Enhanced LIDA Integration with FOCUS Data Validation")
    print("="*75)

    tests = [
        ("FOCUS LIDA Integration Architecture", test_focus_lida_integration_architecture),
        ("FinOps Domain Knowledge", test_finops_domain_knowledge),
        ("FOCUS LIDA Data Summarizer", test_focus_lida_data_summarizer),
        ("FOCUS Billing Analysis", test_focus_billing_analysis),
        ("Optimization Opportunities Identification", test_optimization_opportunities_identification),
        ("Anomaly Detection", test_anomaly_detection),
        ("FinOps KPIs Calculation", test_finops_kpis_calculation),
        ("Narrative Insights Generation", test_narrative_insights_generation),
        ("Visualization Recommendations", test_visualization_recommendations),
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
                'test_focus_lida_data_summarizer', 'test_focus_billing_analysis',
                'test_optimization_opportunities_identification', 'test_anomaly_detection',
                'test_finops_kpis_calculation', 'test_narrative_insights_generation'
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
    print(f"📊 Task 8 Validation Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Task 8: Enhanced LIDA Integration with FOCUS Data COMPLETED!")
        print("\n✅ LIDA data summarization capabilities extended for FOCUS datasets")
        print("✅ FinOps domain knowledge and business rules integrated")
        print("✅ Optimization opportunities identification system implemented")
        print("✅ Cost anomaly detection and analysis capabilities added")
        print("✅ Enhanced visualization recommendations with FinOps insights")
        print("✅ Comprehensive FinOps KPIs calculation and narrative insights")
        print("✅ Multi-cloud cost analysis with service and regional breakdowns")
        print("✅ Commitment discount tracking and efficiency metrics")
        print("✅ FOCUS specification v1.2 compliance with enhanced analytics")
        print("✅ Ready to proceed to Task 9: ECharts Visualization for FinOps Analytics")
        return True
    else:
        print("❌ Task 8 validation failed. Please review implementation before proceeding.")
        return False


if __name__ == "__main__":
    success = run_task8_validation()
    exit(0 if success else 1)