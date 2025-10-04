"""
Frontend Integration with AG-UI System.

This module adapts LIDA's web API to work with CopilotKit actions, implements
streaming responses, adds drill-down capabilities, and creates backend support
for interactive ECharts components with feedback loops.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncGenerator, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class StreamingEventType(Enum):
    """Types of streaming events for progressive visualization generation."""
    ANALYSIS_STARTED = "analysis_started"
    DATA_SUMMARY_GENERATED = "data_summary_generated"
    GOALS_GENERATED = "goals_generated"
    VISUALIZATION_GENERATED = "visualization_generated"
    CHART_RENDERED = "chart_rendered"
    INTERACTION_READY = "interaction_ready"
    ERROR = "error"
    COMPLETED = "completed"


class DrillDownType(Enum):
    """Types of drill-down operations."""
    FILTER = "filter"
    GROUP_BY = "group_by"
    ZOOM = "zoom"
    DETAIL_VIEW = "detail_view"
    RELATED_DATA = "related_data"


@dataclass
class StreamingEvent:
    """Streaming event for progressive visualization generation."""
    event_type: StreamingEventType
    timestamp: datetime
    user_id: str
    session_id: str

    # Event data
    data: Dict[str, Any]
    progress_percentage: float  # 0.0 - 1.0

    # Error information (if applicable)
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Metadata
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None


@dataclass
class DrillDownContext:
    """Context for drill-down operations."""
    drill_down_id: str
    user_id: str
    session_id: str
    parent_visualization_id: str

    # Drill-down operation
    drill_down_type: DrillDownType
    target_dimension: str
    filter_criteria: Dict[str, Any]

    # Navigation state
    breadcrumb_path: List[Dict[str, str]]
    context_preservation: Dict[str, Any]

    # Multi-dimensional exploration
    available_dimensions: List[str]
    related_metrics: List[str]

    # Timestamp
    created_at: datetime


@dataclass
class FeedbackData:
    """User feedback data for chart interactions."""
    feedback_id: str
    user_id: str
    visualization_id: str
    timestamp: datetime

    # Feedback type
    feedback_type: str  # rating, comment, interaction, customization

    # Rating feedback
    rating_score: Optional[int] = None  # 1-5 scale
    rating_aspects: Optional[Dict[str, int]] = None  # clarity, usefulness, accuracy

    # Comment feedback
    comment_text: Optional[str] = None
    sentiment_score: Optional[float] = None  # -1.0 to 1.0

    # Interaction feedback
    interaction_duration_seconds: Optional[float] = None
    click_count: Optional[int] = None
    zoom_count: Optional[int] = None
    export_attempted: Optional[bool] = None

    # Customization feedback
    customization_changes: Optional[Dict[str, Any]] = None
    preferred_chart_type: Optional[str] = None


class CopilotKitVisualizationHandler:
    """
    Handler for CopilotKit actions that integrates with LIDA Enhanced Manager.

    This class provides the backend support for AG-UI actions, streaming responses,
    drill-down capabilities, and interactive chart feedback loops.
    """

    def __init__(
        self,
        lida_manager,
        memory_manager=None,
        persona_selector=None,
        semantic_integration=None
    ):
        """
        Initialize the CopilotKit visualization handler.

        Args:
            lida_manager: LIDA Enhanced Manager instance
            memory_manager: Memory Context Manager instance
            persona_selector: Persona-Aware Visualization Selector instance
            semantic_integration: Semantic Layer Integration instance
        """
        self.lida_manager = lida_manager
        self.memory_manager = memory_manager
        self.persona_selector = persona_selector
        self.semantic_integration = semantic_integration

        # Active streaming sessions
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._drill_down_contexts: Dict[str, DrillDownContext] = {}
        self._user_feedback: Dict[str, List[FeedbackData]] = {}

        logger.info("CopilotKitVisualizationHandler initialized")

    async def handle_generate_visualization(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        data_context: Optional[Dict[str, Any]] = None,
        persona: str = "analyst",
        streaming: bool = True
    ) -> Dict[str, Any]:
        """
        Handle CopilotKit generateVisualization action.

        Args:
            query: Natural language query from user
            user_id: User identifier
            session_id: Optional session identifier
            data_context: Optional data context
            persona: User persona
            streaming: Enable streaming response

        Returns:
            Visualization result with AG-UI integration
        """
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"

            if streaming:
                # Return streaming response handler
                return {
                    "streaming": True,
                    "session_id": session_id,
                    "stream_url": f"/api/lida/stream/{session_id}",
                    "status": "started"
                }
            else:
                # Return complete response
                result = await self._generate_complete_visualization(
                    query, user_id, session_id, data_context, persona
                )
                return result

        except Exception as exc:
            logger.error("Failed to handle generateVisualization action: %s", exc)
            return {
                "error": True,
                "message": str(exc),
                "error_code": "GENERATION_FAILED"
            }

    async def stream_visualization_generation(
        self,
        query: str,
        user_id: str,
        session_id: str,
        data_context: Optional[Dict[str, Any]] = None,
        persona: str = "analyst"
    ) -> AsyncGenerator[StreamingEvent, None]:
        """
        Stream progressive visualization generation with real-time updates.

        Args:
            query: Natural language query
            user_id: User identifier
            session_id: Session identifier
            data_context: Optional data context
            persona: User persona

        Yields:
            StreamingEvent objects for progressive updates
        """
        try:
            start_time = datetime.now()

            # Initialize session
            self._active_sessions[session_id] = {
                "user_id": user_id,
                "query": query,
                "start_time": start_time,
                "status": "active"
            }

            # Step 1: Analysis Started
            yield StreamingEvent(
                event_type=StreamingEventType.ANALYSIS_STARTED,
                timestamp=datetime.now(),
                user_id=user_id,
                session_id=session_id,
                data={"query": query, "persona": persona},
                progress_percentage=0.0
            )

            # Step 2: Get user context if memory manager available
            context = {}
            if self.memory_manager:
                context = await self.memory_manager.get_user_context(user_id)

            # Step 3: Data Summary Generation
            if data_context:
                enhanced_summary = await self.lida_manager.summarize_data(
                    data_context, summary_method="enhanced"
                )
            else:
                # Use dashboard context
                enhanced_summary = await self.lida_manager.summarize_data(
                    self.lida_manager.dashboard_context, summary_method="enhanced"
                )

            yield StreamingEvent(
                event_type=StreamingEventType.DATA_SUMMARY_GENERATED,
                timestamp=datetime.now(),
                user_id=user_id,
                session_id=session_id,
                data={"summary": enhanced_summary.dict()},
                progress_percentage=0.3
            )

            # Step 4: Goals Generation
            goals = await self.lida_manager.generate_goals(
                enhanced_summary, n=3, persona=persona
            )

            yield StreamingEvent(
                event_type=StreamingEventType.GOALS_GENERATED,
                timestamp=datetime.now(),
                user_id=user_id,
                session_id=session_id,
                data={"goals": [goal.dict() for goal in goals]},
                progress_percentage=0.6
            )

            # Step 5: Visualization Generation
            if goals:
                primary_goal = goals[0]
                visualization_spec = await self.lida_manager.visualize_goal(
                    primary_goal, enhanced_summary
                )

                yield StreamingEvent(
                    event_type=StreamingEventType.VISUALIZATION_GENERATED,
                    timestamp=datetime.now(),
                    user_id=user_id,
                    session_id=session_id,
                    data={"visualization": visualization_spec},
                    progress_percentage=0.8
                )

                # Step 6: Chart Rendered (frontend would handle actual rendering)
                yield StreamingEvent(
                    event_type=StreamingEventType.CHART_RENDERED,
                    timestamp=datetime.now(),
                    user_id=user_id,
                    session_id=session_id,
                    data={
                        "chart_config": visualization_spec.get("echarts_config", {}),
                        "chart_type": visualization_spec.get("chart_type", "bar")
                    },
                    progress_percentage=0.9
                )

                # Step 7: Interaction Ready
                yield StreamingEvent(
                    event_type=StreamingEventType.INTERACTION_READY,
                    timestamp=datetime.now(),
                    user_id=user_id,
                    session_id=session_id,
                    data={
                        "interactive_features": visualization_spec.get("interactive_features", []),
                        "drill_down_available": True,
                        "feedback_enabled": True
                    },
                    progress_percentage=1.0
                )

                # Step 8: Completed
                total_duration = (datetime.now() - start_time).total_seconds() * 1000
                yield StreamingEvent(
                    event_type=StreamingEventType.COMPLETED,
                    timestamp=datetime.now(),
                    user_id=user_id,
                    session_id=session_id,
                    data={
                        "final_result": visualization_spec,
                        "total_duration_ms": total_duration
                    },
                    progress_percentage=1.0,
                    duration_ms=total_duration
                )

                # Store interaction in memory if available
                if self.memory_manager:
                    from memory_context_integration import UserInteraction, InteractionType
                    interaction = UserInteraction(
                        interaction_id=f"viz_{session_id}",
                        user_id=user_id,
                        timestamp=start_time,
                        interaction_type=InteractionType.VISUALIZATION_REQUEST,
                        original_query=query,
                        data_context=data_context or {},
                        persona=persona,
                        generated_visualization=visualization_spec,
                        selected_chart_type=visualization_spec.get("chart_type", "bar"),
                        narrative_goal=primary_goal.narrative_goal,
                        generation_time_ms=total_duration
                    )
                    await self.memory_manager.store_interaction(user_id, interaction)

            # Clean up session
            self._active_sessions.pop(session_id, None)

        except Exception as exc:
            logger.error("Streaming visualization generation failed: %s", exc)
            yield StreamingEvent(
                event_type=StreamingEventType.ERROR,
                timestamp=datetime.now(),
                user_id=user_id,
                session_id=session_id,
                data={},
                progress_percentage=0.0,
                error_message=str(exc),
                error_code="STREAMING_FAILED"
            )

    async def handle_drill_down(
        self,
        user_id: str,
        parent_visualization_id: str,
        drill_down_type: str,
        target_dimension: str,
        filter_criteria: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle drill-down operations with context preservation.

        Args:
            user_id: User identifier
            parent_visualization_id: ID of parent visualization
            drill_down_type: Type of drill-down operation
            target_dimension: Target dimension for drill-down
            filter_criteria: Filter criteria for drill-down
            session_id: Optional session identifier

        Returns:
            Drill-down result with navigation context
        """
        try:
            session_id = session_id or f"drill_{datetime.now().timestamp()}"
            drill_down_id = f"drill_{session_id}_{datetime.now().timestamp()}"

            # Get parent context if available
            parent_context = {}
            if self.memory_manager:
                parent_context = await self.memory_manager.get_user_context(user_id)

            # Create drill-down context
            drill_down_context = DrillDownContext(
                drill_down_id=drill_down_id,
                user_id=user_id,
                session_id=session_id,
                parent_visualization_id=parent_visualization_id,
                drill_down_type=DrillDownType(drill_down_type),
                target_dimension=target_dimension,
                filter_criteria=filter_criteria,
                breadcrumb_path=self._build_breadcrumb_path(parent_visualization_id, target_dimension),
                context_preservation=parent_context,
                available_dimensions=self._get_available_dimensions(filter_criteria),
                related_metrics=self._get_related_metrics(target_dimension),
                created_at=datetime.now()
            )

            # Store drill-down context
            self._drill_down_contexts[drill_down_id] = drill_down_context

            # Generate drill-down visualization
            drill_down_query = self._build_drill_down_query(drill_down_context)
            drill_down_data = self._apply_drill_down_filters(filter_criteria)

            # Use LIDA manager to generate drill-down visualization
            drill_down_summary = await self.lida_manager.summarize_data(drill_down_data)
            drill_down_goals = await self.lida_manager.generate_goals(
                drill_down_summary, n=1, persona="analyst"
            )

            if drill_down_goals:
                drill_down_viz = await self.lida_manager.visualize_goal(
                    drill_down_goals[0], drill_down_summary
                )

                result = {
                    "drill_down_id": drill_down_id,
                    "visualization": drill_down_viz,
                    "navigation": {
                        "breadcrumb_path": drill_down_context.breadcrumb_path,
                        "can_go_back": len(drill_down_context.breadcrumb_path) > 1,
                        "available_drill_downs": drill_down_context.available_dimensions,
                        "related_metrics": drill_down_context.related_metrics
                    },
                    "context_preservation": {
                        "parent_filters": filter_criteria,
                        "current_dimension": target_dimension,
                        "drill_down_type": drill_down_type
                    },
                    "interactive_features": [
                        "click_to_filter",
                        "breadcrumb_navigation",
                        "context_preservation",
                        "multi_dimensional_exploration"
                    ]
                }

                logger.info("Generated drill-down visualization for user %s", user_id)
                return result

            else:
                return {
                    "error": True,
                    "message": "Failed to generate drill-down visualization",
                    "error_code": "DRILL_DOWN_GENERATION_FAILED"
                }

        except Exception as exc:
            logger.error("Failed to handle drill-down: %s", exc)
            return {
                "error": True,
                "message": str(exc),
                "error_code": "DRILL_DOWN_FAILED"
            }

    async def handle_user_feedback(
        self,
        user_id: str,
        visualization_id: str,
        feedback_type: str,
        feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle user feedback for chart interactions and learning.

        Args:
            user_id: User identifier
            visualization_id: Visualization identifier
            feedback_type: Type of feedback
            feedback_data: Feedback data

        Returns:
            Feedback processing result
        """
        try:
            feedback_id = f"feedback_{user_id}_{datetime.now().timestamp()}"

            # Create feedback record
            feedback = FeedbackData(
                feedback_id=feedback_id,
                user_id=user_id,
                visualization_id=visualization_id,
                timestamp=datetime.now(),
                feedback_type=feedback_type,
                rating_score=feedback_data.get("rating_score"),
                rating_aspects=feedback_data.get("rating_aspects"),
                comment_text=feedback_data.get("comment_text"),
                sentiment_score=feedback_data.get("sentiment_score"),
                interaction_duration_seconds=feedback_data.get("interaction_duration_seconds"),
                click_count=feedback_data.get("click_count"),
                zoom_count=feedback_data.get("zoom_count"),
                export_attempted=feedback_data.get("export_attempted"),
                customization_changes=feedback_data.get("customization_changes"),
                preferred_chart_type=feedback_data.get("preferred_chart_type")
            )

            # Store feedback
            if user_id not in self._user_feedback:
                self._user_feedback[user_id] = []
            self._user_feedback[user_id].append(feedback)

            # Update memory manager if available
            if self.memory_manager:
                success = await self.memory_manager.update_user_feedback(
                    user_id, visualization_id, feedback_data
                )
                if not success:
                    logger.warning("Failed to update feedback in memory manager")

            # Analyze feedback for learning
            feedback_insights = await self._analyze_feedback(user_id, feedback)

            result = {
                "feedback_id": feedback_id,
                "processed": True,
                "insights": feedback_insights,
                "recommendations": await self._generate_feedback_recommendations(user_id, feedback),
                "learning_updates": {
                    "preference_updates": feedback_insights.get("preference_updates", []),
                    "persona_adjustments": feedback_insights.get("persona_adjustments", [])
                }
            }

            logger.info("Processed feedback %s for user %s", feedback_id, user_id)
            return result

        except Exception as exc:
            logger.error("Failed to handle user feedback: %s", exc)
            return {
                "error": True,
                "message": str(exc),
                "error_code": "FEEDBACK_PROCESSING_FAILED"
            }

    async def get_interactive_features(
        self,
        user_id: str,
        chart_type: str,
        persona: str = "analyst"
    ) -> Dict[str, Any]:
        """
        Get available interactive features for chart type and persona.

        Args:
            user_id: User identifier
            chart_type: Chart type
            persona: User persona

        Returns:
            Available interactive features configuration
        """
        try:
            # Base interactive features
            base_features = {
                "hover_tooltips": True,
                "click_interactions": True,
                "export_options": ["png", "svg", "pdf"],
                "zoom_pan": chart_type in ["scatter", "line", "bar"],
                "brush_selection": chart_type in ["scatter", "line", "heatmap"],
                "drill_down": True,
                "feedback_collection": True
            }

            # Persona-specific features
            if persona == "executive":
                persona_features = {
                    "simplified_interactions": True,
                    "executive_summary": True,
                    "key_insights_highlight": True,
                    "one_click_export": True
                }
            elif persona == "analyst":
                persona_features = {
                    "advanced_filtering": True,
                    "data_exploration": True,
                    "statistical_overlays": True,
                    "custom_calculations": True
                }
            else:
                persona_features = {
                    "guided_exploration": True,
                    "contextual_help": True
                }

            # User context features
            user_features = {}
            if self.memory_manager:
                user_context = await self.memory_manager.get_user_context(user_id)
                user_preferences = user_context.get("user_preferences", {})

                if user_preferences.get("preferred_interaction_features"):
                    user_features["personalized_shortcuts"] = user_preferences["preferred_interaction_features"]

                if user_context.get("interaction_analytics", {}).get("common_follow_up_actions"):
                    user_features["suggested_actions"] = list(user_context["interaction_analytics"]["common_follow_up_actions"].keys())[:3]

            # Combine all features
            interactive_features = {
                **base_features,
                **persona_features,
                **user_features,
                "customization_options": {
                    "color_schemes": ["default", "colorblind_friendly", "high_contrast"],
                    "chart_themes": ["light", "dark", "corporate"],
                    "font_sizes": ["small", "medium", "large"],
                    "interaction_modes": ["touch", "mouse", "keyboard"]
                },
                "accessibility_features": {
                    "screen_reader_support": True,
                    "keyboard_navigation": True,
                    "aria_labels": True,
                    "high_contrast_mode": True,
                    "focus_indicators": True
                }
            }

            return {
                "chart_type": chart_type,
                "persona": persona,
                "features": interactive_features,
                "feature_count": len([k for k, v in interactive_features.items() if isinstance(v, bool) and v])
            }

        except Exception as exc:
            logger.error("Failed to get interactive features: %s", exc)
            return {"error": True, "message": str(exc)}

    # Private helper methods

    async def _generate_complete_visualization(
        self,
        query: str,
        user_id: str,
        session_id: str,
        data_context: Optional[Dict[str, Any]],
        persona: str
    ) -> Dict[str, Any]:
        """Generate complete visualization without streaming."""

        # Use existing LIDA manager methods
        if data_context:
            summary = await self.lida_manager.summarize_data(data_context)
        else:
            summary = await self.lida_manager.summarize_data(self.lida_manager.dashboard_context)

        goals = await self.lida_manager.generate_goals(summary, n=1, persona=persona)

        if goals:
            visualization = await self.lida_manager.visualize_goal(goals[0], summary)
            return {
                "session_id": session_id,
                "visualization": visualization,
                "goal": goals[0].dict(),
                "summary": summary.dict(),
                "interactive_features": await self.get_interactive_features(user_id, visualization.get("chart_type", "bar"), persona)
            }
        else:
            return {
                "error": True,
                "message": "Failed to generate visualization goals",
                "error_code": "GOAL_GENERATION_FAILED"
            }

    def _build_breadcrumb_path(
        self,
        parent_visualization_id: str,
        target_dimension: str
    ) -> List[Dict[str, str]]:
        """Build breadcrumb navigation path."""

        # In a real implementation, this would reconstruct the path from stored contexts
        return [
            {"label": "Overview", "visualization_id": "root"},
            {"label": "Current View", "visualization_id": parent_visualization_id},
            {"label": target_dimension, "visualization_id": f"drill_{target_dimension}"}
        ]

    def _get_available_dimensions(self, filter_criteria: Dict[str, Any]) -> List[str]:
        """Get available dimensions for further drill-down."""

        # Mock implementation - would analyze data structure in practice
        all_dimensions = ["region", "product", "category", "time_period", "customer_segment"]

        # Remove already filtered dimensions
        filtered_dimensions = list(filter_criteria.keys())
        available = [dim for dim in all_dimensions if dim not in filtered_dimensions]

        return available[:5]  # Limit to 5 for UI

    def _get_related_metrics(self, dimension: str) -> List[str]:
        """Get metrics related to the dimension."""

        # Mock implementation - would use semantic layer in practice
        metric_mapping = {
            "region": ["revenue", "sales_count", "customer_count"],
            "product": ["revenue", "units_sold", "profit_margin"],
            "category": ["revenue", "market_share", "growth_rate"],
            "time_period": ["revenue", "growth_rate", "trend_score"],
            "customer_segment": ["revenue", "lifetime_value", "retention_rate"]
        }

        return metric_mapping.get(dimension, ["revenue", "count"])

    def _build_drill_down_query(self, context: DrillDownContext) -> str:
        """Build natural language query for drill-down."""

        dimension = context.target_dimension
        drill_type = context.drill_down_type.value

        if drill_type == "filter":
            return f"Show detailed breakdown by {dimension} with current filters applied"
        elif drill_type == "group_by":
            return f"Group data by {dimension} and show key metrics"
        else:
            return f"Explore {dimension} in detail"

    def _apply_drill_down_filters(self, filter_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Apply drill-down filters to data context."""

        # Mock implementation - would apply actual filters in practice
        return {
            "columns": ["dimension", "metric"],
            "data_types": {"dimension": "categorical", "metric": "numeric"},
            "filters": filter_criteria,
            "row_count": 100  # Estimated after filtering
        }

    async def _analyze_feedback(
        self,
        user_id: str,
        feedback: FeedbackData
    ) -> Dict[str, Any]:
        """Analyze feedback for insights and learning."""

        insights = {
            "feedback_sentiment": "positive" if (feedback.rating_score or 3) >= 4 else "negative",
            "interaction_engagement": "high" if (feedback.interaction_duration_seconds or 0) > 30 else "low",
            "chart_type_satisfaction": feedback.preferred_chart_type or "unknown"
        }

        # Analyze patterns in user feedback
        user_feedback_history = self._user_feedback.get(user_id, [])
        if len(user_feedback_history) > 1:
            recent_ratings = [f.rating_score for f in user_feedback_history[-5:] if f.rating_score]
            if recent_ratings:
                insights["satisfaction_trend"] = "improving" if recent_ratings[-1] > recent_ratings[0] else "declining"

        # Preference updates based on feedback
        if feedback.rating_score and feedback.rating_score >= 4:
            insights["preference_updates"] = [f"Positive feedback for {feedback.visualization_id}"]

        return insights

    async def _generate_feedback_recommendations(
        self,
        user_id: str,
        feedback: FeedbackData
    ) -> List[str]:
        """Generate recommendations based on feedback."""

        recommendations = []

        if feedback.rating_score and feedback.rating_score <= 2:
            recommendations.append("Consider simpler chart types for better clarity")
            recommendations.append("Enable additional interactive features")

        if feedback.preferred_chart_type and feedback.preferred_chart_type != "unknown":
            recommendations.append(f"Use {feedback.preferred_chart_type} charts more frequently")

        if feedback.interaction_duration_seconds and feedback.interaction_duration_seconds < 10:
            recommendations.append("Provide more engaging interactive elements")

        return recommendations


# Factory function for integration
async def create_copilotkit_handler(
    lida_manager,
    memory_manager=None,
    persona_selector=None,
    semantic_integration=None
) -> CopilotKitVisualizationHandler:
    """
    Factory function to create CopilotKitVisualizationHandler instance.

    Args:
        lida_manager: LIDA Enhanced Manager instance
        memory_manager: Optional Memory Context Manager instance
        persona_selector: Optional Persona-Aware Visualization Selector instance
        semantic_integration: Optional Semantic Layer Integration instance

    Returns:
        Configured CopilotKitVisualizationHandler instance
    """
    handler = CopilotKitVisualizationHandler(
        lida_manager=lida_manager,
        memory_manager=memory_manager,
        persona_selector=persona_selector,
        semantic_integration=semantic_integration
    )
    logger.info("Created CopilotKitVisualizationHandler for AG-UI integration")
    return handler