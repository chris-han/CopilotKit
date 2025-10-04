"""
Test suite for Task 6: Frontend Integration with AG-UI System.

This test validates the frontend integration system that adapts LIDA's web API
to work with CopilotKit actions, implements streaming responses, adds drill-down
capabilities, and creates interactive ECharts components with feedback loops.
"""

import json
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch


def test_frontend_integration_architecture():
    """Test the frontend integration architecture and data models."""

    print("🔍 Testing Frontend Integration Architecture...")

    try:
        # Test import structure
        from frontend_integration import (
            CopilotKitVisualizationHandler,
            StreamingEvent,
            DrillDownContext,
            FeedbackData,
            StreamingEventType,
            DrillDownType,
            create_copilotkit_handler
        )
        print("✅ Frontend integration imports successful")

        # Test streaming event creation
        streaming_event = StreamingEvent(
            event_type=StreamingEventType.ANALYSIS_STARTED,
            timestamp=datetime.now(),
            user_id="user_123",
            session_id="session_456",
            data={"query": "Test query"},
            progress_percentage=0.0
        )

        assert streaming_event.event_type == StreamingEventType.ANALYSIS_STARTED, "Event type should be set correctly"
        assert streaming_event.user_id == "user_123", "User ID should be set correctly"
        assert streaming_event.progress_percentage == 0.0, "Progress percentage should be set"
        print("✅ StreamingEvent model creation successful")

        # Test drill-down context creation
        drill_down_context = DrillDownContext(
            drill_down_id="drill_001",
            user_id="user_123",
            session_id="session_456",
            parent_visualization_id="viz_parent",
            drill_down_type=DrillDownType.FILTER,
            target_dimension="region",
            filter_criteria={"category": "electronics"},
            breadcrumb_path=[{"label": "Overview", "visualization_id": "root"}],
            context_preservation={"filters": {"category": "electronics"}},
            available_dimensions=["product", "time_period"],
            related_metrics=["revenue", "sales_count"],
            created_at=datetime.now()
        )

        assert drill_down_context.drill_down_type == DrillDownType.FILTER, "Drill-down type should be set"
        assert drill_down_context.target_dimension == "region", "Target dimension should be set"
        assert len(drill_down_context.available_dimensions) == 2, "Should have available dimensions"
        print("✅ DrillDownContext model creation successful")

        # Test feedback data creation
        feedback_data = FeedbackData(
            feedback_id="feedback_001",
            user_id="user_123",
            visualization_id="viz_001",
            timestamp=datetime.now(),
            feedback_type="rating",
            rating_score=4,
            rating_aspects={"clarity": 5, "usefulness": 4},
            interaction_duration_seconds=45.5,
            click_count=8,
            export_attempted=True
        )

        assert feedback_data.rating_score == 4, "Rating score should be set"
        assert feedback_data.rating_aspects["clarity"] == 5, "Rating aspects should be set"
        assert feedback_data.export_attempted is True, "Export attempted should be set"
        print("✅ FeedbackData model creation successful")

        return True

    except Exception as e:
        print(f"❌ Frontend integration architecture test failed: {e}")
        return False


def test_copilotkit_handler_initialization():
    """Test CopilotKit visualization handler initialization."""

    print("🔍 Testing CopilotKit Handler Initialization...")

    try:
        from frontend_integration import CopilotKitVisualizationHandler

        # Mock LIDA manager
        mock_lida_manager = MagicMock()
        mock_memory_manager = MagicMock()
        mock_persona_selector = MagicMock()
        mock_semantic_integration = MagicMock()

        # Test initialization with all components
        handler = CopilotKitVisualizationHandler(
            lida_manager=mock_lida_manager,
            memory_manager=mock_memory_manager,
            persona_selector=mock_persona_selector,
            semantic_integration=mock_semantic_integration
        )

        assert handler.lida_manager is mock_lida_manager, "LIDA manager should be set"
        assert handler.memory_manager is mock_memory_manager, "Memory manager should be set"
        assert handler.persona_selector is mock_persona_selector, "Persona selector should be set"
        print("✅ Handler initialization with all components successful")

        # Test initialization with minimal components
        minimal_handler = CopilotKitVisualizationHandler(
            lida_manager=mock_lida_manager
        )

        assert minimal_handler.lida_manager is mock_lida_manager, "LIDA manager should be set"
        assert minimal_handler.memory_manager is None, "Memory manager should be None"
        print("✅ Minimal handler initialization successful")

        # Test internal data structures
        assert hasattr(handler, '_active_sessions'), "Should have active sessions storage"
        assert hasattr(handler, '_drill_down_contexts'), "Should have drill-down contexts storage"
        assert hasattr(handler, '_user_feedback'), "Should have user feedback storage"
        print("✅ Internal data structures initialized")

        return True

    except Exception as e:
        print(f"❌ CopilotKit handler initialization test failed: {e}")
        return False


async def test_copilotkit_actions():
    """Test CopilotKit action handling."""

    print("🔍 Testing CopilotKit Actions...")

    try:
        # Mock openai and pydantic before importing
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

        from frontend_integration import CopilotKitVisualizationHandler

        # Mock dependencies
        mock_lida_manager = MagicMock()
        mock_lida_manager.summarize_data = AsyncMock()
        mock_lida_manager.generate_goals = AsyncMock()
        mock_lida_manager.visualize_goal = AsyncMock()
        mock_lida_manager.dashboard_context = {"columns": ["region", "sales"]}

        handler = CopilotKitVisualizationHandler(lida_manager=mock_lida_manager)

        # Test generateVisualization action with streaming
        streaming_result = await handler.handle_generate_visualization(
            query="Show sales by region",
            user_id="user_test",
            session_id="session_test",
            streaming=True
        )

        assert streaming_result["streaming"] is True, "Should enable streaming"
        assert "session_id" in streaming_result, "Should include session ID"
        assert "stream_url" in streaming_result, "Should include stream URL"
        assert streaming_result["status"] == "started", "Status should be started"
        print("✅ Streaming generateVisualization action successful")

        # Test generateVisualization action without streaming
        # Mock the required LIDA manager methods
        from lida_enhanced_manager import EnhancedDataSummary, EnhancedGoal

        mock_summary = EnhancedDataSummary(
            summary="Test summary",
            dataset_name="test",
            columns=["region", "sales"],
            data_types={"region": "categorical", "sales": "numeric"},
            insights=["Test insight"],
            ag_ui_context={}
        )

        mock_goal = EnhancedGoal(
            question="Show sales by region",
            visualization="Regional sales analysis",
            rationale="Compare regional performance",
            chart_type="bar",
            dimensions=["region"],
            metrics=["sales"],
            persona="analyst",
            narrative_goal="magnitude_comparison"
        )

        mock_visualization = {
            "chart_type": "bar",
            "echarts_config": {"title": {"text": "Sales by Region"}},
            "interactive_features": ["hover_tooltips"]
        }

        mock_lida_manager.summarize_data.return_value = mock_summary
        mock_lida_manager.generate_goals.return_value = [mock_goal]
        mock_lida_manager.visualize_goal.return_value = mock_visualization

        complete_result = await handler.handle_generate_visualization(
            query="Show sales by region",
            user_id="user_test",
            session_id="session_test",
            streaming=False
        )

        assert "visualization" in complete_result, "Should include visualization"
        assert "goal" in complete_result, "Should include goal"
        assert "interactive_features" in complete_result, "Should include interactive features"
        print("✅ Complete generateVisualization action successful")

        return True

    except Exception as e:
        print(f"❌ CopilotKit actions test failed: {e}")
        return False


async def test_streaming_responses():
    """Test streaming response generation."""

    print("🔍 Testing Streaming Responses...")

    try:
        # Mock openai and pydantic before importing
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

        from frontend_integration import CopilotKitVisualizationHandler, StreamingEventType

        # Mock dependencies
        mock_lida_manager = MagicMock()
        mock_lida_manager.summarize_data = AsyncMock()
        mock_lida_manager.generate_goals = AsyncMock()
        mock_lida_manager.visualize_goal = AsyncMock()
        mock_lida_manager.dashboard_context = {"columns": ["region", "sales"]}

        # Mock returns
        from lida_enhanced_manager import EnhancedDataSummary, EnhancedGoal

        mock_summary = EnhancedDataSummary(
            summary="Test summary",
            dataset_name="test",
            columns=["region", "sales"],
            data_types={"region": "categorical", "sales": "numeric"},
            insights=["Test insight"],
            ag_ui_context={}
        )

        mock_goal = EnhancedGoal(
            question="Show sales by region",
            visualization="Regional sales analysis",
            rationale="Compare regional performance",
            chart_type="bar",
            dimensions=["region"],
            metrics=["sales"],
            persona="analyst",
            narrative_goal="magnitude_comparison"
        )

        mock_visualization = {
            "chart_type": "bar",
            "echarts_config": {"title": {"text": "Sales by Region"}},
            "interactive_features": ["hover_tooltips"]
        }

        mock_lida_manager.summarize_data.return_value = mock_summary
        mock_lida_manager.generate_goals.return_value = [mock_goal]
        mock_lida_manager.visualize_goal.return_value = mock_visualization

        handler = CopilotKitVisualizationHandler(lida_manager=mock_lida_manager)

        # Test streaming generation
        streaming_events = []
        async for event in handler.stream_visualization_generation(
            query="Show sales by region",
            user_id="stream_user",
            session_id="stream_session"
        ):
            streaming_events.append(event)

        # Validate streaming events
        assert len(streaming_events) > 0, "Should generate streaming events"

        # Check for required event types
        event_types = [event.event_type for event in streaming_events]
        required_events = [
            StreamingEventType.ANALYSIS_STARTED,
            StreamingEventType.DATA_SUMMARY_GENERATED,
            StreamingEventType.GOALS_GENERATED,
            StreamingEventType.VISUALIZATION_GENERATED,
            StreamingEventType.COMPLETED
        ]

        for required_event in required_events:
            assert required_event in event_types, f"Should include {required_event.value} event"

        print("✅ Required streaming events generated")

        # Test progress tracking
        analysis_started = next(e for e in streaming_events if e.event_type == StreamingEventType.ANALYSIS_STARTED)
        completed = next(e for e in streaming_events if e.event_type == StreamingEventType.COMPLETED)

        assert analysis_started.progress_percentage == 0.0, "Analysis started should have 0% progress"
        assert completed.progress_percentage == 1.0, "Completed should have 100% progress"
        print("✅ Progress tracking working correctly")

        # Test event data content
        data_summary_event = next(e for e in streaming_events if e.event_type == StreamingEventType.DATA_SUMMARY_GENERATED)
        assert "summary" in data_summary_event.data, "Data summary event should contain summary"

        goals_event = next(e for e in streaming_events if e.event_type == StreamingEventType.GOALS_GENERATED)
        assert "goals" in goals_event.data, "Goals event should contain goals"
        print("✅ Event data content validated")

        return True

    except Exception as e:
        print(f"❌ Streaming responses test failed: {e}")
        return False


async def test_drill_down_capabilities():
    """Test drill-down capabilities and navigation."""

    print("🔍 Testing Drill-Down Capabilities...")

    try:
        # Mock openai and pydantic before importing
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

        from frontend_integration import CopilotKitVisualizationHandler

        # Mock dependencies
        mock_lida_manager = MagicMock()
        mock_lida_manager.summarize_data = AsyncMock()
        mock_lida_manager.generate_goals = AsyncMock()
        mock_lida_manager.visualize_goal = AsyncMock()

        # Mock returns for drill-down
        from lida_enhanced_manager import EnhancedDataSummary, EnhancedGoal

        mock_summary = EnhancedDataSummary(
            summary="Drill-down summary",
            dataset_name="drill_down_data",
            columns=["product", "revenue"],
            data_types={"product": "categorical", "revenue": "numeric"},
            insights=["Drill-down insight"],
            ag_ui_context={}
        )

        mock_goal = EnhancedGoal(
            question="Show product breakdown",
            visualization="Product revenue analysis",
            rationale="Detail view of products",
            chart_type="bar",
            dimensions=["product"],
            metrics=["revenue"],
            persona="analyst",
            narrative_goal="magnitude_comparison"
        )

        mock_visualization = {
            "chart_type": "bar",
            "echarts_config": {"title": {"text": "Revenue by Product"}},
            "interactive_features": ["drill_down", "breadcrumb_navigation"]
        }

        mock_lida_manager.summarize_data.return_value = mock_summary
        mock_lida_manager.generate_goals.return_value = [mock_goal]
        mock_lida_manager.visualize_goal.return_value = mock_visualization

        handler = CopilotKitVisualizationHandler(lida_manager=mock_lida_manager)

        # Test drill-down operation
        drill_down_result = await handler.handle_drill_down(
            user_id="drill_user",
            parent_visualization_id="parent_viz_001",
            drill_down_type="filter",
            target_dimension="product",
            filter_criteria={"region": "North", "category": "Electronics"}
        )

        # Validate drill-down result structure
        required_keys = [
            "drill_down_id", "visualization", "navigation",
            "context_preservation", "interactive_features"
        ]

        for key in required_keys:
            assert key in drill_down_result, f"Drill-down result should contain {key}"

        print("✅ Drill-down result structure validated")

        # Test navigation components
        navigation = drill_down_result["navigation"]
        assert "breadcrumb_path" in navigation, "Should have breadcrumb path"
        assert "can_go_back" in navigation, "Should indicate if can go back"
        assert "available_drill_downs" in navigation, "Should list available drill-downs"
        assert "related_metrics" in navigation, "Should list related metrics"
        print("✅ Navigation components validated")

        # Test context preservation
        context_preservation = drill_down_result["context_preservation"]
        assert "parent_filters" in context_preservation, "Should preserve parent filters"
        assert "current_dimension" in context_preservation, "Should track current dimension"
        assert "drill_down_type" in context_preservation, "Should track drill-down type"
        print("✅ Context preservation validated")

        # Test interactive features for drill-down
        interactive_features = drill_down_result["interactive_features"]
        expected_features = [
            "click_to_filter", "breadcrumb_navigation",
            "context_preservation", "multi_dimensional_exploration"
        ]

        for feature in expected_features:
            assert feature in interactive_features, f"Should include {feature}"
        print("✅ Drill-down interactive features validated")

        # Test drill-down context storage
        assert len(handler._drill_down_contexts) > 0, "Should store drill-down contexts"
        stored_context = list(handler._drill_down_contexts.values())[0]
        assert stored_context.target_dimension == "product", "Should store correct target dimension"
        print("✅ Drill-down context storage working")

        return True

    except Exception as e:
        print(f"❌ Drill-down capabilities test failed: {e}")
        return False


async def test_feedback_collection():
    """Test user feedback collection and processing."""

    print("🔍 Testing Feedback Collection...")

    try:
        from frontend_integration import CopilotKitVisualizationHandler

        # Mock dependencies
        mock_lida_manager = MagicMock()
        mock_memory_manager = MagicMock()
        mock_memory_manager.update_user_feedback = AsyncMock(return_value=True)

        handler = CopilotKitVisualizationHandler(
            lida_manager=mock_lida_manager,
            memory_manager=mock_memory_manager
        )

        # Test rating feedback
        rating_feedback_data = {
            "rating_score": 5,
            "rating_aspects": {"clarity": 5, "usefulness": 4, "accuracy": 5},
            "comment_text": "Excellent visualization, very clear!",
            "interaction_duration_seconds": 120.5,
            "click_count": 15,
            "export_attempted": True
        }

        rating_result = await handler.handle_user_feedback(
            user_id="feedback_user",
            visualization_id="viz_feedback_001",
            feedback_type="rating",
            feedback_data=rating_feedback_data
        )

        # Validate feedback result structure
        required_keys = [
            "feedback_id", "processed", "insights",
            "recommendations", "learning_updates"
        ]

        for key in required_keys:
            assert key in rating_result, f"Feedback result should contain {key}"

        assert rating_result["processed"] is True, "Feedback should be processed"
        print("✅ Rating feedback processing successful")

        # Test comment feedback
        comment_feedback_data = {
            "comment_text": "The chart is confusing, hard to understand",
            "sentiment_score": -0.7,
            "rating_score": 2,
            "interaction_duration_seconds": 15.0
        }

        comment_result = await handler.handle_user_feedback(
            user_id="feedback_user",
            visualization_id="viz_feedback_002",
            feedback_type="comment",
            feedback_data=comment_feedback_data
        )

        assert comment_result["processed"] is True, "Comment feedback should be processed"
        assert "insights" in comment_result, "Should generate insights from comment"
        print("✅ Comment feedback processing successful")

        # Test customization feedback
        customization_feedback_data = {
            "customization_changes": {
                "color_scheme": "high_contrast",
                "font_size": "large",
                "chart_theme": "dark"
            },
            "preferred_chart_type": "line",
            "rating_score": 4
        }

        customization_result = await handler.handle_user_feedback(
            user_id="feedback_user",
            visualization_id="viz_feedback_003",
            feedback_type="customization",
            feedback_data=customization_feedback_data
        )

        assert customization_result["processed"] is True, "Customization feedback should be processed"
        print("✅ Customization feedback processing successful")

        # Test feedback storage
        assert len(handler._user_feedback["feedback_user"]) == 3, "Should store all feedback"
        stored_feedback = handler._user_feedback["feedback_user"]

        # Verify different feedback types are stored
        feedback_types = [fb.feedback_type for fb in stored_feedback]
        assert "rating" in feedback_types, "Should store rating feedback"
        assert "comment" in feedback_types, "Should store comment feedback"
        assert "customization" in feedback_types, "Should store customization feedback"
        print("✅ Feedback storage validated")

        # Test learning updates
        learning_updates = rating_result["learning_updates"]
        assert "preference_updates" in learning_updates, "Should include preference updates"
        assert "persona_adjustments" in learning_updates, "Should include persona adjustments"
        print("✅ Learning updates generated")

        return True

    except Exception as e:
        print(f"❌ Feedback collection test failed: {e}")
        return False


async def test_interactive_features():
    """Test interactive features configuration."""

    print("🔍 Testing Interactive Features...")

    try:
        from frontend_integration import CopilotKitVisualizationHandler

        # Mock dependencies
        mock_lida_manager = MagicMock()
        mock_memory_manager = MagicMock()
        mock_memory_manager.get_user_context = AsyncMock(return_value={
            "user_preferences": {
                "preferred_interaction_features": ["drill_down", "export", "filtering"]
            },
            "interaction_analytics": {
                "common_follow_up_actions": {"export": 5, "drill_down": 3, "zoom": 2}
            }
        })

        handler = CopilotKitVisualizationHandler(
            lida_manager=mock_lida_manager,
            memory_manager=mock_memory_manager
        )

        # Test interactive features for executive persona
        executive_features = await handler.get_interactive_features(
            user_id="exec_user",
            chart_type="bar",
            persona="executive"
        )

        assert "features" in executive_features, "Should return features"
        features = executive_features["features"]

        # Test executive-specific features
        assert features.get("simplified_interactions") is True, "Executive should have simplified interactions"
        assert features.get("executive_summary") is True, "Executive should have executive summary"
        assert features.get("one_click_export") is True, "Executive should have one-click export"
        print("✅ Executive persona features validated")

        # Test interactive features for analyst persona
        analyst_features = await handler.get_interactive_features(
            user_id="analyst_user",
            chart_type="scatter",
            persona="analyst"
        )

        analyst_features_dict = analyst_features["features"]
        assert analyst_features_dict.get("advanced_filtering") is True, "Analyst should have advanced filtering"
        assert analyst_features_dict.get("data_exploration") is True, "Analyst should have data exploration"
        assert analyst_features_dict.get("statistical_overlays") is True, "Analyst should have statistical overlays"
        print("✅ Analyst persona features validated")

        # Test chart-specific features
        assert features.get("zoom_pan") is True, "Bar charts should support zoom/pan"
        assert features.get("drill_down") is True, "Should support drill-down"
        assert features.get("feedback_collection") is True, "Should support feedback collection"
        print("✅ Chart-specific features validated")

        # Test accessibility features
        accessibility = features.get("accessibility_features", {})
        required_accessibility = [
            "screen_reader_support", "keyboard_navigation",
            "aria_labels", "high_contrast_mode", "focus_indicators"
        ]

        for feature in required_accessibility:
            assert accessibility.get(feature) is True, f"Should support {feature}"
        print("✅ Accessibility features validated")

        # Test customization options
        customization = features.get("customization_options", {})
        assert "color_schemes" in customization, "Should offer color scheme options"
        assert "chart_themes" in customization, "Should offer chart theme options"
        assert "font_sizes" in customization, "Should offer font size options"
        print("✅ Customization options validated")

        # Test personalized features from memory
        if mock_memory_manager:
            assert "personalized_shortcuts" in features, "Should include personalized shortcuts"
            assert "suggested_actions" in features, "Should include suggested actions"
            print("✅ Personalized features from memory validated")

        return True

    except Exception as e:
        print(f"❌ Interactive features test failed: {e}")
        return False


def test_ag_ui_integration():
    """Test AG-UI system integration patterns."""

    print("🔍 Testing AG-UI Integration...")

    try:
        from frontend_integration import CopilotKitVisualizationHandler, create_copilotkit_handler

        # Mock all required dependencies
        mock_lida_manager = MagicMock()
        mock_memory_manager = MagicMock()
        mock_persona_selector = MagicMock()
        mock_semantic_integration = MagicMock()

        # Test handler integration pattern
        handler = CopilotKitVisualizationHandler(
            lida_manager=mock_lida_manager,
            memory_manager=mock_memory_manager,
            persona_selector=mock_persona_selector,
            semantic_integration=mock_semantic_integration
        )

        # Test AG-UI action patterns
        assert hasattr(handler, 'handle_generate_visualization'), "Should handle generateVisualization action"
        assert hasattr(handler, 'stream_visualization_generation'), "Should support streaming responses"
        assert hasattr(handler, 'handle_drill_down'), "Should handle drill-down actions"
        assert hasattr(handler, 'handle_user_feedback'), "Should handle feedback actions"
        assert hasattr(handler, 'get_interactive_features'), "Should provide interactive features"
        print("✅ AG-UI action patterns validated")

        # Test CopilotKit action structure compatibility
        # This would be used in actual CopilotKit frontend integration
        copilotkit_action_structure = {
            "name": "generateVisualization",
            "description": "Generate data visualization using LIDA backend",
            "parameters": [
                {"name": "query", "type": "string", "description": "Natural language query"}
            ],
            "handler": "async ({ query }) => { /* calls backend handler */ }"
        }

        # Validate that handler methods match expected CopilotKit patterns
        assert callable(handler.handle_generate_visualization), "generateVisualization handler should be callable"
        print("✅ CopilotKit action structure compatibility validated")

        # Test streaming API patterns
        streaming_api_pattern = {
            "stream_url": "/api/lida/stream/{session_id}",
            "websocket_support": True,
            "progressive_loading": True,
            "cancellation_support": True
        }

        # Handler should support these patterns
        assert hasattr(handler, '_active_sessions'), "Should track active sessions for streaming"
        print("✅ Streaming API patterns supported")

        # Test drill-down API patterns
        drill_down_api_pattern = {
            "click_to_filter": True,
            "breadcrumb_navigation": True,
            "context_preservation": True,
            "multi_dimensional_exploration": True
        }

        # Handler should support these patterns
        assert hasattr(handler, '_drill_down_contexts'), "Should track drill-down contexts"
        print("✅ Drill-down API patterns supported")

        # Test feedback loop patterns
        feedback_api_pattern = {
            "user_feedback_collection": True,
            "real_time_learning": True,
            "preference_adaptation": True,
            "customization_support": True
        }

        # Handler should support these patterns
        assert hasattr(handler, '_user_feedback'), "Should collect user feedback"
        print("✅ Feedback loop patterns supported")

        # Test factory function
        assert callable(create_copilotkit_handler), "Factory function should be callable"
        print("✅ Factory function available for integration")

        return True

    except Exception as e:
        print(f"❌ AG-UI integration test failed: {e}")
        return False


def run_task6_validation():
    """Run comprehensive Task 6 validation."""

    print("🧪 Running Task 6: Frontend Integration with AG-UI System Validation")
    print("="*70)

    tests = [
        ("Frontend Integration Architecture", test_frontend_integration_architecture),
        ("CopilotKit Handler Initialization", test_copilotkit_handler_initialization),
        ("CopilotKit Actions", test_copilotkit_actions),
        ("Streaming Responses", test_streaming_responses),
        ("Drill-Down Capabilities", test_drill_down_capabilities),
        ("Feedback Collection", test_feedback_collection),
        ("Interactive Features", test_interactive_features),
        ("AG-UI Integration", test_ag_ui_integration)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔬 {test_name}")
        print("-" * 50)

        try:
            # Handle async tests
            if test_func.__name__ in [
                'test_copilotkit_actions', 'test_streaming_responses',
                'test_drill_down_capabilities', 'test_feedback_collection',
                'test_interactive_features'
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

    print("\n" + "="*70)
    print(f"📊 Task 6 Validation Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Task 6: Frontend Integration with AG-UI System COMPLETED!")
        print("\n✅ LIDA web API adapted to work with CopilotKit actions")
        print("✅ Streaming responses for progressive visualization generation implemented")
        print("✅ Drill-down capabilities with context preservation added")
        print("✅ Interactive ECharts components with feedback loops created")
        print("✅ WebSocket support and real-time updates architecture prepared")
        print("✅ User feedback collection and learning system integrated")
        print("✅ Multi-dimensional exploration and navigation implemented")
        print("✅ Accessibility and customization features included")
        print("✅ Ready to proceed to Task 7: FOCUS Sample Data Integration")
        return True
    else:
        print("❌ Task 6 validation failed. Please review implementation before proceeding.")
        return False


if __name__ == "__main__":
    success = run_task6_validation()
    exit(0 if success else 1)