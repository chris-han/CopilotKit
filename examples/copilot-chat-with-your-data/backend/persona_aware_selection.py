"""
Persona-Aware Visualization Selection for LIDA Enhanced Manager.

This module extends LIDA's basic persona parameter with detailed persona profiles,
Cleveland-McGill perceptual hierarchy filtering, FTVV-based algorithm, and
cognitive load assessment capabilities.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PersonaType(Enum):
    """Detailed persona types with specific characteristics."""
    EXECUTIVE = "executive"
    ANALYST = "analyst"
    MANAGER = "manager"
    STAKEHOLDER = "stakeholder"
    CONSUMER = "consumer"
    TECHNICAL_LEAD = "technical_lead"
    DOMAIN_EXPERT = "domain_expert"


class CognitiveLevelType(Enum):
    """Cognitive complexity levels for visualization selection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXPERT = "expert"


class FTVVNarrativeGoal(Enum):
    """FTVV (Few Types, Many Views, Visualization) narrative goals."""
    MAGNITUDE_COMPARISON = "magnitude_comparison"
    RANKING = "ranking"
    CHANGE_OVER_TIME = "change_over_time"
    DISTRIBUTION = "distribution"
    CORRELATION = "correlation"
    PART_TO_WHOLE = "part_to_whole"
    DEVIATION = "deviation"
    FLOW = "flow"
    HIERARCHY = "hierarchy"
    SPATIAL_RELATIONSHIP = "spatial_relationship"
    NETWORK_RELATIONSHIP = "network_relationship"


@dataclass
class PersonaProfile:
    """Detailed persona profile with visualization preferences and constraints."""
    persona_type: PersonaType
    name: str
    description: str

    # Cognitive characteristics
    cognitive_level: CognitiveLevelType
    attention_span_minutes: int
    data_literacy_level: int  # 1-10 scale

    # Visualization preferences
    preferred_chart_types: List[str]
    forbidden_chart_types: List[str]
    max_data_points: int
    max_series_count: int
    max_categories: int

    # Cleveland-McGill constraints
    perceptual_accuracy_threshold: float  # 0.0-1.0
    allow_complex_encodings: bool

    # Accessibility requirements
    color_blind_friendly: bool
    high_contrast_required: bool
    screen_reader_support: bool

    # Business context
    decision_making_level: str  # strategic, tactical, operational
    time_horizon: str  # immediate, short-term, long-term
    key_metrics: List[str]
    interaction_preferences: List[str]  # drill-down, filtering, export


class ClevelandMcGillHierarchy:
    """Implementation of Cleveland-McGill perceptual hierarchy for chart selection."""

    # Perceptual accuracy scores based on Cleveland-McGill research
    ENCODING_ACCURACY_SCORES = {
        # Position encodings (most accurate)
        'position_common_scale': 1.0,
        'position_non_aligned_scale': 0.95,

        # Length encodings
        'length': 0.90,
        'direction': 0.85,

        # Angle encodings
        'angle': 0.70,

        # Area encodings
        'area': 0.60,

        # Volume encodings (least accurate)
        'volume': 0.40,
        'curvature': 0.35,
        'shading_color_saturation': 0.30
    }

    # Chart type to encoding mapping
    CHART_ENCODING_MAP = {
        'bar': 'position_common_scale',
        'column': 'position_common_scale',
        'line': 'position_common_scale',
        'scatter': 'position_common_scale',
        'area': 'position_common_scale',
        'histogram': 'position_common_scale',

        'horizontal_bar': 'position_non_aligned_scale',
        'stacked_bar': 'position_non_aligned_scale',

        'pie': 'angle',
        'donut': 'angle',

        'bubble': 'area',
        'treemap': 'area',

        'heatmap': 'shading_color_saturation',
        'choropleth': 'shading_color_saturation'
    }

    @classmethod
    def get_chart_accuracy_score(cls, chart_type: str) -> float:
        """Get perceptual accuracy score for chart type."""
        encoding = cls.CHART_ENCODING_MAP.get(chart_type, 'area')
        return cls.ENCODING_ACCURACY_SCORES.get(encoding, 0.5)

    @classmethod
    def filter_charts_by_accuracy(
        cls,
        chart_types: List[str],
        min_accuracy: float
    ) -> List[str]:
        """Filter chart types by minimum perceptual accuracy threshold."""
        return [
            chart_type for chart_type in chart_types
            if cls.get_chart_accuracy_score(chart_type) >= min_accuracy
        ]


@dataclass
class CognitiveLoadMetrics:
    """Cognitive load assessment metrics for visualization complexity."""
    visual_complexity_score: float  # 0.0-1.0
    information_density_score: float  # 0.0-1.0
    interaction_complexity_score: float  # 0.0-1.0
    color_complexity_score: float  # 0.0-1.0
    overall_cognitive_load: float  # 0.0-1.0

    # Recommendations
    simplification_needed: bool
    recommended_changes: List[str]


class PersonaAwareVisualizationSelector:
    """
    Advanced visualization selection system that extends LIDA's basic persona
    parameter with detailed persona profiles, perceptual hierarchy filtering,
    and cognitive load assessment.
    """

    def __init__(self):
        """Initialize the persona-aware visualization selector."""
        self.persona_database = self._initialize_persona_database()
        self.cleveland_mcgill = ClevelandMcGillHierarchy()
        self.ftvv_chart_mapping = self._initialize_ftvv_mapping()

        logger.info("PersonaAwareVisualizationSelector initialized")

    def _initialize_persona_database(self) -> Dict[str, PersonaProfile]:
        """Initialize comprehensive persona database."""
        personas = {
            PersonaType.EXECUTIVE.value: PersonaProfile(
                persona_type=PersonaType.EXECUTIVE,
                name="Executive",
                description="C-suite executives focused on strategic KPIs and high-level trends",
                cognitive_level=CognitiveLevelType.MEDIUM,
                attention_span_minutes=5,
                data_literacy_level=6,
                preferred_chart_types=['bar', 'line', 'pie'],
                forbidden_chart_types=['heatmap', 'sankey', 'network', 'violin'],
                max_data_points=20,
                max_series_count=3,
                max_categories=8,
                perceptual_accuracy_threshold=0.80,
                allow_complex_encodings=False,
                color_blind_friendly=True,
                high_contrast_required=True,
                screen_reader_support=True,
                decision_making_level="strategic",
                time_horizon="long-term",
                key_metrics=["revenue", "growth", "roi", "market_share"],
                interaction_preferences=["export", "drill-down"]
            ),

            PersonaType.ANALYST.value: PersonaProfile(
                persona_type=PersonaType.ANALYST,
                name="Data Analyst",
                description="Technical analysts requiring detailed exploration capabilities",
                cognitive_level=CognitiveLevelType.HIGH,
                attention_span_minutes=30,
                data_literacy_level=9,
                preferred_chart_types=['scatter', 'heatmap', 'box_plot', 'violin', 'histogram'],
                forbidden_chart_types=[],
                max_data_points=1000,
                max_series_count=20,
                max_categories=100,
                perceptual_accuracy_threshold=0.60,
                allow_complex_encodings=True,
                color_blind_friendly=True,
                high_contrast_required=False,
                screen_reader_support=True,
                decision_making_level="tactical",
                time_horizon="short-term",
                key_metrics=["correlation", "variance", "distribution", "outliers"],
                interaction_preferences=["filtering", "brush_selection", "zoom", "export"]
            ),

            PersonaType.MANAGER.value: PersonaProfile(
                persona_type=PersonaType.MANAGER,
                name="Operations Manager",
                description="Middle management focused on operational metrics and team performance",
                cognitive_level=CognitiveLevelType.MEDIUM,
                attention_span_minutes=15,
                data_literacy_level=7,
                preferred_chart_types=['bar', 'line', 'area', 'stacked_bar'],
                forbidden_chart_types=['sankey', 'treemap', 'network'],
                max_data_points=100,
                max_series_count=8,
                max_categories=25,
                perceptual_accuracy_threshold=0.75,
                allow_complex_encodings=False,
                color_blind_friendly=True,
                high_contrast_required=False,
                screen_reader_support=True,
                decision_making_level="tactical",
                time_horizon="short-term",
                key_metrics=["efficiency", "productivity", "utilization", "performance"],
                interaction_preferences=["drill-down", "filtering", "export"]
            ),

            PersonaType.STAKEHOLDER.value: PersonaProfile(
                persona_type=PersonaType.STAKEHOLDER,
                name="Business Stakeholder",
                description="Non-technical stakeholders needing clear business insights",
                cognitive_level=CognitiveLevelType.LOW,
                attention_span_minutes=8,
                data_literacy_level=4,
                preferred_chart_types=['bar', 'pie', 'line'],
                forbidden_chart_types=['heatmap', 'scatter', 'box_plot', 'violin', 'sankey'],
                max_data_points=15,
                max_series_count=2,
                max_categories=6,
                perceptual_accuracy_threshold=0.85,
                allow_complex_encodings=False,
                color_blind_friendly=True,
                high_contrast_required=True,
                screen_reader_support=True,
                decision_making_level="strategic",
                time_horizon="long-term",
                key_metrics=["revenue", "cost", "profit", "growth"],
                interaction_preferences=["export"]
            ),

            PersonaType.TECHNICAL_LEAD.value: PersonaProfile(
                persona_type=PersonaType.TECHNICAL_LEAD,
                name="Technical Lead",
                description="Technical leaders requiring system and performance metrics",
                cognitive_level=CognitiveLevelType.EXPERT,
                attention_span_minutes=45,
                data_literacy_level=10,
                preferred_chart_types=['line', 'heatmap', 'scatter', 'histogram', 'network'],
                forbidden_chart_types=[],
                max_data_points=5000,
                max_series_count=50,
                max_categories=200,
                perceptual_accuracy_threshold=0.50,
                allow_complex_encodings=True,
                color_blind_friendly=True,
                high_contrast_required=False,
                screen_reader_support=False,
                decision_making_level="operational",
                time_horizon="immediate",
                key_metrics=["latency", "throughput", "error_rate", "capacity"],
                interaction_preferences=["filtering", "brush_selection", "zoom", "real_time"]
            )
        }

        return personas

    def _initialize_ftvv_mapping(self) -> Dict[FTVVNarrativeGoal, Dict[str, Any]]:
        """Initialize FTVV narrative goal to chart type mapping."""
        return {
            FTVVNarrativeGoal.MAGNITUDE_COMPARISON: {
                'primary_charts': ['bar', 'column', 'horizontal_bar'],
                'secondary_charts': ['bullet_chart', 'waterfall'],
                'weight': 1.0,
                'data_requirements': ['categorical_dimension', 'numeric_measure']
            },

            FTVVNarrativeGoal.RANKING: {
                'primary_charts': ['bar', 'column', 'horizontal_bar'],
                'secondary_charts': ['lollipop', 'dot_plot'],
                'weight': 0.95,
                'data_requirements': ['categorical_dimension', 'numeric_measure', 'orderable']
            },

            FTVVNarrativeGoal.CHANGE_OVER_TIME: {
                'primary_charts': ['line', 'area', 'step_line'],
                'secondary_charts': ['stream_graph', 'ridge_line'],
                'weight': 1.0,
                'data_requirements': ['time_dimension', 'numeric_measure']
            },

            FTVVNarrativeGoal.DISTRIBUTION: {
                'primary_charts': ['histogram', 'box_plot', 'violin'],
                'secondary_charts': ['density_plot', 'strip_plot'],
                'weight': 0.85,
                'data_requirements': ['numeric_measure', 'sufficient_data_points']
            },

            FTVVNarrativeGoal.CORRELATION: {
                'primary_charts': ['scatter', 'scatter_matrix'],
                'secondary_charts': ['correlation_heatmap', 'parallel_coordinates'],
                'weight': 0.90,
                'data_requirements': ['numeric_measure_x', 'numeric_measure_y']
            },

            FTVVNarrativeGoal.PART_TO_WHOLE: {
                'primary_charts': ['pie', 'donut', 'treemap'],
                'secondary_charts': ['stacked_bar', 'waffle_chart'],
                'weight': 0.80,
                'data_requirements': ['categorical_dimension', 'numeric_measure', 'additive']
            },

            FTVVNarrativeGoal.DEVIATION: {
                'primary_charts': ['bar', 'bullet_chart', 'diverging_bar'],
                'secondary_charts': ['error_bar', 'confidence_interval'],
                'weight': 0.75,
                'data_requirements': ['reference_value', 'numeric_measure']
            },

            FTVVNarrativeGoal.FLOW: {
                'primary_charts': ['sankey', 'alluvial'],
                'secondary_charts': ['chord_diagram', 'flow_map'],
                'weight': 0.70,
                'data_requirements': ['source', 'target', 'flow_value']
            },

            FTVVNarrativeGoal.HIERARCHY: {
                'primary_charts': ['treemap', 'sunburst', 'tree'],
                'secondary_charts': ['icicle', 'nested_treemap'],
                'weight': 0.80,
                'data_requirements': ['hierarchical_structure', 'numeric_measure']
            }
        }

    def get_persona_profile(self, persona_id: str) -> Optional[PersonaProfile]:
        """Get detailed persona profile by ID."""
        return self.persona_database.get(persona_id)

    def select_optimal_visualization(
        self,
        data_summary: Dict[str, Any],
        goal: Dict[str, Any],
        persona_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Select optimal visualization using persona-aware, FTVV-based algorithm
        with Cleveland-McGill perceptual hierarchy filtering.

        Args:
            data_summary: Enhanced data summary from LIDA
            goal: Visualization goal with narrative intent
            persona_id: Target persona identifier
            context: Additional context for selection

        Returns:
            Comprehensive visualization selection with rationale
        """
        try:
            # Get persona profile
            persona = self.get_persona_profile(persona_id)
            if not persona:
                persona = self.persona_database[PersonaType.ANALYST.value]  # Default fallback

            # Determine narrative goal from question/intent
            narrative_goal = self._classify_narrative_goal(goal, data_summary)

            # Get candidate chart types from FTVV mapping
            candidate_charts = self._get_ftvv_candidate_charts(narrative_goal, data_summary)

            # Apply Cleveland-McGill perceptual hierarchy filtering
            perceptually_accurate_charts = self.cleveland_mcgill.filter_charts_by_accuracy(
                candidate_charts, persona.perceptual_accuracy_threshold
            )

            # Apply persona constraints
            persona_filtered_charts = self._apply_persona_constraints(
                perceptually_accurate_charts, persona
            )

            # Perform multi-criteria decision matrix scoring
            scored_charts = self._score_charts_multi_criteria(
                persona_filtered_charts, data_summary, goal, persona, narrative_goal
            )

            # Select optimal chart
            optimal_chart = self._select_optimal_chart(scored_charts)

            # Assess cognitive load
            cognitive_assessment = self._assess_cognitive_load(
                optimal_chart, data_summary, persona
            )

            return {
                'selected_chart_type': optimal_chart['chart_type'],
                'selection_score': optimal_chart['total_score'],
                'narrative_goal': narrative_goal.value,
                'persona_profile': {
                    'name': persona.name,
                    'cognitive_level': persona.cognitive_level.value,
                    'data_literacy': persona.data_literacy_level
                },
                'cleveland_mcgill_accuracy': self.cleveland_mcgill.get_chart_accuracy_score(
                    optimal_chart['chart_type']
                ),
                'cognitive_load_assessment': cognitive_assessment.__dict__,
                'alternative_charts': [
                    {
                        'chart_type': chart['chart_type'],
                        'score': chart['total_score'],
                        'rationale': chart['rationale']
                    }
                    for chart in scored_charts[1:4]  # Top 3 alternatives
                ],
                'selection_rationale': optimal_chart['rationale'],
                'data_constraints': {
                    'max_data_points': min(persona.max_data_points,
                                         len(data_summary.get('sample_data', []))),
                    'max_series': persona.max_series_count,
                    'max_categories': persona.max_categories
                },
                'accessibility_features': {
                    'color_blind_friendly': persona.color_blind_friendly,
                    'high_contrast': persona.high_contrast_required,
                    'screen_reader': persona.screen_reader_support
                }
            }

        except Exception as exc:
            logger.error("Failed to select optimal visualization: %s", exc)
            raise

    def _classify_narrative_goal(
        self,
        goal: Dict[str, Any],
        data_summary: Dict[str, Any]
    ) -> FTVVNarrativeGoal:
        """Classify visualization goal into FTVV narrative categories."""

        question = goal.get('question', '').lower()
        visualization = goal.get('visualization', '').lower()

        # Keyword-based classification with data pattern analysis
        if any(word in question for word in ['compare', 'versus', 'vs', 'difference', 'which is']):
            return FTVVNarrativeGoal.MAGNITUDE_COMPARISON

        if any(word in question for word in ['rank', 'top', 'bottom', 'best', 'worst', 'order']):
            return FTVVNarrativeGoal.RANKING

        if any(word in question for word in ['trend', 'over time', 'change', 'evolution', 'growth']):
            return FTVVNarrativeGoal.CHANGE_OVER_TIME

        if any(word in question for word in ['distribution', 'spread', 'histogram', 'frequency']):
            return FTVVNarrativeGoal.DISTRIBUTION

        if any(word in question for word in ['correlation', 'relationship', 'associate', 'related']):
            return FTVVNarrativeGoal.CORRELATION

        if any(word in question for word in ['composition', 'breakdown', 'percentage', 'proportion']):
            return FTVVNarrativeGoal.PART_TO_WHOLE

        if any(word in question for word in ['deviation', 'variance', 'outlier', 'anomaly']):
            return FTVVNarrativeGoal.DEVIATION

        if any(word in question for word in ['flow', 'movement', 'transition', 'path']):
            return FTVVNarrativeGoal.FLOW

        if any(word in question for word in ['hierarchy', 'structure', 'breakdown', 'nested']):
            return FTVVNarrativeGoal.HIERARCHY

        # Default to magnitude comparison for unclear goals
        return FTVVNarrativeGoal.MAGNITUDE_COMPARISON

    def _get_ftvv_candidate_charts(
        self,
        narrative_goal: FTVVNarrativeGoal,
        data_summary: Dict[str, Any]
    ) -> List[str]:
        """Get candidate chart types from FTVV mapping."""

        ftvv_mapping = self.ftvv_chart_mapping.get(narrative_goal)
        if not ftvv_mapping:
            return ['bar', 'line', 'scatter']  # Default fallback

        # Check data requirements
        data_types = data_summary.get('data_types', {})
        columns = data_summary.get('columns', [])

        candidate_charts = ftvv_mapping['primary_charts'][:]

        # Add secondary charts if data supports them
        requirements = ftvv_mapping.get('data_requirements', [])
        if self._check_data_requirements(requirements, data_types, columns):
            candidate_charts.extend(ftvv_mapping['secondary_charts'])

        return candidate_charts

    def _check_data_requirements(
        self,
        requirements: List[str],
        data_types: Dict[str, str],
        columns: List[str]
    ) -> bool:
        """Check if data meets chart requirements."""

        for requirement in requirements:
            if requirement == 'categorical_dimension':
                if not any(dtype == 'categorical' for dtype in data_types.values()):
                    return False
            elif requirement == 'numeric_measure':
                if not any(dtype == 'numeric' for dtype in data_types.values()):
                    return False
            elif requirement == 'time_dimension':
                if not any('date' in col.lower() or 'time' in col.lower()
                          for col in columns):
                    return False
            elif requirement == 'sufficient_data_points':
                if len(data_types) < 50:  # Minimum for distribution analysis
                    return False

        return True

    def _apply_persona_constraints(
        self,
        candidate_charts: List[str],
        persona: PersonaProfile
    ) -> List[str]:
        """Apply persona-specific constraints to filter chart types."""

        # Start with all candidate charts, then apply constraints
        filtered_charts = candidate_charts[:]

        # Remove forbidden chart types
        filtered_charts = [
            chart for chart in filtered_charts
            if chart not in persona.forbidden_chart_types
        ]

        # If persona has preferred charts, prioritize them but don't exclusively use them
        # This allows analysts to have broader selection while still respecting preferences
        if persona.preferred_chart_types:
            # Separate into preferred and allowed
            preferred_charts = [
                chart for chart in filtered_charts
                if chart in persona.preferred_chart_types
            ]
            other_allowed_charts = [
                chart for chart in filtered_charts
                if chart not in persona.preferred_chart_types
            ]

            # For high cognitive level personas, include additional allowed charts
            if persona.cognitive_level in [CognitiveLevelType.HIGH, CognitiveLevelType.EXPERT]:
                filtered_charts = preferred_charts + other_allowed_charts
            else:
                # For lower cognitive levels, stick closer to preferences
                filtered_charts = preferred_charts if preferred_charts else other_allowed_charts

        # Ensure we have at least one chart
        if not filtered_charts:
            filtered_charts = ['bar']  # Safe fallback

        return filtered_charts

    def _score_charts_multi_criteria(
        self,
        chart_types: List[str],
        data_summary: Dict[str, Any],
        goal: Dict[str, Any],
        persona: PersonaProfile,
        narrative_goal: FTVVNarrativeGoal
    ) -> List[Dict[str, Any]]:
        """Score chart types using multi-criteria decision matrix."""

        scored_charts = []

        for chart_type in chart_types:
            # Perceptual accuracy score (30% weight)
            perceptual_score = self.cleveland_mcgill.get_chart_accuracy_score(chart_type)

            # Persona preference score (25% weight)
            preference_score = 1.0 if chart_type in persona.preferred_chart_types else 0.7

            # Narrative goal alignment score (25% weight)
            ftvv_mapping = self.ftvv_chart_mapping.get(narrative_goal, {})
            if chart_type in ftvv_mapping.get('primary_charts', []):
                narrative_score = 1.0
            elif chart_type in ftvv_mapping.get('secondary_charts', []):
                narrative_score = 0.8
            else:
                narrative_score = 0.5

            # Cognitive complexity score (20% weight)
            complexity_score = self._calculate_cognitive_complexity_score(
                chart_type, persona
            )

            # Calculate weighted total score
            total_score = (
                perceptual_score * 0.30 +
                preference_score * 0.25 +
                narrative_score * 0.25 +
                complexity_score * 0.20
            )

            scored_charts.append({
                'chart_type': chart_type,
                'total_score': total_score,
                'perceptual_score': perceptual_score,
                'preference_score': preference_score,
                'narrative_score': narrative_score,
                'complexity_score': complexity_score,
                'rationale': f"Selected for {narrative_goal.value} with {perceptual_score:.2f} perceptual accuracy"
            })

        # Sort by total score descending
        return sorted(scored_charts, key=lambda x: x['total_score'], reverse=True)

    def _calculate_cognitive_complexity_score(
        self,
        chart_type: str,
        persona: PersonaProfile
    ) -> float:
        """Calculate cognitive complexity score for chart type and persona."""

        # Base complexity scores for chart types
        complexity_scores = {
            'bar': 0.9, 'column': 0.9, 'line': 0.85, 'pie': 0.8,
            'area': 0.75, 'scatter': 0.7, 'histogram': 0.65,
            'box_plot': 0.5, 'heatmap': 0.4, 'sankey': 0.2,
            'network': 0.1, 'parallel_coordinates': 0.1
        }

        base_score = complexity_scores.get(chart_type, 0.5)

        # Adjust for persona cognitive level
        if persona.cognitive_level == CognitiveLevelType.LOW:
            return base_score * 0.7  # Prefer simpler charts
        elif persona.cognitive_level == CognitiveLevelType.MEDIUM:
            return base_score * 0.85
        elif persona.cognitive_level == CognitiveLevelType.HIGH:
            return base_score
        else:  # EXPERT
            return min(base_score * 1.2, 1.0)  # Can handle complex charts

    def _select_optimal_chart(self, scored_charts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the optimal chart from scored candidates."""
        if not scored_charts:
            return {
                'chart_type': 'bar',
                'total_score': 0.5,
                'rationale': 'Default fallback selection'
            }

        return scored_charts[0]  # Highest scored chart

    def _assess_cognitive_load(
        self,
        selected_chart: Dict[str, Any],
        data_summary: Dict[str, Any],
        persona: PersonaProfile
    ) -> CognitiveLoadMetrics:
        """Assess cognitive load of selected visualization."""

        chart_type = selected_chart['chart_type']

        # Visual complexity assessment
        visual_complexity = self._calculate_visual_complexity(chart_type, data_summary)

        # Information density assessment
        info_density = self._calculate_information_density(data_summary, persona)

        # Interaction complexity
        interaction_complexity = self._calculate_interaction_complexity(chart_type, persona)

        # Color complexity
        color_complexity = self._calculate_color_complexity(chart_type, data_summary)

        # Overall cognitive load (weighted average)
        overall_load = (
            visual_complexity * 0.35 +
            info_density * 0.30 +
            interaction_complexity * 0.20 +
            color_complexity * 0.15
        )

        # Determine if simplification is needed
        simplification_needed = overall_load > 0.7 or (
            persona.cognitive_level == CognitiveLevelType.LOW and overall_load > 0.5
        )

        # Generate recommendations
        recommendations = []
        if visual_complexity > 0.7:
            recommendations.append("Simplify chart design elements")
        if info_density > 0.8:
            recommendations.append("Reduce data points or use pagination")
        if interaction_complexity > 0.6 and persona.cognitive_level == CognitiveLevelType.LOW:
            recommendations.append("Limit interactive features")
        if color_complexity > 0.7:
            recommendations.append("Use simpler color scheme")

        return CognitiveLoadMetrics(
            visual_complexity_score=visual_complexity,
            information_density_score=info_density,
            interaction_complexity_score=interaction_complexity,
            color_complexity_score=color_complexity,
            overall_cognitive_load=overall_load,
            simplification_needed=simplification_needed,
            recommended_changes=recommendations
        )

    def _calculate_visual_complexity(
        self,
        chart_type: str,
        data_summary: Dict[str, Any]
    ) -> float:
        """Calculate visual complexity score."""

        # Base complexity by chart type
        base_complexity = {
            'bar': 0.2, 'line': 0.3, 'pie': 0.4, 'scatter': 0.5,
            'area': 0.6, 'heatmap': 0.8, 'sankey': 0.9, 'network': 1.0
        }.get(chart_type, 0.5)

        # Adjust for data volume
        data_points = len(data_summary.get('sample_data', []))
        if data_points > 100:
            base_complexity += 0.2
        elif data_points > 50:
            base_complexity += 0.1

        return min(base_complexity, 1.0)

    def _calculate_information_density(
        self,
        data_summary: Dict[str, Any],
        persona: PersonaProfile
    ) -> float:
        """Calculate information density score."""

        data_points = len(data_summary.get('sample_data', []))
        columns = len(data_summary.get('columns', []))

        # Calculate density relative to persona limits
        point_density = min(data_points / persona.max_data_points, 1.0)
        column_density = min(columns / 10, 1.0)  # Assume 10 columns as high density

        return (point_density + column_density) / 2

    def _calculate_interaction_complexity(
        self,
        chart_type: str,
        persona: PersonaProfile
    ) -> float:
        """Calculate interaction complexity score."""

        # Chart types with higher interaction complexity
        interaction_scores = {
            'bar': 0.3, 'line': 0.4, 'scatter': 0.6, 'heatmap': 0.7,
            'network': 0.9, 'sankey': 0.8
        }

        base_score = interaction_scores.get(chart_type, 0.5)

        # Consider persona interaction preferences
        if len(persona.interaction_preferences) > 3:
            base_score += 0.2

        return min(base_score, 1.0)

    def _calculate_color_complexity(
        self,
        chart_type: str,
        data_summary: Dict[str, Any]
    ) -> float:
        """Calculate color complexity score."""

        # Estimate color usage based on data categories
        categorical_cols = [
            col for col, dtype in data_summary.get('data_types', {}).items()
            if dtype == 'categorical'
        ]

        if not categorical_cols:
            return 0.2  # Minimal color usage

        # Estimate unique categories (simplified)
        estimated_categories = min(len(categorical_cols) * 5, 20)

        if estimated_categories > 12:
            return 0.9  # High color complexity
        elif estimated_categories > 8:
            return 0.6
        else:
            return 0.3


# Factory function for integration
async def create_persona_aware_selector() -> PersonaAwareVisualizationSelector:
    """
    Factory function to create PersonaAwareVisualizationSelector instance.

    Returns:
        Configured PersonaAwareVisualizationSelector instance
    """
    selector = PersonaAwareVisualizationSelector()
    logger.info("Created PersonaAwareVisualizationSelector for enhanced LIDA integration")
    return selector