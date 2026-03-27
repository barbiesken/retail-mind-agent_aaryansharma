"""
RetailMind Daily Briefing Generator.

Produces a formatted markdown briefing with critical stock alerts,
worst-rated product analysis, and pricing flags.
Uses OpenAI GPT-4o for AI-powered summaries.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

from agent.tools import products_df, reviews_df

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o"


def generate_daily_briefing() -> str:
    """Generate the daily intelligence briefing as formatted markdown.

    Sections:
        1. Top 3 Critical Stock Products
        2. Worst-Rated Product (with AI summary)
        3. Pricing Flag (lowest margin product)

    Returns:
        Formatted markdown string.
    """
    sections = []
    sections.append("# 📊 Daily Intelligence Briefing — StyleCraft\n")

    # ------------------------------------------------------------------
    # SECTION 1: Top 3 Critical Stock Products
    # ------------------------------------------------------------------
    df = products_df.copy()
    df_active = df[df["avg_daily_sales"] > 0].copy()
    df_active["days_to_stockout"] = (
        df_active["stock_quantity"] / df_active["avg_daily_sales"]
    ).round(1)
    df_active["revenue_at_risk"] = (
        df_active["price"] * df_active["stock_quantity"]
    ).round(2)

    top_critical = df_active.nsmallest(3, "days_to_stockout")

    section1 = "## 🚨 Critical Stock Alerts\n\n"
    section1 += "| Product | Days to Stockout | Revenue at Risk |\n"
    section1 += "|---------|:----------------:|:---------------:|\n"
    for _, row in top_critical.iterrows():
        days = row["days_to_stockout"]
        icon = "🔴" if days < 7 else "🟡"
        section1 += (
            f"| {icon} {row['product_name']} ({row['product_id']}) "
            f"| **{days}** days "
            f"| ₹{row['revenue_at_risk']:,.2f} |\n"
        )
    sections.append(section1)

    # ------------------------------------------------------------------
    # SECTION 2: Worst-Rated Product
    # ------------------------------------------------------------------
    worst = df.loc[df["avg_rating"].idxmin()]
    worst_id = worst["product_id"]
    worst_name = worst["product_name"]
    worst_rating = worst["avg_rating"]

    # Check for reviews
    worst_reviews = reviews_df[reviews_df["product_id"] == worst_id]

    try:
        if not worst_reviews.empty:
            reviews_text = "\n".join(worst_reviews["review_text"].tolist())
            prompt_msg = (
                f"Product: {worst_name} (rating: {worst_rating}/5)\n"
                f"Reviews:\n{reviews_text}\n\n"
                "In ONE sentence, summarise the main reason customers are dissatisfied."
            )
        else:
            prompt_msg = (
                f"Product: {worst_name} has a rating of {worst_rating}/5. "
                "In ONE sentence, infer why customers might be dissatisfied based on this low rating."
            )

        # Daily briefing: temperature=0.2, max_tokens=500
        # Factual but readable
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=500,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": "You are a retail product analyst. Be concise and data-driven.",
                },
                {"role": "user", "content": prompt_msg},
            ],
        )
        dissatisfaction_summary = response.choices[0].message.content.strip()
    except Exception as e:
        dissatisfaction_summary = f"Unable to generate summary: {e}"

    section2 = "## ⭐ Worst-Rated Product\n\n"
    section2 += f"**{worst_name}** ({worst_id}) — **{worst_rating}**/5 ⭐\n\n"
    section2 += f"> {dissatisfaction_summary}\n"
    sections.append(section2)

    # ------------------------------------------------------------------
    # SECTION 3: Pricing Flag
    # ------------------------------------------------------------------
    df["gross_margin"] = ((df["price"] - df["cost"]) / df["price"] * 100).round(2)
    lowest_margin = df.loc[df["gross_margin"].idxmin()]

    section3 = "## 💰 Pricing Flag\n\n"
    margin_val = lowest_margin["gross_margin"]

    if margin_val < 25:
        section3 += (
            f"⚠️ **{lowest_margin['product_name']}** ({lowest_margin['product_id']}) "
            f"has a margin of only **{margin_val}%**\n\n"
            f"**Suggested action:** Review pricing strategy or reduce COGS. "
            f"Current price: ₹{lowest_margin['price']:.2f} | Cost: ₹{lowest_margin['cost']:.2f}\n"
        )
    else:
        section3 += "✅ All products have margins above 25%. No pricing flags today.\n"

    sections.append(section3)

    # Footer
    sections.append("---\n*Ask me anything about inventory, pricing, reviews, or the catalog!*")

    return "\n".join(sections)
