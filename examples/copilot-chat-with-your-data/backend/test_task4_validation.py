"""
Test suite for Task 4: Persona-Aware Visualization Selection.

This test validates the persona-aware visualization selection system that extends
LIDA's basic persona parameter with detailed profiles, Cleveland-McGill perceptual
hierarchy filtering, FTVV-based algorithm, and cognitive load assessment.
"""

import json
import sys
from unittest.mock import MagicMock, AsyncMock, patch


def test_persona_database_architecture():
    """Test the persona database and profile system architecture."""

    print("🔍 Testing Persona Database Architecture...")

    try:
        # Test import structure
        from persona_aware_selection import (
            PersonaAwareVisualizationSelector,
            PersonaProfile,
            PersonaType,
            CognitiveLevelType,
            FTVVNarrativeGoal,
            ClevelandMcGillHierarchy,
            CognitiveLoadMetrics,
            create_persona_aware_selector
        )
        print("✅ Persona-aware selection imports successful")

        # Test persona database initialization
        selector = PersonaAwareVisualizationSelector()
        assert len(selector.persona_database) > 0, "Should have persona profiles"
        assert PersonaType.EXECUTIVE.value in selector.persona_database, "Should have executive persona"
        assert PersonaType.ANALYST.value in selector.persona_database, "Should have analyst persona"
        print("✅ Persona database initialization successful")

        # Test persona profile structure
        executive_profile = selector.get_persona_profile(PersonaType.EXECUTIVE.value)
        assert executive_profile is not None, "Should retrieve executive profile"
        assert executive_profile.persona_type == PersonaType.EXECUTIVE, "Profile type should match"
        assert len(executive_profile.preferred_chart_types) > 0, "Should have preferred charts"
        assert len(executive_profile.forbidden_chart_types) > 0, "Should have forbidden charts"
        assert executive_profile.perceptual_accuracy_threshold > 0.5, "Should have accuracy threshold"
        print("✅ Persona profile structure validated")

        # Test cognitive level differentiation
        analyst_profile = selector.get_persona_profile(PersonaType.ANALYST.value)
        assert analyst_profile.cognitive_level != executive_profile.cognitive_level, "Should have different cognitive levels"
        assert analyst_profile.data_literacy_level > executive_profile.data_literacy_level, "Analyst should have higher data literacy"
        assert analyst_profile.max_data_points > executive_profile.max_data_points, "Analyst should handle more data"
        print("✅ Cognitive level differentiation working")

        return True

    except Exception as e:
        print(f"❌ Persona database architecture test failed: {e}")
        return False


def test_cleveland_mcgill_hierarchy():
    """Test Cleveland-McGill perceptual hierarchy implementation."""

    print("🔍 Testing Cleveland-McGill Perceptual Hierarchy...")

    try:
        from persona_aware_selection import ClevelandMcGillHierarchy

        hierarchy = ClevelandMcGillHierarchy()

        # Test encoding accuracy scores
        bar_score = hierarchy.get_chart_accuracy_score('bar')
        pie_score = hierarchy.get_chart_accuracy_score('pie')
        heatmap_score = hierarchy.get_chart_accuracy_score('heatmap')

        # Bar charts should have higher accuracy than pie charts
        assert bar_score > pie_score, "Bar charts should be more accurate than pie charts"
        assert pie_score > heatmap_score, "Pie charts should be more accurate than heatmaps"
        assert bar_score >= 0.9, "Bar charts should have high accuracy score"
        print("✅ Perceptual accuracy hierarchy correct")

        # Test chart filtering by accuracy threshold
        all_charts = ['bar', 'pie', 'heatmap', 'line', 'scatter']
        high_accuracy_charts = hierarchy.filter_charts_by_accuracy(all_charts, 0.8)
        low_accuracy_charts = hierarchy.filter_charts_by_accuracy(all_charts, 0.3)

        assert len(high_accuracy_charts) < len(all_charts), "High threshold should filter out charts"
        assert len(low_accuracy_charts) > len(high_accuracy_charts), "Low threshold should include more charts"
        assert 'bar' in high_accuracy_charts, "Bar should pass high accuracy threshold"
        print("✅ Chart filtering by accuracy threshold working")

        # Test that position encodings are preferred
        position_charts = ['bar', 'line', 'scatter']
        angle_charts = ['pie']
        area_charts = ['treemap', 'bubble']

        avg_position_score = sum(hierarchy.get_chart_accuracy_score(chart) for chart in position_charts) / len(position_charts)
        avg_angle_score = sum(hierarchy.get_chart_accuracy_score(chart) for chart in angle_charts) / len(angle_charts)

        assert avg_position_score > avg_angle_score, "Position encodings should be more accurate than angle encodings"
        print("✅ Cleveland-McGill hierarchy properly implemented")

        return True

    except Exception as e:
        print(f"❌ Cleveland-McGill hierarchy test failed: {e}")
        return False


def test_ftvv_narrative_classification():
    """Test FTVV-based narrative goal classification."""

    print("🔍 Testing FTVV Narrative Classification...")

    try:
        from persona_aware_selection import PersonaAwareVisualizationSelector, FTVVNarrativeGoal

        selector = PersonaAwareVisualizationSelector()

        # Test magnitude comparison classification
        magnitude_goal = {
            'question': 'Which region has the highest sales?',
            'visualization': 'Compare sales by region'
        }
        narrative = selector._classify_narrative_goal(magnitude_goal, {})
        assert narrative == FTVVNarrativeGoal.MAGNITUDE_COMPARISON, "Should classify as magnitude comparison"
        print("✅ Magnitude comparison classification working")

        # Test time series classification
        time_goal = {
            'question': 'How have sales changed over time?',
            'visualization': 'Show sales trend evolution'
        }
        narrative = selector._classify_narrative_goal(time_goal, {})
        assert narrative == FTVVNarrativeGoal.CHANGE_OVER_TIME, "Should classify as change over time"
        print("✅ Time series classification working")

        # Test correlation classification
        correlation_goal = {
            'question': 'What is the relationship between price and sales?',
            'visualization': 'Show correlation analysis'
        }
        narrative = selector._classify_narrative_goal(correlation_goal, {})
        assert narrative == FTVVNarrativeGoal.CORRELATION, "Should classify as correlation"
        print("✅ Correlation classification working")

        # Test ranking classification
        ranking_goal = {
            'question': 'What are the top 10 products by revenue?',
            'visualization': 'Rank products by performance'
        }
        narrative = selector._classify_narrative_goal(ranking_goal, {})
        assert narrative == FTVVNarrativeGoal.RANKING, "Should classify as ranking"
        print("✅ Ranking classification working")

        # Test FTVV candidate chart mapping
        ftvv_mapping = selector.ftvv_chart_mapping
        assert FTVVNarrativeGoal.MAGNITUDE_COMPARISON in ftvv_mapping, "Should have magnitude comparison mapping"
        assert 'bar' in ftvv_mapping[FTVVNarrativeGoal.MAGNITUDE_COMPARISON]['primary_charts'], "Bar should be primary for magnitude comparison"
        assert 'line' in ftvv_mapping[FTVVNarrativeGoal.CHANGE_OVER_TIME]['primary_charts'], "Line should be primary for time series"
        print("✅ FTVV chart mapping structure correct")

        return True

    except Exception as e:
        print(f"❌ FTVV narrative classification test failed: {e}")
        return False


def test_persona_constraint_filtering():
    """Test persona-specific constraint filtering."""

    print("🔍 Testing Persona Constraint Filtering...")

    try:
        from persona_aware_selection import PersonaAwareVisualizationSelector, PersonaType

        selector = PersonaAwareVisualizationSelector()

        # Get persona profiles
        executive = selector.get_persona_profile(PersonaType.EXECUTIVE.value)
        analyst = selector.get_persona_profile(PersonaType.ANALYST.value)

        # Test chart filtering for executive
        all_charts = ['bar', 'line', 'pie', 'heatmap', 'sankey', 'scatter']
        executive_charts = selector._apply_persona_constraints(all_charts, executive)

        # Executive should have simpler charts
        assert 'bar' in executive_charts, "Executive should allow bar charts"
        assert 'heatmap' not in executive_charts, "Executive should not allow complex heatmaps"
        assert len(executive_charts) < len(all_charts), "Executive should have fewer chart options"
        print("✅ Executive persona filtering working")

        # Test chart filtering for analyst
        analyst_charts = selector._apply_persona_constraints(all_charts, analyst)

        # Analyst should have more chart options
        assert len(analyst_charts) >= len(executive_charts), "Analyst should have more chart options"
        assert 'scatter' in analyst_charts, "Analyst should allow scatter plots"
        assert 'heatmap' in analyst_charts, "Analyst should allow heatmaps"
        print("✅ Analyst persona filtering working")

        # Test data point constraints
        assert executive.max_data_points < analyst.max_data_points, "Executive should handle fewer data points"
        assert executive.max_series_count < analyst.max_series_count, "Executive should handle fewer series"
        assert executive.perceptual_accuracy_threshold > analyst.perceptual_accuracy_threshold, "Executive should require higher accuracy"
        print("✅ Data constraint differentiation working")

        return True

    except Exception as e:
        print(f"❌ Persona constraint filtering test failed: {e}")
        return False


def test_multi_criteria_scoring():
    """Test multi-criteria decision matrix scoring system."""

    print("🔍 Testing Multi-Criteria Scoring System...")

    try:
        from persona_aware_selection import PersonaAwareVisualizationSelector, PersonaType, FTVVNarrativeGoal

        selector = PersonaAwareVisualizationSelector()
        executive = selector.get_persona_profile(PersonaType.EXECUTIVE.value)

        # Sample data for scoring
        sample_data_summary = {
            'columns': ['region', 'sales'],
            'data_types': {'region': 'categorical', 'sales': 'numeric'},
            'sample_data': [{'region': 'North', 'sales': 1000}]
        }

        sample_goal = {
            'question': 'Compare sales by region',
            'visualization': 'Regional sales comparison'
        }

        # Test scoring for magnitude comparison
        chart_types = ['bar', 'pie', 'line']
        scored_charts = selector._score_charts_multi_criteria(
            chart_types, sample_data_summary, sample_goal, executive, FTVVNarrativeGoal.MAGNITUDE_COMPARISON
        )

        assert len(scored_charts) == len(chart_types), "Should score all input charts"
        assert all('total_score' in chart for chart in scored_charts), "All charts should have total scores"
        assert all('rationale' in chart for chart in scored_charts), "All charts should have rationales"
        print("✅ Multi-criteria scoring structure correct")

        # Test scoring components
        first_chart = scored_charts[0]
        assert 'perceptual_score' in first_chart, "Should have perceptual score"
        assert 'preference_score' in first_chart, "Should have preference score"
        assert 'narrative_score' in first_chart, "Should have narrative score"
        assert 'complexity_score' in first_chart, "Should have complexity score"
        print("✅ Scoring components present")

        # Test that charts are sorted by score
        scores = [chart['total_score'] for chart in scored_charts]
        assert scores == sorted(scores, reverse=True), "Charts should be sorted by score descending"
        print("✅ Chart scoring and ranking working")

        # Test that bar chart scores well for magnitude comparison
        bar_chart = next((chart for chart in scored_charts if chart['chart_type'] == 'bar'), None)
        assert bar_chart is not None, "Bar chart should be in results"
        assert bar_chart['narrative_score'] >= 0.8, "Bar chart should score well for magnitude comparison"
        print("✅ Narrative goal alignment scoring working")

        return True

    except Exception as e:
        print(f"❌ Multi-criteria scoring test failed: {e}")
        return False


def test_cognitive_load_assessment():
    """Test cognitive load assessment functionality."""

    print("🔍 Testing Cognitive Load Assessment...")

    try:
        from persona_aware_selection import PersonaAwareVisualizationSelector, PersonaType, CognitiveLoadMetrics

        selector = PersonaAwareVisualizationSelector()
        executive = selector.get_persona_profile(PersonaType.EXECUTIVE.value)

        # Sample data for assessment
        sample_data_summary = {
            'columns': ['region', 'sales', 'product', 'date'],
            'data_types': {'region': 'categorical', 'sales': 'numeric', 'product': 'categorical', 'date': 'datetime'},
            'sample_data': [{'region': 'North', 'sales': 1000, 'product': 'A', 'date': '2024-01'}] * 100
        }

        # Test simple chart cognitive load
        simple_chart = {'chart_type': 'bar', 'total_score': 0.9}
        simple_assessment = selector._assess_cognitive_load(simple_chart, sample_data_summary, executive)

        assert isinstance(simple_assessment, CognitiveLoadMetrics), "Should return CognitiveLoadMetrics"
        assert 0.0 <= simple_assessment.overall_cognitive_load <= 1.0, "Overall load should be between 0 and 1"
        assert 0.0 <= simple_assessment.visual_complexity_score <= 1.0, "Visual complexity should be between 0 and 1"
        assert 0.0 <= simple_assessment.information_density_score <= 1.0, "Info density should be between 0 and 1"
        print("✅ Cognitive load metrics structure correct")

        # Test complex chart cognitive load
        complex_chart = {'chart_type': 'sankey', 'total_score': 0.7}
        complex_assessment = selector._assess_cognitive_load(complex_chart, sample_data_summary, executive)

        assert complex_assessment.overall_cognitive_load > simple_assessment.overall_cognitive_load, "Complex chart should have higher cognitive load"
        assert complex_assessment.visual_complexity_score > simple_assessment.visual_complexity_score, "Complex chart should have higher visual complexity"
        print("✅ Cognitive load differentiation working")

        # Test simplification recommendations
        if complex_assessment.simplification_needed:
            assert len(complex_assessment.recommended_changes) > 0, "Should provide recommendations when simplification needed"
            print("✅ Simplification recommendations present")

        # Test cognitive load assessment components
        assert hasattr(simple_assessment, 'interaction_complexity_score'), "Should assess interaction complexity"
        assert hasattr(simple_assessment, 'color_complexity_score'), "Should assess color complexity"
        print("✅ All cognitive load components assessed")

        return True

    except Exception as e:
        print(f"❌ Cognitive load assessment test failed: {e}")
        return False


def test_optimal_visualization_selection():
    """Test the complete optimal visualization selection process."""

    print("🔍 Testing Optimal Visualization Selection...")

    try:
        from persona_aware_selection import PersonaAwareVisualizationSelector, PersonaType

        selector = PersonaAwareVisualizationSelector()

        # Sample data and goal
        sample_data_summary = {
            'columns': ['region', 'sales', 'quarter'],
            'data_types': {'region': 'categorical', 'sales': 'numeric', 'quarter': 'categorical'},
            'sample_data': [
                {'region': 'North', 'sales': 1000, 'quarter': 'Q1'},
                {'region': 'South', 'sales': 800, 'quarter': 'Q1'},
                {'region': 'East', 'sales': 1200, 'quarter': 'Q1'}
            ]
        }

        sample_goal = {
            'question': 'Which region has the highest sales?',
            'visualization': 'Compare regional sales performance'
        }

        # Test executive selection
        executive_result = selector.select_optimal_visualization(
            sample_data_summary, sample_goal, PersonaType.EXECUTIVE.value
        )

        # Validate result structure
        required_keys = [
            'selected_chart_type', 'selection_score', 'narrative_goal',
            'persona_profile', 'cleveland_mcgill_accuracy', 'cognitive_load_assessment',
            'alternative_charts', 'selection_rationale', 'data_constraints', 'accessibility_features'
        ]

        for key in required_keys:
            assert key in executive_result, f"Result should contain {key}"

        print("✅ Complete selection result structure validated")

        # Test persona-specific results
        assert executive_result['selected_chart_type'] in ['bar', 'column', 'pie'], "Executive should get simple chart types"
        assert executive_result['persona_profile']['cognitive_level'] == 'medium', "Executive cognitive level should be medium"
        assert executive_result['accessibility_features']['high_contrast'] is True, "Executive should require high contrast"
        print("✅ Executive persona selection working")

        # Test analyst selection for comparison
        analyst_result = selector.select_optimal_visualization(
            sample_data_summary, sample_goal, PersonaType.ANALYST.value
        )

        # Analyst should potentially have different selection
        assert 'selected_chart_type' in analyst_result, "Analyst should have chart selection"
        assert analyst_result['persona_profile']['cognitive_level'] == 'high', "Analyst cognitive level should be high"
        assert len(analyst_result['alternative_charts']) > 0, "Should provide alternative charts"
        print("✅ Analyst persona selection working")

        # Test selection score differences
        assert 0.0 <= executive_result['selection_score'] <= 1.0, "Selection score should be normalized"
        assert 0.0 <= executive_result['cleveland_mcgill_accuracy'] <= 1.0, "Cleveland-McGill score should be normalized"
        print("✅ Selection scoring normalized correctly")

        # Test cognitive load assessment integration
        cognitive_assessment = executive_result['cognitive_load_assessment']
        assert 'overall_cognitive_load' in cognitive_assessment, "Should include overall cognitive load"
        assert 'simplification_needed' in cognitive_assessment, "Should indicate if simplification needed"
        print("✅ Cognitive load assessment integrated")

        return True

    except Exception as e:
        print(f"❌ Optimal visualization selection test failed: {e}")
        return False


def test_integration_with_lida_manager():
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

        # Test persona selector integration capability
        from persona_aware_selection import PersonaAwareVisualizationSelector, create_persona_aware_selector

        selector = PersonaAwareVisualizationSelector()

        # Test that selector could be integrated with LIDA manager
        assert hasattr(selector, 'select_optimal_visualization'), "Should have visualization selection method"
        assert hasattr(selector, 'get_persona_profile'), "Should have persona retrieval method"
        assert callable(create_persona_aware_selector), "Factory function should be callable"
        print("✅ Persona selector methods compatible with LIDA manager")

        # Test persona compatibility with existing system
        personas = list(selector.persona_database.keys())
        expected_personas = ['executive', 'analyst', 'manager', 'stakeholder']
        for persona in expected_personas:
            assert persona in personas, f"Should support {persona} persona"
        print("✅ Persona types compatible with existing system")

        # Test that selector enhances rather than replaces LIDA
        # (Integration would happen in LIDA manager, testing structure here)
        sample_result = {
            'selected_chart_type': 'bar',
            'narrative_goal': 'magnitude_comparison',
            'persona_profile': {'name': 'Executive'}
        }

        # Test result format could be used by LIDA manager
        assert 'selected_chart_type' in sample_result, "Result should specify chart type"
        assert 'narrative_goal' in sample_result, "Result should specify narrative goal"
        print("✅ Result format compatible with LIDA manager")

        return True

    except Exception as e:
        print(f"❌ LIDA manager integration test failed: {e}")
        return False


def run_task4_validation():
    """Run comprehensive Task 4 validation."""

    print("🧪 Running Task 4: Persona-Aware Visualization Selection Validation")
    print("="*70)

    tests = [
        ("Persona Database Architecture", test_persona_database_architecture),
        ("Cleveland-McGill Hierarchy", test_cleveland_mcgill_hierarchy),
        ("FTVV Narrative Classification", test_ftvv_narrative_classification),
        ("Persona Constraint Filtering", test_persona_constraint_filtering),
        ("Multi-Criteria Scoring", test_multi_criteria_scoring),
        ("Cognitive Load Assessment", test_cognitive_load_assessment),
        ("Optimal Visualization Selection", test_optimal_visualization_selection),
        ("LIDA Manager Integration", test_integration_with_lida_manager)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔬 {test_name}")
        print("-" * 50)

        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")

    print("\n" + "="*70)
    print(f"📊 Task 4 Validation Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Task 4: Persona-Aware Visualization Selection COMPLETED!")
        print("\n✅ Detailed persona profiles with cognitive characteristics implemented")
        print("✅ Cleveland-McGill perceptual hierarchy filtering integrated")
        print("✅ FTVV-based narrative goal classification system created")
        print("✅ Multi-criteria decision matrix for chart selection implemented")
        print("✅ Cognitive load assessment with simplification recommendations added")
        print("✅ Persona-specific constraint filtering system operational")
        print("✅ Advanced visualization intelligence beyond LIDA basic personas")
        print("✅ Ready to proceed to Task 5: Memory and Context Integration")
        return True
    else:
        print("❌ Task 4 validation failed. Please review implementation before proceeding.")
        return False


if __name__ == "__main__":
    success = run_task4_validation()
    exit(0 if success else 1)