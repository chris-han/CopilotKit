"""Generate deterministic data story steps for the dashboard dataset."""

from __future__ import annotations

from typing import Any, Dict, List

from dashboard_data import DASHBOARD_CONTEXT


def _format_currency(value: float) -> str:
    return f"${value:,.0f}"


def _format_percentage(value: float) -> str:
    return f"{value:.1f}%"


def generate_data_story_steps() -> List[Dict[str, Any]]:
    """Return an ordered list of data story steps derived from the dashboard dataset."""

    sales = DASHBOARD_CONTEXT["salesData"]
    metrics = DASHBOARD_CONTEXT["metrics"]
    product_data = DASHBOARD_CONTEXT["productData"]
    category_data = DASHBOARD_CONTEXT["categoryData"]
    regional_data = DASHBOARD_CONTEXT["regionalData"]
    demographics_data = DASHBOARD_CONTEXT["demographicsData"]

    latest_month = sales[-1]
    previous_month = sales[-2]
    revenue_delta = latest_month["Sales"] - previous_month["Sales"]
    revenue_delta_pct = (revenue_delta / previous_month["Sales"]) * 100 if previous_month["Sales"] else 0

    top_product = max(product_data, key=lambda item: item["sales"])
    lagging_product = min(product_data, key=lambda item: item["growth"])
    leading_category = max(category_data, key=lambda item: item["value"])

    top_region = max(regional_data, key=lambda item: item["sales"])
    second_region = sorted(regional_data, key=lambda item: item["sales"], reverse=True)[1]
    top_demo = max(demographics_data, key=lambda item: item["spending"])

    steps: List[Dict[str, Any]] = [
        {
            "id": "story-overview",
            "stepType": "overview",
            "title": "Overall performance remains strong",
            "markdown": (
                "The dashboard closed the latest month with **"
                f"{_format_currency(latest_month['Sales'])}** in revenue and **"
                f"{_format_currency(latest_month['Profit'])}** profit. Month-over-month revenue moved "
                f"{revenue_delta_pct:+.1f}% compared to {previous_month['date']} and customer reach hit "
                f"{latest_month['Customers']:,}."
            ),
            "chartIds": ["sales-overview"],
            "kpis": [
                {"label": "Revenue", "value": _format_currency(metrics["totalRevenue"]), "trend": "up" if revenue_delta >= 0 else "down"},
                {"label": "Profit", "value": _format_currency(metrics["totalProfit"]), "trend": "up"},
                {"label": "Customers", "value": f"{metrics['totalCustomers']:,}"},
            ],
            "reviewPrompt": "Highlight revenue overview",
        },
        {
            "id": "story-products",
            "stepType": "change",
            "title": "Product leaders and laggards",
            "markdown": (
                f"**{top_product['name']}** continues to lead with {_format_currency(top_product['sales'])} in sales "
                f"and {top_product['growth']:.1f}% growth. In contrast, **{lagging_product['name']}** is contracting "
                f"at {lagging_product['growth']:.1f}% and is worth a closer look."
            ),
            "chartIds": ["product-performance"],
            "kpis": [
                {"label": top_product["name"], "value": _format_currency(top_product["sales"]), "trend": "up"},
                {"label": lagging_product["name"], "value": _format_currency(lagging_product["sales"]), "trend": "down"},
            ],
            "reviewPrompt": "Review product performance",
        },
        {
            "id": "story-categories",
            "stepType": "change",
            "title": "Category mix skewed toward electronics",
            "markdown": (
                f"Electronics drives {leading_category['value']}% of revenue and is still growing at {leading_category['growth']:.1f}%. "
                f"Other categories such as Home & Kitchen ({_format_percentage(category_data[2]['growth'])}) are also contributing incremental growth."
            ),
            "chartIds": ["sales-by-category"],
            "kpis": [
                {"label": leading_category["name"], "value": f"{leading_category['value']}%", "trend": "up"},
                {"label": "Home & Kitchen", "value": f"{category_data[2]['value']}%", "trend": "up"},
            ],
            "reviewPrompt": "Revisit category mix",
        },
        {
            "id": "story-regions",
            "stepType": "change",
            "title": "Regional concentration remains high",
            "markdown": (
                f"**{top_region['region']}** contributes {_format_currency(top_region['sales'])} ({top_region['marketShare']}% share). "
                f"{second_region['region']} follows with {_format_currency(second_region['sales'])} ({second_region['marketShare']}%)."
            ),
            "chartIds": ["regional-sales"],
            "kpis": [
                {"label": top_region["region"], "value": _format_currency(top_region["sales"]), "trend": "neutral"},
                {"label": second_region["region"], "value": _format_currency(second_region["sales"]), "trend": "neutral"},
            ],
            "reviewPrompt": "Review regional performance",
        },
        {
            "id": "story-summary",
            "stepType": "summary",
            "title": "Next steps",
            "markdown": (
                f"Focus expansion on **{second_region['region']}** to balance reliance on {top_region['region']}."
                " Double down on **Home & Kitchen** momentum while fixing lagging products like"
                f" **{lagging_product['name']}**. The core demographic (ages {top_demo['ageGroup']}) remains the most valuable segment."
            ),
            "chartIds": ["customer-demographics"],
            "kpis": [
                {"label": top_demo["ageGroup"], "value": _format_currency(top_demo["spending"]), "trend": "up"},
            ],
            "reviewPrompt": "Highlight customer demographics",
        },
    ]

    return steps
