"""Generate deterministic data story steps for the dashboard dataset."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

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


def _format_markdown_list(items: Sequence[str]) -> str:
    """Render a markdown bullet list from the provided text items."""

    return "\n".join(f"- {item}" for item in items if item).strip()


_STRATEGIC_AUDIO_LEADS = {
    "risks": (
        "On risks...",
        "Now, let’s shift gears and examine the risks that could impact our ability to execute...",
    ),
    "opportunities": (
        "Moving to opportunities...",
        "Now, on opportunities...",
    ),
    "recommendations": (
        "Here are my recommendations...",
        "My recommendations...",
    ),
}


def _select_audio_lead(section: str, bullet_index: int, total_bullets: int) -> str:
    """Return a human-style spoken lead-in for the first strategic bullet."""

    if bullet_index != 0:
        return ""

    options = _STRATEGIC_AUDIO_LEADS.get(section.lower())
    if not options:
        return ""

    if not total_bullets:
        return ""

    variant_index = min(total_bullets - 1, len(options) - 1)
    return options[variant_index]


def _build_strategic_talking_points(section: str, bullets: Sequence[str]) -> List[Dict[str, Any]]:
    """Construct talking points for a strategic section with optional audio leads."""

    non_empty_bullets = [bullet for bullet in bullets if bullet]
    total_bullets = len(non_empty_bullets)

    talking_points: List[Dict[str, Any]] = []
    for idx, bullet in enumerate(non_empty_bullets):
        entry: Dict[str, Any] = {
            "id": f"story-strategic-{section}-point-{idx + 1}",
            "markdown": bullet,
            "chartIds": ["strategic-commentary"],
        }
        lead = _select_audio_lead(section, idx, total_bullets)
        if lead:
            entry["audioLeadIn"] = lead
        talking_points.append(entry)

    return talking_points


_SECTION_HEADING_PATTERN = re.compile(
    r"^(?:#{1,6}\s*)?(risks|opportunities|recommendations)\s*:?$",
    re.IGNORECASE,
)


def _parse_strategic_commentary(markdown: str) -> Dict[str, Dict[str, List[str] | str]]:
    """Extract bullet text per strategic commentary section from markdown."""

    sections: Dict[str, Dict[str, List[str]]] = {
        "risks": {"raw_lines": []},
        "opportunities": {"raw_lines": []},
        "recommendations": {"raw_lines": []},
    }
    active_key: Optional[str] = None

    for raw_line in markdown.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue

        heading_match = _SECTION_HEADING_PATTERN.match(stripped)
        if heading_match:
            active_key = heading_match.group(1).lower()
            sections[active_key]["bullets"] = []
            continue

        if active_key is None:
            continue

        section_data = sections[active_key]
        section_data.setdefault("bullets", [])
        section_data["raw_lines"].append(stripped)
        if stripped[0] in {"-", "*"}:
            bullet_text = stripped.lstrip("-* ").strip()
            if bullet_text:
                section_data["bullets"].append(bullet_text)

    parsed: Dict[str, Dict[str, List[str] | str]] = {}
    for key, data in sections.items():
        raw_lines = [line for line in data.get("raw_lines", []) if line.strip()]
        bullets = [bullet for bullet in data.get("bullets", []) if bullet]
        if not bullets and raw_lines:
            bullets = [line.lstrip("-* ").strip() for line in raw_lines if line.strip()]
        markdown_block = "\n".join(raw_lines).strip()
        if not markdown_block and bullets:
            markdown_block = _format_markdown_list(bullets)
        parsed[key] = {"markdown": markdown_block, "bullets": bullets}

    return parsed


def _resolve_commentary_section(
    parsed_section: Optional[Dict[str, List[str] | str]],
    default_points: Sequence[str],
) -> Tuple[List[str], str]:
    """Return talking points and markdown for a strategic section."""

    points = [point for point in default_points if point]
    markdown = _format_markdown_list(points)

    if not parsed_section:
        return points, markdown

    parsed_points = [
        str(item).strip()
        for item in (parsed_section.get("bullets") or [])
        if str(item).strip()
    ]
    parsed_markdown = str(parsed_section.get("markdown", "")).strip()

    if parsed_points or parsed_markdown:
        if not parsed_points and parsed_markdown:
            parsed_points = [
                line.lstrip("-* ").strip()
                for line in parsed_markdown.splitlines()
                if line.strip()
            ]
        if parsed_points:
            points = parsed_points
        if parsed_markdown:
            markdown = parsed_markdown
        else:
            markdown = _format_markdown_list(points)

    return points, markdown


def generate_data_story_steps(strategic_commentary: Optional[str] = None) -> List[Dict[str, Any]]:
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
    profit_delta = latest_month["Profit"] - previous_month["Profit"]
    expense_delta = latest_month["Expenses"] - previous_month["Expenses"]

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

    default_risk_points: List[str] = [
        (
            f"Revenue remains concentrated in **{top_region['region']}** at {top_region['marketShare']}% share "
            f"while {second_region['region']} trails at {second_region['marketShare']}%, keeping exposure skewed."
        )
    ]
    if primary_declining and secondary_declining:
        default_risk_points.append(
            f"Core products like **{primary_declining['name']}** ({primary_declining['growth']:.1f}%) and "
            f"**{secondary_declining['name']}** ({secondary_declining['growth']:.1f}%) are contracting, signaling churn risk."
        )
    elif primary_declining:
        default_risk_points.append(
            f"**{primary_declining['name']}** is contracting at {primary_declining['growth']:.1f}%, hinting at lifecycle or retention pressure."
        )
    if declining_category:
        default_risk_points.append(
            f"The **{declining_category['name']}** category shrank {declining_category['growth']:.1f}% while electronics already represent "
            f"{leading_category['value']}% of revenue, limiting diversification."
        )

    default_opportunity_points: List[str] = [
        (
            f"**{fastest_category['name']}** is growing {fastest_category['growth']:.1f}% on"
            f" {fastest_category['value']}% of revenue; bundle with electronics to lift basket size."
        ),
        (
            f"**{expansion_region['region']}** delivered {_format_currency(expansion_region['sales'])}"
            f" at {expansion_region['marketShare']}% share, leaving headroom for targeted expansion."
        ),
        (
            f"The **{dominant_age_group['ageGroup']}** cohort already represents"
            f" {dominant_age_group['percentage']}% of customers; loyalty offers can upsell wearables and subscriptions."
        ),
    ]

    default_recommendation_points: List[str] = [
        (
            f"Launch retention plays around **{lagging_product['name']}** ({lagging_product['growth']:.1f}%)"
            + (
                f" and **{secondary_declining['name']}** ({secondary_declining['growth']:.1f}%)"
                if secondary_declining
                else ""
            )
            + " to stabilise core hardware revenue."
        ),
        (
            f"Rebalance go-to-market spend toward **{second_region['region']}** and"
            f" **{expansion_region['region']}** to ease reliance on {top_region['region']} ({top_region['marketShare']}% share)."
        ),
        (
            f"Use {_format_currency(top_product['sales'])} momentum from **{top_product['name']}** and"
            f" {metrics['profitMargin']} margins to fund campaigns that grow emerging segments."
        ),
    ]

    parsed_commentary: Dict[str, Dict[str, List[str] | str]] = {}
    if strategic_commentary:
        parsed_commentary = _parse_strategic_commentary(strategic_commentary)

    risk_points, strategic_risk_markdown = _resolve_commentary_section(
        parsed_commentary.get("risks"),
        default_risk_points,
    )
    opportunity_points, strategic_opportunity_markdown = _resolve_commentary_section(
        parsed_commentary.get("opportunities"),
        default_opportunity_points,
    )
    recommendation_points, strategic_recommendation_markdown = _resolve_commentary_section(
        parsed_commentary.get("recommendations"),
        default_recommendation_points,
    )

    overview_points = [
        {
            "id": "story-overview-sales",
            "markdown": (
                f"Monthly **sales** hit {_format_currency(latest_month['Sales'])} in {latest_month['date']},"
                f" {('up' if revenue_delta >= 0 else 'down')} {_format_currency(abs(revenue_delta))} versus {previous_month['date']}."
            ),
            "chartIds": ["sales-overview"],
            "chartFocus": [
                {
                    "chartId": "sales-overview",
                    "seriesName": "Sales",
                    "dataName": latest_month["date"],
                }
            ],
        },
        {
            "id": "story-overview-profit",
            "markdown": (
                f"Operating **profit** reached {_format_currency(latest_month['Profit'])},"
                f" {('up' if profit_delta >= 0 else 'down')} {_format_currency(abs(profit_delta))} from {previous_month['date']}."
            ),
            "chartIds": ["sales-overview"],
            "chartFocus": [
                {
                    "chartId": "sales-overview",
                    "seriesName": "Profit",
                    "dataName": latest_month["date"],
                }
            ],
        },
        {
            "id": "story-overview-expenses",
            "markdown": (
                f"Monthly **expenses** landed at {_format_currency(latest_month['Expenses'])},"
                f" {('up' if expense_delta >= 0 else 'down')} {_format_currency(abs(expense_delta))} versus {previous_month['date']}."
            ),
            "chartIds": ["sales-overview"],
            "chartFocus": [
                {
                    "chartId": "sales-overview",
                    "seriesName": "Expenses",
                    "dataName": latest_month["date"],
                }
            ],
        },
    ]

    product_points = [
        {
            "id": "story-products-smartphone",
            "markdown": (
                f"**{top_product['name']}** leads with {_format_currency(top_product['sales'])} in sales "
                f"and {top_product['growth']:.1f}% growth."
            ),
            "chartIds": ["product-performance"],
            "chartFocus": [
                {
                    "chartId": "product-performance",
                    "dataName": top_product["name"],
                }
            ],
        },
        {
            "id": "story-products-laggard",
            "markdown": (
                f"**{lagging_product['name']}** is slipping with {lagging_product['growth']:.1f}% growth on "
                f"{_format_currency(lagging_product['sales'])} in sales."
            ),
            "chartIds": ["product-performance"],
            "chartFocus": [
                {
                    "chartId": "product-performance",
                    "dataName": lagging_product["name"],
                }
            ],
        },
    ]

    category_points = [
        {
            "id": "story-categories-electronics",
            "markdown": (
                f"Electronics accounts for {leading_category['value']}% of revenue and is still growing {leading_category['growth']:.1f}%."
            ),
            "chartIds": ["sales-by-category"],
            "chartFocus": [
                {
                    "chartId": "sales-by-category",
                    "dataName": leading_category["name"],
                }
            ],
        },
        {
            "id": "story-categories-home",
            "markdown": (
                f"Home & Kitchen contributes {category_data[2]['value']}% and is expanding {_format_percentage(category_data[2]['growth'])}."
            ),
            "chartIds": ["sales-by-category"],
            "chartFocus": [
                {
                    "chartId": "sales-by-category",
                    "dataName": category_data[2]["name"],
                }
            ],
        },
    ]

    regional_points = [
        {
            "id": "story-regions-leader",
            "markdown": (
                f"{top_region['region']} leads revenue with {_format_currency(top_region['sales'])} and {top_region['marketShare']}% share."
            ),
            "chartIds": ["regional-sales"],
            "chartFocus": [
                {
                    "chartId": "regional-sales",
                    "dataName": top_region["region"],
                }
            ],
        },
        {
            "id": "story-regions-expansion",
            "markdown": (
                f"{expansion_region['region']} remains a growth lever at {_format_currency(expansion_region['sales'])} and {expansion_region['marketShare']}% share."
            ),
            "chartIds": ["regional-sales"],
            "chartFocus": [
                {
                    "chartId": "regional-sales",
                    "dataName": expansion_region["region"],
                }
            ],
        },
    ]

    demographics_points = [
        {
            "id": "story-demographics-top",
            "markdown": (
                f"Age {top_demo['ageGroup']} shoppers now spend {_format_currency(top_demo['spending'])}, "
                f"leading cohort revenue."
            ),
            "chartIds": ["customer-demographics"],
            "chartFocus": [
                {
                    "chartId": "customer-demographics",
                    "dataName": top_demo["ageGroup"],
                }
            ],
        },
        {
            "id": "story-demographics-dominant",
            "markdown": (
                f"Ages {dominant_age_group['ageGroup']} make up {dominant_age_group['percentage']}% of customers,"
                " anchoring engagement."
            ),
            "chartIds": ["customer-demographics"],
            "chartFocus": [
                {
                    "chartId": "customer-demographics",
                    "dataName": dominant_age_group["ageGroup"],
                }
            ],
        },
        {
            "id": "story-demographics-tail",
            "markdown": (
                f"Smaller cohorts like ages {demographics_data[-1]['ageGroup']} still contribute"
                f" {_format_currency(demographics_data[-1]['spending'])}, highlighting an upsell path."
            ),
            "chartIds": ["customer-demographics"],
            "chartFocus": [
                {
                    "chartId": "customer-demographics",
                    "dataName": demographics_data[-1]["ageGroup"],
                }
            ],
        },
    ]

    steps: List[Dict[str, Any]] = [
        {
            "id": "story-overview",
            "stepType": "overview",
            "title": "Overall performance remains strong",
            "markdown": "\n\n".join(point["markdown"] for point in overview_points),
            "chartIds": ["sales-overview"],
            "talkingPoints": overview_points,
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
            "markdown": "\n\n".join(point["markdown"] for point in product_points),
            "chartIds": ["product-performance"],
            "talkingPoints": product_points,
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
            "markdown": "\n\n".join(point["markdown"] for point in category_points),
            "chartIds": ["sales-by-category"],
            "talkingPoints": category_points,
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
            "markdown": "\n\n".join(point["markdown"] for point in regional_points),
            "chartIds": ["regional-sales"],
            "talkingPoints": regional_points,
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
            "markdown": "\n\n".join(point["markdown"] for point in demographics_points),
            "chartIds": ["customer-demographics"],
            "talkingPoints": demographics_points,
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
            "talkingPoints": _build_strategic_talking_points("risks", risk_points),
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
            "talkingPoints": _build_strategic_talking_points("opportunities", opportunity_points),
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
            "talkingPoints": _build_strategic_talking_points("recommendations", recommendation_points),
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
