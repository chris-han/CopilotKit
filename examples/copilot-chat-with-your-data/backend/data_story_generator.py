"""Generate deterministic data story steps for the dashboard dataset."""

from __future__ import annotations

from typing import Any, Dict, List

from dashboard_data import DASHBOARD_CONTEXT


def _to_number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace("%", "").replace(",", "")
        try:
            return float(cleaned)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError(f"Cannot parse numeric value from '{value}'") from exc
    raise TypeError(f"Unsupported value type for numeric conversion: {type(value)!r}")


def _format_currency(value: Any, decimals: int = 0) -> str:
    number = _to_number(value)
    return f"${number:,.{decimals}f}"


def _format_percentage(value: Any, decimals: int = 1) -> str:
    number = _to_number(value)
    return f"{number:.{decimals}f}%"


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
    product_table_lines = [
        "| Product | Sales | Growth (%) | Units Sold |",
        "|---------|-------|------------|------------|",
        *(
            f"| {entry['name']} | {_format_currency(entry['sales'])} | {entry['growth']:.1f}% | {entry['units']} |"
            for entry in product_data
        ),
    ]

    sorted_regions = sorted(regional_data, key=lambda item: item["sales"], reverse=True)
    top_region = sorted_regions[0]
    second_region = sorted_regions[1] if len(sorted_regions) > 1 else sorted_regions[0]
    expansion_region = sorted_regions[2] if len(sorted_regions) > 2 else sorted_regions[-1]
    top_demo = max(demographics_data, key=lambda item: item["spending"])
    demographics_table_lines = [
        "| Age Group | Percentage (%) | Spending ($) |",
        "|-----------|----------------|--------------|",
        *(
            f"| {entry['ageGroup']} | {entry['percentage']}% | {_format_currency(entry['spending'])} |"
            for entry in demographics_data
        ),
    ]

    declining_products = sorted(
        (entry for entry in product_data if entry.get("growth", 0) < 0),
        key=lambda item: item["growth"],
    )
    primary_declining = declining_products[0] if declining_products else None
    secondary_declining = declining_products[1] if len(declining_products) > 1 else None
    declining_category = next((entry for entry in category_data if entry.get("growth", 0) < 0), None)
    fastest_category = max(category_data, key=lambda item: item["growth"])
    dominant_age_group = max(demographics_data, key=lambda item: item["percentage"])

    def _strategic_tab_event(tab: str) -> List[Dict[str, Any]]:
        return [
            {
                "name": "chart.highlight",
                "value": {
                    "chartId": "strategic-commentary",
                    "tab": tab,
                },
            }
        ]

    strategic_risk_bullets: List[str] = [
        (
            f"- Revenue remains concentrated in **{top_region['region']}** at {top_region['marketShare']}% share "
            f"while {second_region['region']} trails at {second_region['marketShare']}%, keeping exposure skewed."
        )
    ]
    if primary_declining and secondary_declining:
        strategic_risk_bullets.append(
            f"- Core products like **{primary_declining['name']}** ({primary_declining['growth']:.1f}%) and "
            f"**{secondary_declining['name']}** ({secondary_declining['growth']:.1f}%) are contracting, signaling churn risk."
        )
    elif primary_declining:
        strategic_risk_bullets.append(
            f"- **{primary_declining['name']}** is contracting at {primary_declining['growth']:.1f}%, hinting at lifecycle or retention pressure."
        )
    if declining_category:
        strategic_risk_bullets.append(
            f"- The **{declining_category['name']}** category shrank {declining_category['growth']:.1f}% while electronics already represent "
            f"{leading_category['value']}% of revenue, limiting diversification."
        )
    strategic_risk_markdown = "\n".join(bullet for bullet in strategic_risk_bullets if bullet).strip()

    strategic_opportunity_markdown = "\n".join(
        [
            (
                f"- **{fastest_category['name']}** is growing {fastest_category['growth']:.1f}% on"
                f" {fastest_category['value']}% of revenue; bundle with electronics to lift basket size."
            ),
            (
                f"- **{expansion_region['region']}** delivered {_format_currency(expansion_region['sales'])}"
                f" at {expansion_region['marketShare']}% share, leaving headroom for targeted expansion."
            ),
            (
                f"- The **{dominant_age_group['ageGroup']}** cohort already represents"
                f" {dominant_age_group['percentage']}% of customers; loyalty offers can upsell wearables and subscriptions."
            ),
        ]
    )

    strategic_recommendation_markdown = "\n".join(
        [
            (
                f"- Launch retention plays around **{lagging_product['name']}** ({lagging_product['growth']:.1f}%)"
                + (
                    f" and **{secondary_declining['name']}** ({secondary_declining['growth']:.1f}%)"
                    if secondary_declining
                    else ""
                )
                + " to stabilise core hardware revenue."
            ),
            (
                f"- Rebalance go-to-market spend toward **{second_region['region']}** and"
                f" **{expansion_region['region']}** to ease reliance on {top_region['region']} ({top_region['marketShare']}% share)."
            ),
            (
                f"- Use {_format_currency(top_product['sales'])} momentum from **{top_product['name']}** and"
                f" {metrics['profitMargin']} margins to fund campaigns that grow emerging segments."
            ),
        ]
    )

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
                "\n\nProduct Performance:\n\n"
                + "\n".join(product_table_lines)
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
            "id": "story-demographics",
            "stepType": "change",
            "title": "Customer demographics keep spending concentrated",
            "markdown": (
                f"The highest-spending segment remains **ages {top_demo['ageGroup']}**, generating {_format_currency(top_demo['spending'])}."
                " Engagement from other age groups is steadier but smaller, suggesting room for targeted campaigns."
                "\n\nCustomer Demographics:\n\n"
                + "\n".join(demographics_table_lines)
            ),
            "chartIds": ["customer-demographics"],
            "kpis": [
                {"label": top_demo["ageGroup"], "value": _format_currency(top_demo["spending"]), "trend": "up"},
                {"label": "Conversion Rate", "value": _format_percentage(metrics["conversionRate"]), "trend": "neutral"},
            ],
            "reviewPrompt": "Review customer demographics",
        },
        {
            "id": "story-strategic-risks",
            "stepType": "summary",
            "title": "Strategic commentary – risks",
            "markdown": strategic_risk_markdown,
            "chartIds": ["strategic-commentary"],
            "agUiEvents": _strategic_tab_event("risks"),
            "kpis": [
                {"label": "North America Share", "value": f"{top_region['marketShare']}%", "trend": "neutral"},
                {
                    "label": f"{lagging_product['name']} Growth",
                    "value": f"{lagging_product['growth']:.1f}%",
                    "trend": "down",
                },
            ]
            + (
                [
                    {
                        "label": f"{secondary_declining['name']} Growth",
                        "value": f"{secondary_declining['growth']:.1f}%",
                        "trend": "down",
                    }
                ]
                if secondary_declining
                else []
            ),
            "reviewPrompt": "Review strategic risks",
        },
        {
            "id": "story-strategic-opportunities",
            "stepType": "summary",
            "title": "Strategic commentary – opportunities",
            "markdown": strategic_opportunity_markdown,
            "chartIds": ["strategic-commentary"],
            "agUiEvents": _strategic_tab_event("opportunities"),
            "kpis": [
                {
                    "label": f"{fastest_category['name']} Growth",
                    "value": f"{fastest_category['growth']:.1f}%",
                    "trend": "up",
                },
                {
                    "label": f"{top_product['name']} Sales",
                    "value": _format_currency(top_product['sales']),
                    "trend": "up",
                },
                {
                    "label": f"{expansion_region['region']} Share",
                    "value": f"{expansion_region['marketShare']}%",
                    "trend": "up",
                },
            ],
            "reviewPrompt": "Review strategic opportunities",
        },
        {
            "id": "story-strategic-recommendations",
            "stepType": "summary",
            "title": "Strategic commentary – recommendations",
            "markdown": strategic_recommendation_markdown,
            "chartIds": ["strategic-commentary"],
            "agUiEvents": _strategic_tab_event("recommendations"),
            "kpis": [
                {"label": "Profit Margin", "value": metrics["profitMargin"], "trend": "up"},
                {
                    "label": "Avg Order Value",
                    "value": _format_currency(metrics["averageOrderValue"], decimals=2),
                    "trend": "neutral",
                },
            ],
            "reviewPrompt": "Review strategic recommendations",
        },
    ]

    return steps
