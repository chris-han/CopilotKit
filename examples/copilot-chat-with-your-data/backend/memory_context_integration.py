"""
Memory and Context Integration for LIDA Enhanced Manager.

This module replaces LIDA's stateless design with Mem0 context persistence,
implementing user interaction history tracking and contextual visualization
recommendations beyond LIDA's session scope.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class InteractionType(Enum):
    """Types of user interactions to track."""
    VISUALIZATION_REQUEST = "visualization_request"
    CHART_INTERACTION = "chart_interaction"
    DRILL_DOWN = "drill_down"
    EXPORT = "export"
    FEEDBACK = "feedback"
    PREFERENCE_UPDATE = "preference_update"


class ContextType(Enum):
    """Types of context information."""
    USER_PREFERENCES = "user_preferences"
    SESSION_HISTORY = "session_history"
    VISUALIZATION_PATTERNS = "visualization_patterns"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    INTERACTION_ANALYTICS = "interaction_analytics"


@dataclass
class UserInteraction:
    """Individual user interaction record."""
    interaction_id: str
    user_id: str
    timestamp: datetime
    interaction_type: InteractionType

    # Request context
    original_query: str
    data_context: Dict[str, Any]
    persona: str

    # Response context
    generated_visualization: Dict[str, Any]
    selected_chart_type: str
    narrative_goal: str

    # User behavior
    interaction_duration_seconds: Optional[float] = None
    user_feedback: Optional[Dict[str, Any]] = None
    follow_up_actions: List[str] = None

    # Performance metrics
    generation_time_ms: Optional[float] = None
    cognitive_load_score: Optional[float] = None
    user_satisfaction_score: Optional[int] = None  # 1-5 scale


@dataclass
class UserPreferences:
    """User's learned preferences and patterns."""
    user_id: str
    persona: str

    # Chart preferences
    preferred_chart_types: List[str]
    avoided_chart_types: List[str]
    complexity_tolerance: float  # 0.0-1.0

    # Interaction preferences
    typical_session_duration_minutes: float
    preferred_interaction_features: List[str]
    common_drill_down_patterns: List[List[str]]

    # Context preferences
    preferred_data_granularity: str  # summary, detailed, raw
    typical_question_types: List[str]
    domain_focus_areas: List[str]

    # Performance patterns
    average_satisfaction_score: float
    most_successful_chart_types: List[str]
    common_follow_up_patterns: List[str]

    # Temporal patterns
    last_updated: datetime
    interaction_count: int
    active_session_count: int


@dataclass
class ContextualRecommendation:
    """Contextual recommendation based on user history."""
    recommendation_id: str
    user_id: str
    recommendation_type: str  # chart_type, interaction, drill_down

    # Recommendation details
    recommended_action: str
    confidence_score: float  # 0.0-1.0
    reasoning: str

    # Context basis
    based_on_interactions: List[str]  # interaction_ids
    pattern_strength: float
    temporal_relevance: float

    # Personalization
    persona_alignment: float
    complexity_appropriateness: float

    # Metadata
    generated_at: datetime
    expires_at: Optional[datetime] = None


class MemoryContextManager:
    """
    Context-aware memory manager that replaces LIDA's stateless design
    with persistent user context, interaction history, and personalized
    recommendations.
    """

    def __init__(self, mem0_client=None):
        """
        Initialize the memory context manager.

        Args:
            mem0_client: Optional Mem0 client for persistent storage
        """
        self.mem0_client = mem0_client
        self.mock_mode = mem0_client is None

        # In-memory storage for mock mode
        self._user_interactions: Dict[str, List[UserInteraction]] = {}
        self._user_preferences: Dict[str, UserPreferences] = {}
        self._contextual_recommendations: Dict[str, List[ContextualRecommendation]] = {}

        # Analytics and pattern recognition
        self._interaction_patterns: Dict[str, Dict[str, Any]] = {}
        self._session_analytics: Dict[str, Dict[str, Any]] = {}

        logger.info("MemoryContextManager initialized (mock_mode=%s)", self.mock_mode)

    async def store_interaction(
        self,
        user_id: str,
        interaction: UserInteraction
    ) -> bool:
        """
        Store user interaction with context persistence.

        Args:
            user_id: User identifier
            interaction: User interaction to store

        Returns:
            Success status of storage operation
        """
        try:
            if self.mock_mode:
                # Store in memory for mock mode
                if user_id not in self._user_interactions:
                    self._user_interactions[user_id] = []
                self._user_interactions[user_id].append(interaction)

                # Update user preferences based on interaction
                await self._update_user_preferences(user_id, interaction)

                # Generate new recommendations
                await self._generate_contextual_recommendations(user_id)

                logger.debug("Stored interaction %s for user %s", interaction.interaction_id, user_id)
                return True
            else:
                # Use Mem0 client for persistent storage
                interaction_data = asdict(interaction)
                # Convert datetime objects to ISO strings for JSON serialization
                interaction_data['timestamp'] = interaction.timestamp.isoformat()

                result = await self.mem0_client.store(
                    user_id=user_id,
                    data=interaction_data,
                    category="interaction"
                )
                return result.get('success', False)

        except Exception as exc:
            logger.error("Failed to store interaction: %s", exc)
            return False

    async def get_user_context(
        self,
        user_id: str,
        context_types: Optional[List[ContextType]] = None,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Retrieve comprehensive user context for visualization generation.

        Args:
            user_id: User identifier
            context_types: Specific context types to retrieve
            lookback_days: Days of history to consider

        Returns:
            Comprehensive user context dictionary
        """
        try:
            if context_types is None:
                context_types = list(ContextType)

            context = {}
            cutoff_date = datetime.now() - timedelta(days=lookback_days)

            # Get user preferences
            if ContextType.USER_PREFERENCES in context_types:
                preferences = await self._get_user_preferences(user_id)
                context['user_preferences'] = asdict(preferences) if preferences else {}

            # Get session history
            if ContextType.SESSION_HISTORY in context_types:
                recent_interactions = await self._get_recent_interactions(user_id, cutoff_date)
                context['session_history'] = [asdict(interaction) for interaction in recent_interactions]

            # Get visualization patterns
            if ContextType.VISUALIZATION_PATTERNS in context_types:
                patterns = await self._analyze_visualization_patterns(user_id, cutoff_date)
                context['visualization_patterns'] = patterns

            # Get domain knowledge
            if ContextType.DOMAIN_KNOWLEDGE in context_types:
                domain_knowledge = await self._extract_domain_knowledge(user_id, cutoff_date)
                context['domain_knowledge'] = domain_knowledge

            # Get interaction analytics
            if ContextType.INTERACTION_ANALYTICS in context_types:
                analytics = await self._get_interaction_analytics(user_id, cutoff_date)
                context['interaction_analytics'] = analytics

            logger.debug("Retrieved context for user %s with %d types", user_id, len(context_types))
            return context

        except Exception as exc:
            logger.error("Failed to retrieve user context: %s", exc)
            return {}

    async def get_contextual_recommendations(
        self,
        user_id: str,
        current_query: str,
        data_context: Dict[str, Any],
        max_recommendations: int = 5
    ) -> List[ContextualRecommendation]:
        """
        Generate contextual recommendations based on user history and patterns.

        Args:
            user_id: User identifier
            current_query: Current visualization query
            data_context: Current data context
            max_recommendations: Maximum number of recommendations

        Returns:
            List of contextual recommendations
        """
        try:
            # Get existing recommendations
            existing_recommendations = self._contextual_recommendations.get(user_id, [])

            # Filter valid recommendations
            valid_recommendations = [
                rec for rec in existing_recommendations
                if rec.expires_at is None or rec.expires_at > datetime.now()
            ]

            # Generate new recommendations if needed
            if len(valid_recommendations) < max_recommendations:
                new_recommendations = await self._generate_query_specific_recommendations(
                    user_id, current_query, data_context
                )
                valid_recommendations.extend(new_recommendations)

            # Sort by confidence and relevance
            sorted_recommendations = sorted(
                valid_recommendations[:max_recommendations],
                key=lambda r: (r.confidence_score * r.temporal_relevance),
                reverse=True
            )

            logger.debug("Generated %d contextual recommendations for user %s",
                        len(sorted_recommendations), user_id)
            return sorted_recommendations

        except Exception as exc:
            logger.error("Failed to generate contextual recommendations: %s", exc)
            return []

    async def inject_context_into_query(
        self,
        user_id: str,
        original_query: str,
        data_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance query with user context and historical patterns.

        Args:
            user_id: User identifier
            original_query: Original user query
            data_context: Data context for visualization

        Returns:
            Enhanced query with contextual information
        """
        try:
            # Get user context
            user_context = await self.get_user_context(user_id)

            # Get user preferences
            preferences = user_context.get('user_preferences', {})

            # Analyze query patterns
            query_analysis = await self._analyze_query_intent(original_query, user_context)

            # Create enhanced query
            enhanced_query = {
                'original_query': original_query,
                'data_context': data_context,
                'user_context': {
                    'user_id': user_id,
                    'persona': preferences.get('persona', 'analyst'),
                    'preferred_chart_types': preferences.get('preferred_chart_types', []),
                    'complexity_tolerance': preferences.get('complexity_tolerance', 0.5),
                    'typical_interaction_features': preferences.get('preferred_interaction_features', [])
                },
                'query_analysis': query_analysis,
                'historical_patterns': {
                    'common_follow_ups': preferences.get('common_follow_up_patterns', []),
                    'successful_chart_types': preferences.get('most_successful_chart_types', []),
                    'drill_down_patterns': preferences.get('common_drill_down_patterns', [])
                },
                'contextual_hints': await self._generate_contextual_hints(user_id, original_query)
            }

            logger.debug("Enhanced query with context for user %s", user_id)
            return enhanced_query

        except Exception as exc:
            logger.error("Failed to inject context into query: %s", exc)
            return {
                'original_query': original_query,
                'data_context': data_context,
                'user_context': {'user_id': user_id}
            }

    async def update_user_feedback(
        self,
        user_id: str,
        interaction_id: str,
        feedback: Dict[str, Any]
    ) -> bool:
        """
        Update user feedback for an interaction and adjust preferences.

        Args:
            user_id: User identifier
            interaction_id: Interaction identifier
            feedback: User feedback data

        Returns:
            Success status of update operation
        """
        try:
            if self.mock_mode:
                # Find and update interaction
                user_interactions = self._user_interactions.get(user_id, [])
                for interaction in user_interactions:
                    if interaction.interaction_id == interaction_id:
                        interaction.user_feedback = feedback
                        interaction.user_satisfaction_score = feedback.get('satisfaction_score')

                        # Learn from feedback
                        await self._learn_from_feedback(user_id, interaction, feedback)
                        break

                return True
            else:
                # Use Mem0 client to update feedback
                feedback_data = {
                    'interaction_id': interaction_id,
                    'feedback': feedback,
                    'timestamp': datetime.now().isoformat()
                }

                result = await self.mem0_client.update(
                    user_id=user_id,
                    interaction_id=interaction_id,
                    data=feedback_data
                )
                return result.get('success', False)

        except Exception as exc:
            logger.error("Failed to update user feedback: %s", exc)
            return False

    async def get_interaction_analytics(
        self,
        user_id: str,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate analytics about user interactions and patterns.

        Args:
            user_id: User identifier
            time_period_days: Analysis time period in days

        Returns:
            Comprehensive interaction analytics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=time_period_days)
            recent_interactions = await self._get_recent_interactions(user_id, cutoff_date)

            if not recent_interactions:
                return {'total_interactions': 0}

            # Calculate analytics
            analytics = {
                'total_interactions': len(recent_interactions),
                'interaction_types': self._analyze_interaction_types(recent_interactions),
                'chart_type_usage': self._analyze_chart_usage(recent_interactions),
                'satisfaction_trends': self._analyze_satisfaction_trends(recent_interactions),
                'session_patterns': self._analyze_session_patterns(recent_interactions),
                'performance_metrics': self._analyze_performance_metrics(recent_interactions),
                'temporal_patterns': self._analyze_temporal_patterns(recent_interactions),
                'complexity_preferences': self._analyze_complexity_preferences(recent_interactions)
            }

            logger.debug("Generated interaction analytics for user %s", user_id)
            return analytics

        except Exception as exc:
            logger.error("Failed to generate interaction analytics: %s", exc)
            return {}

    # Private helper methods

    async def _get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences from storage."""
        if self.mock_mode:
            return self._user_preferences.get(user_id)
        else:
            # Would retrieve from Mem0 client
            return None

    async def _get_recent_interactions(
        self,
        user_id: str,
        cutoff_date: datetime
    ) -> List[UserInteraction]:
        """Get recent user interactions."""
        if self.mock_mode:
            user_interactions = self._user_interactions.get(user_id, [])
            return [
                interaction for interaction in user_interactions
                if interaction.timestamp >= cutoff_date
            ]
        else:
            # Would retrieve from Mem0 client
            return []

    async def _update_user_preferences(
        self,
        user_id: str,
        interaction: UserInteraction
    ) -> None:
        """Update user preferences based on new interaction."""

        if user_id not in self._user_preferences:
            # Create new preferences
            self._user_preferences[user_id] = UserPreferences(
                user_id=user_id,
                persona=interaction.persona,
                preferred_chart_types=[],
                avoided_chart_types=[],
                complexity_tolerance=0.5,
                typical_session_duration_minutes=15.0,
                preferred_interaction_features=[],
                common_drill_down_patterns=[],
                preferred_data_granularity="summary",
                typical_question_types=[],
                domain_focus_areas=[],
                average_satisfaction_score=3.0,
                most_successful_chart_types=[],
                common_follow_up_patterns=[],
                last_updated=datetime.now(),
                interaction_count=0,
                active_session_count=1
            )

        preferences = self._user_preferences[user_id]

        # Update based on interaction
        preferences.interaction_count += 1
        preferences.last_updated = datetime.now()

        # Update chart type preferences based on satisfaction
        if interaction.user_satisfaction_score:
            if interaction.user_satisfaction_score >= 4:
                if interaction.selected_chart_type not in preferences.preferred_chart_types:
                    preferences.preferred_chart_types.append(interaction.selected_chart_type)
            elif interaction.user_satisfaction_score <= 2:
                if interaction.selected_chart_type not in preferences.avoided_chart_types:
                    preferences.avoided_chart_types.append(interaction.selected_chart_type)

        # Update complexity tolerance
        if interaction.cognitive_load_score:
            current_tolerance = preferences.complexity_tolerance
            # Adjust based on interaction success
            if interaction.user_satisfaction_score and interaction.user_satisfaction_score >= 4:
                preferences.complexity_tolerance = min(1.0, current_tolerance + 0.05)
            elif interaction.user_satisfaction_score and interaction.user_satisfaction_score <= 2:
                preferences.complexity_tolerance = max(0.0, current_tolerance - 0.05)

    async def _generate_contextual_recommendations(self, user_id: str) -> None:
        """Generate new contextual recommendations for user."""

        recent_interactions = await self._get_recent_interactions(
            user_id, datetime.now() - timedelta(days=7)
        )

        if not recent_interactions:
            return

        recommendations = []

        # Chart type recommendations based on success patterns
        successful_charts = [
            interaction.selected_chart_type for interaction in recent_interactions
            if interaction.user_satisfaction_score and interaction.user_satisfaction_score >= 4
        ]

        if successful_charts:
            chart_counts = {}
            for chart in successful_charts:
                chart_counts[chart] = chart_counts.get(chart, 0) + 1

            most_successful = max(chart_counts.items(), key=lambda x: x[1])

            recommendations.append(ContextualRecommendation(
                recommendation_id=f"chart_{user_id}_{datetime.now().timestamp()}",
                user_id=user_id,
                recommendation_type="chart_type",
                recommended_action=f"Consider using {most_successful[0]} charts",
                confidence_score=min(0.9, most_successful[1] / len(recent_interactions)),
                reasoning=f"You've had {most_successful[1]} successful interactions with {most_successful[0]} charts",
                based_on_interactions=[i.interaction_id for i in recent_interactions],
                pattern_strength=most_successful[1] / len(recent_interactions),
                temporal_relevance=1.0,
                persona_alignment=0.8,
                complexity_appropriateness=0.7,
                generated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7)
            ))

        self._contextual_recommendations[user_id] = recommendations

    async def _generate_query_specific_recommendations(
        self,
        user_id: str,
        query: str,
        data_context: Dict[str, Any]
    ) -> List[ContextualRecommendation]:
        """Generate recommendations specific to current query."""

        recommendations = []

        # Analyze query intent
        query_lower = query.lower()

        if any(word in query_lower for word in ['compare', 'versus', 'difference']):
            recommendations.append(ContextualRecommendation(
                recommendation_id=f"query_{user_id}_{datetime.now().timestamp()}",
                user_id=user_id,
                recommendation_type="chart_type",
                recommended_action="Use bar or column charts for comparison",
                confidence_score=0.8,
                reasoning="Query indicates comparison intent",
                based_on_interactions=[],
                pattern_strength=0.8,
                temporal_relevance=1.0,
                persona_alignment=0.9,
                complexity_appropriateness=0.8,
                generated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=1)
            ))

        return recommendations

    async def _analyze_query_intent(
        self,
        query: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze query intent with user context."""

        query_lower = query.lower()

        # Basic intent classification
        intents = []
        if any(word in query_lower for word in ['compare', 'versus', 'vs']):
            intents.append('comparison')
        if any(word in query_lower for word in ['trend', 'over time', 'change']):
            intents.append('temporal')
        if any(word in query_lower for word in ['relationship', 'correlation']):
            intents.append('correlation')
        if any(word in query_lower for word in ['distribution', 'spread']):
            intents.append('distribution')

        return {
            'primary_intent': intents[0] if intents else 'exploration',
            'all_intents': intents,
            'complexity_indicators': len([word for word in query_lower.split() if len(word) > 6]),
            'specificity_score': len(query.split()) / 20.0  # Rough measure
        }

    async def _generate_contextual_hints(
        self,
        user_id: str,
        query: str
    ) -> List[str]:
        """Generate contextual hints for query enhancement."""

        hints = []
        preferences = await self._get_user_preferences(user_id)

        if preferences:
            if preferences.preferred_chart_types:
                hints.append(f"Consider using {', '.join(preferences.preferred_chart_types[:2])} charts")

            if preferences.common_drill_down_patterns:
                hints.append("Based on your history, you might want to drill down by region or time")

        return hints

    async def _learn_from_feedback(
        self,
        user_id: str,
        interaction: UserInteraction,
        feedback: Dict[str, Any]
    ) -> None:
        """Learn and update preferences from user feedback."""

        preferences = self._user_preferences.get(user_id)
        if not preferences:
            return

        satisfaction = feedback.get('satisfaction_score', 3)

        # Update average satisfaction
        total_interactions = preferences.interaction_count
        current_avg = preferences.average_satisfaction_score
        preferences.average_satisfaction_score = (
            (current_avg * (total_interactions - 1) + satisfaction) / total_interactions
        )

        # Update successful chart types
        if satisfaction >= 4:
            if interaction.selected_chart_type not in preferences.most_successful_chart_types:
                preferences.most_successful_chart_types.append(interaction.selected_chart_type)

    # Analytics helper methods

    def _analyze_interaction_types(self, interactions: List[UserInteraction]) -> Dict[str, int]:
        """Analyze distribution of interaction types."""
        type_counts = {}
        for interaction in interactions:
            interaction_type = interaction.interaction_type.value
            type_counts[interaction_type] = type_counts.get(interaction_type, 0) + 1
        return type_counts

    def _analyze_chart_usage(self, interactions: List[UserInteraction]) -> Dict[str, int]:
        """Analyze chart type usage patterns."""
        chart_counts = {}
        for interaction in interactions:
            chart_type = interaction.selected_chart_type
            chart_counts[chart_type] = chart_counts.get(chart_type, 0) + 1
        return chart_counts

    def _analyze_satisfaction_trends(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze user satisfaction trends."""
        satisfaction_scores = [
            interaction.user_satisfaction_score for interaction in interactions
            if interaction.user_satisfaction_score is not None
        ]

        if not satisfaction_scores:
            return {'average': 0, 'trend': 'neutral'}

        average = sum(satisfaction_scores) / len(satisfaction_scores)

        # Simple trend analysis
        if len(satisfaction_scores) >= 2:
            recent_avg = sum(satisfaction_scores[-3:]) / len(satisfaction_scores[-3:])
            early_avg = sum(satisfaction_scores[:3]) / len(satisfaction_scores[:3])
            trend = 'improving' if recent_avg > early_avg else 'declining' if recent_avg < early_avg else 'stable'
        else:
            trend = 'neutral'

        return {'average': average, 'trend': trend, 'total_scores': len(satisfaction_scores)}

    def _analyze_session_patterns(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze user session patterns."""
        if not interactions:
            return {}

        # Group by day for session analysis
        daily_interactions = {}
        for interaction in interactions:
            day = interaction.timestamp.date()
            if day not in daily_interactions:
                daily_interactions[day] = []
            daily_interactions[day].append(interaction)

        session_lengths = [len(day_interactions) for day_interactions in daily_interactions.values()]
        avg_session_length = sum(session_lengths) / len(session_lengths) if session_lengths else 0

        return {
            'total_sessions': len(daily_interactions),
            'average_interactions_per_session': avg_session_length,
            'most_active_day': max(daily_interactions.items(), key=lambda x: len(x[1]))[0].isoformat() if daily_interactions else None
        }

    def _analyze_performance_metrics(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze performance metrics."""
        generation_times = [
            interaction.generation_time_ms for interaction in interactions
            if interaction.generation_time_ms is not None
        ]

        cognitive_loads = [
            interaction.cognitive_load_score for interaction in interactions
            if interaction.cognitive_load_score is not None
        ]

        return {
            'average_generation_time_ms': sum(generation_times) / len(generation_times) if generation_times else 0,
            'average_cognitive_load': sum(cognitive_loads) / len(cognitive_loads) if cognitive_loads else 0,
            'total_measured_interactions': len(generation_times)
        }

    def _analyze_temporal_patterns(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze temporal usage patterns."""
        if not interactions:
            return {}

        # Analyze hour of day patterns
        hour_counts = {}
        for interaction in interactions:
            hour = interaction.timestamp.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        most_active_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else 0

        return {
            'most_active_hour': most_active_hour,
            'hourly_distribution': hour_counts,
            'total_days_active': len(set(interaction.timestamp.date() for interaction in interactions))
        }

    def _analyze_complexity_preferences(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze user complexity preferences."""
        complexity_scores = [
            interaction.cognitive_load_score for interaction in interactions
            if interaction.cognitive_load_score is not None
        ]

        satisfaction_by_complexity = {}
        for interaction in interactions:
            if interaction.cognitive_load_score and interaction.user_satisfaction_score:
                complexity_bucket = 'low' if interaction.cognitive_load_score < 0.3 else 'medium' if interaction.cognitive_load_score < 0.7 else 'high'
                if complexity_bucket not in satisfaction_by_complexity:
                    satisfaction_by_complexity[complexity_bucket] = []
                satisfaction_by_complexity[complexity_bucket].append(interaction.user_satisfaction_score)

        # Calculate average satisfaction by complexity
        avg_satisfaction_by_complexity = {}
        for complexity, scores in satisfaction_by_complexity.items():
            avg_satisfaction_by_complexity[complexity] = sum(scores) / len(scores)

        return {
            'average_complexity_tolerance': sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0.5,
            'satisfaction_by_complexity': avg_satisfaction_by_complexity,
            'preferred_complexity_level': max(avg_satisfaction_by_complexity.items(), key=lambda x: x[1])[0] if avg_satisfaction_by_complexity else 'medium'
        }

    async def _get_interaction_analytics(
        self,
        user_id: str,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Get interaction analytics for user context."""
        return await self.get_interaction_analytics(user_id, (datetime.now() - cutoff_date).days)

    async def _analyze_visualization_patterns(
        self,
        user_id: str,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Analyze visualization patterns for user context."""
        recent_interactions = await self._get_recent_interactions(user_id, cutoff_date)

        if not recent_interactions:
            return {}

        return {
            'most_used_chart_types': self._analyze_chart_usage(recent_interactions),
            'narrative_goal_patterns': self._analyze_narrative_patterns(recent_interactions),
            'interaction_flow_patterns': self._analyze_interaction_flows(recent_interactions)
        }

    def _analyze_narrative_patterns(self, interactions: List[UserInteraction]) -> Dict[str, int]:
        """Analyze narrative goal patterns."""
        narrative_counts = {}
        for interaction in interactions:
            narrative = interaction.narrative_goal
            narrative_counts[narrative] = narrative_counts.get(narrative, 0) + 1
        return narrative_counts

    def _analyze_interaction_flows(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze interaction flow patterns."""
        # Simple analysis of follow-up actions
        follow_up_patterns = {}
        for interaction in interactions:
            if interaction.follow_up_actions:
                for action in interaction.follow_up_actions:
                    follow_up_patterns[action] = follow_up_patterns.get(action, 0) + 1

        return {
            'common_follow_up_actions': follow_up_patterns,
            'average_follow_ups_per_interaction': sum(len(i.follow_up_actions or []) for i in interactions) / len(interactions)
        }

    async def _extract_domain_knowledge(
        self,
        user_id: str,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Extract domain knowledge from user interactions."""
        recent_interactions = await self._get_recent_interactions(user_id, cutoff_date)

        # Extract domain terms and patterns
        domain_terms = set()
        data_types_used = set()

        for interaction in recent_interactions:
            # Extract from queries
            query_words = interaction.original_query.lower().split()
            domain_terms.update([word for word in query_words if len(word) > 4])

            # Extract from data context
            if interaction.data_context:
                columns = interaction.data_context.get('columns', [])
                data_types_used.update(interaction.data_context.get('data_types', {}).values())

        return {
            'domain_vocabulary': list(domain_terms)[:20],  # Top 20 terms
            'common_data_types': list(data_types_used),
            'expertise_indicators': len(domain_terms) / max(len(recent_interactions), 1)
        }


# Factory function for integration
async def create_memory_context_manager(mem0_client=None) -> MemoryContextManager:
    """
    Factory function to create MemoryContextManager instance.

    Args:
        mem0_client: Optional Mem0 client for persistent storage

    Returns:
        Configured MemoryContextManager instance
    """
    manager = MemoryContextManager(mem0_client)
    logger.info("Created MemoryContextManager for LIDA context persistence")
    return manager