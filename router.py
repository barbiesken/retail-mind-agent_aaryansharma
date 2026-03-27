"""
RetailMind Router Agent — LLM-powered query classification and dispatch.

Uses OpenAI GPT-4o for intent classification and entity extraction.
Routes queries to the appropriate tool functions and formats responses.
"""

import os
import json
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

from agent import tools, memory

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o"

# ---------------------------------------------------------------------------
# System Prompts
# ---------------------------------------------------------------------------
ROUTER_SYSTEM_PROMPT = """You are a query classifier for a retail analytics AI agent.
Classify the user's query into exactly one of these intents:

INVENTORY: questions about stock levels, stockout risk, restock needs, how long inventory will last, which products are running low
PRICING: questions about margins, profitability, pricing tiers, cost efficiency, price comparisons
REVIEWS: questions about customer feedback, ratings, complaints, sentiment, what customers think
CATALOG: questions about product search, category overviews, top performers, browsing the catalog, product discovery
GENERAL: greetings, meta questions about the agent, general retail knowledge not in the data

Respond with ONLY the intent word. Nothing else."""

ENTITY_EXTRACTION_PROMPT = """You are an entity extractor. From the user query, extract:

product_id: any product code like SC001, SC002... SC030 (or null)
product_name_hint: any product name mentioned (or null)
category: one of Tops/Dresses/Bottoms/Outerwear/Accessories (or null)
Respond ONLY as JSON: {"product_id": null, "product_name_hint": null, "category": null}"""

RESPONSE_SYSTEM_PROMPT = """You are RetailMind's Product Intelligence Agent for StyleCraft, a D2C fashion brand. You help product manager Priya Mehta make data-driven decisions about the catalog.
Your personality: professional, concise, action-oriented. You surface insights, not just data.
When presenting tool results:
- Use markdown tables for product comparisons
- Use bullet points for lists of issues
- Bold critical numbers (stockout days, low margins)
- Always end inventory/pricing responses with a 1-line recommended action
- Use emojis sparingly for visual clarity: 🚨 critical, ⚠️ warning, ✅ healthy

You have access to real-time data from StyleCraft's catalog. Never fabricate numbers — always use the tool results provided.
If the category filter is set (not "All Categories"), scope your response to that category when relevant."""


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------
def _classify_intent(user_query: str) -> str:
    """Classify user query into one of 5 intents using LLM."""
    try:
        # Router classification: temperature=0.0, max_tokens=10
        # Deterministic — must pick exactly one intent
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=10,
            temperature=0.0,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_query},
            ],
        )
        intent = response.choices[0].message.content.strip().upper()

        valid_intents = {"INVENTORY", "PRICING", "REVIEWS", "CATALOG", "GENERAL"}
        if intent not in valid_intents:
            return "GENERAL"
        return intent

    except Exception as e:
        print(f"[Router] Classification error: {e}")
        return "GENERAL"


def _extract_entities(user_query: str) -> dict:
    """Extract product_id, product_name_hint, and category from user query."""
    try:
        # Entity extraction: temperature=0.0, max_tokens=100
        # JSON only, no creativity needed
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=100,
            temperature=0.0,
            messages=[
                {"role": "system", "content": ENTITY_EXTRACTION_PROMPT},
                {"role": "user", "content": user_query},
            ],
        )
        text = response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            entities = json.loads(text)
        except json.JSONDecodeError:
            # Try extracting JSON from markdown code block
            if "```" in text:
                json_str = text.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                entities = json.loads(json_str.strip())
            else:
                entities = {"product_id": None, "product_name_hint": None, "category": None}

        return entities

    except Exception as e:
        print(f"[Router] Entity extraction error: {e}")
        return {"product_id": None, "product_name_hint": None, "category": None}


def _resolve_product_id(entities: dict) -> Optional[str]:
    """Resolve a product_id from entities, searching by name if needed."""
    product_id = entities.get("product_id")
    if product_id:
        return product_id

    # If we have a name hint but no ID, search for it
    name_hint = entities.get("product_name_hint")
    if name_hint:
        results = tools.search_products(name_hint)
        if results:
            return results[0]["product_id"]

    return None


def _format_response(intent: str, tool_result, user_query: str,
                     category_filter: str = "All Categories") -> str:
    """Use LLM to format tool results into a user-friendly response."""
    try:
        category_context = ""
        if category_filter and category_filter != "All Categories":
            category_context = f"\nActive category filter: {category_filter}"

        # Response generation: temperature=0.3, max_tokens=800
        # Clear, actionable formatting
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=800,
            temperature=0.3,
            messages=[
                {"role": "system", "content": RESPONSE_SYSTEM_PROMPT + category_context},
                {
                    "role": "user",
                    "content": (
                        f"User query: {user_query}\n\n"
                        f"Intent: {intent}\n\n"
                        f"Tool results:\n{json.dumps(tool_result, indent=2, default=str)}\n\n"
                        "Format this data into a clear, actionable response for the user. "
                        "Use markdown formatting."
                    ),
                },
            ],
        )
        return response.choices[0].message.content

    except Exception as e:
        # Fallback: return raw result as formatted string
        return (
            f"**Results:**\n```json\n{json.dumps(tool_result, indent=2, default=str)}\n```"
            f"\n\n_Error formatting response: {e}_"
        )


def _handle_general(user_query: str, conversation_history: list) -> str:
    """Handle GENERAL intent with conversation context."""
    try:
        messages = [{"role": "system", "content": RESPONSE_SYSTEM_PROMPT}]
        # Include conversation history for context-aware replies
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_query})

        # General responses: temperature=0.5, max_tokens=600
        # Conversational but grounded
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=600,
            temperature=0.5,
            messages=messages,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"I'm sorry, I encountered an error: {str(e)}. Please try again."


# ---------------------------------------------------------------------------
# Main Router Function
# ---------------------------------------------------------------------------
def route_query(user_query: str, conversation_history: list,
                category_filter: str = "All") -> str:
    """Route user query to the appropriate tool and return formatted response.

    Args:
        user_query: The user's natural language question.
        conversation_history: List of previous messages for context.
        category_filter: Active category filter from sidebar.

    Returns:
        Formatted markdown string response to display to user.
    """
    # Step 1: Classify intent
    intent = _classify_intent(user_query)

    # Step 2: Handle GENERAL intent directly (no tool needed)
    if intent == "GENERAL":
        return _handle_general(user_query, conversation_history)

    # Step 3: Extract entities
    entities = _extract_entities(user_query)

    # Step 4: Dispatch to appropriate tool(s) based on intent
    try:
        if intent == "INVENTORY":
            product_id = _resolve_product_id(entities)
            if product_id:
                result = tools.get_inventory_health(product_id)
                if "error" in result:
                    return (
                        f"I couldn't find product **{product_id}** in the catalog. "
                        "Try searching by product name instead."
                    )
            else:
                # No specific product — generate overall restock alert
                result = tools.generate_restock_alert()
                if not result:
                    return "✅ Great news! No products are at critical stock levels right now."

        elif intent == "PRICING":
            product_id = _resolve_product_id(entities)
            if not product_id:
                return (
                    "I need a specific product to analyse pricing. "
                    "Try asking about a product by name or ID (e.g., SC001)."
                )
            result = tools.get_pricing_analysis(product_id)
            if "error" in result:
                return (
                    f"I couldn't find product **{product_id}** in the catalog. "
                    "Try searching by product name instead."
                )

        elif intent == "REVIEWS":
            product_id = _resolve_product_id(entities)
            if not product_id:
                return (
                    "I need a specific product to analyse reviews. "
                    "Try asking about a product by name or ID (e.g., SC001)."
                )
            result = tools.get_review_insights(product_id)
            if "error" in result:
                return (
                    f"I couldn't find reviews for product **{product_id}**. "
                    "The product may not have any customer reviews yet."
                )

        elif intent == "CATALOG":
            category = entities.get("category")
            name_hint = entities.get("product_name_hint")

            # Apply sidebar filter if no explicit category in query
            if not category and category_filter and category_filter not in ("All", "All Categories"):
                category = category_filter

            if category:
                result = tools.get_category_performance(category)
                if "error" in result:
                    return (
                        f"Category **{category}** not found. "
                        "Available: Tops, Dresses, Bottoms, Outerwear, Accessories."
                    )
            elif name_hint:
                result = tools.search_products(name_hint)
                if not result:
                    return f"No products found matching **{name_hint}**. Try a different search term."
            else:
                # Default: search with whatever the user asked
                result = tools.search_products(user_query)
                if not result:
                    return "I couldn't find matching products. Try being more specific or ask about a category."

        else:
            return _handle_general(user_query, conversation_history)

        # Step 5: Format the response using LLM
        return _format_response(intent, result, user_query, category_filter)

    except Exception as e:
        return f"I encountered an error processing your request: {str(e)}. Please try again."
