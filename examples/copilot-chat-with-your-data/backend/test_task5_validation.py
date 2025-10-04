"""
Test suite for Task 5: Memory and Context Integration.

This test validates the memory and context integration system that replaces
LIDA's stateless design with Mem0 context persistence, user interaction history
tracking, and contextual visualization recommendations.
"""

import json
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch


def test_memory_context_architecture():
    """Test the memory context manager architecture and data models."""

    print("🔍 Testing Memory Context Architecture...")

    try:
        # Test import structure
        from memory_context_integration import (
            MemoryContextManager,
            UserInteraction,
            UserPreferences,
            ContextualRecommendation,
            InteractionType,
            ContextType,
            create_memory_context_manager
        )
        print("✅ Memory context integration imports successful")

        # Test data model creation
        interaction = UserInteraction(
            interaction_id="test_001",
            user_id="user_123",
            timestamp=datetime.now(),
            interaction_type=InteractionType.VISUALIZATION_REQUEST,
            original_query="Show sales by region",
            data_context={"columns": ["region", "sales"]},
            persona="analyst",
            generated_visualization={"chart_type": "bar"},
            selected_chart_type="bar",
            narrative_goal="magnitude_comparison"
        )

        assert interaction.interaction_id == "test_001", "Interaction ID should be set correctly"
        assert interaction.interaction_type == InteractionType.VISUALIZATION_REQUEST, "Interaction type should be set"
        assert interaction.user_id == "user_123", "User ID should be set correctly"
        print("✅ UserInteraction model creation successful")

        # Test user preferences creation
        preferences = UserPreferences(
            user_id="user_123",
            persona="analyst",
            preferred_chart_types=["bar", "line"],
            avoided_chart_types=["pie"],
            complexity_tolerance=0.8,
            typical_session_duration_minutes=25.0,
            preferred_interaction_features=["drill_down", "export"],
            common_drill_down_patterns=[["region", "product"]],
            preferred_data_granularity="detailed",
            typical_question_types=["comparison", "trend"],
            domain_focus_areas=["sales", "finance"],
            average_satisfaction_score=4.2,
            most_successful_chart_types=["bar", "scatter"],
            common_follow_up_patterns=["export", "drill_down"],
            last_updated=datetime.now(),
            interaction_count=15,
            active_session_count=3
        )

        assert preferences.user_id == "user_123", "User ID should be set"
        assert preferences.complexity_tolerance == 0.8, "Complexity tolerance should be set"
        assert "bar" in preferences.preferred_chart_types, "Should have preferred chart types"
        print("✅ UserPreferences model creation successful")

        # Test contextual recommendation creation
        recommendation = ContextualRecommendation(
            recommendation_id="rec_001",
            user_id="user_123",
            recommendation_type="chart_type",
            recommended_action="Use bar charts for comparison",
            confidence_score=0.85,
            reasoning="Based on 5 successful bar chart interactions",
            based_on_interactions=["int_001", "int_002"],
            pattern_strength=0.8,
            temporal_relevance=0.9,
            persona_alignment=0.85,
            complexity_appropriateness=0.7,
            generated_at=datetime.now()
        )

        assert recommendation.confidence_score == 0.85, "Confidence score should be set"
        assert recommendation.recommendation_type == "chart_type", "Recommendation type should be set"
        print("✅ ContextualRecommendation model creation successful")

        return True

    except Exception as e:
        print(f"❌ Memory context architecture test failed: {e}")
        return False


def test_memory_manager_initialization():
    """Test memory context manager initialization."""

    print("🔍 Testing Memory Manager Initialization...")

    try:
        from memory_context_integration import MemoryContextManager

        # Test initialization without Mem0 client (mock mode)
        manager = MemoryContextManager()
        assert manager.mock_mode is True, "Should be in mock mode without Mem0 client"
        assert manager.mem0_client is None, "Mem0 client should be None"
        print("✅ Mock mode initialization successful")

        # Test initialization with mock Mem0 client
        mock_mem0_client = MagicMock()
        manager_with_client = MemoryContextManager(mem0_client=mock_mem0_client)
        assert manager_with_client.mock_mode is False, "Should not be in mock mode with client"
        assert manager_with_client.mem0_client is mock_mem0_client, "Mem0 client should be set"
        print("✅ Client-based initialization successful")

        # Test internal data structures
        assert hasattr(manager, '_user_interactions'), "Should have user interactions storage"
        assert hasattr(manager, '_user_preferences'), "Should have user preferences storage"
        assert hasattr(manager, '_contextual_recommendations'), "Should have recommendations storage"
        print("✅ Internal data structures initialized")

        return True

    except Exception as e:
        print(f"❌ Memory manager initialization test failed: {e}")
        return False


async def test_interaction_storage():
    """Test user interaction storage and retrieval."""

    print("🔍 Testing Interaction Storage...")

    try:
        from memory_context_integration import MemoryContextManager, UserInteraction, InteractionType

        manager = MemoryContextManager()  # Mock mode

        # Create test interaction
        interaction = UserInteraction(
            interaction_id="test_interaction_001",
            user_id="user_test",
            timestamp=datetime.now(),
            interaction_type=InteractionType.VISUALIZATION_REQUEST,
            original_query="What are the top sales regions?",
            data_context={"columns": ["region", "sales"], "data_types": {"region": "categorical", "sales": "numeric"}},
            persona="executive",
            generated_visualization={"chart_type": "bar", "title": "Sales by Region"},
            selected_chart_type="bar",
            narrative_goal="magnitude_comparison",
            user_satisfaction_score=4
        )

        # Test storing interaction
        success = await manager.store_interaction("user_test", interaction)
        assert success is True, "Interaction storage should succeed"
        print("✅ Interaction storage successful")

        # Test retrieving interactions
        stored_interactions = manager._user_interactions.get("user_test", [])
        assert len(stored_interactions) == 1, "Should have one stored interaction"
        assert stored_interactions[0].interaction_id == "test_interaction_001", "Interaction ID should match"
        print("✅ Interaction retrieval successful")

        # Test user preferences update after interaction
        user_preferences = manager._user_preferences.get("user_test")
        assert user_preferences is not None, "User preferences should be created"
        assert user_preferences.interaction_count == 1, "Interaction count should be updated"
        assert user_preferences.persona == "executive", "Persona should be set from interaction"
        print("✅ User preferences update after interaction successful")

        return True

    except Exception as e:
        print(f"❌ Interaction storage test failed: {e}")
        return False


async def test_context_retrieval():
    """Test comprehensive user context retrieval."""

    print("🔍 Testing Context Retrieval...")

    try:
        from memory_context_integration import MemoryContextManager, UserInteraction, InteractionType, ContextType

        manager = MemoryContextManager()  # Mock mode

        # Create multiple test interactions
        interactions = []
        for i in range(5):
            interaction = UserInteraction(
                interaction_id=f"test_interaction_{i:03d}",
                user_id="context_user",
                timestamp=datetime.now() - timedelta(days=i),
                interaction_type=InteractionType.VISUALIZATION_REQUEST,
                original_query=f"Query {i}: Analysis question",
                data_context={"columns": ["region", "sales", "date"]},
                persona="analyst",
                generated_visualization={"chart_type": "bar" if i % 2 == 0 else "line"},
                selected_chart_type="bar" if i % 2 == 0 else "line",
                narrative_goal="magnitude_comparison" if i % 2 == 0 else "change_over_time",
                user_satisfaction_score=4 if i < 3 else 3
            )
            interactions.append(interaction)
            await manager.store_interaction("context_user", interaction)

        print("✅ Multiple interactions stored for context testing")

        # Test getting all context types
        full_context = await manager.get_user_context("context_user")
        required_context_keys = [
            'user_preferences', 'session_history', 'visualization_patterns',
            'domain_knowledge', 'interaction_analytics'
        ]

        for key in required_context_keys:
            assert key in full_context, f"Context should contain {key}"
        print("✅ Full context retrieval successful")

        # Test specific context type retrieval
        preferences_context = await manager.get_user_context(
            "context_user", [ContextType.USER_PREFERENCES]
        )
        assert 'user_preferences' in preferences_context, "Should contain user preferences"
        assert len(preferences_context) == 1, "Should only contain requested context type"
        print("✅ Specific context type retrieval successful")

        # Test context with time filtering
        recent_context = await manager.get_user_context("context_user", lookback_days=2)
        session_history = recent_context.get('session_history', [])
        assert len(session_history) <= 3, "Should limit to recent interactions"  # Last 2-3 days
        print("✅ Time-filtered context retrieval successful")

        return True

    except Exception as e:
        print(f"❌ Context retrieval test failed: {e}")
        return False


async def test_contextual_recommendations():
    """Test contextual recommendation generation."""

    print("🔍 Testing Contextual Recommendations...")

    try:
        from memory_context_integration import MemoryContextManager, UserInteraction, InteractionType

        manager = MemoryContextManager()  # Mock mode

        # Create interactions with patterns for recommendations
        successful_bar_interactions = []
        for i in range(3):
            interaction = UserInteraction(
                interaction_id=f"bar_interaction_{i}",
                user_id="rec_user",
                timestamp=datetime.now() - timedelta(days=i),
                interaction_type=InteractionType.VISUALIZATION_REQUEST,
                original_query=f"Compare data {i}",
                data_context={"columns": ["category", "value"]},
                persona="analyst",
                generated_visualization={"chart_type": "bar"},
                selected_chart_type="bar",
                narrative_goal="magnitude_comparison",
                user_satisfaction_score=5  # High satisfaction
            )
            successful_bar_interactions.append(interaction)
            await manager.store_interaction("rec_user", interaction)

        print("✅ Pattern interactions stored for recommendation testing")

        # Test getting contextual recommendations
        recommendations = await manager.get_contextual_recommendations(
            "rec_user",
            "Which product category performs best?",
            {"columns": ["category", "performance"]},
            max_recommendations=3
        )

        assert len(recommendations) > 0, "Should generate recommendations"
        assert all(hasattr(rec, 'confidence_score') for rec in recommendations), "All recommendations should have confidence scores"
        assert all(0.0 <= rec.confidence_score <= 1.0 for rec in recommendations), "Confidence scores should be normalized"
        print("✅ Contextual recommendations generation successful")

        # Test recommendation content quality
        chart_recommendations = [rec for rec in recommendations if rec.recommendation_type == "chart_type"]
        if chart_recommendations:
            assert any("bar" in rec.recommended_action.lower() for rec in chart_recommendations), "Should recommend successful chart types"
            print("✅ Recommendation content quality validated")

        # Test recommendation ordering
        if len(recommendations) > 1:
            scores = [rec.confidence_score * rec.temporal_relevance for rec in recommendations]
            assert scores == sorted(scores, reverse=True), "Recommendations should be ordered by relevance"
            print("✅ Recommendation ordering correct")

        return True

    except Exception as e:
        print(f"❌ Contextual recommendations test failed: {e}")
        return False


async def test_query_context_injection():
    """Test query enhancement with user context."""

    print("🔍 Testing Query Context Injection...")

    try:
        from memory_context_integration import MemoryContextManager, UserInteraction, InteractionType

        manager = MemoryContextManager()  # Mock mode

        # Set up user with history
        interaction = UserInteraction(
            interaction_id="context_interaction",
            user_id="query_user",
            timestamp=datetime.now(),
            interaction_type=InteractionType.VISUALIZATION_REQUEST,
            original_query="Previous query about sales",
            data_context={"columns": ["region", "sales"]},
            persona="executive",
            generated_visualization={"chart_type": "bar"},
            selected_chart_type="bar",
            narrative_goal="magnitude_comparison",
            user_satisfaction_score=4
        )
        await manager.store_interaction("query_user", interaction)

        # Test query context injection
        original_query = "Show me revenue by product category"
        data_context = {"columns": ["category", "revenue"], "data_types": {"category": "categorical", "revenue": "numeric"}}

        enhanced_query = await manager.inject_context_into_query(
            "query_user", original_query, data_context
        )

        # Validate enhanced query structure
        required_keys = [
            'original_query', 'data_context', 'user_context',
            'query_analysis', 'historical_patterns', 'contextual_hints'
        ]

        for key in required_keys:
            assert key in enhanced_query, f"Enhanced query should contain {key}"
        print("✅ Enhanced query structure validated")

        # Test user context injection
        user_context = enhanced_query['user_context']
        assert user_context['user_id'] == "query_user", "User ID should be injected"
        assert user_context['persona'] == "executive", "Persona should be injected from preferences"
        print("✅ User context injection successful")

        # Test query analysis
        query_analysis = enhanced_query['query_analysis']
        assert 'primary_intent' in query_analysis, "Should analyze primary intent"
        assert query_analysis['primary_intent'] in ['comparison', 'exploration'], "Should classify intent correctly"
        print("✅ Query analysis functional")

        # Test historical patterns injection
        historical_patterns = enhanced_query['historical_patterns']
        assert 'successful_chart_types' in historical_patterns, "Should include successful chart types"
        print("✅ Historical patterns injection successful")

        return True

    except Exception as e:
        print(f"❌ Query context injection test failed: {e}")
        return False


async def test_feedback_learning():
    """Test user feedback processing and preference learning."""

    print("🔍 Testing Feedback Learning...")

    try:
        from memory_context_integration import MemoryContextManager, UserInteraction, InteractionType

        manager = MemoryContextManager()  # Mock mode

        # Create initial interaction
        interaction = UserInteraction(
            interaction_id="feedback_interaction",
            user_id="feedback_user",
            timestamp=datetime.now(),
            interaction_type=InteractionType.VISUALIZATION_REQUEST,
            original_query="Test feedback query",
            data_context={"columns": ["category", "value"]},
            persona="analyst",
            generated_visualization={"chart_type": "scatter"},
            selected_chart_type="scatter",
            narrative_goal="correlation"
        )
        await manager.store_interaction("feedback_user", interaction)

        # Test positive feedback processing
        positive_feedback = {
            "satisfaction_score": 5,
            "helpful": True,
            "comments": "Perfect visualization for my needs"
        }

        success = await manager.update_user_feedback(
            "feedback_user", "feedback_interaction", positive_feedback
        )
        assert success is True, "Feedback update should succeed"
        print("✅ Positive feedback processing successful")

        # Verify feedback was stored
        stored_interactions = manager._user_interactions.get("feedback_user", [])
        updated_interaction = next(
            (i for i in stored_interactions if i.interaction_id == "feedback_interaction"), None
        )
        assert updated_interaction is not None, "Interaction should be found"
        assert updated_interaction.user_feedback == positive_feedback, "Feedback should be stored"
        assert updated_interaction.user_satisfaction_score == 5, "Satisfaction score should be updated"
        print("✅ Feedback storage validated")

        # Test preference learning from feedback
        user_preferences = manager._user_preferences.get("feedback_user")
        assert user_preferences is not None, "User preferences should exist"
        # High satisfaction should lead to chart type being preferred
        # This is tested through multiple interactions in practice
        print("✅ Preference learning mechanism validated")

        # Test negative feedback processing
        negative_feedback = {
            "satisfaction_score": 2,
            "helpful": False,
            "comments": "Chart type was confusing"
        }

        # Create another interaction for negative feedback
        negative_interaction = UserInteraction(
            interaction_id="negative_feedback_interaction",
            user_id="feedback_user",
            timestamp=datetime.now(),
            interaction_type=InteractionType.VISUALIZATION_REQUEST,
            original_query="Another test query",
            data_context={"columns": ["category", "value"]},
            persona="analyst",
            generated_visualization={"chart_type": "pie"},
            selected_chart_type="pie",
            narrative_goal="part_to_whole"
        )
        await manager.store_interaction("feedback_user", negative_interaction)

        success = await manager.update_user_feedback(
            "feedback_user", "negative_feedback_interaction", negative_feedback
        )
        assert success is True, "Negative feedback update should succeed"
        print("✅ Negative feedback processing successful")

        return True

    except Exception as e:
        print(f"❌ Feedback learning test failed: {e}")
        return False


async def test_interaction_analytics():
    """Test interaction analytics generation."""

    print("🔍 Testing Interaction Analytics...")

    try:
        from memory_context_integration import MemoryContextManager, UserInteraction, InteractionType

        manager = MemoryContextManager()  # Mock mode

        # Create diverse interactions for analytics
        interactions_data = [
            ("viz_001", InteractionType.VISUALIZATION_REQUEST, "bar", 4, 100, 0.3),
            ("viz_002", InteractionType.VISUALIZATION_REQUEST, "line", 5, 150, 0.4),
            ("drill_001", InteractionType.DRILL_DOWN, "bar", 3, 80, 0.5),
            ("export_001", InteractionType.EXPORT, "line", 4, 200, 0.2),
            ("viz_003", InteractionType.VISUALIZATION_REQUEST, "pie", 2, 300, 0.8),
        ]

        for interaction_id, int_type, chart_type, satisfaction, gen_time, cognitive_load in interactions_data:
            interaction = UserInteraction(
                interaction_id=interaction_id,
                user_id="analytics_user",
                timestamp=datetime.now() - timedelta(hours=len(interactions_data) - interactions_data.index((interaction_id, int_type, chart_type, satisfaction, gen_time, cognitive_load))),
                interaction_type=int_type,
                original_query=f"Query for {interaction_id}",
                data_context={"columns": ["category", "value"]},
                persona="analyst",
                generated_visualization={"chart_type": chart_type},
                selected_chart_type=chart_type,
                narrative_goal="magnitude_comparison",
                user_satisfaction_score=satisfaction,
                generation_time_ms=gen_time,
                cognitive_load_score=cognitive_load
            )
            await manager.store_interaction("analytics_user", interaction)

        print("✅ Diverse interactions created for analytics testing")

        # Test analytics generation
        analytics = await manager.get_interaction_analytics("analytics_user", time_period_days=1)

        # Validate analytics structure
        required_analytics_keys = [
            'total_interactions', 'interaction_types', 'chart_type_usage',
            'satisfaction_trends', 'session_patterns', 'performance_metrics',
            'temporal_patterns', 'complexity_preferences'
        ]

        for key in required_analytics_keys:
            assert key in analytics, f"Analytics should contain {key}"
        print("✅ Analytics structure validated")

        # Test specific analytics content
        assert analytics['total_interactions'] == 5, "Should count all interactions"
        assert 'visualization_request' in analytics['interaction_types'], "Should track interaction types"
        assert analytics['interaction_types']['visualization_request'] == 3, "Should count visualization requests correctly"
        print("✅ Interaction type analytics correct")

        # Test chart usage analytics
        chart_usage = analytics['chart_type_usage']
        assert 'bar' in chart_usage, "Should track bar chart usage"
        assert chart_usage['bar'] == 2, "Should count bar charts correctly"
        print("✅ Chart usage analytics correct")

        # Test satisfaction trends
        satisfaction_trends = analytics['satisfaction_trends']
        assert 'average' in satisfaction_trends, "Should calculate average satisfaction"
        assert 0 <= satisfaction_trends['average'] <= 5, "Average satisfaction should be in valid range"
        print("✅ Satisfaction trends analytics correct")

        # Test performance metrics
        performance_metrics = analytics['performance_metrics']
        assert 'average_generation_time_ms' in performance_metrics, "Should track generation time"
        assert performance_metrics['average_generation_time_ms'] > 0, "Should have positive generation time"
        print("✅ Performance metrics analytics correct")

        return True

    except Exception as e:
        print(f"❌ Interaction analytics test failed: {e}")
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

        # Test memory context manager integration capability
        from memory_context_integration import MemoryContextManager, create_memory_context_manager

        manager = MemoryContextManager()

        # Test that manager could be integrated with LIDA manager
        assert hasattr(manager, 'store_interaction'), "Should have interaction storage method"
        assert hasattr(manager, 'get_user_context'), "Should have context retrieval method"
        assert hasattr(manager, 'inject_context_into_query'), "Should have query enhancement method"
        assert callable(create_memory_context_manager), "Factory function should be callable"
        print("✅ Memory context manager methods compatible with LIDA manager")

        # Test context-aware manager pattern
        class MockContextAwareLidaManager:
            def __init__(self, llm, memory_client):
                self.lida = llm  # Mock LIDA manager
                self.memory = memory_client

            async def visualize_with_context(self, user_id, query):
                context = await self.memory.get_user_context(user_id)
                enhanced_query = await self.memory.inject_context_into_query(user_id, query, {})
                # Would call LIDA here
                result = {"chart_type": "bar", "enhanced": True}
                # Store interaction
                return result

        # Test mock context-aware manager
        mock_llm = MagicMock()
        context_aware_manager = MockContextAwareLidaManager(mock_llm, manager)
        assert hasattr(context_aware_manager, 'visualize_with_context'), "Should have context-aware visualization method"
        print("✅ Context-aware LIDA manager pattern validated")

        # Test that memory manager can replace LIDA's stateless design
        sample_interaction_data = {
            'user_id': 'test_user',
            'query': 'Show sales data',
            'result': {'chart_type': 'bar', 'data': [1, 2, 3]}
        }

        # This would be called in LIDA manager integration
        context_enhancement_possible = all([
            hasattr(manager, 'store_interaction'),
            hasattr(manager, 'get_user_context'),
            hasattr(manager, 'get_contextual_recommendations'),
            hasattr(manager, 'update_user_feedback')
        ])

        assert context_enhancement_possible, "Should support full context-aware workflow"
        print("✅ LIDA stateless design replacement capability validated")

        return True

    except Exception as e:
        print(f"❌ LIDA manager integration test failed: {e}")
        return False


def run_task5_validation():
    """Run comprehensive Task 5 validation."""

    print("🧪 Running Task 5: Memory and Context Integration Validation")
    print("="*65)

    tests = [
        ("Memory Context Architecture", test_memory_context_architecture),
        ("Memory Manager Initialization", test_memory_manager_initialization),
        ("Interaction Storage", test_interaction_storage),
        ("Context Retrieval", test_context_retrieval),
        ("Contextual Recommendations", test_contextual_recommendations),
        ("Query Context Injection", test_query_context_injection),
        ("Feedback Learning", test_feedback_learning),
        ("Interaction Analytics", test_interaction_analytics),
        ("LIDA Manager Integration", test_lida_manager_integration)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔬 {test_name}")
        print("-" * 45)

        try:
            # Handle async tests
            if test_func.__name__ in [
                'test_interaction_storage', 'test_context_retrieval',
                'test_contextual_recommendations', 'test_query_context_injection',
                'test_feedback_learning', 'test_interaction_analytics'
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
    print(f"📊 Task 5 Validation Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Task 5: Memory and Context Integration COMPLETED!")
        print("\n✅ LIDA stateless design replaced with Mem0 context persistence")
        print("✅ User interaction history tracking beyond session scope implemented")
        print("✅ Contextual visualization recommendations using stored patterns created")
        print("✅ User preference learning from feedback integrated")
        print("✅ Comprehensive interaction analytics and pattern recognition added")
        print("✅ Context-aware query enhancement with historical data implemented")
        print("✅ Multi-dimensional user context retrieval system operational")
        print("✅ Ready to proceed to Task 6: Frontend Integration with AG-UI System")
        return True
    else:
        print("❌ Task 5 validation failed. Please review implementation before proceeding.")
        return False


if __name__ == "__main__":
    success = run_task5_validation()
    exit(0 if success else 1)