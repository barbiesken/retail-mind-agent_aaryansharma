"""
RetailMind Product Intelligence Agent — Tool Functions.

All 6 tool functions plus tool schemas for StyleCraft product catalog analytics.
Data is loaded at module level from CSVs using relative paths.
Uses OpenAI GPT-4o for AI-powered analysis.
"""

import os
import json
import pandas as pd
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Data Loading (module level, relative paths)
# ---------------------------------------------------------------------------
_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
products_df = pd.read_csv(os.path.join(_data_dir, "retailmind_products.csv"))
reviews_df = pd.read_csv(os.path.join(_data_dir, "retailmind_reviews.csv"))

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o"

# Cache for review insights to avoid repeat API calls
_review_insights_cache: dict = {}

# ---------------------------------------------------------------------------
# TOOL SCHEMAS (for documentation and LLM awareness)
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {
        "name": "search_products",
        "description": (
            "Search StyleCraft product catalog by name or keyword, "
            "with optional category filter. Returns top 5 matching products."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term for product name",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter",
                    "enum": ["Tops", "Dresses", "Bottoms", "Outerwear", "Accessories"],
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_inventory_health",
        "description": (
            "Check inventory health for a specific product. Returns stock levels, "
            "days to stockout, and status (Critical/Low/Healthy)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Product ID (e.g. SC001)",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "get_pricing_analysis",
        "description": (
            "Analyse pricing and margin health for a specific product. Returns "
            "gross margin, price positioning, and suggested actions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Product ID (e.g. SC001)",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "get_review_insights",
        "description": (
            "Get AI-powered customer review analysis for a product, including "
            "sentiment summary, positive themes, and negative themes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Product ID (e.g. SC001)",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "get_category_performance",
        "description": (
            "Get performance overview for an entire product category including "
            "ratings, margins, stock health, and top revenue products."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category name",
                    "enum": ["Tops", "Dresses", "Bottoms", "Outerwear", "Accessories"],
                },
            },
            "required": ["category"],
        },
    },
    {
        "name": "generate_restock_alert",
        "description": (
            "Generate urgent restock alerts for products at risk of stockout "
            "within a given number of days."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "threshold_days": {
                    "type": "integer",
                    "description": "Days threshold for stockout risk (default 7)",
                },
            },
            "required": [],
        },
    },
]


# ---------------------------------------------------------------------------
# TOOL 1: search_products
# ---------------------------------------------------------------------------
def search_products(query: str, category: str = None) -> list:
    """Search products by name/keyword with optional category filter.

    Returns top 5 matches as list of dicts.
    """
    df = products_df.copy()

    # Apply category filter first if provided
    if category:
        df = df[df["category"].str.lower() == category.lower()]

    # Case-insensitive search on product_name and category columns
    mask = (
        df["product_name"].str.contains(query, case=False, na=False)
        | df["category"].str.contains(query, case=False, na=False)
    )
    results = df[mask].head(5)

    if results.empty:
        return []

    return results[
        ["product_id", "product_name", "category", "price", "stock_quantity", "avg_rating"]
    ].to_dict(orient="records")


# ---------------------------------------------------------------------------
# TOOL 2: get_inventory_health
# ---------------------------------------------------------------------------
def get_inventory_health(product_id: str) -> dict:
    """Check inventory health for a single product."""
    product = products_df[products_df["product_id"] == product_id]

    if product.empty:
        return {"error": "Product not found"}

    row = product.iloc[0]
    avg_daily = row["avg_daily_sales"]

    # Handle zero daily sales
    if avg_daily == 0:
        days_to_stockout = 999
        status = "Healthy"
    else:
        days_to_stockout = round(row["stock_quantity"] / avg_daily, 1)
        if days_to_stockout < 7:
            status = "Critical"
        elif days_to_stockout <= 14:
            status = "Low"
        else:
            status = "Healthy"

    return {
        "product_id": row["product_id"],
        "product_name": row["product_name"],
        "stock_quantity": int(row["stock_quantity"]),
        "avg_daily_sales": float(avg_daily),
        "days_to_stockout": days_to_stockout,
        "status": status,
        "reorder_level": int(row["reorder_level"]),
    }


# ---------------------------------------------------------------------------
# TOOL 3: get_pricing_analysis
# ---------------------------------------------------------------------------
def get_pricing_analysis(product_id: str) -> dict:
    """Analyse pricing, margin, and positioning for a product."""
    product = products_df[products_df["product_id"] == product_id]

    if product.empty:
        return {"error": "Product not found"}

    row = product.iloc[0]
    price = float(row["price"])
    cost = float(row["cost"])

    gross_margin = round((price - cost) / price * 100, 2)

    # Category average price
    cat_products = products_df[products_df["category"] == row["category"]]
    category_avg_price = round(cat_products["price"].mean(), 2)

    # Price positioning
    if price > category_avg_price * 1.2:
        price_positioning = "Premium"
    elif price < category_avg_price * 0.8:
        price_positioning = "Budget"
    else:
        price_positioning = "Mid-Range"

    low_margin_flag = gross_margin < 20

    suggested_action = (
        "Review pricing or reduce COGS — margin below 20%"
        if low_margin_flag
        else "Margin healthy"
    )

    return {
        "product_id": row["product_id"],
        "product_name": row["product_name"],
        "price": price,
        "cost": cost,
        "gross_margin": gross_margin,
        "price_positioning": price_positioning,
        "category_avg_price": category_avg_price,
        "low_margin_flag": low_margin_flag,
        "suggested_action": suggested_action,
    }


# ---------------------------------------------------------------------------
# TOOL 4: get_review_insights
# ---------------------------------------------------------------------------
def get_review_insights(product_id: str) -> dict:
    """Get AI-powered review analysis for a product (cached)."""
    # Return cached result if available
    if product_id in _review_insights_cache:
        return _review_insights_cache[product_id]

    product = products_df[products_df["product_id"] == product_id]
    if product.empty:
        return {"error": "Product not found"}

    product_name = product.iloc[0]["product_name"]
    product_reviews = reviews_df[reviews_df["product_id"] == product_id]

    if product_reviews.empty:
        return {"error": "No reviews found for product"}

    avg_rating = round(product_reviews["rating"].mean(), 2)
    total_reviews = len(product_reviews)
    reviews_text = "\n".join(product_reviews["review_text"].tolist())

    try:
        # Review summarisation: temperature=0.3, max_tokens=300
        # Some creativity for natural summaries
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=300,
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a product analyst. Given customer reviews, provide:\n"
                        "1) A 2-sentence sentiment summary.\n"
                        "2) Top 2 positive themes.\n"
                        "3) Top 2 negative themes.\n"
                        "Be concise and data-driven.\n\n"
                        "Respond ONLY in this exact JSON format:\n"
                        '{"sentiment_summary": "...", '
                        '"positive_themes": ["...", "..."], '
                        '"negative_themes": ["...", "..."]}'
                    ),
                },
                {
                    "role": "user",
                    "content": f"Product: {product_name}\nReviews:\n{reviews_text}",
                },
            ],
        )

        llm_text = response.choices[0].message.content.strip()
        # Try to parse JSON from the response
        try:
            parsed = json.loads(llm_text)
        except json.JSONDecodeError:
            # Attempt to extract JSON from markdown code block
            if "```" in llm_text:
                json_str = llm_text.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                parsed = json.loads(json_str.strip())
            else:
                parsed = {
                    "sentiment_summary": llm_text,
                    "positive_themes": ["Unable to parse themes"],
                    "negative_themes": ["Unable to parse themes"],
                }

        result = {
            "product_id": product_id,
            "product_name": product_name,
            "avg_rating": avg_rating,
            "total_reviews": total_reviews,
            "sentiment_summary": parsed.get("sentiment_summary", ""),
            "positive_themes": parsed.get("positive_themes", [])[:2],
            "negative_themes": parsed.get("negative_themes", [])[:2],
        }

    except Exception as e:
        result = {
            "product_id": product_id,
            "product_name": product_name,
            "avg_rating": avg_rating,
            "total_reviews": total_reviews,
            "sentiment_summary": f"Error generating AI summary: {str(e)}",
            "positive_themes": ["N/A"],
            "negative_themes": ["N/A"],
        }

    # Cache the result
    _review_insights_cache[product_id] = result
    return result


# ---------------------------------------------------------------------------
# TOOL 5: get_category_performance
# ---------------------------------------------------------------------------
def get_category_performance(category: str) -> dict:
    """Get performance overview for an entire product category."""
    cat_df = products_df[products_df["category"].str.lower() == category.lower()]

    if cat_df.empty:
        return {"error": "Category not found"}

    # Compute days_to_stockout for stock health counts
    cat_df = cat_df.copy()
    cat_df["days_to_stockout"] = cat_df.apply(
        lambda r: r["stock_quantity"] / r["avg_daily_sales"]
        if r["avg_daily_sales"] > 0
        else 999,
        axis=1,
    )

    total_skus = len(cat_df)
    avg_rating = round(cat_df["avg_rating"].mean(), 2)
    avg_margin_pct = round(
        ((cat_df["price"] - cat_df["cost"]) / cat_df["price"] * 100).mean(), 2
    )
    total_stock_units = int(cat_df["stock_quantity"].sum())
    critical_stock_count = int((cat_df["days_to_stockout"] < 7).sum())
    low_stock_count = int(
        ((cat_df["days_to_stockout"] >= 7) & (cat_df["days_to_stockout"] <= 14)).sum()
    )

    # Top 3 by daily revenue
    cat_df["daily_revenue"] = cat_df["price"] * cat_df["avg_daily_sales"]
    top_3 = cat_df.nlargest(3, "daily_revenue")
    top_3_revenue_products = top_3[["product_id", "product_name", "daily_revenue"]].copy()
    top_3_revenue_products["daily_revenue"] = top_3_revenue_products["daily_revenue"].round(2)
    top_3_revenue_products = top_3_revenue_products.to_dict(orient="records")

    return {
        "category": category,
        "total_skus": total_skus,
        "avg_rating": avg_rating,
        "avg_margin_pct": avg_margin_pct,
        "total_stock_units": total_stock_units,
        "critical_stock_count": critical_stock_count,
        "low_stock_count": low_stock_count,
        "top_3_revenue_products": top_3_revenue_products,
    }


# ---------------------------------------------------------------------------
# TOOL 6: generate_restock_alert
# ---------------------------------------------------------------------------
def generate_restock_alert(threshold_days: int = 7) -> list:
    """Generate restock alerts for products at risk of stockout."""
    df = products_df.copy()

    # Only consider products with actual sales
    df = df[df["avg_daily_sales"] > 0].copy()

    df["days_to_stockout"] = (df["stock_quantity"] / df["avg_daily_sales"]).round(1)

    # Filter products at or below threshold
    at_risk = df[df["days_to_stockout"] <= threshold_days].copy()

    if at_risk.empty:
        return []

    # Revenue at risk = price × (stock_quantity + avg_daily_sales × threshold_days)
    at_risk["revenue_at_risk"] = (
        at_risk["price"] * (at_risk["stock_quantity"] + at_risk["avg_daily_sales"] * threshold_days)
    ).round(2)

    # Status flag
    at_risk["status"] = at_risk["days_to_stockout"].apply(
        lambda d: "Critical" if d < 7 else "Low"
    )

    # Sort ascending by days_to_stockout
    at_risk = at_risk.sort_values("days_to_stockout", ascending=True)

    return at_risk[
        [
            "product_id",
            "product_name",
            "category",
            "stock_quantity",
            "avg_daily_sales",
            "days_to_stockout",
            "revenue_at_risk",
            "status",
        ]
    ].to_dict(orient="records")
