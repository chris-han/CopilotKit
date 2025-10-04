"""
Enhanced LIDA Manager for integration with AG-UI FastAPI backend.

This module adapts Microsoft LIDA's Manager class for async operation and
integration with the existing AG-UI protocol, Pydantic AI agents, and
Azure OpenAI services.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence

from openai import AsyncAzureOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Import ECharts adapter
try:
    from echarts_lida_adapter import EChartsLidaAdapter, create_echarts_lida_adapter
    ECHARTS_ADAPTER_AVAILABLE = True
except ImportError:
    EChartsLidaAdapter = None
    create_echarts_lida_adapter = None
    ECHARTS_ADAPTER_AVAILABLE = False
    logger.warning("ECharts adapter not available")

# Optional LIDA imports with fallback for testing
try:
    from lida import Manager
    from lida.datamodel import Goal, Summary
    from lida.utils import clean_code_snippet
    LIDA_AVAILABLE = True
except ImportError:
    # Fallback for testing when LIDA is not available
    Manager = None
    Goal = None
    Summary = None
    clean_code_snippet = None
    LIDA_AVAILABLE = False
    logger.warning("LIDA library not available, running in mock mode")


class EnhancedDataSummary(BaseModel):
    """Enhanced data summary with AG-UI context."""

    summary: str
    dataset_name: str
    columns: List[str]
    data_types: Dict[str, str]
    insights: List[str]
    ag_ui_context: Dict[str, Any]
    row_count: Optional[int] = None
    sample_data: Optional[List[Dict[str, Any]]] = None


class EnhancedGoal(BaseModel):
    """Enhanced goal with AG-UI integration."""

    question: str
    visualization: str
    rationale: str
    chart_type: str
    dimensions: List[str]
    metrics: List[str]
    persona: str
    narrative_goal: str
    ag_ui_compatible: bool = True


class LidaEnhancedManager:
    """
    Async-enabled LIDA Manager that integrates with AG-UI backend.

    This class adapts LIDA's core functionality for use with:
    - FastAPI async/await patterns
    - AG-UI protocol streaming
    - Existing Azure OpenAI integration
    - Chart highlighting system
    """

    def __init__(
        self,
        azure_client: AsyncAzureOpenAI,
        deployment_name: str,
        dashboard_context: Dict[str, Any],
        echarts_mcp_client=None
    ):
        """
        Initialize the enhanced LIDA manager.

        Args:
            azure_client: Configured Azure OpenAI async client
            deployment_name: Azure OpenAI deployment name
            dashboard_context: AG-UI dashboard context data
            echarts_mcp_client: Optional ECharts MCP client for visualization generation
        """
        self.azure_client = azure_client
        self.deployment_name = deployment_name
        self.dashboard_context = dashboard_context

        # Initialize base LIDA manager (will be replaced with async operations)
        # For now, we create a minimal text-gen interface
        self._text_gen = self._create_async_text_gen()

        # Initialize ECharts adapter
        self.echarts_adapter = None
        self._initialize_echarts_adapter(echarts_mcp_client)

        logger.info("LidaEnhancedManager initialized with Azure OpenAI deployment: %s", deployment_name)

    def _create_async_text_gen(self):
        """Create async text generation interface for LIDA compatibility."""

        class AsyncTextGen:
            def __init__(self, azure_client: AsyncAzureOpenAI, deployment_name: str):
                self.azure_client = azure_client
                self.deployment_name = deployment_name

            async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
                """Generate text using Azure OpenAI async client."""
                try:
                    response = await self.azure_client.chat.completions.create(
                        model=self.deployment_name,
                        messages=messages,
                        temperature=kwargs.get('temperature', 0.0),
                        max_tokens=kwargs.get('max_tokens', 1000)
                    )
                    return response.choices[0].message.content
                except Exception as exc:
                    logger.error("Failed to generate text with Azure OpenAI: %s", exc)
                    raise

        return AsyncTextGen(self.azure_client, self.deployment_name)

    def _initialize_echarts_adapter(self, echarts_mcp_client):
        """Initialize ECharts adapter for visualization generation."""
        try:
            if ECHARTS_ADAPTER_AVAILABLE:
                self.echarts_adapter = EChartsLidaAdapter(echarts_mcp_client)
                logger.info("ECharts adapter initialized successfully")
            else:
                logger.warning("ECharts adapter not available, using fallback visualization")
        except Exception as exc:
            logger.error("Failed to initialize ECharts adapter: %s", exc)
            self.echarts_adapter = None

    async def summarize_data(
        self,
        data: Dict[str, Any],
        summary_method: str = "default"
    ) -> EnhancedDataSummary:
        """
        Create enhanced data summary with AG-UI context.

        Args:
            data: Data to summarize (from dashboard context or external source)
            summary_method: Method for summarization

        Returns:
            Enhanced data summary with AG-UI integration
        """
        try:
            # Extract data characteristics
            dataset_name = data.get('name', 'dashboard_data')

            # For AG-UI dashboard context, extract structure
            if 'metrics' in data and 'dimensions' in data:
                columns = []
                data_types = {}

                # Extract from AG-UI metrics
                for metric in data.get('metrics', []):
                    metric_name = metric.get('name', 'unknown_metric')
                    columns.append(metric_name)
                    data_types[metric_name] = metric.get('type', 'numeric')

                # Extract from AG-UI dimensions
                for dimension in data.get('dimensions', []):
                    dim_name = dimension.get('name', 'unknown_dimension')
                    columns.append(dim_name)
                    data_types[dim_name] = dimension.get('type', 'categorical')

                sample_data = data.get('sample_data', [])
                row_count = len(sample_data) if sample_data else None
            else:
                # Handle other data formats
                columns = list(data.keys()) if isinstance(data, dict) else []
                data_types = {col: 'unknown' for col in columns}
                sample_data = None
                row_count = None

            # Generate data insights using Azure OpenAI
            insights = await self._generate_data_insights(data, columns, data_types)

            # Create data summary
            summary_text = await self._create_summary_text(data, columns, insights)

            return EnhancedDataSummary(
                summary=summary_text,
                dataset_name=dataset_name,
                columns=columns,
                data_types=data_types,
                insights=insights,
                ag_ui_context=self.dashboard_context,
                row_count=row_count,
                sample_data=sample_data
            )

        except Exception as exc:
            logger.error("Failed to summarize data: %s", exc)
            raise

    async def _generate_data_insights(
        self,
        data: Dict[str, Any],
        columns: List[str],
        data_types: Dict[str, str]
    ) -> List[str]:
        """Generate insights about the data using Azure OpenAI."""

        prompt_messages = [
            {
                "role": "system",
                "content": """You are a data analyst expert. Analyze the provided data structure and generate key insights about potential patterns, relationships, and analysis opportunities. Focus on business-relevant observations."""
            },
            {
                "role": "user",
                "content": f"""
                Analyze this data structure:

                Columns: {columns}
                Data Types: {json.dumps(data_types, indent=2)}
                Context: {json.dumps(self.dashboard_context.get('description', 'Dashboard data'), indent=2)}

                Provide 3-5 key insights about:
                1. Potential analysis opportunities
                2. Key relationships to explore
                3. Business questions this data could answer
                4. Recommended visualization approaches

                Return as a simple list of insights, one per line.
                """
            }
        ]

        try:
            insights_text = await self._text_gen.generate(prompt_messages, temperature=0.3)

            # Parse insights from response
            insights = [
                line.strip().lstrip('- ').lstrip('* ').lstrip('• ')
                for line in insights_text.split('\n')
                if line.strip() and not line.strip().startswith('#')
            ]

            return insights[:5]  # Limit to 5 insights

        except Exception as exc:
            logger.warning("Failed to generate data insights: %s", exc)
            return ["Data structure analysis available", "Visualization opportunities identified"]

    async def _create_summary_text(
        self,
        data: Dict[str, Any],
        columns: List[str],
        insights: List[str]
    ) -> str:
        """Create comprehensive summary text."""

        summary_parts = [
            f"Dataset: {data.get('name', 'Dashboard Data')}",
            f"Columns ({len(columns)}): {', '.join(columns[:10])}{'...' if len(columns) > 10 else ''}",
            f"Key Insights: {'; '.join(insights[:3])}"
        ]

        if 'description' in data:
            summary_parts.insert(1, f"Description: {data['description']}")

        return ". ".join(summary_parts) + "."

    async def generate_goals(
        self,
        summary: EnhancedDataSummary,
        n: int = 5,
        persona: str = "analyst"
    ) -> List[EnhancedGoal]:
        """
        Generate visualization goals enhanced for AG-UI integration.

        Args:
            summary: Enhanced data summary
            n: Number of goals to generate
            persona: Target user persona

        Returns:
            List of enhanced goals with AG-UI compatibility
        """
        try:
            # Create persona-aware prompt
            persona_context = self._get_persona_context(persona)

            prompt_messages = [
                {
                    "role": "system",
                    "content": f"""You are a visualization expert creating analysis goals for a {persona}.

                    Generate specific, actionable visualization goals that:
                    1. Address business questions relevant to {persona_context}
                    2. Leverage available data columns effectively
                    3. Suggest appropriate chart types
                    4. Consider cognitive load and clarity

                    Format each goal as JSON with: question, visualization, rationale, chart_type, dimensions, metrics"""
                },
                {
                    "role": "user",
                    "content": f"""
                    Data Summary: {summary.summary}
                    Available Columns: {summary.columns}
                    Data Types: {json.dumps(summary.data_types)}
                    Insights: {summary.insights}
                    Context: {json.dumps(summary.ag_ui_context.get('description', 'Business dashboard'))}

                    Generate {n} visualization goals for {persona} persona.
                    Each goal should be actionable and specific to this data.
                    """
                }
            ]

            response = await self._text_gen.generate(prompt_messages, temperature=0.4)

            # Parse goals from response
            goals = await self._parse_goals_response(response, persona, summary)

            return goals[:n]

        except Exception as exc:
            logger.error("Failed to generate goals: %s", exc)
            # Return fallback goals
            return await self._create_fallback_goals(summary, n, persona)

    def _get_persona_context(self, persona: str) -> str:
        """Get context description for persona."""
        persona_contexts = {
            "executive": "high-level strategic insights, KPIs, trends",
            "analyst": "detailed analysis, patterns, correlations",
            "manager": "operational metrics, team performance, resource utilization",
            "stakeholder": "business impact, ROI, decision support"
        }
        return persona_contexts.get(persona, "data analysis and insights")

    async def _parse_goals_response(
        self,
        response: str,
        persona: str,
        summary: EnhancedDataSummary
    ) -> List[EnhancedGoal]:
        """Parse goals from LLM response."""
        goals = []

        try:
            # Try to extract JSON goals from response
            lines = response.split('\n')
            current_json = ""

            for line in lines:
                line = line.strip()
                if line.startswith('{') or current_json:
                    current_json += line + '\n'
                    if line.endswith('}'):
                        try:
                            goal_data = json.loads(current_json)
                            enhanced_goal = EnhancedGoal(
                                question=goal_data.get('question', 'Analysis question'),
                                visualization=goal_data.get('visualization', 'Chart visualization'),
                                rationale=goal_data.get('rationale', 'Data analysis rationale'),
                                chart_type=goal_data.get('chart_type', 'bar'),
                                dimensions=goal_data.get('dimensions', [summary.columns[0]] if summary.columns else []),
                                metrics=goal_data.get('metrics', []),
                                persona=persona,
                                narrative_goal=self._infer_narrative_goal(goal_data.get('chart_type', 'bar')),
                                ag_ui_compatible=True
                            )
                            goals.append(enhanced_goal)
                            current_json = ""
                        except json.JSONDecodeError:
                            current_json = ""

            return goals

        except Exception as exc:
            logger.warning("Failed to parse goals response: %s", exc)
            return []

    def _infer_narrative_goal(self, chart_type: str) -> str:
        """Infer narrative goal from chart type."""
        narrative_mapping = {
            'bar': 'magnitude_comparison',
            'line': 'change_over_time',
            'pie': 'part_to_whole',
            'scatter': 'correlation',
            'area': 'change_over_time',
            'column': 'magnitude_comparison'
        }
        return narrative_mapping.get(chart_type, 'magnitude_comparison')

    async def _create_fallback_goals(
        self,
        summary: EnhancedDataSummary,
        n: int,
        persona: str
    ) -> List[EnhancedGoal]:
        """Create fallback goals when parsing fails."""
        fallback_goals = []

        columns = summary.columns[:5]  # Use first 5 columns

        for i, column in enumerate(columns):
            if i >= n:
                break

            goal = EnhancedGoal(
                question=f"What are the key patterns in {column}?",
                visualization=f"Analyze {column} distribution and trends",
                rationale=f"Understanding {column} patterns provides business insights",
                chart_type="bar" if summary.data_types.get(column) == "categorical" else "line",
                dimensions=[column],
                metrics=[],
                persona=persona,
                narrative_goal="magnitude_comparison",
                ag_ui_compatible=True
            )
            fallback_goals.append(goal)

        return fallback_goals

    async def visualize_goal(
        self,
        goal: EnhancedGoal,
        summary: EnhancedDataSummary
    ) -> Dict[str, Any]:
        """
        Generate visualization specification for a goal using ECharts adapter.

        This method uses the ECharts adapter to generate interactive visualizations
        and prepares them for AG-UI chart highlighting integration.

        Args:
            goal: Enhanced goal to visualize
            summary: Data summary context

        Returns:
            Visualization specification compatible with AG-UI with ECharts config
        """
        try:
            # Use ECharts adapter to generate interactive visualization
            if self.echarts_adapter:
                echarts_result = await self.echarts_adapter.generate_visualization(
                    goal=goal.dict(),
                    data_summary=summary.dict(),
                    persona=goal.persona
                )
            else:
                # Fallback without ECharts adapter
                echarts_result = self._create_fallback_visualization(goal, summary)

            # Create comprehensive AG-UI compatible visualization spec
            viz_spec = {
                "goal": goal.dict(),
                "chart_type": goal.chart_type,
                "title": goal.question,
                "echarts_config": echarts_result.get("echarts_config", {}),
                "interactive_features": echarts_result.get("interactive_features", []),
                "accessibility_features": echarts_result.get("accessibility_features", []),
                "data_requirements": {
                    "dimensions": goal.dimensions,
                    "metrics": goal.metrics,
                    "filters": []
                },
                "ag_ui_highlight": {
                    "chart_ids": self._map_to_chart_ids(goal),
                    "narrative_goal": goal.narrative_goal
                },
                "persona": goal.persona,
                "summary": summary.dict(),
                "data": echarts_result.get("data", []),
                "cleveland_mcgill_optimized": True,
                "wcag_compliant": True
            }

            return viz_spec

        except Exception as exc:
            logger.error("Failed to create visualization spec: %s", exc)
            raise

    def _create_fallback_visualization(
        self,
        goal: EnhancedGoal,
        summary: EnhancedDataSummary
    ) -> Dict[str, Any]:
        """Create fallback visualization when ECharts adapter is unavailable."""
        return {
            "echarts_config": {
                "title": {"text": goal.question},
                "tooltip": {"trigger": "item"},
                "series": [{
                    "name": "Data",
                    "type": goal.chart_type,
                    "data": []
                }]
            },
            "interactive_features": ["hover_tooltips"],
            "accessibility_features": ["aria_labels"],
            "data": []
        }

    def _map_to_chart_ids(self, goal: EnhancedGoal) -> List[str]:
        """Map goals to existing AG-UI chart IDs for highlighting."""

        # Map based on question content and chart type
        chart_mapping = {
            "sales": ["sales-overview", "regional-sales"],
            "product": ["product-performance", "sales-by-category"],
            "customer": ["customer-demographics"],
            "region": ["regional-sales"],
            "category": ["sales-by-category"],
            "overview": ["sales-overview"]
        }

        question_lower = goal.question.lower()
        chart_ids = []

        for keyword, ids in chart_mapping.items():
            if keyword in question_lower:
                chart_ids.extend(ids)

        # Default to sales-overview if no matches
        return chart_ids if chart_ids else ["sales-overview"]


# Utility function for integration with main.py
async def create_lida_enhanced_manager(
    azure_client: AsyncAzureOpenAI,
    deployment_name: str,
    dashboard_context: Dict[str, Any],
    echarts_mcp_client=None
) -> LidaEnhancedManager:
    """
    Factory function to create LidaEnhancedManager instance with ECharts integration.

    Args:
        azure_client: Configured Azure OpenAI async client
        deployment_name: Azure OpenAI deployment name
        dashboard_context: AG-UI dashboard context
        echarts_mcp_client: Optional ECharts MCP client for interactive visualizations

    Returns:
        Configured LidaEnhancedManager instance with ECharts adapter
    """
    manager = LidaEnhancedManager(
        azure_client=azure_client,
        deployment_name=deployment_name,
        dashboard_context=dashboard_context,
        echarts_mcp_client=echarts_mcp_client
    )
    logger.info("Created LidaEnhancedManager with ECharts integration for AG-UI")
    return manager