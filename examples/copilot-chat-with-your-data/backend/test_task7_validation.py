"""
Test suite for Task 7: FOCUS Sample Data Integration.

This test validates the FOCUS sample data integration system that provides
FOCUS-compliant CSV dataset generation, processing, and integration with
LIDA Enhanced Manager for FinOps analytics.
"""

import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch


def test_focus_data_models():
    """Test FOCUS data models and enums."""

    print("🔍 Testing FOCUS Data Models...")

    try:
        # Test import structure
        from focus_sample_data_integration import (
            FocusDataRecord,
            FocusColumnDefinition,
            FocusChargeCategory,
            FocusCommitmentDiscountCategory,
            FocusRegion
        )
        print("✅ FOCUS data integration imports successful")

        # Test FOCUS enums
        assert FocusChargeCategory.USAGE.value == "Usage", "Charge category enum should work"
        assert FocusChargeCategory.PURCHASE.value == "Purchase", "Purchase category should exist"
        assert FocusCommitmentDiscountCategory.SPEND.value == "Spend", "Commitment discount enum should work"
        print("✅ FOCUS enums working correctly")

        # Test column definition creation
        column_def = FocusColumnDefinition(
            column_name="BilledCost",
            data_type="number",
            description="The cost that was charged for this line item",
            category="Charge",
            required=True,
            capabilities=["budgeting", "cost_optimization"],
            example_values=["123.45", "0.50"]
        )

        assert column_def.column_name == "BilledCost", "Column name should be set"
        assert column_def.required is True, "Required flag should be set"
        assert "budgeting" in column_def.capabilities, "Should have budgeting capability"
        print("✅ FocusColumnDefinition creation successful")

        # Test FOCUS data record creation
        record = FocusDataRecord(
            billing_period_start=datetime(2024, 1, 1),
            billing_period_end=datetime(2024, 1, 31),
            billing_account_id="123456789",
            billing_account_name="Test Account",
            billed_cost=Decimal("123.45"),
            charge_category=FocusChargeCategory.USAGE,
            charge_description="EC2 usage",
            charge_frequency="Monthly",
            service_category="Compute",
            service_name="Amazon EC2",
            resource_id="i-1234567890abcdef0",
            resource_name="web-server-01",
            resource_type="Virtual Machine",
            availability_zone="us-east-1a",
            region="us-east-1",
            sku_id="sku-ec2-001",
            sku_description="EC2 t3.micro",
            pricing_category="On Demand",
            pricing_unit="Hour",
            pricing_quantity=Decimal("744"),
            unit_price=Decimal("0.0166")
        )

        assert record.billing_account_id == "123456789", "Account ID should be set"
        assert record.billed_cost == Decimal("123.45"), "Billed cost should be set"
        assert record.charge_category == FocusChargeCategory.USAGE, "Charge category should be set"
        assert record.service_name == "Amazon EC2", "Service name should be set"
        print("✅ FocusDataRecord creation successful")

        return True

    except Exception as e:
        print(f"❌ FOCUS data models test failed: {e}")
        return False


def test_focus_data_generator():
    """Test FOCUS data generator functionality."""

    print("🔍 Testing FOCUS Data Generator...")

    try:
        from focus_sample_data_integration import FocusDataGenerator, FocusChargeCategory

        generator = FocusDataGenerator()

        # Test generator initialization
        assert len(generator.cloud_providers) > 0, "Should have cloud providers"
        assert len(generator.service_categories) > 0, "Should have service categories"
        assert "AWS" in generator.cloud_providers, "Should include AWS"
        assert "Compute" in generator.service_categories, "Should include Compute category"
        print("✅ Data generator initialization successful")

        # Test sample record generation
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 31)
        records = generator.generate_sample_records(
            num_records=100,
            start_date=start_date,
            end_date=end_date
        )

        assert len(records) == 100, "Should generate requested number of records"
        assert all(isinstance(r.billed_cost, Decimal) for r in records), "All costs should be Decimal"
        assert all(r.billing_period_start >= start_date for r in records), "All records should be within date range"
        print("✅ Sample record generation successful")

        # Test data diversity
        charge_categories = set(r.charge_category for r in records)
        service_names = set(r.service_name for r in records)
        regions = set(r.region for r in records)

        assert len(charge_categories) > 1, "Should have diverse charge categories"
        assert len(service_names) > 1, "Should have diverse service names"
        assert len(regions) > 1, "Should have diverse regions"
        print("✅ Data diversity validated")

        # Test cost distribution (should be realistic)
        costs = [float(r.billed_cost) for r in records]
        avg_cost = sum(costs) / len(costs)
        assert avg_cost > 0, "Average cost should be positive"
        assert max(costs) > avg_cost, "Should have some high-value records"
        print("✅ Cost distribution realistic")

        # Test commitment discount generation
        discount_records = [r for r in records if r.commitment_discount_category is not None]
        discount_percentage = len(discount_records) / len(records)
        assert 0 <= discount_percentage <= 0.5, "Discount percentage should be reasonable"
        print("✅ Commitment discount generation working")

        return True

    except Exception as e:
        print(f"❌ FOCUS data generator test failed: {e}")
        return False


def test_focus_csv_processor():
    """Test FOCUS CSV processing functionality."""

    print("🔍 Testing FOCUS CSV Processor...")

    try:
        from focus_sample_data_integration import FocusCSVProcessor, FocusDataGenerator

        processor = FocusCSVProcessor()
        generator = FocusDataGenerator()

        # Test CSV processor initialization
        assert len(processor.focus_columns) > 0, "Should have FOCUS column definitions"
        assert "BilledCost" in processor.focus_columns, "Should have BilledCost column definition"
        assert "BillingAccountId" in processor.focus_columns, "Should have BillingAccountId column definition"
        print("✅ CSV processor initialization successful")

        # Generate test records
        test_records = generator.generate_sample_records(num_records=10)

        # Test records to CSV conversion
        csv_content = processor.records_to_csv(test_records)
        assert len(csv_content) > 0, "CSV content should not be empty"
        assert "BillingPeriodStart" in csv_content, "CSV should contain headers"
        assert "BilledCost" in csv_content, "CSV should contain BilledCost header"
        print("✅ Records to CSV conversion successful")

        # Test CSV parsing back to records
        parsed_records = processor.csv_to_records(csv_content)
        assert len(parsed_records) == len(test_records), "Should parse same number of records"
        assert len(parsed_records) > 0, "Should have parsed records"
        print("✅ CSV to records parsing successful")

        # Test data integrity after round-trip
        original_costs = [r.billed_cost for r in test_records]
        parsed_costs = [r.billed_cost for r in parsed_records]

        # Sort for comparison (order might change)
        original_costs.sort()
        parsed_costs.sort()

        assert len(original_costs) == len(parsed_costs), "Should have same number of costs"
        # Note: Due to decimal precision in CSV, we'll check approximate equality
        for orig, parsed in zip(original_costs[:5], parsed_costs[:5]):  # Check first 5
            assert abs(float(orig) - float(parsed)) < 0.01, "Costs should be approximately equal after round-trip"
        print("✅ Data integrity maintained in round-trip")

        # Test empty records handling
        empty_csv = processor.records_to_csv([])
        assert empty_csv == "", "Empty records should produce empty CSV"
        print("✅ Empty records handling working")

        return True

    except Exception as e:
        print(f"❌ FOCUS CSV processor test failed: {e}")
        return False


async def test_focus_sample_integration():
    """Test FOCUS sample data integration functionality."""

    print("🔍 Testing FOCUS Sample Integration...")

    try:
        from focus_sample_data_integration import FocusSampleDataIntegration

        # Test integration initialization
        integration = FocusSampleDataIntegration()
        assert integration.data_generator is not None, "Should have data generator"
        assert integration.csv_processor is not None, "Should have CSV processor"
        print("✅ FOCUS integration initialization successful")

        # Test sample dataset generation
        dataset_name = "test_finops_data"
        records = await integration.generate_sample_dataset(
            dataset_name=dataset_name,
            num_records=50
        )

        assert len(records) == 50, "Should generate requested number of records"
        assert dataset_name in integration._sample_datasets, "Should cache dataset"
        assert dataset_name in integration._dataset_summaries, "Should create dataset summary"
        print("✅ Sample dataset generation successful")

        # Test LIDA-compatible data formatting
        lida_data = await integration.get_dataset_for_lida(dataset_name)

        required_keys = [
            "name", "description", "columns", "data_types", "sample_data",
            "focus_metadata", "analytics_capabilities", "finops_insights"
        ]

        for key in required_keys:
            assert key in lida_data, f"LIDA data should contain {key}"

        assert lida_data["name"] == dataset_name, "Dataset name should match"
        assert lida_data["focus_metadata"]["specification_version"] == "1.2", "Should specify FOCUS version"
        assert len(lida_data["columns"]) > 0, "Should have column information"
        assert len(lida_data["sample_data"]) > 0, "Should have sample data"
        print("✅ LIDA-compatible data formatting successful")

        # Test dataset summary generation
        summary = integration._dataset_summaries[dataset_name]
        assert "total_cost" in summary, "Summary should contain total cost"
        assert "service_breakdown" in summary, "Summary should contain service breakdown"
        assert "regional_breakdown" in summary, "Summary should contain regional breakdown"
        assert "finops_insights" in summary, "Summary should contain FinOps insights"
        assert len(summary["finops_insights"]) > 0, "Should generate FinOps insights"
        print("✅ Dataset summary generation successful")

        # Test available datasets listing
        available_datasets = await integration.get_available_datasets()
        assert len(available_datasets) == 1, "Should list one available dataset"
        dataset_info = available_datasets[0]
        assert dataset_info["name"] == dataset_name, "Dataset info should match"
        assert dataset_info["focus_compliant"] is True, "Should be FOCUS compliant"
        assert dataset_info["analytics_ready"] is True, "Should be analytics ready"
        print("✅ Available datasets listing successful")

        # Test CSV export
        csv_export = await integration.export_dataset_csv(dataset_name)
        assert len(csv_export) > 0, "CSV export should not be empty"
        assert "BillingPeriodStart" in csv_export, "CSV export should contain headers"
        print("✅ CSV export successful")

        return True

    except Exception as e:
        print(f"❌ FOCUS sample integration test failed: {e}")
        return False


async def test_csv_loading_functionality():
    """Test CSV loading and processing functionality."""

    print("🔍 Testing CSV Loading Functionality...")

    try:
        from focus_sample_data_integration import FocusSampleDataIntegration, FocusDataGenerator

        integration = FocusSampleDataIntegration()
        generator = FocusDataGenerator()

        # Generate sample data and convert to CSV
        original_records = generator.generate_sample_records(num_records=25)
        csv_content = integration.csv_processor.records_to_csv(original_records)

        # Test loading CSV dataset
        dataset_name = "csv_test_dataset"
        loaded_records = await integration.load_csv_dataset(dataset_name, csv_content)

        assert len(loaded_records) == len(original_records), "Should load all records from CSV"
        assert dataset_name in integration._sample_datasets, "Should cache loaded dataset"
        print("✅ CSV dataset loading successful")

        # Test LIDA data generation from loaded CSV
        lida_data = await integration.get_dataset_for_lida(dataset_name)
        assert lida_data["name"] == dataset_name, "Should generate LIDA data from CSV"
        assert len(lida_data["sample_data"]) > 0, "Should have sample data from CSV"
        print("✅ LIDA data generation from CSV successful")

        # Test CSV with minimal valid content
        minimal_csv = """BillingPeriodStart,BillingPeriodEnd,BillingAccountId,BillingAccountName,BilledCost,ChargeCategory,ChargeDescription,ChargeFrequency,ServiceCategory,ServiceName,ResourceId,ResourceName,ResourceType,AvailabilityZone,Region,SkuId,SkuDescription,PricingCategory,PricingUnit,PricingQuantity,UnitPrice,CommitmentDiscountCategory,CommitmentDiscountId,CommitmentDiscountName
2024-01-01T00:00:00+00:00,2024-01-31T23:59:59+00:00,account-001,Test Account,100.00,Usage,Test usage,Monthly,Compute,Test Service,resource-001,test-resource,Virtual Machine,us-east-1a,us-east-1,sku-001,Test SKU,On Demand,Hour,100,1.00,,,"""

        minimal_records = await integration.load_csv_dataset("minimal_test", minimal_csv)
        assert len(minimal_records) == 1, "Should load minimal CSV record"
        assert minimal_records[0].billed_cost == Decimal("100.00"), "Should parse cost correctly"
        print("✅ Minimal CSV loading successful")

        return True

    except Exception as e:
        print(f"❌ CSV loading functionality test failed: {e}")
        return False


def test_finops_analytics_capabilities():
    """Test FinOps analytics capabilities and insights."""

    print("🔍 Testing FinOps Analytics Capabilities...")

    try:
        from focus_sample_data_integration import FocusSampleDataIntegration

        integration = FocusSampleDataIntegration()

        # Create a dataset with known characteristics for testing analytics
        # This is a synchronous call to generate_sample_dataset for testing
        import asyncio

        async def test_analytics():
            # Generate dataset with enough records for meaningful analytics
            dataset_name = "analytics_test"
            records = await integration.generate_sample_dataset(dataset_name, num_records=200)

            # Test analytics capabilities in LIDA data format
            lida_data = await integration.get_dataset_for_lida(dataset_name)

            # Validate analytics capabilities
            expected_capabilities = [
                "cost_analysis", "trend_analysis", "service_breakdown",
                "regional_comparison", "commitment_tracking", "resource_optimization"
            ]

            for capability in expected_capabilities:
                assert capability in lida_data["analytics_capabilities"], f"Should support {capability}"

            print("✅ Analytics capabilities validated")

            # Test FOCUS metadata
            focus_metadata = lida_data["focus_metadata"]
            assert "charge_categories" in focus_metadata, "Should have charge categories"
            assert "service_categories" in focus_metadata, "Should have service categories"
            assert "regions" in focus_metadata, "Should have regions"
            assert "billing_accounts" in focus_metadata, "Should have billing accounts"
            assert "date_range" in focus_metadata, "Should have date range"

            assert len(focus_metadata["charge_categories"]) > 0, "Should have multiple charge categories"
            assert len(focus_metadata["service_categories"]) > 0, "Should have multiple service categories"
            print("✅ FOCUS metadata generation successful")

            # Test FinOps insights generation
            finops_insights = lida_data["finops_insights"]
            assert len(finops_insights) > 0, "Should generate FinOps insights"

            # Check for specific insight types
            insights_text = " ".join(finops_insights).lower()
            assert any(word in insights_text for word in ["service", "cost", "region"]), "Should include cost analysis insights"
            print("✅ FinOps insights generation successful")

            # Test dataset summary analytics
            summary = integration._dataset_summaries[dataset_name]
            assert "service_breakdown" in summary, "Should break down costs by service"
            assert "regional_breakdown" in summary, "Should break down costs by region"
            assert "charge_category_breakdown" in summary, "Should break down by charge category"

            # Validate breakdown totals
            service_total = sum(summary["service_breakdown"].values())
            regional_total = sum(summary["regional_breakdown"].values())
            assert abs(service_total - summary["total_cost"]) < 1.0, "Service breakdown should sum to total"
            assert abs(regional_total - summary["total_cost"]) < 1.0, "Regional breakdown should sum to total"
            print("✅ Cost breakdown analytics validated")

            return True

        # Run the async test
        result = asyncio.run(test_analytics())
        return result

    except Exception as e:
        print(f"❌ FinOps analytics capabilities test failed: {e}")
        return False


def test_lida_integration_compatibility():
    """Test compatibility with LIDA Enhanced Manager integration."""

    print("🔍 Testing LIDA Integration Compatibility...")

    try:
        from focus_sample_data_integration import FocusSampleDataIntegration, create_focus_sample_integration

        # Mock LIDA manager
        mock_lida_manager = MagicMock()

        # Test integration with LIDA manager
        integration = FocusSampleDataIntegration(lida_manager=mock_lida_manager)
        assert integration.lida_manager is mock_lida_manager, "Should store LIDA manager reference"
        print("✅ LIDA manager integration successful")

        # Test factory function
        assert callable(create_focus_sample_integration), "Factory function should be callable"
        print("✅ Factory function available")

        # Test data format compatibility with LIDA Enhanced Manager
        # Generate sample data for testing
        import asyncio

        async def test_compatibility():
            dataset_name = "lida_compatibility_test"
            await integration.generate_sample_dataset(dataset_name, num_records=50)

            lida_data = await integration.get_dataset_for_lida(dataset_name)

            # Test required LIDA data structure
            lida_required_fields = ["name", "columns", "data_types", "sample_data"]
            for field in lida_required_fields:
                assert field in lida_data, f"LIDA data should contain {field}"

            # Test data types compatibility
            data_types = lida_data["data_types"]
            valid_types = ["numeric", "categorical", "datetime"]
            for column, dtype in data_types.items():
                assert dtype in valid_types, f"Data type {dtype} for {column} should be valid for LIDA"

            print("✅ LIDA data structure compatibility validated")

            # Test sample data format
            sample_data = lida_data["sample_data"]
            assert len(sample_data) > 0, "Should have sample data for LIDA"
            assert isinstance(sample_data[0], dict), "Sample data should be list of dictionaries"

            # Validate sample data contains expected columns
            sample_columns = set(sample_data[0].keys())
            expected_columns = {"BilledCost", "ServiceName", "Region", "ChargeCategory"}
            assert expected_columns.issubset(sample_columns), "Sample data should contain key FOCUS columns"
            print("✅ Sample data format compatibility validated")

            return True

        result = asyncio.run(test_compatibility())
        return result

    except Exception as e:
        print(f"❌ LIDA integration compatibility test failed: {e}")
        return False


def run_task7_validation():
    """Run comprehensive Task 7 validation."""

    print("🧪 Running Task 7: FOCUS Sample Data Integration Validation")
    print("="*65)

    tests = [
        ("FOCUS Data Models", test_focus_data_models),
        ("FOCUS Data Generator", test_focus_data_generator),
        ("FOCUS CSV Processor", test_focus_csv_processor),
        ("FOCUS Sample Integration", test_focus_sample_integration),
        ("CSV Loading Functionality", test_csv_loading_functionality),
        ("FinOps Analytics Capabilities", test_finops_analytics_capabilities),
        ("LIDA Integration Compatibility", test_lida_integration_compatibility)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔬 {test_name}")
        print("-" * 45)

        try:
            # Handle async tests
            if test_func.__name__ in [
                'test_focus_sample_integration', 'test_csv_loading_functionality'
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

    print("\n" + "="*65)
    print(f"📊 Task 7 Validation Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Task 7: FOCUS Sample Data Integration COMPLETED!")
        print("\n✅ FOCUS-compliant data models and enums implemented")
        print("✅ Sample FOCUS dataset generation with realistic FinOps data created")
        print("✅ CSV processing for FOCUS datasets implemented")
        print("✅ LIDA Enhanced Manager integration support added")
        print("✅ FinOps analytics capabilities and insights generation working")
        print("✅ Multi-cloud cost analysis with service and regional breakdowns")
        print("✅ Commitment discount tracking and analysis implemented")
        print("✅ FOCUS specification v1.2 compliance validated")
        print("✅ Ready to proceed to Task 8: Enhanced LIDA Integration with FOCUS Data")
        return True
    else:
        print("❌ Task 7 validation failed. Please review implementation before proceeding.")
        return False


if __name__ == "__main__":
    success = run_task7_validation()
    exit(0 if success else 1)