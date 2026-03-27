"""
RetailMind – StyleCraft Product Intelligence Agent

Premium Streamlit application with glassmorphism design, animated elements,
quick-action buttons, and a polished conversational chat interface.
"""

import streamlit as st
from agent import tools, memory, router
from agent.briefing import generate_daily_briefing
from agent.tools import products_df

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="RetailMind – StyleCraft Intelligence",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Premium CSS — Glassmorphism, Animations, Typography
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global — Force Inter everywhere ──────────────────────── */
    html, body, [class*="css"],
    .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2,
    .stMarkdown h3, .stMarkdown h4, .stMarkdown li, .stMarkdown td,
    .stMarkdown th, .stMarkdown blockquote, .stChatMessage,
    [data-testid="stChatMessageContent"] * {
        font-family: 'Inter', sans-serif !important;
    }
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 40%, #24243e 100%);
    }
    .main .block-container {
        padding-top: 2rem;
        max-width: 1100px;
    }

    /* ── MAIN AREA — Force light text on dark background ──────── */
    .main .stMarkdown h1, .main .stMarkdown h2, .main .stMarkdown h3,
    .main .stMarkdown h4, .main .stMarkdown h5, .main .stMarkdown h6 {
        color: #f1f5f9 !important;
    }
    .main .stMarkdown p, .main .stMarkdown li, .main .stMarkdown td,
    .main .stMarkdown th, .main .stMarkdown span {
        color: #e2e8f0 !important;
    }
    .main .stMarkdown blockquote, .main .stMarkdown blockquote p {
        color: #cbd5e1 !important;
        border-left-color: rgba(99,102,241,0.5) !important;
    }
    .main .stMarkdown strong, .main .stMarkdown b {
        color: #ffffff !important;
    }
    .main .stMarkdown a {
        color: #818cf8 !important;
    }
    .main .stMarkdown table {
        border-collapse: collapse;
    }
    .main .stMarkdown table th {
        background: rgba(99,102,241,0.15) !important;
        color: #c7d2fe !important;
        font-weight: 600 !important;
    }
    .main .stMarkdown table td, .main .stMarkdown table th {
        border-color: rgba(255,255,255,0.1) !important;
        padding: 8px 12px !important;
    }
    .main .stMarkdown table tr:hover td {
        background: rgba(255,255,255,0.03) !important;
    }
    .main .stMarkdown hr {
        border-color: rgba(255,255,255,0.1) !important;
    }
    .main .stMarkdown em {
        color: #94a3b8 !important;
    }

    /* ── Chat message content — ensure readability ─────────────── */
    [data-testid="stChatMessageContent"] h1,
    [data-testid="stChatMessageContent"] h2,
    [data-testid="stChatMessageContent"] h3 {
        color: #f1f5f9 !important;
    }
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] li,
    [data-testid="stChatMessageContent"] td,
    [data-testid="stChatMessageContent"] th {
        color: #e2e8f0 !important;
    }
    [data-testid="stChatMessageContent"] strong {
        color: #ffffff !important;
    }
    [data-testid="stChatMessageContent"] blockquote,
    [data-testid="stChatMessageContent"] blockquote p {
        color: #cbd5e1 !important;
    }

    /* ── Sidebar ──────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0b1f 0%, #141233 50%, #1c1a3a 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e2e8f0;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: #94a3b8;
    }

    /* ── Hero Header ──────────────────────────────────────────── */
    .hero-container {
        background: linear-gradient(135deg, rgba(99,102,241,0.12) 0%, rgba(139,92,246,0.08) 100%);
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 20px;
        padding: 28px 32px 22px 32px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-title {
        font-family: 'Inter', sans-serif !important;
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #818cf8 0%, #a78bfa 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 4px 0;
        position: relative;
        z-index: 1;
    }
    .hero-subtitle {
        font-family: 'Inter', sans-serif !important;
        color: #94a3b8;
        font-size: 0.95rem;
        font-weight: 400;
        margin: 0;
        position: relative;
        z-index: 1;
    }
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        font-size: 0.65rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-left: 10px;
        vertical-align: middle;
        position: relative;
        z-index: 1;
    }

    /* ── Quick Actions ────────────────────────────────────────── */
    .stButton > button {
        border-radius: 12px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.82rem !important;
        padding: 6px 16px !important;
        transition: all 0.25s ease !important;
        letter-spacing: 0.3px;
    }

    /* ── Chat Messages ────────────────────────────────────────── */
    .stChatMessage {
        border-radius: 16px;
        margin-bottom: 6px;
        animation: slideIn 0.3s ease-out;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ── Chat Input ───────────────────────────────────────────── */
    .stChatInput > div {
        border-radius: 16px !important;
    }

    /* ── Sidebar Stat Card ─────────────────────────────────────── */
    .stat-card {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 12px 16px;
        margin-bottom: 8px;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .stat-card:hover {
        background: rgba(255, 255, 255, 0.07);
        border-color: rgba(99,102,241,0.3);
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(99,102,241,0.12);
    }
    .stat-label {
        color: #94a3b8;
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .stat-value {
        color: #f1f5f9;
        font-size: 1.3rem;
        font-weight: 700;
    }
    .stat-value.critical {
        color: #f87171;
    }
    .stat-value.healthy {
        color: #4ade80;
    }

    /* ── Sidebar Divider ──────────────────────────────────────── */
    .sidebar-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99,102,241,0.3), transparent);
        margin: 16px 0;
    }

    /* ── Status Dot ───────────────────────────────────────────── */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 2s infinite;
    }
    .status-dot.green {
        background: #22c55e;
        box-shadow: 0 0 8px rgba(34,197,94,0.5);
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* ── Sidebar Footer ───────────────────────────────────────── */
    .sidebar-footer {
        text-align: center;
        color: #475569;
        font-size: 0.72rem;
        margin-top: 20px;
        padding: 12px 0;
        border-top: 1px solid rgba(255,255,255,0.05);
    }

    /* ── Hide Streamlit branding ──────────────────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "briefing_shown" not in st.session_state:
    st.session_state.briefing_shown = False
if "category_filter" not in st.session_state:
    st.session_state.category_filter = "All Categories"

# ---------------------------------------------------------------------------
# Precompute sidebar metrics
# ---------------------------------------------------------------------------
df = products_df.copy()
df["days_to_stockout"] = df.apply(
    lambda r: r["stock_quantity"] / r["avg_daily_sales"]
    if r["avg_daily_sales"] > 0
    else 999,
    axis=1,
)
df["gross_margin"] = ((df["price"] - df["cost"]) / df["price"] * 100).round(2)

total_skus = len(df)
critical_stock = int((df["days_to_stockout"] < 7).sum())
low_stock = int(((df["days_to_stockout"] >= 7) & (df["days_to_stockout"] <= 14)).sum())
healthy_stock = total_skus - critical_stock - low_stock
avg_margin = df["gross_margin"].mean()
avg_rating = df["avg_rating"].mean()
total_revenue_daily = (df["price"] * df["avg_daily_sales"]).sum()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div style="text-align:center; padding: 8px 0 0 0;">'
        '<span style="font-size:2rem;">🛍️</span><br>'
        '<span style="font-size:1.1rem; font-weight:700; '
        'background: linear-gradient(135deg, #818cf8, #c084fc); '
        '-webkit-background-clip: text; -webkit-text-fill-color: transparent;">'
        'RetailMind</span><br>'
        '<span style="font-size:0.7rem; color:#64748b; letter-spacing:1.5px; '
        'text-transform:uppercase;">StyleCraft Intelligence</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Status indicator
    st.markdown(
        '<p style="color:#94a3b8; font-size:0.78rem; margin-bottom:4px;">'
        '<span class="status-dot green"></span> Agent Online · GPT-4o</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Category filter
    st.markdown(
        '<p style="color:#cbd5e1; font-size:0.8rem; font-weight:600; '
        'letter-spacing:0.5px; text-transform:uppercase; margin-bottom:2px;">'
        '🎯 Category Filter</p>',
        unsafe_allow_html=True,
    )
    category_options = [
        "All Categories", "Tops", "Dresses", "Bottoms", "Outerwear", "Accessories"
    ]
    selected_category = st.selectbox(
        "Category Filter",
        options=category_options,
        index=category_options.index(st.session_state.category_filter),
        key="category_select",
        label_visibility="collapsed",
    )
    st.session_state.category_filter = selected_category

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # ── Catalog Health Dashboard (custom HTML cards — no truncation) ──
    st.markdown(
        '<p style="color:#cbd5e1; font-size:0.8rem; font-weight:600; '
        'letter-spacing:0.5px; text-transform:uppercase; margin-bottom:8px;">'
        '📊 Catalog Health</p>',
        unsafe_allow_html=True,
    )

    critical_cls = ' critical' if critical_stock > 0 else ''
    st.markdown(
        f"""
        <div class="stat-card">
            <span class="stat-label">Total SKUs</span>
            <span class="stat-value">{total_skus}</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">🚨 Critical Stock</span>
            <span class="stat-value{critical_cls}">{critical_stock}</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">Avg Margin</span>
            <span class="stat-value">{avg_margin:.1f}%</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">Avg Rating</span>
            <span class="stat-value">⭐ {avg_rating:.1f}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # ── Stock Health Bar ──
    st.markdown(
        '<p style="color:#cbd5e1; font-size:0.8rem; font-weight:600; '
        'letter-spacing:0.5px; text-transform:uppercase; margin-bottom:6px;">'
        '📦 Stock Distribution</p>',
        unsafe_allow_html=True,
    )

    healthy_pct = healthy_stock / total_skus * 100
    low_pct = low_stock / total_skus * 100
    critical_pct = critical_stock / total_skus * 100

    st.markdown(
        f"""
        <div style="display:flex; border-radius:8px; overflow:hidden; height:12px; margin-bottom:8px;">
            <div style="width:{healthy_pct}%; background:linear-gradient(90deg,#22c55e,#4ade80);"
                 title="Healthy: {healthy_stock}"></div>
            <div style="width:{low_pct}%; background:linear-gradient(90deg,#f59e0b,#fbbf24);"
                 title="Low: {low_stock}"></div>
            <div style="width:{critical_pct}%; background:linear-gradient(90deg,#ef4444,#f87171);"
                 title="Critical: {critical_stock}"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.68rem; color:#94a3b8;">
            <span>🟢 Healthy ({healthy_stock})</span>
            <span>🟡 Low ({low_stock})</span>
            <span>🔴 Critical ({critical_stock})</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # ── Daily Revenue Estimate ──
    st.markdown(
        f"""
        <div style="background: rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.15);
                    border-radius:12px; padding:14px; text-align:center;">
            <p style="color:#94a3b8; font-size:0.72rem; margin:0 0 4px 0; text-transform:uppercase;
                      letter-spacing:0.8px; font-weight:500;">Est. Daily Revenue</p>
            <p style="color:#818cf8; font-size:1.4rem; font-weight:800; margin:0;">
                ₹{total_revenue_daily:,.0f}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Clear Chat button
    if st.button("🗑️  Clear Conversation", use_container_width=True):
        memory.clear_memory()
        st.session_state.messages = []
        st.session_state.briefing_shown = False
        st.rerun()

    st.markdown(
        '<div class="sidebar-footer">'
        'RetailMind v1.0 · Powered by OpenAI<br>'
        '© 2026 StyleCraft Intelligence'
        '</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main Area — Hero Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-container">
        <p class="hero-title">🛍️ RetailMind <span class="hero-badge">AI Agent</span></p>
        <p class="hero-subtitle">
            StyleCraft Product Intelligence — Ask about inventory, pricing, reviews, or the catalog
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Quick Action Buttons
# ---------------------------------------------------------------------------
st.markdown(
    '<p style="color:#94a3b8; font-size:0.78rem; font-weight:500; '
    'letter-spacing:0.5px; margin-bottom:6px;">⚡ QUICK ACTIONS</p>',
    unsafe_allow_html=True,
)

qcol1, qcol2, qcol3, qcol4, qcol5 = st.columns(5)
quick_query = None
with qcol1:
    if st.button("🚨 Stock Alerts", use_container_width=True):
        quick_query = "Which products are critically low on stock?"
with qcol2:
    if st.button("📊 Top Sellers", use_container_width=True):
        quick_query = "Show me the top performing products across all categories"
with qcol3:
    if st.button("💰 Margin Check", use_container_width=True):
        quick_query = "Which products have the lowest profit margins?"
with qcol4:
    if st.button("⭐ Review Scan", use_container_width=True):
        quick_query = "What are customers saying about the worst-rated products?"
with qcol5:
    if st.button("📦 Restock Now", use_container_width=True):
        quick_query = "Generate a restock alert for all products running low"

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Daily Briefing on Startup
# ---------------------------------------------------------------------------
if not st.session_state.briefing_shown:
    with st.spinner("🔮 Generating your daily intelligence briefing..."):
        try:
            briefing = generate_daily_briefing()
        except Exception as e:
            briefing = (
                "⚠️ Could not generate daily briefing. "
                f"Please check your API key configuration.\n\nError: {e}"
            )
    st.session_state.messages.append({"role": "assistant", "content": briefing})
    memory.add_message("assistant", briefing)
    st.session_state.briefing_shown = True

# ---------------------------------------------------------------------------
# Chat Display
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Chat Input (manual or quick action)
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask me about StyleCraft's catalog...")

# Use quick action query if a button was pressed
if quick_query:
    user_input = quick_query

if user_input:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    memory.add_message("user", user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("✨ Analyzing..."):
            try:
                response = router.route_query(
                    user_input,
                    memory.get_history(),
                    st.session_state.category_filter,
                )
            except Exception as e:
                response = (
                    "I'm sorry, I encountered an error processing your request. "
                    f"Please try again.\n\nError: {e}"
                )
        st.markdown(response)

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})
    memory.add_message("assistant", response)
