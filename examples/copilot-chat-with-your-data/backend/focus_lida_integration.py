"""
Enhanced LIDA Integration with FOCUS Data.

This module extends LIDA's data summarization capabilities specifically for
FOCUS-compliant datasets, adding FinOps domain knowledge, optimization
opportunities identification, and specialized insights for cloud cost analysis.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from decimal import Decimal
import statistics

logger = logging.getLogger(__name__)


class FinOpsOptimizationType(Enum):
    """Types of FinOps optimization opportunities."""
    RIGHTSIZING = "rightsizing"
    COMMITMENT_OPPORTUNITY = "commitment_opportunity"
    UNUSED_RESOURCES = "unused_resources"
    ZOMBIE_RESOURCES = "zombie_resources"
    REGIONAL_OPTIMIZATION = "regional_optimization"
    SERVICE_CONSOLIDATION = "service_consolidation"
    SCHEDULING_OPTIMIZATION = "scheduling_optimization"


class FinOpsAnomalyType(Enum):
    """Types of FinOps anomalies to detect."""
    COST_SPIKE = "cost_spike"
    UNUSUAL_PATTERN = "unusual_pattern"
    MISSING_DISCOUNTS = "missing_discounts"
    ORPHANED_RESOURCES = "orphaned_resources"
    INEFFICIENT_USAGE = "inefficient_usage"


@dataclass
class FinOpsOptimizationOpportunity:
    """FinOps optimization opportunity with detailed analysis."""
    opportunity_id: str
    optimization_type: FinOpsOptimizationType
    title: str
    description: str

    # Impact analysis
    potential_savings_monthly: Decimal
    confidence_score: float  # 0.0-1.0
    implementation_effort: str  # low, medium, high

    # Affected resources
    affected_services: List[str]
    affected_accounts: List[str]
    affected_regions: List[str]

    # Recommendations
    recommended_actions: List[str]
    implementation_timeline: str

    # Supporting data
    supporting_evidence: Dict[str, Any]
    created_at: datetime


@dataclass
class FinOpsAnomaly:
    """FinOps anomaly detection result."""
    anomaly_id: str
    anomaly_type: FinOpsAnomalyType
    severity: str  # low, medium, high, critical
    title: str
    description: str

    # Affected scope
    affected_period_start: datetime
    affected_period_end: datetime
    affected_services: List[str]
    affected_accounts: List[str]

    # Anomaly metrics
    baseline_value: Decimal
    anomalous_value: Decimal
    deviation_percentage: float

    # Investigation guidance
    investigation_suggestions: List[str]
    related_opportunities: List[str]  # opportunity IDs

    detected_at: datetime


@dataclass
class FocusEnhancedSummary:
    """Enhanced LIDA summary with FOCUS-specific insights."""
    # Base LIDA summary data
    base_summary: Dict[str, Any]

    # FOCUS-specific insights
    billing_accounts_analysis: Dict[str, Any]
    service_distribution_analysis: Dict[str, Any]
    charge_categories_analysis: Dict[str, Any]
    cost_trends_analysis: Dict[str, Any]
    commitment_discounts_analysis: Dict[str, Any]
    regional_analysis: Dict[str, Any]

    # FinOps domain knowledge
    optimization_opportunities: List[FinOpsOptimizationOpportunity]
    anomaly_candidates: List[FinOpsAnomaly]
    finops_kpis: Dict[str, float]
    cost_efficiency_metrics: Dict[str, float]

    # Enhanced insights for LIDA
    finops_narrative_insights: List[str]
    visualization_recommendations: List[Dict[str, Any]]
    drill_down_suggestions: List[Dict[str, Any]]

    # Metadata
    focus_specification_version: str
    analysis_timestamp: datetime


class FinOpsDomainKnowledge:
    """FinOps domain knowledge and business rules."""

    def __init__(self):
        """Initialize FinOps domain knowledge."""
        self.cost_thresholds = {
            'high_cost_service': 10000.0,  # Monthly cost threshold
            'anomaly_deviation': 30.0,  # Percentage deviation for anomaly detection
            'rightsizing_threshold': 20.0,  # Utilization threshold for rightsizing
            'commitment_savings_threshold': 15.0  # Minimum savings percentage for commitment recommendations
        }

        self.service_categories = {
            'compute': ['EC2', 'Virtual Machines', 'Compute Engine', 'Lambda', 'Functions'],
            'storage': ['S3', 'Blob Storage', 'Cloud Storage', 'EBS', 'Disk Storage'],
            'database': ['RDS', 'SQL Database', 'Cloud SQL', 'DynamoDB', 'Cosmos DB'],
            'networking': ['VPC', 'Virtual Network', 'CloudFront', 'CDN', 'Load Balancer']
        }

        self.optimization_patterns = {
            'unused_resources': {
                'compute': {'min_utilization': 5.0, 'observation_days': 7},
                'storage': {'min_access_frequency': 1, 'observation_days': 30},
                'database': {'min_connections': 1, 'observation_days': 14}
            },
            'rightsizing': {
                'compute': {'max_utilization': 80.0, 'min_utilization': 20.0},
                'database': {'max_utilization': 85.0, 'min_utilization': 15.0}
            }
        }

    def identify_service_category(self, service_name: str) -> str:
        """Identify the category of a service."""
        service_lower = service_name.lower()

        for category, services in self.service_categories.items():
            if any(svc.lower() in service_lower for svc in services):
                return category

        return 'other'

    def calculate_efficiency_score(self, cost_data: Dict[str, Any]) -> float:
        """Calculate cost efficiency score based on FinOps best practices."""
        efficiency_factors = []

        # Commitment discount usage
        if 'commitment_coverage' in cost_data:
            commitment_score = min(cost_data['commitment_coverage'] / 70.0, 1.0) * 0.3
            efficiency_factors.append(commitment_score)

        # Service distribution (avoid concentration risk)
        if 'service_distribution_entropy' in cost_data:
            distribution_score = min(cost_data['service_distribution_entropy'] / 2.0, 1.0) * 0.2
            efficiency_factors.append(distribution_score)

        # Regional optimization
        if 'regional_cost_variance' in cost_data:
            regional_score = max(0, 1.0 - cost_data['regional_cost_variance'] / 50.0) * 0.2
            efficiency_factors.append(regional_score)

        # Cost trend stability
        if 'cost_trend_stability' in cost_data:
            stability_score = cost_data['cost_trend_stability'] * 0.3
            efficiency_factors.append(stability_score)

        return sum(efficiency_factors) if efficiency_factors else 0.5


class FocusLidaDataSummarizer:
    """Enhanced LIDA data summarizer for FOCUS datasets."""

    def __init__(self, lida_manager=None):
        """
        Initialize FOCUS LIDA data summarizer.

        Args:
            lida_manager: Optional LIDA Enhanced Manager instance
        """
        self.lida_manager = lida_manager
        self.finops_domain = FinOpsDomainKnowledge()

        # Load FOCUS field definitions
        self.focus_field_definitions = self._load_focus_field_definitions()

        logger.info("FocusLidaDataSummarizer initialized")

    def _load_focus_field_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load FOCUS field definitions for enhanced analysis."""
        return {
            'BilledCost': {
                'type': 'numeric',
                'aggregation': 'sum',
                'description': 'The cost charged for this line item',
                'finops_category': 'cost',
                'visualization_priority': 'high'
            },
            'ChargeCategory': {
                'type': 'categorical',
                'description': 'The category of the charge',
                'finops_category': 'billing',
                'visualization_priority': 'high',
                'values': ['Usage', 'Purchase', 'Tax', 'Credit', 'Adjustment']
            },
            'ServiceName': {
                'type': 'categorical',
                'description': 'The name of the service',
                'finops_category': 'resource',
                'visualization_priority': 'high'
            },
            'Region': {
                'type': 'categorical',
                'description': 'Geographic region',
                'finops_category': 'location',
                'visualization_priority': 'medium'
            },
            'BillingAccountId': {
                'type': 'categorical',
                'description': 'Billing account identifier',
                'finops_category': 'account',
                'visualization_priority': 'medium'
            },
            'ResourceId': {
                'type': 'categorical',
                'description': 'Resource identifier',
                'finops_category': 'resource',
                'visualization_priority': 'low'
            }
        }

    async def summarize_focus_data(
        self,
        focus_data: Dict[str, Any]
    ) -> FocusEnhancedSummary:
        """
        Create enhanced summary for FOCUS datasets with FinOps insights.

        Args:
            focus_data: FOCUS dataset formatted for LIDA

        Returns:
            Enhanced FOCUS summary with FinOps domain knowledge
        """
        try:
            # Create base LIDA summary
            base_summary = await self._create_base_summary(focus_data)

            # Extract FOCUS records for detailed analysis
            sample_data = focus_data.get('sample_data', [])

            # Perform FOCUS-specific analysis
            billing_accounts = await self._analyze_billing_accounts(sample_data)
            service_distribution = await self._analyze_service_distribution(sample_data)
            charge_categories = await self._analyze_charge_categories(sample_data)
            cost_trends = await self._analyze_cost_trends(sample_data)
            commitment_discounts = await self._analyze_commitment_discounts(sample_data)
            regional_analysis = await self._analyze_regional_distribution(sample_data)

            # Apply FinOps domain knowledge
            optimization_opportunities = await self._identify_optimization_opportunities(sample_data)
            anomaly_candidates = await self._identify_potential_anomalies(sample_data)
            finops_kpis = await self._calculate_finops_kpis(sample_data)
            cost_efficiency = await self._calculate_cost_efficiency_metrics(sample_data)

            # Generate enhanced insights for LIDA
            narrative_insights = await self._generate_finops_narrative_insights(
                sample_data, optimization_opportunities, anomaly_candidates
            )
            viz_recommendations = await self._generate_visualization_recommendations(sample_data)
            drill_down_suggestions = await self._generate_drill_down_suggestions(sample_data)

            enhanced_summary = FocusEnhancedSummary(
                base_summary=base_summary,
                billing_accounts_analysis=billing_accounts,
                service_distribution_analysis=service_distribution,
                charge_categories_analysis=charge_categories,
                cost_trends_analysis=cost_trends,
                commitment_discounts_analysis=commitment_discounts,
                regional_analysis=regional_analysis,
                optimization_opportunities=optimization_opportunities,
                anomaly_candidates=anomaly_candidates,
                finops_kpis=finops_kpis,
                cost_efficiency_metrics=cost_efficiency,
                finops_narrative_insights=narrative_insights,
                visualization_recommendations=viz_recommendations,
                drill_down_suggestions=drill_down_suggestions,
                focus_specification_version="1.2",
                analysis_timestamp=datetime.now()
            )

            logger.info("Enhanced FOCUS summary created with %d optimization opportunities and %d anomalies",
                       len(optimization_opportunities), len(anomaly_candidates))

            return enhanced_summary

        except Exception as exc:
            logger.error("Failed to create FOCUS enhanced summary: %s", exc)
            raise

    async def _create_base_summary(self, focus_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create base LIDA summary for FOCUS data."""

        if self.lida_manager:
            # Use LIDA manager if available
            return await self.lida_manager.summarize_data(focus_data)
        else:
            # Create basic summary
            return {
                'name': focus_data.get('name', 'FOCUS Dataset'),
                'columns': focus_data.get('columns', []),
                'data_types': focus_data.get('data_types', {}),
                'row_count': focus_data.get('row_count', 0),
                'insights': ['FOCUS-compliant dataset ready for FinOps analysis']
            }

    async def _analyze_billing_accounts(self, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze billing accounts distribution and costs."""
        if not sample_data:
            return {}

        account_costs = {}
        account_records = {}

        for record in sample_data:
            account_id = record.get('BillingAccountId', 'unknown')
            account_name = record.get('BillingAccountName', account_id)
            cost = float(record.get('BilledCost', 0))

            if account_id not in account_costs:
                account_costs[account_id] = {'cost': 0, 'name': account_name, 'records': 0}

            account_costs[account_id]['cost'] += cost
            account_costs[account_id]['records'] += 1

        # Calculate statistics
        total_cost = sum(acc['cost'] for acc in account_costs.values())
        total_accounts = len(account_costs)

        # Identify top accounts
        top_accounts = sorted(account_costs.items(), key=lambda x: x[1]['cost'], reverse=True)[:5]

        return {
            'total_accounts': total_accounts,
            'total_cost': total_cost,
            'average_cost_per_account': total_cost / total_accounts if total_accounts > 0 else 0,
            'top_accounts': [
                {
                    'account_id': acc_id,
                    'account_name': acc_data['name'],
                    'cost': acc_data['cost'],
                    'percentage': (acc_data['cost'] / total_cost * 100) if total_cost > 0 else 0
                }
                for acc_id, acc_data in top_accounts
            ],
            'cost_distribution': {acc_id: acc_data['cost'] for acc_id, acc_data in account_costs.items()}
        }

    async def _analyze_service_distribution(self, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze service distribution and costs."""
        if not sample_data:
            return {}

        service_costs = {}
        service_categories = {}

        for record in sample_data:
            service_name = record.get('ServiceName', 'unknown')
            service_category = record.get('ServiceCategory', self.finops_domain.identify_service_category(service_name))
            cost = float(record.get('BilledCost', 0))

            # Service-level analysis
            if service_name not in service_costs:
                service_costs[service_name] = 0
            service_costs[service_name] += cost

            # Category-level analysis
            if service_category not in service_categories:
                service_categories[service_category] = 0
            service_categories[service_category] += cost

        total_cost = sum(service_costs.values())

        # Calculate service concentration (using Herfindahl-Hirschman Index)
        hhi = sum((cost / total_cost) ** 2 for cost in service_costs.values()) if total_cost > 0 else 0

        # Top services
        top_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'total_services': len(service_costs),
            'total_cost': total_cost,
            'service_concentration_index': hhi,
            'top_services': [
                {
                    'service_name': svc,
                    'cost': cost,
                    'percentage': (cost / total_cost * 100) if total_cost > 0 else 0
                }
                for svc, cost in top_services
            ],
            'category_breakdown': service_categories,
            'service_costs': service_costs
        }

    async def _analyze_charge_categories(self, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze charge categories distribution."""
        if not sample_data:
            return {}

        category_costs = {}
        category_counts = {}

        for record in sample_data:
            category = record.get('ChargeCategory', 'unknown')
            cost = float(record.get('BilledCost', 0))

            if category not in category_costs:
                category_costs[category] = 0
                category_counts[category] = 0

            category_costs[category] += cost
            category_counts[category] += 1

        total_cost = sum(category_costs.values())

        return {
            'category_costs': category_costs,
            'category_counts': category_counts,
            'total_cost': total_cost,
            'usage_percentage': (category_costs.get('Usage', 0) / total_cost * 100) if total_cost > 0 else 0,
            'credit_percentage': (category_costs.get('Credit', 0) / total_cost * 100) if total_cost > 0 else 0
        }

    async def _analyze_cost_trends(self, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze cost trends over time."""
        if not sample_data:
            return {}

        # Group by billing period
        period_costs = {}

        for record in sample_data:
            period_start = record.get('BillingPeriodStart', '')
            cost = float(record.get('BilledCost', 0))

            if period_start:
                # Extract date part for grouping
                try:
                    date_part = period_start.split('T')[0]  # Get YYYY-MM-DD part
                    if date_part not in period_costs:
                        period_costs[date_part] = 0
                    period_costs[date_part] += cost
                except:
                    continue

        if len(period_costs) < 2:
            return {'insufficient_data': True}

        # Calculate trend
        sorted_periods = sorted(period_costs.items())
        costs = [cost for _, cost in sorted_periods]

        # Simple trend calculation
        if len(costs) >= 2:
            trend_direction = 'increasing' if costs[-1] > costs[0] else 'decreasing'
            trend_magnitude = abs(costs[-1] - costs[0]) / costs[0] * 100 if costs[0] > 0 else 0
        else:
            trend_direction = 'stable'
            trend_magnitude = 0

        return {
            'period_costs': dict(sorted_periods),
            'trend_direction': trend_direction,
            'trend_magnitude_percentage': trend_magnitude,
            'cost_volatility': statistics.stdev(costs) if len(costs) > 1 else 0,
            'average_monthly_cost': statistics.mean(costs)
        }

    async def _analyze_commitment_discounts(self, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze commitment discount usage and opportunities."""
        if not sample_data:
            return {}

        total_records = len(sample_data)
        commitment_records = 0
        commitment_savings = 0

        for record in sample_data:
            if record.get('CommitmentDiscountCategory'):
                commitment_records += 1
                # Estimate savings (this would be more sophisticated in production)
                cost = float(record.get('BilledCost', 0))
                commitment_savings += cost * 0.15  # Estimate 15% savings

        coverage_percentage = (commitment_records / total_records * 100) if total_records > 0 else 0

        return {
            'total_records': total_records,
            'commitment_records': commitment_records,
            'coverage_percentage': coverage_percentage,
            'estimated_monthly_savings': commitment_savings,
            'has_commitment_opportunity': coverage_percentage < 60  # Industry benchmark
        }

    async def _analyze_regional_distribution(self, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze regional cost distribution."""
        if not sample_data:
            return {}

        regional_costs = {}

        for record in sample_data:
            region = record.get('Region', 'unknown')
            cost = float(record.get('BilledCost', 0))

            if region not in regional_costs:
                regional_costs[region] = 0
            regional_costs[region] += cost

        total_cost = sum(regional_costs.values())

        # Calculate regional concentration
        region_percentages = {region: (cost / total_cost * 100) for region, cost in regional_costs.items()} if total_cost > 0 else {}

        # Identify dominant region
        dominant_region = max(regional_costs.items(), key=lambda x: x[1]) if regional_costs else ('unknown', 0)

        return {
            'regional_costs': regional_costs,
            'total_regions': len(regional_costs),
            'dominant_region': {
                'region': dominant_region[0],
                'cost': dominant_region[1],
                'percentage': region_percentages.get(dominant_region[0], 0)
            },
            'regional_distribution': region_percentages
        }

    async def _identify_optimization_opportunities(
        self,
        sample_data: List[Dict[str, Any]]
    ) -> List[FinOpsOptimizationOpportunity]:
        """Identify FinOps optimization opportunities."""
        opportunities = []

        if not sample_data:
            return opportunities

        # Analyze for commitment discount opportunities
        commitment_analysis = await self._analyze_commitment_discounts(sample_data)
        if commitment_analysis.get('has_commitment_opportunity', False):
            opportunity = FinOpsOptimizationOpportunity(
                opportunity_id=f"commit_opp_{datetime.now().timestamp()}",
                optimization_type=FinOpsOptimizationType.COMMITMENT_OPPORTUNITY,
                title="Commitment Discount Opportunity",
                description=f"Current commitment coverage is {commitment_analysis.get('coverage_percentage', 0):.1f}%. Industry best practice is 60-80%.",
                potential_savings_monthly=Decimal(str(max(commitment_analysis.get('estimated_monthly_savings', 0) * 0.5, 100.0))),
                confidence_score=0.8,
                implementation_effort="medium",
                affected_services=["Compute", "Database"],
                affected_accounts=["All"],
                affected_regions=["All"],
                recommended_actions=[
                    "Analyze historical usage patterns",
                    "Consider Reserved Instances or Savings Plans",
                    "Start with 50% commitment coverage"
                ],
                implementation_timeline="2-4 weeks",
                supporting_evidence={
                    "current_coverage": commitment_analysis.get('coverage_percentage', 0),
                    "benchmark_coverage": 70.0
                },
                created_at=datetime.now()
            )
            opportunities.append(opportunity)

        # Analyze for regional optimization
        regional_analysis = await self._analyze_regional_distribution(sample_data)
        dominant_region_pct = regional_analysis.get('dominant_region', {}).get('percentage', 0)

        if dominant_region_pct > 80:
            opportunity = FinOpsOptimizationOpportunity(
                opportunity_id=f"regional_opp_{datetime.now().timestamp()}",
                optimization_type=FinOpsOptimizationType.REGIONAL_OPTIMIZATION,
                title="Regional Cost Concentration Risk",
                description=f"Over {dominant_region_pct:.1f}% of costs are concentrated in {regional_analysis.get('dominant_region', {}).get('region', 'one region')}.",
                potential_savings_monthly=Decimal("0"),  # More about risk than direct savings
                confidence_score=0.6,
                implementation_effort="high",
                affected_services=["All"],
                affected_accounts=["All"],
                affected_regions=[regional_analysis.get('dominant_region', {}).get('region', 'unknown')],
                recommended_actions=[
                    "Evaluate multi-region deployment options",
                    "Consider disaster recovery implications",
                    "Analyze regional pricing differences"
                ],
                implementation_timeline="3-6 months",
                supporting_evidence={
                    "concentration_percentage": dominant_region_pct,
                    "risk_threshold": 80.0
                },
                created_at=datetime.now()
            )
            opportunities.append(opportunity)

        # Analyze for service optimization
        service_analysis = await self._analyze_service_distribution(sample_data)
        if service_analysis.get('service_concentration_index', 0) > 0.25:  # High concentration
            opportunity = FinOpsOptimizationOpportunity(
                opportunity_id=f"service_opt_{datetime.now().timestamp()}",
                optimization_type=FinOpsOptimizationType.SERVICE_CONSOLIDATION,
                title="Service Portfolio Optimization",
                description="High service concentration detected. Consider consolidating or optimizing service usage.",
                potential_savings_monthly=Decimal(str(max(service_analysis.get('total_cost', 0) * 0.05, 50.0))),  # 5% potential savings
                confidence_score=0.7,
                implementation_effort="medium",
                affected_services=list(service_analysis.get('service_costs', {}).keys())[:5],
                affected_accounts=["All"],
                affected_regions=["All"],
                recommended_actions=[
                    "Review service utilization patterns",
                    "Identify redundant or overlapping services",
                    "Consider service consolidation opportunities"
                ],
                implementation_timeline="4-8 weeks",
                supporting_evidence={
                    "concentration_index": service_analysis.get('service_concentration_index', 0),
                    "total_services": len(service_analysis.get('service_costs', {}))
                },
                created_at=datetime.now()
            )
            opportunities.append(opportunity)

        logger.info("Identified %d optimization opportunities", len(opportunities))
        return opportunities

    async def _identify_potential_anomalies(
        self,
        sample_data: List[Dict[str, Any]]
    ) -> List[FinOpsAnomaly]:
        """Identify potential cost anomalies."""
        anomalies = []

        if not sample_data:
            return anomalies

        # Analyze cost spikes
        cost_trend = await self._analyze_cost_trends(sample_data)

        if not cost_trend.get('insufficient_data', False):
            trend_magnitude = cost_trend.get('trend_magnitude_percentage', 0)

            if trend_magnitude > 50:  # 50% increase/decrease threshold
                anomaly = FinOpsAnomaly(
                    anomaly_id=f"spike_{datetime.now().timestamp()}",
                    anomaly_type=FinOpsAnomalyType.COST_SPIKE,
                    severity="high" if trend_magnitude > 100 else "medium",
                    title="Significant Cost Trend Change",
                    description=f"Cost trend shows {trend_magnitude:.1f}% change, indicating potential anomaly.",
                    affected_period_start=datetime.now() - timedelta(days=30),
                    affected_period_end=datetime.now(),
                    affected_services=["All"],
                    affected_accounts=["All"],
                    baseline_value=Decimal(str(cost_trend.get('average_monthly_cost', 0) * 0.8)),  # Estimated baseline
                    anomalous_value=Decimal(str(cost_trend.get('average_monthly_cost', 0))),
                    deviation_percentage=trend_magnitude,
                    investigation_suggestions=[
                        "Review recent infrastructure changes",
                        "Check for new service deployments",
                        "Analyze usage pattern changes",
                        "Verify billing accuracy"
                    ],
                    related_opportunities=[],
                    detected_at=datetime.now()
                )
                anomalies.append(anomaly)

        # Analyze for missing discounts
        commitment_analysis = await self._analyze_commitment_discounts(sample_data)
        charge_analysis = await self._analyze_charge_categories(sample_data)

        usage_cost = charge_analysis.get('category_costs', {}).get('Usage', 0)
        credit_percentage = charge_analysis.get('credit_percentage', 0)

        if usage_cost > 10000 and credit_percentage < 5:  # High usage with low credits
            anomaly = FinOpsAnomaly(
                anomaly_id=f"discount_{datetime.now().timestamp()}",
                anomaly_type=FinOpsAnomalyType.MISSING_DISCOUNTS,
                severity="medium",
                title="Potential Missing Discounts",
                description=f"High usage costs (${usage_cost:,.2f}) with low credit percentage ({credit_percentage:.1f}%).",
                affected_period_start=datetime.now() - timedelta(days=30),
                affected_period_end=datetime.now(),
                affected_services=["All"],
                affected_accounts=["All"],
                baseline_value=Decimal("10"),  # Expected credit percentage
                anomalous_value=Decimal(str(credit_percentage)),
                deviation_percentage=abs(10 - credit_percentage),
                investigation_suggestions=[
                    "Review commitment discount eligibility",
                    "Check for available promotional credits",
                    "Verify discount application in billing",
                    "Analyze commitment discount opportunities"
                ],
                related_opportunities=[],
                detected_at=datetime.now()
            )
            anomalies.append(anomaly)

        logger.info("Identified %d potential anomalies", len(anomalies))
        return anomalies

    async def _calculate_finops_kpis(self, sample_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate key FinOps KPIs."""
        if not sample_data:
            return {}

        # Calculate basic KPIs
        total_cost = sum(float(record.get('BilledCost', 0)) for record in sample_data)
        total_records = len(sample_data)

        # Commitment coverage
        commitment_records = sum(1 for record in sample_data if record.get('CommitmentDiscountCategory'))
        commitment_coverage = (commitment_records / total_records * 100) if total_records > 0 else 0

        # Service diversity (using entropy)
        service_counts = {}
        for record in sample_data:
            service = record.get('ServiceName', 'unknown')
            service_counts[service] = service_counts.get(service, 0) + 1

        if service_counts:
            import math
            service_entropy = -sum((count / total_records) *
                                 math.log2(count / total_records) if count > 0 else 0
                                 for count in service_counts.values())
        else:
            service_entropy = 0

        # Regional diversity
        region_counts = {}
        for record in sample_data:
            region = record.get('Region', 'unknown')
            region_counts[region] = region_counts.get(region, 0) + 1

        regional_diversity = len(region_counts)

        return {
            'total_monthly_cost': total_cost,
            'average_cost_per_record': total_cost / total_records if total_records > 0 else 0,
            'commitment_coverage_percentage': commitment_coverage,
            'service_diversity_score': service_entropy,
            'regional_diversity_count': regional_diversity,
            'cost_per_service': total_cost / len(service_counts) if service_counts else 0
        }

    async def _calculate_cost_efficiency_metrics(self, sample_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate cost efficiency metrics."""
        if not sample_data:
            return {}

        # Calculate efficiency based on FinOps best practices
        commitment_analysis = await self._analyze_commitment_discounts(sample_data)
        service_analysis = await self._analyze_service_distribution(sample_data)
        regional_analysis = await self._analyze_regional_distribution(sample_data)

        efficiency_data = {
            'commitment_coverage': commitment_analysis.get('coverage_percentage', 0),
            'service_distribution_entropy': service_analysis.get('service_concentration_index', 0),
            'regional_cost_variance': 100 - regional_analysis.get('dominant_region', {}).get('percentage', 100),
            'cost_trend_stability': 0.8  # Placeholder - would calculate from actual trends
        }

        overall_efficiency = self.finops_domain.calculate_efficiency_score(efficiency_data)

        return {
            'overall_efficiency_score': overall_efficiency,
            'commitment_efficiency': min(commitment_analysis.get('coverage_percentage', 0) / 70.0, 1.0),
            'service_distribution_efficiency': 1.0 - service_analysis.get('service_concentration_index', 0),
            'regional_optimization_score': efficiency_data['regional_cost_variance'] / 50.0
        }

    async def _generate_finops_narrative_insights(
        self,
        sample_data: List[Dict[str, Any]],
        opportunities: List[FinOpsOptimizationOpportunity],
        anomalies: List[FinOpsAnomaly]
    ) -> List[str]:
        """Generate narrative insights for FinOps analysis."""
        insights = []

        if not sample_data:
            return ["No data available for FinOps analysis"]

        # Cost overview insight
        total_cost = sum(float(record.get('BilledCost', 0)) for record in sample_data)
        insights.append(f"Total monthly cloud spend: ${total_cost:,.2f} across {len(sample_data)} line items")

        # Service analysis insight
        service_analysis = await self._analyze_service_distribution(sample_data)
        top_service = service_analysis.get('top_services', [{}])[0]
        if top_service:
            insights.append(f"Top service by cost: {top_service.get('service_name', 'Unknown')} (${top_service.get('cost', 0):,.2f}, {top_service.get('percentage', 0):.1f}%)")

        # Optimization opportunities insight
        if opportunities:
            total_potential_savings = sum(float(opp.potential_savings_monthly) for opp in opportunities)
            insights.append(f"{len(opportunities)} optimization opportunities identified with potential monthly savings of ${total_potential_savings:,.2f}")

        # Anomaly detection insight
        if anomalies:
            high_severity_anomalies = len([a for a in anomalies if a.severity in ['high', 'critical']])
            insights.append(f"{len(anomalies)} cost anomalies detected, {high_severity_anomalies} requiring immediate attention")

        # Commitment discount insight
        commitment_analysis = await self._analyze_commitment_discounts(sample_data)
        coverage = commitment_analysis.get('coverage_percentage', 0)
        if coverage < 60:
            insights.append(f"Commitment discount coverage at {coverage:.1f}% - consider increasing for additional savings")
        elif coverage > 80:
            insights.append(f"Excellent commitment discount coverage at {coverage:.1f}%")

        # Regional distribution insight
        regional_analysis = await self._analyze_regional_distribution(sample_data)
        if regional_analysis.get('total_regions', 0) > 1:
            insights.append(f"Multi-region deployment across {regional_analysis['total_regions']} regions with {regional_analysis.get('dominant_region', {}).get('region', 'unknown')} as primary")

        return insights

    async def _generate_visualization_recommendations(
        self,
        sample_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate visualization recommendations for FOCUS data."""
        recommendations = []

        if not sample_data:
            return recommendations

        # Cost over time visualization
        recommendations.append({
            'chart_type': 'line',
            'title': 'Cost Trends Over Time',
            'dimensions': ['BillingPeriodStart'],
            'metrics': ['BilledCost'],
            'narrative_goal': 'change_over_time',
            'description': 'Track cost evolution and identify trends',
            'priority': 'high'
        })

        # Service cost breakdown
        recommendations.append({
            'chart_type': 'bar',
            'title': 'Cost by Service',
            'dimensions': ['ServiceName'],
            'metrics': ['BilledCost'],
            'narrative_goal': 'magnitude_comparison',
            'description': 'Compare costs across different services',
            'priority': 'high'
        })

        # Regional distribution
        recommendations.append({
            'chart_type': 'pie',
            'title': 'Cost Distribution by Region',
            'dimensions': ['Region'],
            'metrics': ['BilledCost'],
            'narrative_goal': 'part_to_whole',
            'description': 'Understand regional cost allocation',
            'priority': 'medium'
        })

        # Charge category breakdown
        recommendations.append({
            'chart_type': 'stacked_bar',
            'title': 'Charge Categories by Account',
            'dimensions': ['BillingAccountName', 'ChargeCategory'],
            'metrics': ['BilledCost'],
            'narrative_goal': 'part_to_whole',
            'description': 'Analyze charge types across billing accounts',
            'priority': 'medium'
        })

        # Commitment discount analysis
        recommendations.append({
            'chart_type': 'scatter',
            'title': 'Service Cost vs Commitment Coverage',
            'dimensions': ['ServiceName'],
            'metrics': ['BilledCost', 'CommitmentDiscountCategory'],
            'narrative_goal': 'correlation',
            'description': 'Identify commitment discount opportunities',
            'priority': 'medium'
        })

        return recommendations

    async def _generate_drill_down_suggestions(
        self,
        sample_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate drill-down suggestions for FOCUS data exploration."""
        suggestions = []

        if not sample_data:
            return suggestions

        # Service-based drill-downs
        suggestions.append({
            'dimension': 'ServiceName',
            'title': 'Drill Down by Service',
            'description': 'Explore costs within specific cloud services',
            'suggested_filters': ['Region', 'ChargeCategory'],
            'metrics': ['BilledCost', 'PricingQuantity']
        })

        # Account-based drill-downs
        suggestions.append({
            'dimension': 'BillingAccountName',
            'title': 'Drill Down by Account',
            'description': 'Analyze spending patterns within billing accounts',
            'suggested_filters': ['ServiceCategory', 'Region'],
            'metrics': ['BilledCost']
        })

        # Time-based drill-downs
        suggestions.append({
            'dimension': 'BillingPeriodStart',
            'title': 'Drill Down by Time Period',
            'description': 'Examine cost evolution and seasonal patterns',
            'suggested_filters': ['ServiceName', 'ChargeCategory'],
            'metrics': ['BilledCost']
        })

        # Regional drill-downs
        suggestions.append({
            'dimension': 'Region',
            'title': 'Drill Down by Region',
            'description': 'Compare regional costs and optimization opportunities',
            'suggested_filters': ['ServiceName', 'ResourceType'],
            'metrics': ['BilledCost', 'PricingQuantity']
        })

        return suggestions


# Factory function for integration
async def create_focus_lida_integration(lida_manager=None) -> FocusLidaDataSummarizer:
    """
    Factory function to create FocusLidaDataSummarizer instance.

    Args:
        lida_manager: Optional LIDA Enhanced Manager instance

    Returns:
        Configured FocusLidaDataSummarizer instance
    """
    summarizer = FocusLidaDataSummarizer(lida_manager)
    logger.info("Created FocusLidaDataSummarizer for enhanced FOCUS data analysis")
    return summarizer