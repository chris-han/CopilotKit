"""
FOCUS Sample Data Integration for LIDA Enhanced Manager.

This module implements integration with FOCUS (FinOps Open Cost & Usage Specification)
sample CSV datasets to build core FinOps analytics capabilities. It provides sample
data generation, CSV loading, and FOCUS-compliant data processing.
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import io
import random
from decimal import Decimal

logger = logging.getLogger(__name__)


class FocusChargeCategory(Enum):
    """FOCUS Charge Category values."""
    USAGE = "Usage"
    PURCHASE = "Purchase"
    TAX = "Tax"
    CREDIT = "Credit"
    ADJUSTMENT = "Adjustment"


class FocusCommitmentDiscountCategory(Enum):
    """FOCUS Commitment Discount Category values."""
    SPEND = "Spend"
    USAGE = "Usage"


class FocusRegion(Enum):
    """Common cloud regions for FOCUS data."""
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    EU_CENTRAL_1 = "eu-central-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"
    AP_NORTHEAST_1 = "ap-northeast-1"


@dataclass
class FocusColumnDefinition:
    """Definition of a FOCUS column with metadata."""
    column_name: str
    data_type: str  # string, number, datetime, boolean
    description: str
    category: str  # Account, Billing, Charge, etc.
    required: bool
    capabilities: List[str]  # budgeting, forecasting, cost_optimization, etc.
    example_values: List[str]


@dataclass
class FocusDataRecord:
    """A single FOCUS-compliant data record."""
    # Timeframe columns
    billing_period_start: datetime
    billing_period_end: datetime

    # Account columns
    billing_account_id: str
    billing_account_name: str

    # Charge columns
    billed_cost: Decimal
    charge_category: FocusChargeCategory
    charge_description: str
    charge_frequency: str

    # Service columns
    service_category: str
    service_name: str

    # Resource columns
    resource_id: str
    resource_name: str
    resource_type: str

    # Location columns
    availability_zone: str
    region: str

    # SKU columns
    sku_id: str
    sku_description: str

    # Pricing columns
    pricing_category: str
    pricing_unit: str
    pricing_quantity: Decimal
    unit_price: Decimal

    # Optional commitment discount columns
    commitment_discount_category: Optional[FocusCommitmentDiscountCategory] = None
    commitment_discount_id: Optional[str] = None
    commitment_discount_name: Optional[str] = None


class FocusDataGenerator:
    """Generator for FOCUS-compliant sample data."""

    def __init__(self):
        """Initialize the FOCUS data generator."""
        self.cloud_providers = ["AWS", "Azure", "GCP"]
        self.service_categories = [
            "Compute", "Storage", "Database", "Networking",
            "Analytics", "AI/ML", "Security", "Management"
        ]
        self.resource_types = [
            "Virtual Machine", "Storage Account", "Database Instance",
            "Load Balancer", "Function", "Container", "API Gateway"
        ]

        # Sample service mappings by provider
        self.provider_services = {
            "AWS": {
                "Compute": ["EC2", "Lambda", "ECS", "EKS"],
                "Storage": ["S3", "EBS", "EFS"],
                "Database": ["RDS", "DynamoDB", "Redshift"],
                "Networking": ["VPC", "CloudFront", "Route53"]
            },
            "Azure": {
                "Compute": ["Virtual Machines", "Functions", "Container Instances"],
                "Storage": ["Blob Storage", "Disk Storage", "File Storage"],
                "Database": ["SQL Database", "Cosmos DB", "MySQL"],
                "Networking": ["Virtual Network", "Load Balancer", "CDN"]
            },
            "GCP": {
                "Compute": ["Compute Engine", "Cloud Functions", "GKE"],
                "Storage": ["Cloud Storage", "Persistent Disk"],
                "Database": ["Cloud SQL", "Firestore", "BigQuery"],
                "Networking": ["VPC", "Cloud CDN", "Cloud DNS"]
            }
        }

    def generate_sample_records(
        self,
        num_records: int = 1000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[FocusDataRecord]:
        """
        Generate sample FOCUS-compliant data records.

        Args:
            num_records: Number of records to generate
            start_date: Start date for billing periods
            end_date: End date for billing periods

        Returns:
            List of FOCUS data records
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=90)
        if end_date is None:
            end_date = datetime.now()

        records = []

        for i in range(num_records):
            # Generate random billing period
            period_start = start_date + timedelta(
                days=random.randint(0, (end_date - start_date).days)
            )
            period_end = period_start + timedelta(days=30)  # Monthly billing

            # Select random cloud provider and service
            provider = random.choice(self.cloud_providers)
            service_category = random.choice(self.service_categories)

            if service_category in self.provider_services.get(provider, {}):
                service_name = random.choice(self.provider_services[provider][service_category])
            else:
                service_name = f"{provider} {service_category}"

            # Generate costs with realistic distribution
            base_cost = random.lognormvariate(4, 2)  # Log-normal distribution for realistic cost spread
            billed_cost = Decimal(str(round(base_cost, 2)))

            # Generate pricing details
            pricing_quantity = Decimal(str(random.randint(1, 1000)))
            unit_price = billed_cost / pricing_quantity if pricing_quantity > 0 else Decimal('0.01')

            # Generate resource details
            resource_id = f"resource-{provider.lower()}-{i:06d}"
            resource_name = f"{service_name.replace(' ', '-').lower()}-{random.randint(1000, 9999)}"
            resource_type = random.choice(self.resource_types)

            # Generate location details
            region = random.choice(list(FocusRegion)).value
            availability_zone = f"{region}{random.choice(['a', 'b', 'c'])}"

            # Generate account details
            account_id = f"account-{random.randint(100000, 999999)}"
            account_name = f"{random.choice(['Development', 'Production', 'Staging', 'Testing'])} Account"

            # Generate charge details
            charge_category = random.choice(list(FocusChargeCategory))
            charge_description = f"{service_name} {charge_category.value.lower()}"

            # Generate commitment discount (20% chance)
            commitment_discount_category = None
            commitment_discount_id = None
            commitment_discount_name = None

            if random.random() < 0.2:  # 20% chance of commitment discount
                commitment_discount_category = random.choice(list(FocusCommitmentDiscountCategory))
                commitment_discount_id = f"commitment-{random.randint(1000, 9999)}"
                commitment_discount_name = f"{commitment_discount_category.value} Commitment"

            record = FocusDataRecord(
                billing_period_start=period_start,
                billing_period_end=period_end,
                billing_account_id=account_id,
                billing_account_name=account_name,
                billed_cost=billed_cost,
                charge_category=charge_category,
                charge_description=charge_description,
                charge_frequency="Monthly",
                service_category=service_category,
                service_name=service_name,
                resource_id=resource_id,
                resource_name=resource_name,
                resource_type=resource_type,
                availability_zone=availability_zone,
                region=region,
                sku_id=f"sku-{service_name.replace(' ', '').lower()}-{random.randint(100, 999)}",
                sku_description=f"{service_name} SKU",
                pricing_category="On Demand",
                pricing_unit="Hour" if service_category == "Compute" else "GB-Month",
                pricing_quantity=pricing_quantity,
                unit_price=unit_price,
                commitment_discount_category=commitment_discount_category,
                commitment_discount_id=commitment_discount_id,
                commitment_discount_name=commitment_discount_name
            )

            records.append(record)

        return records


class FocusCSVProcessor:
    """Processor for FOCUS CSV files."""

    def __init__(self):
        """Initialize the FOCUS CSV processor."""
        self.focus_columns = self._define_focus_columns()

    def _define_focus_columns(self) -> Dict[str, FocusColumnDefinition]:
        """Define FOCUS column specifications."""
        return {
            # Timeframe columns
            "BillingPeriodStart": FocusColumnDefinition(
                column_name="BillingPeriodStart",
                data_type="datetime",
                description="The start date and time of the billing period",
                category="Timeframe",
                required=True,
                capabilities=["budgeting", "forecasting", "reporting"],
                example_values=["2024-01-01T00:00:00Z", "2024-02-01T00:00:00Z"]
            ),
            "BillingPeriodEnd": FocusColumnDefinition(
                column_name="BillingPeriodEnd",
                data_type="datetime",
                description="The end date and time of the billing period",
                category="Timeframe",
                required=True,
                capabilities=["budgeting", "forecasting", "reporting"],
                example_values=["2024-01-31T23:59:59Z", "2024-02-29T23:59:59Z"]
            ),

            # Account columns
            "BillingAccountId": FocusColumnDefinition(
                column_name="BillingAccountId",
                data_type="string",
                description="The unique identifier of the billing account",
                category="Account",
                required=True,
                capabilities=["cost_allocation", "reporting"],
                example_values=["123456789012", "account-prod-001"]
            ),
            "BillingAccountName": FocusColumnDefinition(
                column_name="BillingAccountName",
                data_type="string",
                description="The display name of the billing account",
                category="Account",
                required=False,
                capabilities=["reporting", "visualization"],
                example_values=["Production Account", "Development Account"]
            ),

            # Charge columns
            "BilledCost": FocusColumnDefinition(
                column_name="BilledCost",
                data_type="number",
                description="The cost that was charged for this line item",
                category="Charge",
                required=True,
                capabilities=["budgeting", "cost_optimization", "forecasting"],
                example_values=["123.45", "0.50", "1000.00"]
            ),
            "ChargeCategory": FocusColumnDefinition(
                column_name="ChargeCategory",
                data_type="string",
                description="The category of the charge",
                category="Charge",
                required=True,
                capabilities=["cost_optimization", "reporting"],
                example_values=["Usage", "Purchase", "Tax", "Credit"]
            ),

            # Service columns
            "ServiceCategory": FocusColumnDefinition(
                column_name="ServiceCategory",
                data_type="string",
                description="The category of the service",
                category="Service",
                required=False,
                capabilities=["cost_optimization", "resource_management"],
                example_values=["Compute", "Storage", "Database", "Networking"]
            ),
            "ServiceName": FocusColumnDefinition(
                column_name="ServiceName",
                data_type="string",
                description="The name of the service",
                category="Service",
                required=True,
                capabilities=["cost_optimization", "resource_management"],
                example_values=["Amazon EC2", "Azure Virtual Machines", "Google Compute Engine"]
            ),

            # Resource columns
            "ResourceId": FocusColumnDefinition(
                column_name="ResourceId",
                data_type="string",
                description="The unique identifier of the resource",
                category="Resource",
                required=False,
                capabilities=["resource_management", "cost_allocation"],
                example_values=["i-1234567890abcdef0", "vm-production-web-01"]
            ),

            # Location columns
            "Region": FocusColumnDefinition(
                column_name="Region",
                data_type="string",
                description="The geographic region where the resource is located",
                category="Location",
                required=False,
                capabilities=["cost_optimization", "compliance"],
                example_values=["us-east-1", "eu-west-1", "ap-southeast-1"]
            )
        }

    def records_to_csv(self, records: List[FocusDataRecord]) -> str:
        """
        Convert FOCUS records to CSV format.

        Args:
            records: List of FOCUS data records

        Returns:
            CSV content as string
        """
        if not records:
            return ""

        # Define CSV headers based on FOCUS specification
        headers = [
            "BillingPeriodStart", "BillingPeriodEnd", "BillingAccountId", "BillingAccountName",
            "BilledCost", "ChargeCategory", "ChargeDescription", "ChargeFrequency",
            "ServiceCategory", "ServiceName", "ResourceId", "ResourceName", "ResourceType",
            "AvailabilityZone", "Region", "SkuId", "SkuDescription",
            "PricingCategory", "PricingUnit", "PricingQuantity", "UnitPrice",
            "CommitmentDiscountCategory", "CommitmentDiscountId", "CommitmentDiscountName"
        ]

        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(headers)

        # Write data rows
        for record in records:
            row = [
                record.billing_period_start.isoformat(),
                record.billing_period_end.isoformat(),
                record.billing_account_id,
                record.billing_account_name,
                str(record.billed_cost),
                record.charge_category.value,
                record.charge_description,
                record.charge_frequency,
                record.service_category,
                record.service_name,
                record.resource_id,
                record.resource_name,
                record.resource_type,
                record.availability_zone,
                record.region,
                record.sku_id,
                record.sku_description,
                record.pricing_category,
                record.pricing_unit,
                str(record.pricing_quantity),
                str(record.unit_price),
                record.commitment_discount_category.value if record.commitment_discount_category else "",
                record.commitment_discount_id or "",
                record.commitment_discount_name or ""
            ]
            writer.writerow(row)

        return output.getvalue()

    def csv_to_records(self, csv_content: str) -> List[FocusDataRecord]:
        """
        Parse CSV content into FOCUS records.

        Args:
            csv_content: CSV content as string

        Returns:
            List of FOCUS data records
        """
        records = []

        csv_reader = csv.DictReader(io.StringIO(csv_content))

        for row in csv_reader:
            try:
                # Parse charge category
                charge_category = FocusChargeCategory(row.get("ChargeCategory", "Usage"))

                # Parse commitment discount category
                commitment_discount_category = None
                if row.get("CommitmentDiscountCategory"):
                    commitment_discount_category = FocusCommitmentDiscountCategory(
                        row["CommitmentDiscountCategory"]
                    )

                record = FocusDataRecord(
                    billing_period_start=datetime.fromisoformat(row["BillingPeriodStart"].replace('Z', '+00:00')),
                    billing_period_end=datetime.fromisoformat(row["BillingPeriodEnd"].replace('Z', '+00:00')),
                    billing_account_id=row["BillingAccountId"],
                    billing_account_name=row["BillingAccountName"],
                    billed_cost=Decimal(row["BilledCost"]),
                    charge_category=charge_category,
                    charge_description=row["ChargeDescription"],
                    charge_frequency=row["ChargeFrequency"],
                    service_category=row["ServiceCategory"],
                    service_name=row["ServiceName"],
                    resource_id=row["ResourceId"],
                    resource_name=row["ResourceName"],
                    resource_type=row["ResourceType"],
                    availability_zone=row["AvailabilityZone"],
                    region=row["Region"],
                    sku_id=row["SkuId"],
                    sku_description=row["SkuDescription"],
                    pricing_category=row["PricingCategory"],
                    pricing_unit=row["PricingUnit"],
                    pricing_quantity=Decimal(row["PricingQuantity"]),
                    unit_price=Decimal(row["UnitPrice"]),
                    commitment_discount_category=commitment_discount_category,
                    commitment_discount_id=row.get("CommitmentDiscountId") or None,
                    commitment_discount_name=row.get("CommitmentDiscountName") or None
                )

                records.append(record)

            except Exception as exc:
                logger.warning("Failed to parse FOCUS record: %s", exc)
                continue

        return records


class FocusSampleDataIntegration:
    """
    FOCUS Sample Data Integration for LIDA Enhanced Manager.

    This class provides comprehensive integration with FOCUS-compliant sample
    datasets, enabling FinOps analytics capabilities through LIDA Enhanced Manager.
    """

    def __init__(self, lida_manager=None):
        """
        Initialize FOCUS sample data integration.

        Args:
            lida_manager: Optional LIDA Enhanced Manager instance
        """
        self.lida_manager = lida_manager
        self.data_generator = FocusDataGenerator()
        self.csv_processor = FocusCSVProcessor()

        # Sample datasets cache
        self._sample_datasets: Dict[str, List[FocusDataRecord]] = {}
        self._dataset_summaries: Dict[str, Dict[str, Any]] = {}

        logger.info("FocusSampleDataIntegration initialized")

    async def generate_sample_dataset(
        self,
        dataset_name: str,
        num_records: int = 1000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[FocusDataRecord]:
        """
        Generate and cache a sample FOCUS dataset.

        Args:
            dataset_name: Name for the dataset
            num_records: Number of records to generate
            start_date: Start date for billing periods
            end_date: End date for billing periods

        Returns:
            List of FOCUS data records
        """
        try:
            logger.info("Generating FOCUS sample dataset '%s' with %d records", dataset_name, num_records)

            records = self.data_generator.generate_sample_records(
                num_records=num_records,
                start_date=start_date,
                end_date=end_date
            )

            # Cache the dataset
            self._sample_datasets[dataset_name] = records

            # Generate summary
            summary = await self._create_dataset_summary(dataset_name, records)
            self._dataset_summaries[dataset_name] = summary

            logger.info("Generated FOCUS dataset '%s' with %d records", dataset_name, len(records))
            return records

        except Exception as exc:
            logger.error("Failed to generate FOCUS sample dataset: %s", exc)
            raise

    async def load_csv_dataset(
        self,
        dataset_name: str,
        csv_content: str
    ) -> List[FocusDataRecord]:
        """
        Load FOCUS dataset from CSV content.

        Args:
            dataset_name: Name for the dataset
            csv_content: CSV content string

        Returns:
            List of FOCUS data records
        """
        try:
            logger.info("Loading FOCUS dataset '%s' from CSV", dataset_name)

            records = self.csv_processor.csv_to_records(csv_content)

            # Cache the dataset
            self._sample_datasets[dataset_name] = records

            # Generate summary
            summary = await self._create_dataset_summary(dataset_name, records)
            self._dataset_summaries[dataset_name] = summary

            logger.info("Loaded FOCUS dataset '%s' with %d records", dataset_name, len(records))
            return records

        except Exception as exc:
            logger.error("Failed to load FOCUS CSV dataset: %s", exc)
            raise

    async def get_dataset_for_lida(
        self,
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Get FOCUS dataset formatted for LIDA Enhanced Manager.

        Args:
            dataset_name: Name of the dataset

        Returns:
            Dataset formatted for LIDA processing
        """
        try:
            if dataset_name not in self._sample_datasets:
                raise ValueError(f"Dataset '{dataset_name}' not found")

            records = self._sample_datasets[dataset_name]
            summary = self._dataset_summaries.get(dataset_name, {})

            # Convert to LIDA-compatible format
            lida_data = {
                "name": dataset_name,
                "description": f"FOCUS-compliant FinOps dataset with {len(records)} records",
                "type": "focus_finops",
                "columns": self._extract_column_info(records),
                "data_types": self._extract_data_types(records),
                "sample_data": self._convert_to_sample_data(records[:100]),  # Limit sample
                "row_count": len(records),
                "focus_metadata": {
                    "specification_version": "1.2",
                    "charge_categories": list(set(r.charge_category.value for r in records)),
                    "service_categories": list(set(r.service_category for r in records)),
                    "regions": list(set(r.region for r in records)),
                    "billing_accounts": list(set(r.billing_account_id for r in records)),
                    "date_range": {
                        "start": min(r.billing_period_start for r in records).isoformat(),
                        "end": max(r.billing_period_end for r in records).isoformat()
                    }
                },
                "analytics_capabilities": [
                    "cost_analysis", "trend_analysis", "service_breakdown",
                    "regional_comparison", "commitment_tracking", "resource_optimization"
                ],
                "finops_insights": summary.get("finops_insights", [])
            }

            return lida_data

        except Exception as exc:
            logger.error("Failed to format dataset for LIDA: %s", exc)
            raise

    async def get_available_datasets(self) -> List[Dict[str, Any]]:
        """
        Get list of available FOCUS datasets.

        Returns:
            List of dataset information
        """
        datasets = []

        for dataset_name in self._sample_datasets.keys():
            records = self._sample_datasets[dataset_name]
            summary = self._dataset_summaries.get(dataset_name, {})

            dataset_info = {
                "name": dataset_name,
                "record_count": len(records),
                "total_cost": float(sum(r.billed_cost for r in records)),
                "date_range": {
                    "start": min(r.billing_period_start for r in records).isoformat(),
                    "end": max(r.billing_period_end for r in records).isoformat()
                },
                "service_count": len(set(r.service_name for r in records)),
                "account_count": len(set(r.billing_account_id for r in records)),
                "region_count": len(set(r.region for r in records)),
                "focus_compliant": True,
                "analytics_ready": len(records) > 0
            }

            datasets.append(dataset_info)

        return datasets

    async def export_dataset_csv(self, dataset_name: str) -> str:
        """
        Export dataset as CSV content.

        Args:
            dataset_name: Name of the dataset

        Returns:
            CSV content as string
        """
        if dataset_name not in self._sample_datasets:
            raise ValueError(f"Dataset '{dataset_name}' not found")

        records = self._sample_datasets[dataset_name]
        return self.csv_processor.records_to_csv(records)

    # Private helper methods

    async def _create_dataset_summary(
        self,
        dataset_name: str,
        records: List[FocusDataRecord]
    ) -> Dict[str, Any]:
        """Create comprehensive dataset summary."""

        if not records:
            return {}

        # Calculate basic statistics
        total_cost = sum(r.billed_cost for r in records)
        avg_cost = total_cost / len(records)

        # Service analysis
        service_costs = {}
        for record in records:
            service = record.service_name
            if service not in service_costs:
                service_costs[service] = Decimal('0')
            service_costs[service] += record.billed_cost

        # Regional analysis
        regional_costs = {}
        for record in records:
            region = record.region
            if region not in regional_costs:
                regional_costs[region] = Decimal('0')
            regional_costs[region] += record.billed_cost

        # Account analysis
        account_costs = {}
        for record in records:
            account = record.billing_account_name
            if account not in account_costs:
                account_costs[account] = Decimal('0')
            account_costs[account] += record.billed_cost

        # Generate FinOps insights
        finops_insights = []

        # Top service insight
        top_service = max(service_costs.items(), key=lambda x: x[1])
        finops_insights.append(f"Top service by cost: {top_service[0]} (${float(top_service[1]):,.2f})")

        # Regional cost distribution
        top_region = max(regional_costs.items(), key=lambda x: x[1])
        finops_insights.append(f"Highest cost region: {top_region[0]} (${float(top_region[1]):,.2f})")

        # Cost optimization opportunities
        usage_records = [r for r in records if r.charge_category == FocusChargeCategory.USAGE]
        if len(usage_records) > 0:
            avg_usage_cost = sum(r.billed_cost for r in usage_records) / len(usage_records)
            finops_insights.append(f"Average usage cost per record: ${float(avg_usage_cost):.2f}")

        # Commitment discount analysis
        discount_records = [r for r in records if r.commitment_discount_category is not None]
        if discount_records:
            discount_percentage = len(discount_records) / len(records) * 100
            finops_insights.append(f"Commitment discount coverage: {discount_percentage:.1f}% of records")

        return {
            "total_cost": float(total_cost),
            "average_cost": float(avg_cost),
            "record_count": len(records),
            "service_breakdown": {k: float(v) for k, v in service_costs.items()},
            "regional_breakdown": {k: float(v) for k, v in regional_costs.items()},
            "account_breakdown": {k: float(v) for k, v in account_costs.items()},
            "charge_category_breakdown": {
                category.value: len([r for r in records if r.charge_category == category])
                for category in FocusChargeCategory
            },
            "finops_insights": finops_insights,
            "date_range": {
                "start": min(r.billing_period_start for r in records).isoformat(),
                "end": max(r.billing_period_end for r in records).isoformat()
            }
        }

    def _extract_column_info(self, records: List[FocusDataRecord]) -> List[str]:
        """Extract column names from records."""
        if not records:
            return []

        # Get column names from FOCUS specification
        return [
            "BillingPeriodStart", "BillingPeriodEnd", "BillingAccountId", "BillingAccountName",
            "BilledCost", "ChargeCategory", "ServiceCategory", "ServiceName",
            "ResourceId", "ResourceName", "Region", "PricingUnit", "PricingQuantity"
        ]

    def _extract_data_types(self, records: List[FocusDataRecord]) -> Dict[str, str]:
        """Extract data types for columns."""
        return {
            "BillingPeriodStart": "datetime",
            "BillingPeriodEnd": "datetime",
            "BillingAccountId": "categorical",
            "BillingAccountName": "categorical",
            "BilledCost": "numeric",
            "ChargeCategory": "categorical",
            "ServiceCategory": "categorical",
            "ServiceName": "categorical",
            "ResourceId": "categorical",
            "ResourceName": "categorical",
            "Region": "categorical",
            "PricingUnit": "categorical",
            "PricingQuantity": "numeric"
        }

    def _convert_to_sample_data(self, records: List[FocusDataRecord]) -> List[Dict[str, Any]]:
        """Convert records to sample data format."""
        sample_data = []

        for record in records:
            sample_record = {
                "BillingPeriodStart": record.billing_period_start.isoformat(),
                "BillingPeriodEnd": record.billing_period_end.isoformat(),
                "BillingAccountId": record.billing_account_id,
                "BillingAccountName": record.billing_account_name,
                "BilledCost": float(record.billed_cost),
                "ChargeCategory": record.charge_category.value,
                "ServiceCategory": record.service_category,
                "ServiceName": record.service_name,
                "ResourceId": record.resource_id,
                "ResourceName": record.resource_name,
                "Region": record.region,
                "PricingUnit": record.pricing_unit,
                "PricingQuantity": float(record.pricing_quantity)
            }
            sample_data.append(sample_record)

        return sample_data


# Factory function for integration
async def create_focus_sample_integration(lida_manager=None) -> FocusSampleDataIntegration:
    """
    Factory function to create FocusSampleDataIntegration instance.

    Args:
        lida_manager: Optional LIDA Enhanced Manager instance

    Returns:
        Configured FocusSampleDataIntegration instance
    """
    integration = FocusSampleDataIntegration(lida_manager)
    logger.info("Created FocusSampleDataIntegration for FinOps analytics")
    return integration