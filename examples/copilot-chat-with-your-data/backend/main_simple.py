"""Simplified FastAPI runtime for testing chart suggestions without external dependencies."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="CopilotKit FastAPI Runtime - Simplified", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("copilotkit-backend")

# Global user preference memory
_user_preferences: Dict[str, Dict[str, Any]] = {}

def _get_user_context(user_id: str) -> Dict[str, Any]:
    """Get user context and preferences from memory."""
    if user_id not in _user_preferences:
        _user_preferences[user_id] = {
            "preferred_chart_types": [],
            "avoided_chart_types": [],
            "visualization_history": [],
            "common_goals": [],
            "persona_preferences": {},
            "dataset_preferences": {}
        }
    return _user_preferences[user_id]


def _update_user_preferences(user_id: str, choice_data: Dict[str, Any]) -> None:
    """Update user preferences based on their chart selection."""
    context = _get_user_context(user_id)

    # Update preferred chart types
    chosen_chart_type = choice_data.get("chart_type")
    if chosen_chart_type:
        if chosen_chart_type not in context["preferred_chart_types"]:
            context["preferred_chart_types"].append(chosen_chart_type)

        # If they consistently choose this type, increase its priority
        recent_choices = context["visualization_history"][-5:]  # Last 5 choices
        chart_frequency = sum(1 for choice in recent_choices if choice.get("chart_type") == chosen_chart_type)
        if chart_frequency >= 3:  # If chosen 3+ times in last 5
            # Move to front of preferred list
            context["preferred_chart_types"] = [chosen_chart_type] + [
                ct for ct in context["preferred_chart_types"] if ct != chosen_chart_type
            ]

    # Update visualization history
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "goal": choice_data.get("goal", ""),
        "chart_type": chosen_chart_type,
        "dataset": choice_data.get("dataset", ""),
        "persona": choice_data.get("persona", ""),
        "suggestion_id": choice_data.get("suggestion_id", "")
    }
    context["visualization_history"].append(history_entry)

    # Keep only last 50 entries
    if len(context["visualization_history"]) > 50:
        context["visualization_history"] = context["visualization_history"][-50:]

    # Update common goals
    goal = choice_data.get("goal", "").lower()
    if goal and goal not in context["common_goals"]:
        context["common_goals"].append(goal)

    # Update persona preferences
    persona = choice_data.get("persona", "")
    if persona:
        if persona not in context["persona_preferences"]:
            context["persona_preferences"][persona] = {"chart_types": [], "goals": []}

        persona_prefs = context["persona_preferences"][persona]
        if chosen_chart_type and chosen_chart_type not in persona_prefs["chart_types"]:
            persona_prefs["chart_types"].append(chosen_chart_type)
        if goal and goal not in persona_prefs["goals"]:
            persona_prefs["goals"].append(goal)

    logger.info("Updated preferences for user %s: preferred_types=%s", user_id, context["preferred_chart_types"])


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "copilotkit-fastapi-runtime-simplified",
        "features": ["chart_suggestions", "user_preferences"]
    }


@app.get("/finops-web/datasets")
async def get_focus_datasets() -> Dict[str, Any]:
    """Mock dataset endpoint for testing."""
    sample_datasets = [
        {
            "name": "small_company_finops",
            "description": "FOCUS-compliant FinOps dataset for small company with 500 records",
            "rows": 500,
            "compliance_score": 0.95,
            "dataset_type": "focus_sample",
            "service_count": 8,
            "account_count": 3,
            "region_count": 4,
            "data_quality_score": 0.92,
            "optimization_opportunities_count": 5,
            "anomaly_candidates_count": 1,
        },
        {
            "name": "enterprise_multi_cloud",
            "description": "FOCUS-compliant FinOps dataset for enterprise multi-cloud with 2000 records",
            "rows": 2000,
            "compliance_score": 0.88,
            "dataset_type": "focus_sample",
            "service_count": 25,
            "account_count": 8,
            "region_count": 6,
            "data_quality_score": 0.89,
            "optimization_opportunities_count": 12,
            "anomaly_candidates_count": 3,
        }
    ]
    return {"datasets": sample_datasets}


@app.post("/finops-web/select-dataset")
async def select_focus_dataset(request: Request) -> Dict[str, Any]:
    """Mock dataset selection endpoint."""
    payload = await request.json()
    dataset_name = payload.get("dataset_name")

    if not dataset_name:
        raise HTTPException(status_code=400, detail="Missing dataset_name parameter")

    # Mock dataset response
    mock_response = {
        "dataset": {
            "name": dataset_name,
            "description": "FOCUS-compliant FinOps dataset for cost analysis and optimization",
            "rows": 1000,
            "compliance_score": 0.95,
            "data_quality_score": 0.92,
        },
        "preview": {
            "columns": ["ServiceName", "BilledCost", "UsageQuantity", "BillingDate", "AccountId", "Region"],
            "sample_records": [
                {"ServiceName": "EC2", "BilledCost": 125.50, "UsageQuantity": 100, "BillingDate": "2024-01-01", "AccountId": "123456789", "Region": "us-east-1"},
                {"ServiceName": "S3", "BilledCost": 45.25, "UsageQuantity": 200, "BillingDate": "2024-01-01", "AccountId": "123456789", "Region": "us-east-1"},
                {"ServiceName": "RDS", "BilledCost": 89.75, "UsageQuantity": 50, "BillingDate": "2024-01-01", "AccountId": "123456789", "Region": "us-west-2"},
            ],
            "statistics": {
                "BilledCost": {"min": 10.0, "max": 500.0, "mean": 125.5, "count": 1000},
                "UsageQuantity": {"min": 1, "max": 1000, "mean": 150, "count": 1000}
            },
        }
    }

    return mock_response


def _generate_chart_suggestions(goal: str, user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate chart suggestions based on goal analysis and user preferences."""
    goal_lower = goal.lower()

    # Chart type priorities based on goal analysis
    chart_priorities = []

    if any(word in goal_lower for word in ["distribution", "breakdown", "compare", "by"]):
        chart_priorities = ["bar", "pie", "line"]
    elif any(word in goal_lower for word in ["trend", "over time", "timeline", "changes"]):
        chart_priorities = ["line", "bar", "area"]
    elif any(word in goal_lower for word in ["proportion", "percentage", "share", "composition"]):
        chart_priorities = ["pie", "bar", "donut"]
    elif any(word in goal_lower for word in ["correlation", "relationship", "vs", "against"]):
        chart_priorities = ["scatter", "line", "bar"]
    else:
        # Default priorities
        chart_priorities = ["bar", "pie", "line"]

    suggestions = []

    # Generate suggestions for top 3 chart types
    for i, chart_type in enumerate(chart_priorities[:3]):
        config = _generate_sample_config(chart_type, goal)

        suggestion = {
            "id": f"suggestion_{i+1}",
            "chart_type": chart_type,
            "config": config,
            "title": goal,
            "reasoning": _get_chart_reasoning(chart_type, goal),
            "best_for": _get_chart_best_use(chart_type),
            "priority": i + 1
        }

        # Adjust priority based on user preferences
        if user_context and user_context.get("preferred_chart_types"):
            preferred_types = user_context["preferred_chart_types"]
            if chart_type in preferred_types:
                suggestion["priority"] -= 0.5  # Higher priority for preferred types

        suggestions.append(suggestion)

    # Sort by priority
    suggestions.sort(key=lambda x: x["priority"])

    return suggestions


def _generate_sample_config(chart_type: str, title: str) -> Dict[str, Any]:
    """Generate sample ECharts configuration."""
    sample_data = [
        ["EC2", 125.50],
        ["S3", 45.25],
        ["RDS", 89.75],
        ["Lambda", 25.00],
        ["CloudWatch", 15.50]
    ]

    if chart_type in ["bar", "line"]:
        return {
            "title": {"text": title, "left": "center"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": [item[0] for item in sample_data]},
            "yAxis": {"type": "value"},
            "series": [{
                "name": "Cost",
                "type": chart_type,
                "data": [item[1] for item in sample_data],
                "itemStyle": {"color": "#5470c6" if chart_type == "bar" else "#91cc75"}
            }],
            "animation": True
        }
    elif chart_type == "pie":
        return {
            "title": {"text": title, "left": "center"},
            "tooltip": {"trigger": "item", "formatter": "{a}<br/>{b}: {c} ({d}%)"},
            "series": [{
                "name": "Cost",
                "type": "pie",
                "radius": ["40%", "70%"],
                "data": [{"name": item[0], "value": item[1]} for item in sample_data]
            }]
        }

    return {"title": {"text": title}}


def _get_chart_reasoning(chart_type: str, goal: str) -> str:
    """Get reasoning for why this chart type is suitable for the goal."""
    reasoning_map = {
        "bar": "Best for comparing discrete categories and showing exact values clearly",
        "line": "Ideal for showing trends, changes over time, and continuous data patterns",
        "pie": "Perfect for showing proportions, percentages, and parts of a whole",
        "scatter": "Excellent for exploring relationships and correlations between variables",
        "area": "Great for showing cumulative values and trends with emphasis on magnitude"
    }
    base_reasoning = reasoning_map.get(chart_type, "Suitable for general data visualization")

    if "comparison" in goal.lower() or "compare" in goal.lower():
        if chart_type == "bar":
            return base_reasoning + ". Excellent choice for your comparison needs."
    elif "trend" in goal.lower() or "time" in goal.lower():
        if chart_type == "line":
            return base_reasoning + ". Perfect match for trend analysis."
    elif "distribution" in goal.lower() or "breakdown" in goal.lower():
        if chart_type in ["pie", "bar"]:
            return base_reasoning + ". Ideal for showing distribution patterns."

    return base_reasoning


def _get_chart_best_use(chart_type: str) -> str:
    """Get description of what this chart type is best used for."""
    use_cases = {
        "bar": "Comparing quantities across categories, ranking data, showing discrete values",
        "line": "Time series analysis, trend identification, continuous data visualization",
        "pie": "Showing proportions, market share analysis, budget breakdowns",
        "scatter": "Correlation analysis, outlier detection, relationship exploration",
        "area": "Cumulative data, stacked comparisons, volume emphasis"
    }
    return use_cases.get(chart_type, "General purpose data visualization")


@app.post("/lida/visualize")
async def lida_visualize(request: Request) -> Dict[str, Any]:
    """Generate chart suggestions based on goal and user preferences."""
    try:
        payload = await request.json()
        dataset_name = payload.get("dataset_name")
        goal = payload.get("goal")
        chart_type = payload.get("chart_type")
        persona = payload.get("persona", "default")
        user_id = payload.get("user_id", "default_user")

        if not dataset_name:
            raise HTTPException(status_code=400, detail="Missing dataset_name parameter")
        if not goal:
            raise HTTPException(status_code=400, detail="Missing goal parameter")

        logger.info("LIDA visualize request: dataset=%s, goal=%s, chart_type=%s, persona=%s, user=%s",
                   dataset_name, goal, chart_type, persona, user_id)

        # Get user context for personalized suggestions
        user_context = _get_user_context(user_id)

        # Generate multiple chart suggestions
        suggestions = _generate_chart_suggestions(goal, user_context)

        # Generate insights
        insights = [
            f"Generated {len(suggestions)} chart suggestions for your goal",
            f"Based on your preferences: {', '.join(user_context.get('preferred_chart_types', [])[:3]) or 'No preferences yet'}",
            f"Dataset: {dataset_name} with sample FinOps data"
        ]

        response = {
            "suggestions": suggestions,
            "goal": goal,
            "user_id": user_id,
            "user_preferences": {
                "preferred_chart_types": user_context.get("preferred_chart_types", []),
                "recent_goals": user_context.get("common_goals", [])[-5:],
                "persona_preferences": user_context.get("persona_preferences", {}).get(persona, {})
            },
            "insights": insights,
            "data_summary": {
                "total_records": 1000,
                "columns": ["ServiceName", "BilledCost", "UsageQuantity", "BillingDate", "AccountId", "Region"],
                "dataset_type": "focus_finops"
            },
            "suggestion_count": len(suggestions),
            "dataset_name": dataset_name,
            "persona": persona,
            "recommendation": "Please select your preferred chart type. Your choice will help us provide better suggestions in the future."
        }

        logger.info("Successfully generated %d LIDA visualization suggestions for goal: '%s'", len(suggestions), goal)
        return response

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("LIDA visualization generation failed")
        raise HTTPException(status_code=500, detail=f"Visualization error: {exc}") from exc


@app.post("/lida/select-chart")
async def lida_select_chart(request: Request) -> Dict[str, Any]:
    """Record user's chart selection to update preferences."""
    try:
        payload = await request.json()
        user_id = payload.get("user_id", "default_user")
        suggestion_id = payload.get("suggestion_id")
        chart_type = payload.get("chart_type")
        goal = payload.get("goal")
        dataset_name = payload.get("dataset_name")
        persona = payload.get("persona", "default")

        if not suggestion_id or not chart_type:
            raise HTTPException(status_code=400, detail="Missing suggestion_id or chart_type parameter")

        logger.info("Recording chart selection: user=%s, chart_type=%s, goal=%s", user_id, chart_type, goal)

        # Update user preferences based on their selection
        choice_data = {
            "chart_type": chart_type,
            "goal": goal or "",
            "dataset": dataset_name or "",
            "persona": persona,
            "suggestion_id": suggestion_id
        }

        _update_user_preferences(user_id, choice_data)

        # Get updated preferences to return current state
        updated_context = _get_user_context(user_id)

        return {
            "success": True,
            "message": "Chart selection recorded successfully",
            "user_id": user_id,
            "selected_chart_type": chart_type,
            "updated_preferences": {
                "preferred_chart_types": updated_context.get("preferred_chart_types", []),
                "total_visualizations": len(updated_context.get("visualization_history", [])),
                "common_goals": updated_context.get("common_goals", [])[-5:],
                "persona_preferences": updated_context.get("persona_preferences", {})
            }
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to record chart selection")
        raise HTTPException(status_code=500, detail=f"Selection recording error: {exc}") from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_simple:app", host="0.0.0.0", port=8004, reload=True)