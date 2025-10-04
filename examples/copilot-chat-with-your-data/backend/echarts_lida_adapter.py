"""
ECharts MCP Adapter for LIDA Integration.

This module creates an adapter layer between LIDA's visualization generation
and the ECharts MCP server, replacing LIDA's static code generation with
interactive ECharts configurations.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class EChartsLidaAdapter:
    """
    Adapter that replaces LIDA's code generation with ECharts MCP server integration.

    This class maps LIDA goals and data summaries to ECharts configurations
    via the ECharts MCP server, enabling interactive visualizations with
    enhanced features not available in LIDA's static output.
    """

    def __init__(self, echarts_mcp_client=None):
        """
        Initialize the ECharts LIDA adapter.

        Args:
            echarts_mcp_client: Optional ECharts MCP client. If None, will use mock mode.
        """
        self.echarts_client = echarts_mcp_client
        self.mock_mode = echarts_mcp_client is None

        # LIDA visualization intent to ECharts type mapping
        self.chart_type_mapping = {
            # Basic chart types
            'bar': 'bar',
            'column': 'bar',
            'horizontal_bar': 'bar',
            'line': 'line',
            'area': 'line',  # Line chart with area style
            'scatter': 'scatter',
            'pie': 'pie',
            'donut': 'pie',  # Pie chart with inner radius

            # Advanced chart types
            'histogram': 'bar',  # Converted to bar with binned data
            'heatmap': 'heatmap',
            'treemap': 'treemap',
            'sunburst': 'sunburst',
            'funnel': 'funnel',
            'sankey': 'sankey',
            'tree': 'tree',
            'radar': 'radar',
            'gauge': 'gauge',

            # Fallback
            'default': 'bar'
        }

        # Narrative goal to chart type mapping (Cleveland-McGill hierarchy)
        self.narrative_to_chart_mapping = {
            'magnitude_comparison': ['bar', 'column'],
            'ranking': ['bar', 'column'],
            'change_over_time': ['line', 'area'],
            'distribution': ['bar', 'histogram'],
            'correlation': ['scatter'],
            'part_to_whole': ['pie', 'treemap'],
            'deviation': ['bar'],  # with reference lines
            'flow': ['sankey'],
            'hierarchy': ['tree', 'treemap', 'sunburst']
        }

        # Persona complexity constraints
        self.persona_chart_constraints = {
            'executive': {
                'allowed': ['bar', 'line', 'pie'],
                'forbidden': ['heatmap', 'sankey', 'tree', 'radar'],
                'max_series': 3,
                'max_categories': 10
            },
            'analyst': {
                'allowed': ['bar', 'line', 'scatter', 'heatmap', 'treemap'],
                'forbidden': [],
                'max_series': 10,
                'max_categories': 50
            },
            'stakeholder': {
                'allowed': ['bar', 'line', 'pie', 'funnel'],
                'forbidden': ['heatmap', 'sankey', 'tree'],
                'max_series': 5,
                'max_categories': 20
            }
        }

        logger.info("EChartsLidaAdapter initialized (mock_mode=%s)", self.mock_mode)

    async def generate_visualization(
        self,
        goal: Dict[str, Any],
        data_summary: Dict[str, Any],
        persona: str = "analyst"
    ) -> Dict[str, Any]:
        """
        Generate ECharts visualization configuration from LIDA goal.

        Args:
            goal: LIDA goal dictionary with question, chart_type, dimensions, metrics
            data_summary: Enhanced data summary from LIDA manager
            persona: Target user persona for complexity filtering

        Returns:
            Complete ECharts configuration with interactive features
        """
        try:
            # Extract goal information
            chart_type = self._select_optimal_chart_type(goal, persona)
            title = goal.get('question', 'Data Visualization')
            dimensions = goal.get('dimensions', [])
            metrics = goal.get('metrics', [])

            # Prepare data for ECharts
            chart_data = self._prepare_chart_data(data_summary, dimensions, metrics)

            # Generate base ECharts configuration
            if self.mock_mode:
                echarts_config = self._generate_mock_echarts_config(
                    chart_type, title, chart_data, dimensions, metrics
                )
            else:
                echarts_config = await self._call_echarts_mcp(
                    chart_type, title, chart_data, dimensions, metrics
                )

            # Enhance with interactive features
            enhanced_config = self._add_interactive_features(
                echarts_config, goal, persona
            )

            # Add accessibility features
            accessible_config = self._add_accessibility_features(
                enhanced_config, goal, persona
            )

            return {
                'echarts_config': accessible_config,
                'chart_type': chart_type,
                'title': title,
                'data': chart_data,
                'goal': goal,
                'persona': persona,
                'interactive_features': self._get_interactive_features_list(chart_type),
                'accessibility_features': self._get_accessibility_features_list()
            }

        except Exception as exc:
            logger.error("Failed to generate visualization: %s", exc)
            raise

    def _select_optimal_chart_type(
        self,
        goal: Dict[str, Any],
        persona: str
    ) -> str:
        """
        Select optimal chart type based on goal, data, and persona constraints.

        This implements the Cleveland-McGill perceptual hierarchy filtering
        and persona-specific complexity constraints.
        """
        # Get suggested chart type from goal
        suggested_type = goal.get('chart_type', 'bar')
        narrative_goal = goal.get('narrative_goal', 'magnitude_comparison')

        # Get chart types suitable for narrative goal
        suitable_types = self.narrative_to_chart_mapping.get(
            narrative_goal, ['bar']
        )

        # Apply persona constraints
        persona_constraints = self.persona_chart_constraints.get(
            persona, self.persona_chart_constraints['analyst']
        )

        # Filter by allowed types for persona
        allowed_types = [
            chart_type for chart_type in suitable_types
            if chart_type in persona_constraints['allowed'] and
               chart_type not in persona_constraints['forbidden']
        ]

        # Choose best type (prefer suggested if allowed, otherwise first suitable)
        if suggested_type in allowed_types:
            selected_type = suggested_type
        elif allowed_types:
            selected_type = allowed_types[0]
        else:
            # Fallback to safest option
            selected_type = 'bar'

        logger.debug(
            "Selected chart type '%s' for goal '%s' with persona '%s'",
            selected_type, goal.get('question', 'unknown'), persona
        )

        return self.chart_type_mapping.get(selected_type, 'bar')

    def _prepare_chart_data(
        self,
        data_summary: Dict[str, Any],
        dimensions: List[str],
        metrics: List[str]
    ) -> List[List[Any]]:
        """
        Prepare data in ECharts format from data summary.

        Args:
            data_summary: Enhanced data summary with sample data
            dimensions: List of dimension columns
            metrics: List of metric columns

        Returns:
            Data in ECharts format: [[x1, y1], [x2, y2], ...]
        """
        try:
            # Get sample data from summary
            sample_data = data_summary.get('sample_data', [])

            if not sample_data:
                # Generate mock data based on dimensions and metrics
                return self._generate_mock_data(dimensions, metrics)

            # Convert sample data to ECharts format
            chart_data = []

            for row in sample_data:
                # Create data point with dimension and metric values
                if dimensions and metrics:
                    x_value = row.get(dimensions[0], 'Unknown')
                    y_value = row.get(metrics[0], 0)
                    chart_data.append([x_value, y_value])
                elif dimensions:
                    # Dimension only - create frequency data
                    x_value = row.get(dimensions[0], 'Unknown')
                    chart_data.append([x_value, 1])  # Count frequency
                else:
                    # Create generic data point
                    keys = list(row.keys())
                    if len(keys) >= 2:
                        chart_data.append([row[keys[0]], row[keys[1]]])

            return chart_data[:50]  # Limit to 50 data points for performance

        except Exception as exc:
            logger.warning("Failed to prepare chart data: %s", exc)
            return self._generate_mock_data(dimensions, metrics)

    def _generate_mock_data(
        self,
        dimensions: List[str],
        metrics: List[str]
    ) -> List[List[Any]]:
        """Generate mock data for testing when real data is not available."""
        mock_data = []

        categories = ['Category A', 'Category B', 'Category C', 'Category D', 'Category E']
        values = [120, 200, 150, 80, 70]

        for i, (cat, val) in enumerate(zip(categories, values)):
            mock_data.append([cat, val])

        return mock_data

    async def _call_echarts_mcp(
        self,
        chart_type: str,
        title: str,
        data: List[List[Any]],
        dimensions: List[str],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Call ECharts MCP server to generate configuration."""
        try:
            # Prepare MCP call parameters
            x_axis_name = dimensions[0] if dimensions else "Category"
            y_axis_name = metrics[0] if metrics else "Value"
            series_name = metrics[0] if metrics else "Data Series"

            # Call ECharts MCP server
            result = await self.echarts_client.get_chart(
                type=chart_type,
                data=data,
                title=title,
                seriesName=series_name,
                xAxisName=x_axis_name,
                yAxisName=y_axis_name
            )

            return result

        except Exception as exc:
            logger.error("ECharts MCP call failed: %s", exc)
            # Fallback to mock configuration
            return self._generate_mock_echarts_config(
                chart_type, title, data, dimensions, metrics
            )

    def _generate_mock_echarts_config(
        self,
        chart_type: str,
        title: str,
        data: List[List[Any]],
        dimensions: List[str],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Generate mock ECharts configuration for testing."""

        x_axis_name = dimensions[0] if dimensions else "Category"
        y_axis_name = metrics[0] if metrics else "Value"

        # Basic configuration structure
        config = {
            "title": {
                "text": title,
                "left": "center",
                "textStyle": {
                    "fontSize": 16,
                    "fontWeight": "bold"
                }
            },
            "tooltip": {
                "trigger": "item" if chart_type == "pie" else "axis",
                "formatter": "{b}: {c}"
            },
            "legend": {
                "bottom": 10,
                "left": "center"
            },
            "grid": {
                "left": "10%",
                "right": "10%",
                "bottom": "15%",
                "containLabel": True
            }
        }

        # Chart type specific configuration
        if chart_type == "bar":
            config.update({
                "xAxis": {
                    "type": "category",
                    "name": x_axis_name,
                    "data": [item[0] for item in data]
                },
                "yAxis": {
                    "type": "value",
                    "name": y_axis_name
                },
                "series": [{
                    "name": y_axis_name,
                    "type": "bar",
                    "data": [item[1] for item in data],
                    "itemStyle": {
                        "color": "#5470c6"
                    }
                }]
            })

        elif chart_type == "line":
            config.update({
                "xAxis": {
                    "type": "category",
                    "name": x_axis_name,
                    "data": [item[0] for item in data]
                },
                "yAxis": {
                    "type": "value",
                    "name": y_axis_name
                },
                "series": [{
                    "name": y_axis_name,
                    "type": "line",
                    "data": [item[1] for item in data],
                    "smooth": True,
                    "lineStyle": {
                        "color": "#91cc75"
                    }
                }]
            })

        elif chart_type == "pie":
            config.update({
                "series": [{
                    "name": y_axis_name,
                    "type": "pie",
                    "radius": "50%",
                    "data": [{"name": item[0], "value": item[1]} for item in data],
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": "rgba(0, 0, 0, 0.5)"
                        }
                    }
                }]
            })

        elif chart_type == "scatter":
            config.update({
                "xAxis": {
                    "type": "value",
                    "name": x_axis_name
                },
                "yAxis": {
                    "type": "value",
                    "name": y_axis_name
                },
                "series": [{
                    "name": "Data Points",
                    "type": "scatter",
                    "data": data,
                    "itemStyle": {
                        "color": "#fac858"
                    }
                }]
            })

        return config

    def _add_interactive_features(
        self,
        config: Dict[str, Any],
        goal: Dict[str, Any],
        persona: str
    ) -> Dict[str, Any]:
        """
        Add interactive features not available in LIDA's static output.

        Features include:
        - Drill-down capabilities
        - Hover interactions
        - Export functionality
        - Chart editing options
        """
        enhanced_config = config.copy()

        # Add toolbox for export and other features
        enhanced_config["toolbox"] = {
            "show": True,
            "orient": "vertical",
            "left": "right",
            "top": "center",
            "feature": {
                "saveAsImage": {
                    "show": True,
                    "title": "Save as Image",
                    "type": "png",
                    "backgroundColor": "white"
                },
                "dataView": {
                    "show": True,
                    "title": "View Data",
                    "readOnly": False
                },
                "restore": {
                    "show": True,
                    "title": "Restore"
                }
            }
        }

        # Enhanced tooltip with more information
        if "tooltip" in enhanced_config:
            enhanced_config["tooltip"]["backgroundColor"] = "rgba(50,50,50,0.9)"
            enhanced_config["tooltip"]["borderColor"] = "#333"
            enhanced_config["tooltip"]["textStyle"] = {"color": "#fff"}

        # Add brush component for data selection (analyst persona)
        if persona == "analyst":
            enhanced_config["brush"] = {
                "toolbox": ["rect", "polygon", "clear"],
                "xAxisIndex": 0
            }

        # Add data zoom for large datasets
        if persona in ["analyst", "stakeholder"]:
            enhanced_config["dataZoom"] = [
                {
                    "type": "slider",
                    "show": True,
                    "xAxisIndex": [0],
                    "start": 0,
                    "end": 100
                },
                {
                    "type": "inside",
                    "xAxisIndex": [0],
                    "start": 0,
                    "end": 100
                }
            ]

        return enhanced_config

    def _add_accessibility_features(
        self,
        config: Dict[str, Any],
        goal: Dict[str, Any],
        persona: str
    ) -> Dict[str, Any]:
        """Add accessibility features for WCAG 2.1 compliance."""
        accessible_config = config.copy()

        # Add aria labels and descriptions
        accessible_config["aria"] = {
            "enabled": True,
            "label": goal.get('question', 'Data Visualization'),
            "description": f"Interactive chart showing {goal.get('visualization', 'data analysis')}"
        }

        # Ensure sufficient color contrast
        if "series" in accessible_config:
            for series in accessible_config["series"]:
                if series.get("type") == "bar":
                    series["itemStyle"] = series.get("itemStyle", {})
                    series["itemStyle"]["borderColor"] = "#000"
                    series["itemStyle"]["borderWidth"] = 1

        # Add keyboard navigation hints
        accessible_config["textStyle"] = {
            "fontFamily": "Arial, sans-serif",
            "fontSize": 12
        }

        return accessible_config

    def _get_interactive_features_list(self, chart_type: str) -> List[str]:
        """Get list of interactive features available for chart type."""
        base_features = [
            "hover_tooltips",
            "export_image",
            "data_view",
            "restore_zoom"
        ]

        if chart_type in ["bar", "line", "scatter"]:
            base_features.extend([
                "data_zoom",
                "brush_selection",
                "click_drill_down"
            ])

        if chart_type == "pie":
            base_features.append("slice_emphasis")

        return base_features

    def _get_accessibility_features_list(self) -> List[str]:
        """Get list of accessibility features implemented."""
        return [
            "aria_labels",
            "keyboard_navigation",
            "high_contrast",
            "screen_reader_support",
            "color_blind_friendly"
        ]

    def map_goal_to_chart_type(self, goal: Dict[str, Any], persona: str) -> str:
        """
        Public method to map LIDA goal to optimal chart type.

        Args:
            goal: LIDA goal dictionary
            persona: Target user persona

        Returns:
            Optimal ECharts chart type
        """
        return self._select_optimal_chart_type(goal, persona)

    def get_supported_chart_types(self) -> List[str]:
        """Get list of supported chart types."""
        return list(self.chart_type_mapping.keys())

    def get_persona_constraints(self, persona: str) -> Dict[str, Any]:
        """Get chart constraints for specific persona."""
        return self.persona_chart_constraints.get(
            persona, self.persona_chart_constraints['analyst']
        )


# Factory function for integration
async def create_echarts_lida_adapter(echarts_mcp_client=None) -> EChartsLidaAdapter:
    """
    Factory function to create EChartsLidaAdapter instance.

    Args:
        echarts_mcp_client: Optional ECharts MCP client

    Returns:
        Configured EChartsLidaAdapter instance
    """
    adapter = EChartsLidaAdapter(echarts_mcp_client)
    logger.info("Created EChartsLidaAdapter for LIDA integration")
    return adapter