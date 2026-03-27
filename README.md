# RetailMind — StyleCraft Product Intelligence Agent

RetailMind is an AI-powered product intelligence agent built for **StyleCraft**, a D2C fashion brand. It helps product managers make data-driven decisions about catalog management, inventory health, pricing strategy, and customer sentiment — all through a natural-language conversational interface.

The agent uses an **LLM-based router pattern** to classify user queries into five intents (Inventory, Pricing, Reviews, Catalog, General), extract relevant entities, dispatch to one of **six specialised analytical tools**, and format results into clear, actionable insights. On startup, it generates a **Daily Intelligence Briefing** highlighting critical stock alerts, the worst-rated product, and pricing flags that need attention.

---

## Architecture Overview

```
User Query → LLM Router (intent classification)
                → Entity Extractor (product ID / category)
                    → Tool Dispatch (6 tools)
                        → LLM Response Formatter
                            → Streamlit Chat UI
```

**Core Components:**
- **Router Agent** (`agent/router.py`) — LLM-powered query classifier + dispatcher
- **6 Tool Functions** (`agent/tools.py`) — search, inventory, pricing, reviews, category, restock
- **Daily Briefing** (`agent/briefing.py`) — auto-generated intelligence summary
- **Memory** (`agent/memory.py`) — sliding-window conversation history (10 messages)
- **Streamlit UI** (`app.py`) — chat interface with sidebar analytics dashboard

---

## Setup Instructions

```bash
git clone <repo>
cd retailmind-agent
pip install -r requirements.txt
cp .env.example .env
# Add your Anthropic API key to .env
python run.py
```

### `.env` Configuration

```env
ANTHROPIC_API_KEY=your_key_here
```

---

## Tool Descriptions

| # | Tool | Description |
|---|------|-------------|
| 1 | `search_products(query, category)` | Search catalog by name/keyword with optional category filter. Returns top 5 matches. |
| 2 | `get_inventory_health(product_id)` | Days-to-stockout calculation with Critical/Low/Healthy status flags. |
| 3 | `get_pricing_analysis(product_id)` | Gross margin, price positioning (Premium/Mid-Range/Budget), and COGS alerts. |
| 4 | `get_review_insights(product_id)` | AI-powered sentiment summary with positive/negative themes from customer reviews. |
| 5 | `get_category_performance(category)` | Category-level KPIs: SKU count, margins, stock health, top revenue products. |
| 6 | `generate_restock_alert(threshold)` | Finds all products at risk of stockout within N days, sorted by urgency. |

---

## Sample Queries

Test each intent with these example prompts:

### 🏷️ Catalog (CATALOG intent)
- "Show me all dresses"
- "What are the top sellers in Accessories?"
- "Search for cotton"

### 📦 Inventory (INVENTORY intent)
- "Which products are running low on stock?"
- "How many days of stock does SC015 have left?"
- "Check inventory for the Cashmere Beanie"

### 💰 Pricing (PRICING intent)
- "What's the margin on SC030?"
- "Is the Silk Blend Blouse priced competitively?"
- "Analyse pricing for the Leather Look Leggings"

### ⭐ Reviews (REVIEWS intent)
- "What do customers think about the Bodycon Mini Dress?"
- "Summarise reviews for SC019"
- "Any complaints about SC015?"

### 💬 General (GENERAL intent)
- "Hello!"
- "What can you help me with?"
- "What makes a good product pricing strategy?"

---

## Tech Stack

- **Python 3.10+**
- **Streamlit** — Chat UI & dashboard
- **Anthropic Claude** (claude-sonnet-4-20250514) — LLM backbone
- **Pandas / NumPy** — Data analysis
- **python-dotenv** — Environment configuration

---

## Data

- `data/retailmind_products.csv` — 30 StyleCraft SKUs across 5 categories
- `data/retailmind_reviews.csv` — 60 customer reviews with ratings and text

---

*Built with ❤️ for StyleCraft by RetailMind*
