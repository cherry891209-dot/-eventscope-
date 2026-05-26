# app.py
# EventScope — Financial Event Simulation Platform
# Main Streamlit Application

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ─── Page Config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="EventScope | 金融事件模擬平台",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    :root {
        --bg-main: #f6f7f9;
        --surface: #ffffff;
        --surface-soft: #eef3f5;
        --border: #d8e0e5;
        --border-strong: #becbd3;
        --text-main: #17212b;
        --text-muted: #61717d;
        --accent: #0f766e;
        --accent-strong: #115e59;
        --accent-soft: #dff3ef;
        --danger: #b4534a;
        --warning: #b7831f;
        --shadow: 0 10px 28px rgba(31, 41, 55, 0.08);
    }
    html, body, [data-testid="stApp"] {
        background: var(--bg-main);
        color: var(--text-main);
        font-family: Inter, 'Avenir Next', 'SF Pro Display', 'PingFang TC', 'Microsoft JhengHei', sans-serif;
    }
    [data-testid="stAppViewContainer"] { background: transparent; }
    .block-container {
        max-width: 1260px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--border);
        box-shadow: 12px 0 32px rgba(31, 41, 55, 0.04);
    }
    [data-testid="stSidebar"] * { color: var(--text-main); }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] {
        gap: 6px;
    }
    [data-testid="stSidebar"] label[data-baseweb="radio"] {
        border-radius: 8px;
        padding: 8px 10px;
        border: 1px solid transparent;
    }
    [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {
        background: var(--accent-soft);
        border-color: #afd8d2;
        color: var(--accent-strong);
    }
    h1, h2, h3, h4, h5, h6 { color: var(--text-main); letter-spacing: 0; }

    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 14px 16px;
        box-shadow: var(--shadow);
    }
    [data-testid="stMetricValue"] { color: var(--text-main); font-size: 1.45rem; font-weight: 750; }
    [data-testid="stMetricLabel"] { color: var(--text-muted); font-size: 0.82rem; }
    [data-testid="stMetricDelta"] { color: var(--accent-strong); }

    /* Buttons */
    .stButton > button {
        background: var(--accent);
        color: white;
        font-weight: 700;
        border: 1px solid var(--accent);
        border-radius: 8px;
        padding: 0.52rem 1.2rem;
        transition: all 0.2s;
        box-shadow: 0 6px 14px rgba(15, 118, 110, 0.16);
    }
    .stButton > button:hover {
        background: var(--accent-strong);
        border-color: var(--accent-strong);
        box-shadow: 0 8px 18px rgba(15, 118, 110, 0.22);
        transform: translateY(-1px);
    }
    .stButton > button[kind="secondary"] {
        background: #ffffff;
        color: var(--text-main);
        border-color: var(--border-strong);
        box-shadow: none;
    }

    /* Input widgets */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stTextInput > div > div,
    .stTextArea textarea,
    [data-testid="stDataEditor"] {
        background-color: #ffffff;
        border: 1px solid var(--border);
        color: var(--text-main);
        border-radius: 8px;
    }
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    textarea {
        background: #ffffff !important;
        border-color: var(--border) !important;
    }
    .stSlider [data-baseweb="slider"] { padding-top: 0.5rem; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        border-bottom: 1px solid var(--border);
        gap: 4px;
        padding: 0;
    }
    .stTabs [data-baseweb="tab"] {
        color: var(--text-muted);
        font-weight: 600;
        padding: 10px 14px;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: var(--accent-strong) !important;
        border-bottom: 2px solid var(--accent);
    }

    /* Event cards */
    .event-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        transition: all 0.2s;
        box-shadow: var(--shadow);
    }
    .event-card:hover { box-shadow: 0 14px 34px rgba(31, 41, 55, 0.12); transform: translateY(-1px); }
    .event-card h4 { color: var(--text-main) !important; margin: 0 0 6px 0; font-size: 1rem; }
    .event-card p { color: var(--text-muted) !important; margin: 0; font-size: 0.85rem; line-height: 1.55; }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
    }

    /* Hero section */
    .hero-section {
        position: relative;
        overflow: hidden;
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 34px 34px 30px;
        margin-bottom: 24px;
        box-shadow: var(--shadow);
    }
    .hero-section::after {
        content: "";
        position: absolute;
        right: 30px;
        top: 28px;
        width: min(34%, 360px);
        height: calc(100% - 56px);
        background:
            linear-gradient(90deg, rgba(15,118,110,0.16) 1px, transparent 1px),
            linear-gradient(180deg, rgba(15,118,110,0.12) 1px, transparent 1px);
        background-size: 22px 22px;
        mask-image: linear-gradient(90deg, transparent, #000 26%, #000);
        opacity: 0.72;
        pointer-events: none;
    }
    .hero-title {
        position: relative;
        z-index: 1;
        font-size: clamp(2.1rem, 4vw, 3.5rem);
        font-weight: 850;
        color: var(--text-main);
        margin: 0;
        letter-spacing: 0;
    }
    .hero-subtitle {
        position: relative;
        z-index: 1;
        font-size: 1.05rem;
        color: var(--text-muted);
        margin-top: 10px;
        max-width: 620px;
    }
    .hero-kicker {
        position: relative;
        z-index: 1;
        display: inline-block;
        margin-bottom: 14px;
        padding: 5px 10px;
        border-radius: 999px;
        border: 1px solid #bfe3de;
        background: var(--accent-soft);
        color: var(--accent-strong);
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    /* Section headers */
    .section-header {
        font-size: 1.08rem;
        font-weight: 700;
        color: var(--text-main);
        border-bottom: 1px solid var(--border);
        padding-bottom: 8px;
        margin: 24px 0 14px 0;
    }

    /* Info box */
    .info-box {
        background: #f0f7f6;
        border: 1px solid #cce6e1;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 10px 0;
        color: #315b57;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    .glass-panel {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 16px 18px;
        box-shadow: var(--shadow);
    }
    .summary-tile {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 14px 16px;
        min-height: 110px;
        box-shadow: var(--shadow);
    }
    .summary-tile-label {
        color: var(--text-muted);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .summary-tile-value {
        color: var(--text-main);
        font-size: 1.2rem;
        font-weight: 700;
        margin-top: 8px;
    }
    .summary-tile-note {
        color: var(--text-muted);
        font-size: 0.82rem;
        margin-top: 8px;
        line-height: 1.5;
    }

    /* Divider */
    hr { border-color: var(--border); }

    /* Streamlit overrides */
    .stAlert { border-radius: 8px; }
    div[data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: 8px;
        box-shadow: 0 8px 20px rgba(31, 41, 55, 0.05);
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 8px;
        overflow: hidden;
    }
    code {
        background: #eef3f5 !important;
        color: #0f5f68 !important;
        border-radius: 5px;
        padding: 2px 5px;
    }
    [style*="color:#f0b90b"], [style*="color: #f0b90b"] { color: var(--accent-strong) !important; }
    [style*="color:#6688aa"], [style*="color: #6688aa"],
    [style*="color:#8ca0b8"], [style*="color: #8ca0b8"],
    [style*="color:#b0c4d8"], [style*="color: #b0c4d8"] { color: var(--text-muted) !important; }
    [style*="background:#0d1f3c"], [style*="background: #0d1f3c"],
    [style*="background:#1e3050"], [style*="background: #1e3050"],
    [style*="background:#081423"], [style*="background: #081423"] {
        background: var(--surface-soft) !important;
        border-color: var(--border) !important;
    }
    @media (max-width: 760px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
        .hero-section { padding: 26px 20px; }
        .hero-section::after { display: none; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Imports (after page config) ─────────────────────────────────────────────
from data.events_db import (
    HISTORICAL_EVENTS,
    ASSET_UNIVERSE,
    EVENT_CATEGORIES,
    get_events_by_category,
    get_event_by_id,
    get_similar_events,
)
from data.fetcher import build_returns_matrix, SYNTHETIC_PATTERNS
from analysis.event_study import run_event_study, calculate_historical_cars
from analysis.causality import (
    granger_causality_matrix,
    transfer_entropy_matrix,
    build_causality_network,
    get_transmission_path,
)
from analysis.monte_carlo import (
    simulate_event_impact,
    portfolio_stress_test,
    generate_scenario_comparison,
)
from visualization.charts import (
    plot_impact_network,
    plot_car_distribution,
    plot_multi_asset_forecast,
    plot_historical_comparison,
    plot_portfolio_waterfall,
    plot_event_timeline,
    plot_propagation_cascade,
)
from portfolio.stress_test import (
    DEFAULT_PORTFOLIO,
    parse_portfolio_input,
    validate_portfolio,
    get_hedge_suggestions,
)

# ─── Category colour map ──────────────────────────────────────────────────────
CAT_COLORS = {
    "貨幣政策": "#a1aaeb",
    "地緣政治": "#eb9393",
    "金融危機": "#ffb53d",
    "商品衝擊": "#f0d069",
    "科技產業": "#94f1fb",
    "自然災害": "#99bd67",
}

PORTFOLIO_PRESETS = {
    "課堂示範": DEFAULT_PORTFOLIO.copy(),
    "科技成長": {"^IXIC": 0.30, "2330.TW": 0.20, "BTC-USD": 0.15, "^GSPC": 0.20, "GLD": 0.05, "^TNX": 0.10},
    "防禦避險": {"GLD": 0.30, "^TNX": 0.25, "^DXY": 0.15, "^GSPC": 0.15, "^TWII": 0.10, "BTC-USD": 0.05},
    "通膨交易": {"CL=F": 0.25, "GC=F": 0.20, "GLD": 0.15, "^DXY": 0.10, "EEM": 0.10, "^GSPC": 0.20},
}


def normalize_portfolio_weights(portfolio: dict) -> dict:
    positive = {ticker: float(weight) for ticker, weight in portfolio.items() if float(weight) > 0}
    total = sum(positive.values())
    if total <= 0:
        return {}
    return {ticker: weight / total for ticker, weight in positive.items()}


def portfolio_to_rows(portfolio: dict) -> list[dict]:
    rows = []
    for ticker, weight in portfolio.items():
        info = ASSET_UNIVERSE.get(ticker, {})
        rows.append(
            {
                "Ticker": ticker,
                "資產名稱": info.get("name_zh", ticker),
                "類別": info.get("category", "其他"),
                "權重 (%)": round(float(weight) * 100, 2),
            }
        )
    return rows


def rows_to_portfolio(rows: list[dict]) -> dict:
    portfolio = {}
    for row in rows:
        ticker = str(row.get("Ticker", "")).strip().upper()
        if not ticker:
            continue
        try:
            weight_pct = float(row.get("權重 (%)", 0))
        except (TypeError, ValueError):
            continue
        if weight_pct <= 0:
            continue
        portfolio[ticker] = weight_pct / 100.0
    return portfolio

# ─── Session state init ───────────────────────────────────────────────────────
for key in [
    "analysis_done", "selected_event", "simulation_results",
    "historical_cars", "causality_network", "portfolio_result",
    "returns_matrix", "event_study_df",
]:
    if key not in st.session_state:
        st.session_state[key] = None
if "portfolio_dict" not in st.session_state:
    st.session_state["portfolio_dict"] = DEFAULT_PORTFOLIO.copy()
if "portfolio_editor_rows" not in st.session_state:
    st.session_state["portfolio_editor_rows"] = portfolio_to_rows(DEFAULT_PORTFOLIO)
if "portfolio_input_mode" not in st.session_state:
    st.session_state["portfolio_input_mode"] = "快速配置器"


# ─── Cached Analysis Functions ───────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def cached_build_returns(event_date: str, tickers_tuple: tuple, category: str):
    tickers = list(tickers_tuple)
    return build_returns_matrix(
        event_date, tickers=tickers, estimation_window=120,
        event_window_pre=5, event_window_post=20,
        event_category=category,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def cached_event_study(event_date: str, tickers_tuple: tuple, category: str):
    matrix_data = cached_build_returns(event_date, tickers_tuple, category)
    returns = matrix_data["returns"]
    if returns.empty:
        return pd.DataFrame()
    return run_event_study(returns, event_date, estimation_window=120, event_window=(-1, 10))


@st.cache_data(ttl=3600, show_spinner=False)
def cached_historical_cars(event_id: str, tickers_tuple: tuple):
    event = get_event_by_id(event_id)
    if not event:
        return pd.DataFrame()
    similar = get_similar_events(event_id, n=8)
    return calculate_historical_cars(event, similar, list(tickers_tuple))


@st.cache_data(ttl=3600, show_spinner=False)
def cached_causality(event_date: str, tickers_tuple: tuple, category: str):
    matrix_data = cached_build_returns(event_date, tickers_tuple, category)
    returns = matrix_data["estimation_returns"]
    if returns.empty or returns.shape[0] < 20:
        returns = matrix_data["returns"]
    if returns.shape[0] < 10:
        return {}, {}, {"nodes": list(tickers_tuple), "edges": [], "centrality": {}}

    gm = granger_causality_matrix(returns, max_lag=3)
    te = transfer_entropy_matrix(returns, bins=4)
    net = build_causality_network(gm, te)
    return gm, te, net


@st.cache_data(ttl=3600, show_spinner=False)
def cached_simulate(event_id: str, tickers_tuple: tuple, intensity: float):
    hist_cars = cached_historical_cars(event_id, tickers_tuple)
    if hist_cars.empty:
        # Fallback synthetic
        event = get_event_by_id(event_id)
        cat = event["category"] if event else "金融危機"
        pattern = SYNTHETIC_PATTERNS.get(cat, {})
        rng = np.random.default_rng(42)
        rows = []
        for t in tickers_tuple:
            base = pattern.get(t, -0.02)
            arr = rng.normal(base * intensity, abs(base) * 0.4 + 0.01, 500)
            rows.append({"ticker": t, "data": arr})
        # Build a mini historical_cars from synthetic
        synth = pd.DataFrame(
            {t: rng.normal(pattern.get(t, -0.02), 0.015, 8) for t in tickers_tuple}
        )
        return simulate_event_impact(synth, n_simulations=5000, event_intensity=intensity)

    return simulate_event_impact(hist_cars, n_simulations=5000, event_intensity=intensity)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_category_historical_cars(category: str, tickers_tuple: tuple, reference_event_id: str | None = None):
    category_events = [e for e in HISTORICAL_EVENTS if e["category"] == category]
    if not category_events:
        return pd.DataFrame()

    reference_event = get_event_by_id(reference_event_id) if reference_event_id else None
    if reference_event is None or reference_event.get("category") != category:
        category_events = sorted(
            category_events,
            key=lambda e: (e["magnitude"], e["date"]),
            reverse=True,
        )
        reference_event = category_events[0]

    similar_events = [
        e for e in category_events
        if e["id"] != reference_event["id"]
    ]
    similar_events = sorted(
        similar_events,
        key=lambda e: (e["magnitude"], e["date"]),
        reverse=True,
    )[:8]
    return calculate_historical_cars(reference_event, similar_events, list(tickers_tuple))


def build_custom_scenario(
    name: str,
    category: str,
    reference_event: dict,
    intensity: float,
    notes: str = "",
) -> dict:
    scenario_name = name.strip() if name.strip() else f"{category}自訂情境"
    scenario_desc = (
        notes.strip()
        if notes.strip()
        else f"使用者自訂的 {category} 情境，模型以「{reference_event['name_zh']}」及同類歷史事件進行校準。"
    )
    return {
        "id": f"custom::{category}::{reference_event['id']}",
        "name_zh": scenario_name,
        "name_en": "Custom Scenario",
        "category": category,
        "date": reference_event["date"],
        "description_zh": scenario_desc,
        "description_en": scenario_desc,
        "primary_shock": reference_event["primary_shock"],
        "magnitude": min(5.0, max(1.0, reference_event["magnitude"] * intensity)),
        "reference_event_id": reference_event["id"],
        "reference_event_name": reference_event["name_zh"],
        "is_custom": True,
    }


# ─── Sidebar Navigation ───────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 18px 4px 14px 4px;">
          <div style="font-size:0.78rem; color:#0f766e; font-weight:800; letter-spacing:0.08em; text-transform:uppercase;">EventScope</div>
          <div style="font-size:1.35rem; font-weight:850; color:#17212b; margin-top:2px;">金融事件工作台</div>
          <div style="font-size:0.82rem; color:#61717d; margin-top:6px; line-height:1.5;">情境模擬、傳導網路與投組壓力測試</div>
        </div>
        <hr style="border-color:#d8e0e5; margin:8px 0 14px;">
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "導覽",
        options=["🏠 首頁", "🔬 事件分析", "📚 事件資料庫", "📖 方法論說明"],
        label_visibility="collapsed",
    )

    st.markdown("<hr style='border-color:#d8e0e5; margin:20px 0 10px 0;'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-size:0.78rem; color:#61717d; line-height:1.6;">
          <b style="color:#17212b;">EventScope v1.0</b><br>
          金融科技課程專案<br>
          Powered by Streamlit + Plotly
        </div>
        """,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════════════════
# PAGE 1: 首頁 / Dashboard
# ════════════════════════════════════════════════════════════════════════════

if page == "🏠 首頁":
    # Hero section
    st.markdown(
        """
        <div class="hero-section">
          <div class="hero-kicker">Scenario Intelligence Studio</div>
          <div class="hero-title">EventScope</div>
          <div class="hero-subtitle">金融事件情境模擬與衝擊傳導分析平台</div>
          <div style="position:relative; z-index:1; margin-top:14px; color:#61717d; font-size:0.9rem;">
            Financial Event Simulation · Contagion Network · Monte Carlo Risk Assessment
          </div>
          <div style="position:relative; z-index:1; margin-top:22px; display:flex; gap:10px; flex-wrap:wrap;">
            <span class="badge" style="background:#dff3ef; color:#115e59; border:1px solid #bfe3de;">事件研究</span>
            <span class="badge" style="background:#e8eef6; color:#3f5f8a; border:1px solid #cdd9ea;">傳導網路</span>
            <span class="badge" style="background:#f5ead8; color:#8a5b16; border:1px solid #e5cfa8;">投組壓測</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("歷史事件數", f"{len(HISTORICAL_EVENTS)} 件")
    with col2:
        st.metric("追蹤資產數", f"{len(ASSET_UNIVERSE)} 種")
    with col3:
        st.metric("事件類別", f"{len(EVENT_CATEGORIES)} 類")
    with col4:
        years = set(e["date"][:4] for e in HISTORICAL_EVENTS)
        st.metric("時間跨度", f"{min(years)}–{max(years)}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Platform capabilities
    st.markdown('<div class="section-header">🚀 平台功能</div>', unsafe_allow_html=True)
    cap1, cap2, cap3, cap4 = st.columns(4)
    capabilities = [
        ("📊", "事件研究", "Market Model + 累積異常報酬（CAR）分析，量化事件對各資產的衝擊"),
        ("🕸️", "傳導網路", "Granger因果 + 轉移熵 建立有向傳導網路，識別系統性風險擴散路徑"),
        ("🎲", "蒙地卡羅", "Bootstrap 10,000次模擬，生成各資產報酬分佈與 VaR / CVaR 指標"),
        ("💼", "壓力測試", "自定義投資組合，模擬極端事件下的持倉損益與對沖建議"),
    ]
    for col, (icon, title, desc) in zip([cap1, cap2, cap3, cap4], capabilities):
        with col:
            st.markdown(
                f"""
                <div class="event-card">
                  <h4>{icon} {title}</h4>
                  <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Featured recent events
    st.markdown('<div class="section-header">⭐ 精選重大事件</div>', unsafe_allow_html=True)
    featured_ids = ["covid_crash_2020", "fed_hike_cycle_2022", "svb_collapse_2023",
                    "deepseek_shock_2025", "russia_ukraine_2022", "lehman_2008"]
    featured = [get_event_by_id(eid) for eid in featured_ids if get_event_by_id(eid)]

    fc1, fc2, fc3 = st.columns(3)
    for i, ev in enumerate(featured):
        col = [fc1, fc2, fc3][i % 3]
        cat_color = CAT_COLORS.get(ev["category"], "#888")
        mag_stars = "★" * round(ev["magnitude"]) + "☆" * (5 - round(ev["magnitude"]))
        with col:
            st.markdown(
                f"""
                <div class="event-card">
                  <span class="badge" style="background:{cat_color}22; color:{cat_color};">{ev["category"]}</span>
                  <span style="color:#6688aa; font-size:0.8rem;">{ev["date"]}</span>
                  <h4 style="margin-top:6px;">{ev["name_zh"]}</h4>
                  <p>{ev["description_zh"]}</p>
                  <div style="margin-top:8px; color:{cat_color}; font-size:0.85rem;">{mag_stars}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # CTA
    st.markdown(
        """
        <div class="info-box" style="text-align:center; padding:28px;">
          <div style="font-size:1.1rem; color:#17212b; font-weight:700; margin-bottom:10px;">
            選擇左側「🔬 事件分析」開始模擬任一歷史事件的市場衝擊
          </div>
          <div style="color:#61717d; font-size:0.9rem;">
            支援 30+ 歷史事件 · 12 種資產 · 離線合成資料備援
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════════════════
# PAGE 2: 事件分析 / Event Analysis
# ════════════════════════════════════════════════════════════════════════════

elif page == "🔬 事件分析":
    st.markdown('<div class="hero-title" style="font-size:2rem; text-align:left;">🔬 事件情境分析</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle" style="text-align:left; margin-bottom:20px;">選擇歷史事件，模擬其對各金融資產的衝擊與傳導路徑</div>', unsafe_allow_html=True)

    # ── Step 1: Select Event ──────────────────────────────────────────────
    st.markdown('<div class="section-header">Step 1 · 選擇事件情境</div>', unsafe_allow_html=True)

    scenario_mode = st.radio(
        "情境模式",
        options=["歷史事件", "自訂情境"],
        horizontal=True,
    )

    s1_col1, s1_col2 = st.columns([1, 2])
    with s1_col1:
        all_cats = ["全部"] + EVENT_CATEGORIES
        default_cat = "全部" if scenario_mode == "歷史事件" else "貨幣政策"
        selected_cat = st.radio(
            "事件類別篩選",
            all_cats if scenario_mode == "歷史事件" else EVENT_CATEGORIES,
            horizontal=False,
            index=(all_cats.index(default_cat) if scenario_mode == "歷史事件" else 0),
        )

    with s1_col2:
        intensity = st.slider(
            "事件強度倍數",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="0.5x = 溫和情境 / 1.0x = 歷史基準 / 2.0x = 極端情境",
        )

        if scenario_mode == "歷史事件":
            filtered_events = get_events_by_category(selected_cat)
            event_options = {f"{e['date']} — {e['name_zh']}": e["id"] for e in filtered_events}
            selected_label = st.selectbox("選擇事件", list(event_options.keys()))
            selected_event_id = event_options[selected_label]
            selected_event = get_event_by_id(selected_event_id)
        else:
            category_events = sorted(
                [e for e in HISTORICAL_EVENTS if e["category"] == selected_cat],
                key=lambda e: e["date"],
                reverse=True,
            )
            reference_options = {
                f"{e['date']} — {e['name_zh']}": e["id"]
                for e in category_events
            }
            custom_name = st.text_input(
                "自訂情境名稱",
                value=f"{selected_cat}自訂情境",
                help="例如：聯準會升息 2 碼、油價暴漲 30%、AI 監管升級",
            )
            reference_label = st.selectbox(
                "校準基準事件",
                list(reference_options.keys()),
                help="模型會參考這個事件的市場結構，並結合同類歷史事件做模擬。",
            )
            custom_notes = st.text_area(
                "情境說明（選填）",
                value="",
                height=90,
                placeholder="補充事件背景、假設條件或你想特別觀察的市場衝擊。",
            )
            reference_event = get_event_by_id(reference_options[reference_label])
            selected_event = build_custom_scenario(
                custom_name,
                selected_cat,
                reference_event,
                intensity,
                notes=custom_notes,
            )
            st.markdown(
                f"""
                <div class="info-box">
                  自訂情境會以 <b>{reference_event["name_zh"]}</b> 作為市場結構校準基準，
                  並納入同類別歷史事件進行統計模擬。
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Event detail card
    if selected_event:
        cat_color = CAT_COLORS.get(selected_event["category"], "#888")
        mag = selected_event["magnitude"]
        mag_bar = "█" * round(mag) + "░" * (5 - round(mag))
        calibration_note = ""
        if selected_event.get("is_custom"):
            calibration_note = (
                f"&nbsp;&nbsp;<span style='color:#8ca0b8; font-size:0.82rem;'>校準基準：</span>"
                f"<span style='color:#e0e8f0; font-weight:600;'>{selected_event['reference_event_name']}</span>"
            )
        st.markdown(
            f"""
            <div class="event-card" style="border-left-color:{cat_color};">
              <span class="badge" style="background:{cat_color}22; color:{cat_color};">{selected_event["category"]}</span>
              <span class="badge" style="background:#1e3050; color:#8ca0b8;">主要衝擊：{selected_event["primary_shock"]}</span>
              <h4>{selected_event["name_zh"]} <span style="color:#6688aa; font-weight:400;">({selected_event["name_en"]})</span></h4>
              <p>{selected_event["description_zh"]}</p>
              <div style="margin-top:8px;">
                <span style="color:#8ca0b8; font-size:0.82rem;">事件日期：</span>
                <span style="color:{cat_color}; font-weight:600;">{selected_event["date"]}</span>
                {calibration_note}
                &nbsp;&nbsp;
                <span style="color:#8ca0b8; font-size:0.82rem;">嚴重程度：</span>
                <span style="color:{cat_color}; font-family:monospace;">{mag_bar} ({mag}/5)</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        summary_cols = st.columns(3)
        summary_items = [
            ("事件類型", selected_event["category"], f"主衝擊資產：{selected_event['primary_shock']}"),
            ("校準尺度", f"{intensity:.1f}x", "0.5x 溫和 / 1.0x 歷史基準 / 2.0x 極端"),
            ("可分析資產", f"{len(ASSET_UNIVERSE)} 項", "支援股市、商品、債券、匯率與加密資產"),
        ]
        for col, (label, value, note) in zip(summary_cols, summary_items):
            with col:
                st.markdown(
                    f"""
                    <div class="summary-tile">
                      <div class="summary-tile-label">{label}</div>
                      <div class="summary-tile-value">{value}</div>
                      <div class="summary-tile-note">{note}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ── Step 2: Select Assets ─────────────────────────────────────────────
    st.markdown('<div class="section-header">Step 2 · 選擇分析資產</div>', unsafe_allow_html=True)

    all_tickers = list(ASSET_UNIVERSE.keys())
    ticker_display = {t: f"{t}  ({ASSET_UNIVERSE[t]['name_zh']})" for t in all_tickers}

    selected_tickers = st.multiselect(
        "選擇資產（可多選）",
        options=all_tickers,
        default=all_tickers,
        format_func=lambda t: ticker_display[t],
    )

    if not selected_tickers:
        st.warning("請至少選擇一個資產。")
        st.stop()

    # ── Step 3: Run Analysis ──────────────────────────────────────────────
    st.markdown('<div class="section-header">Step 3 · 執行分析</div>', unsafe_allow_html=True)

    run_col, status_col = st.columns([1, 3])
    with run_col:
        run_analysis = st.button("🚀 執行分析", type="primary", use_container_width=True)

    if run_analysis and selected_event:
        tickers_tuple = tuple(selected_tickers)
        event_date = selected_event["date"]
        category = selected_event["category"]
        reference_event_id = selected_event.get("reference_event_id")

        progress_bar = st.progress(0, text="正在初始化分析...")

        try:
            with st.spinner("📊 計算事件研究中..."):
                progress_bar.progress(15, text="計算累積異常報酬（CAR）...")
                if selected_event.get("is_custom"):
                    hist_cars = cached_category_historical_cars(category, tickers_tuple, reference_event_id)
                else:
                    hist_cars = cached_historical_cars(selected_event["id"], tickers_tuple)
                st.session_state["historical_cars"] = hist_cars

            progress_bar.progress(35, text="執行蒙地卡羅模擬...")
            with st.spinner("🎲 蒙地卡羅模擬中 (5,000次)..."):
                if selected_event.get("is_custom"):
                    sim_results = simulate_event_impact(hist_cars, n_simulations=5000, event_intensity=intensity)
                else:
                    sim_results = cached_simulate(selected_event["id"], tickers_tuple, intensity)
                st.session_state["simulation_results"] = sim_results

            progress_bar.progress(60, text="建立因果傳導網路...")
            with st.spinner("🕸️ 計算 Granger 因果性與轉移熵..."):
                gm, te, net = cached_causality(event_date, tickers_tuple, category)
                st.session_state["causality_network"] = net

            progress_bar.progress(80, text="投資組合壓力測試...")
            with st.spinner("💼 執行投資組合壓力測試..."):
                port_dict = st.session_state["portfolio_dict"]
                port_result = portfolio_stress_test(port_dict, sim_results)
                st.session_state["portfolio_result"] = port_result

            progress_bar.progress(100, text="分析完成！")
            st.session_state["analysis_done"] = True
            st.session_state["selected_event"] = selected_event
            st.success(f"✓ 分析完成 — {selected_event['name_zh']} ({event_date})")

        except Exception as e:
            st.error(f"分析過程中發生錯誤：{e}")
            st.session_state["analysis_done"] = False

    # ── Results Section ───────────────────────────────────────────────────
    if st.session_state.get("analysis_done") and st.session_state.get("simulation_results") is not None:
        current_event = st.session_state.get("selected_event", selected_event)
        sim_results = st.session_state["simulation_results"]
        hist_cars = st.session_state["historical_cars"]
        net = st.session_state["causality_network"]
        port_result = st.session_state["portfolio_result"]

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-header">📊 分析結果 — {current_event["name_zh"]}</div>',
            unsafe_allow_html=True,
        )

        tab1, tab2, tab3, tab4 = st.tabs(
            ["📊 衝擊預測", "🕸️ 傳導路徑", "📈 歷史比對", "💼 持倉壓力測試"]
        )

        # ── Tab 1: Impact Forecast ────────────────────────────────────────
        with tab1:
            st.plotly_chart(
                plot_multi_asset_forecast(sim_results, ASSET_UNIVERSE),
                use_container_width=True,
            )

            st.markdown('<div class="section-header" style="font-size:1rem;">各資產詳細統計</div>', unsafe_allow_html=True)

            display_df = sim_results[["ticker", "mean_return", "std_return", "p5", "p95", "prob_negative"]].copy()
            display_df.columns = ["資產", "期望報酬", "標準差", "P5 (最差5%)", "P95 (最佳5%)", "下跌機率"]
            for col in ["期望報酬", "標準差", "P5 (最差5%)", "P95 (最佳5%)"]:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2%}")
            display_df["下跌機率"] = display_df["下跌機率"].apply(lambda x: f"{x:.1%}")

            # Add asset names
            display_df.insert(1, "名稱", display_df["資產"].apply(
                lambda t: ASSET_UNIVERSE.get(t, {}).get("name_zh", t)
            ))

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
            )

            # Scenario comparison
            st.markdown('<div class="section-header" style="font-size:1rem;">情境比較</div>', unsafe_allow_html=True)
            if hist_cars is not None and not hist_cars.empty:
                scenarios = generate_scenario_comparison(hist_cars)
                sc1, sc2, sc3 = st.columns(3)
                for col, (scen_key, scen_label, scen_color) in zip(
                    [sc1, sc2, sc3],
                    [("best", "🟢 樂觀情境", ASSET_UNIVERSE), ("base", "🟡 基準情境", ASSET_UNIVERSE), ("worst", "🔴 悲觀情境", ASSET_UNIVERSE)],
                ):
                    scenario_returns = scenarios.get(scen_key, {})
                    with col:
                        st.markdown(f"**{scen_label}**")
                        top5 = sorted(scenario_returns.items(), key=lambda x: x[1], reverse=(scen_key == "best"))[:5]
                        for ticker, ret in top5:
                            name = ASSET_UNIVERSE.get(ticker, {}).get("name_zh", ticker)
                            color = "#2f8f68" if ret >= 0 else "#b4534a"
                            st.markdown(f"<span style='color:#8ca0b8;font-size:0.85rem;'>{name}:</span> <span style='color:{color};font-weight:600;'>{ret:.2%}</span>", unsafe_allow_html=True)

        # ── Tab 2: Contagion Network ──────────────────────────────────────
        with tab2:
            net_col1, net_col2 = st.columns([3, 2])
            with net_col1:
                if net and net.get("edges"):
                    st.plotly_chart(
                        plot_impact_network(net, current_event["name_zh"], ASSET_UNIVERSE),
                        use_container_width=True,
                    )
                else:
                    st.info("資料不足以建立傳導網路，顯示替代分析。")

            with net_col2:
                st.markdown("**🔍 主要傳導路徑**")
                if net and net.get("edges"):
                    top_edges = sorted(net["edges"], key=lambda x: x["weight"], reverse=True)[:8]
                    for e in top_edges:
                        src_name = ASSET_UNIVERSE.get(e["source"], {}).get("name_zh", e["source"])
                        tgt_name = ASSET_UNIVERSE.get(e["target"], {}).get("name_zh", e["target"])
                        color = "#2f8f68" if e.get("direction") == "positive" else "#b4534a"
                        arrow = "➡️" if e.get("direction") == "positive" else "⬇️"
                        st.markdown(
                            f"<div style='font-size:0.85rem; margin:6px 0; padding:6px 10px; background:#0d1f3c; border-radius:6px;'>"
                            f"<span style='color:#f0b90b;'>{src_name}</span> {arrow} "
                            f"<span style='color:{color};'>{tgt_name}</span>"
                            f"<span style='color:#6688aa; float:right;'>強度: {e['weight']:.2f}</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    st.markdown("**📊 節點中心度（影響力）**")
                    centrality = net.get("centrality", {})
                    if centrality:
                        top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:6]
                        for ticker, c_val in top_central:
                            name = ASSET_UNIVERSE.get(ticker, {}).get("name_zh", ticker)
                            bar_width = int(c_val * 100)
                            st.markdown(
                                f"<div style='margin:4px 0;'><span style='color:#e0e8f0;font-size:0.82rem;'>{name}</span>"
                                f"<div style='background:#1e3050; border-radius:4px; margin-top:2px;'>"
                                f"<div style='background:#f0b90b; width:{bar_width}%; height:6px; border-radius:4px;'></div></div></div>",
                                unsafe_allow_html=True,
                            )
                else:
                    st.markdown(
                        '<div class="info-box">傳導網路需要足夠長度的估計窗口資料。'
                        '此情境已使用合成資料，部分因果關係可能無法充分顯示。</div>',
                        unsafe_allow_html=True,
                    )

            # Sankey
            st.markdown("**🔀 衝擊傳導桑基圖**")
            if net:
                primary_shock_ticker = current_event.get("primary_shock", "")
                # Map primary shock to a ticker
                shock_map = {
                    "US_EQUITY": "^GSPC", "TECH_EQUITY": "^IXIC",
                    "OIL": "CL=F", "GOLD": "GLD", "JPY": "^DXY",
                    "USD": "^DXY", "EUR": "^DXY", "GBP": "^DXY",
                    "US_BOND": "^TNX", "CRYPTO": "BTC-USD",
                    "CN_EQUITY": "EEM", "TW_EQUITY": "^TWII",
                    "US_BANK": "^GSPC", "WHEAT": "CL=F",
                }
                sankey_source = shock_map.get(primary_shock_ticker, selected_tickers[0] if selected_tickers else "^GSPC")
                if sankey_source not in selected_tickers:
                    sankey_source = selected_tickers[0]

                st.plotly_chart(
                    plot_propagation_cascade(net, sankey_source, sim_results),
                    use_container_width=True,
                )

        # ── Tab 3: Historical Comparison ──────────────────────────────────
        with tab3:
            if hist_cars is not None and not hist_cars.empty:
                st.plotly_chart(
                    plot_historical_comparison(hist_cars, current_event["name_zh"]),
                    use_container_width=True,
                )

                # Similar events list
                st.markdown('<div class="section-header" style="font-size:1rem;">相似歷史事件</div>', unsafe_allow_html=True)
                anchor_id = current_event.get("reference_event_id", current_event["id"])
                anchor_event = get_event_by_id(anchor_id)
                similar_events = get_similar_events(anchor_id, n=8)
                event_cards = [anchor_event] + similar_events if anchor_event else similar_events
                for ev in event_cards:
                    cat_color = CAT_COLORS.get(ev["category"], "#888")
                    is_anchor = anchor_event is not None and ev["id"] == anchor_event["id"]
                    expander_label = f"📌 {ev['date']} — {ev['name_zh']}"
                    if current_event.get("is_custom") and is_anchor:
                        expander_label += "（校準基準）"
                    with st.expander(expander_label, expanded=is_anchor):
                        st.markdown(
                            f"""
                            <div style="color:#b0c4d8; font-size:0.9rem; line-height:1.7;">
                            <b style="color:#f0b90b;">事件描述：</b>{ev['description_zh']}<br>
                            <b style="color:#f0b90b;">英文名稱：</b>{ev['name_en']}<br>
                            <b style="color:#f0b90b;">主要衝擊：</b><span style="color:{cat_color};">{ev['primary_shock']}</span>
                            &nbsp;&nbsp;
                            <b style="color:#f0b90b;">嚴重程度：</b>{'★' * round(ev['magnitude'])} ({ev['magnitude']}/5)
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            else:
                st.info("歷史比對資料尚未載入，請先執行分析。")

        # ── Tab 4: Portfolio Stress Test ──────────────────────────────────
        with tab4:
            st.markdown('<div class="section-header" style="font-size:1rem;">📝 投資組合設定</div>', unsafe_allow_html=True)
            current_portfolio = st.session_state.get("portfolio_dict", DEFAULT_PORTFOLIO.copy())
            action_col1, action_col2, action_col3 = st.columns([1.2, 1, 1])
            with action_col1:
                preset_name = st.selectbox("預設配置", list(PORTFOLIO_PRESETS.keys()))
            with action_col2:
                input_mode = st.radio(
                    "編輯方式",
                    ["快速配置器", "文字輸入"],
                    horizontal=True,
                    key="portfolio_input_mode",
                )
            with action_col3:
                st.markdown(
                    f"""
                    <div class="glass-panel" style="padding:12px 14px; min-height:84px;">
                      <div class="summary-tile-label">目前資產數</div>
                      <div class="summary-tile-value" style="font-size:1.05rem;">{len(current_portfolio)} 檔</div>
                      <div class="summary-tile-note">權重總和 {sum(current_portfolio.values()):.1%}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            preset_btn1, preset_btn2, preset_btn3 = st.columns(3)
            if preset_btn1.button("套用預設配置", use_container_width=True):
                preset_portfolio = PORTFOLIO_PRESETS[preset_name].copy()
                st.session_state["portfolio_dict"] = preset_portfolio
                st.session_state["portfolio_editor_rows"] = portfolio_to_rows(preset_portfolio)
                current_portfolio = preset_portfolio
            if preset_btn2.button("平均分配目前資產", use_container_width=True):
                tickers = list(current_portfolio.keys()) or list(DEFAULT_PORTFOLIO.keys())
                equal_weight = 1 / len(tickers)
                equal_portfolio = {ticker: equal_weight for ticker in tickers}
                st.session_state["portfolio_dict"] = equal_portfolio
                st.session_state["portfolio_editor_rows"] = portfolio_to_rows(equal_portfolio)
                current_portfolio = equal_portfolio
            if preset_btn3.button("重設為課堂示範", use_container_width=True):
                st.session_state["portfolio_dict"] = DEFAULT_PORTFOLIO.copy()
                st.session_state["portfolio_editor_rows"] = portfolio_to_rows(DEFAULT_PORTFOLIO)
                current_portfolio = DEFAULT_PORTFOLIO.copy()

            pt_col1, pt_col2 = st.columns([2.2, 1])
            if input_mode == "文字輸入":
                with pt_col1:
                    port_input = st.text_area(
                        "輸入投資組合（格式：TICKER:權重%）",
                        value="\n".join(f"{t}:{w*100:.0f}%" for t, w in current_portfolio.items()),
                        height=180,
                        help="範例：^GSPC:30%, ^IXIC:20%, GLD:15%, BTC-USD:10%, ^TWII:20%, ^TNX:5%",
                    )
                    port_dict = parse_portfolio_input(port_input)
                    if not port_dict:
                        port_dict = current_portfolio
                with pt_col2:
                    st.markdown(
                        '<div class="info-box">支援格式：<br>'
                        '<code>TICKER:30%</code><br>'
                        '<code>TICKER:0.30</code><br><br>'
                        '適合熟悉 ticker 的快速調整。<br><br>'
                        '有效資產代碼：<br>' +
                        "、".join(list(ASSET_UNIVERSE.keys())[:8]) + "...",
                        unsafe_allow_html=True,
                    )
            else:
                with pt_col1:
                    editor_rows = st.data_editor(
                        st.session_state.get("portfolio_editor_rows", portfolio_to_rows(current_portfolio)),
                        num_rows="dynamic",
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Ticker": st.column_config.SelectboxColumn(
                                "Ticker",
                                options=list(ASSET_UNIVERSE.keys()),
                                required=True,
                            ),
                            "資產名稱": st.column_config.TextColumn("資產名稱", disabled=True),
                            "類別": st.column_config.TextColumn("類別", disabled=True),
                            "權重 (%)": st.column_config.NumberColumn("權重 (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.2f"),
                        },
                        key="portfolio_editor_widget",
                    )
                    hydrated_rows = []
                    for row in editor_rows:
                        ticker = str(row.get("Ticker", "")).strip().upper()
                        info = ASSET_UNIVERSE.get(ticker, {})
                        hydrated_rows.append(
                            {
                                "Ticker": ticker,
                                "資產名稱": info.get("name_zh", ticker),
                                "類別": info.get("category", "其他"),
                                "權重 (%)": row.get("權重 (%)", 0.0),
                            }
                        )
                    st.session_state["portfolio_editor_rows"] = hydrated_rows
                    port_dict = rows_to_portfolio(hydrated_rows)
                    if not port_dict:
                        port_dict = current_portfolio
                with pt_col2:
                    st.markdown(
                        """
                        <div class="glass-panel">
                          <div class="summary-tile-label">配置器說明</div>
                          <div class="summary-tile-note" style="margin-top:10px;">
                            可直接新增或刪除列，並用下拉選擇資產。<br><br>
                            權重不需手動加總到 100%，系統會先檢查並提示你目前差距。
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            is_valid, val_msg = validate_portfolio(port_dict)
            if is_valid:
                normalized_portfolio = normalize_portfolio_weights(port_dict)
                st.session_state["portfolio_dict"] = normalized_portfolio
                st.session_state["portfolio_editor_rows"] = portfolio_to_rows(normalized_portfolio)
                port_dict = normalized_portfolio
                st.success(val_msg)
            else:
                st.warning(val_msg)
                port_dict = current_portfolio
                st.session_state["portfolio_dict"] = current_portfolio

            breakdown_col1, breakdown_col2 = st.columns([1.1, 1])
            if port_dict:
                alloc_df = pd.DataFrame(
                    [
                        {
                            "ticker": ticker,
                            "name_zh": ASSET_UNIVERSE.get(ticker, {}).get("name_zh", ticker),
                            "category": ASSET_UNIVERSE.get(ticker, {}).get("category", "其他"),
                            "weight": weight,
                            "color": ASSET_UNIVERSE.get(ticker, {}).get("color", "#3f7cac"),
                        }
                        for ticker, weight in port_dict.items()
                    ]
                ).sort_values("weight", ascending=False)
                with breakdown_col1:
                    st.dataframe(
                        alloc_df[["ticker", "name_zh", "category", "weight"]].rename(
                            columns={"ticker": "Ticker", "name_zh": "名稱", "category": "類別", "weight": "權重"}
                        ).assign(權重=lambda df: df["權重"].map(lambda x: f"{x:.1%}")),
                        use_container_width=True,
                        hide_index=True,
                    )
                with breakdown_col2:
                    pie_fig = go.Figure(
                        go.Pie(
                            labels=alloc_df["name_zh"],
                            values=alloc_df["weight"],
                            hole=0.58,
                            marker=dict(colors=alloc_df["color"].tolist(), line=dict(color="#ffffff", width=2)),
                            textinfo="label+percent",
                        )
                    )
                    pie_fig.update_layout(
                        plot_bgcolor="#f6f7f9",
                        paper_bgcolor="#ffffff",
                        font=dict(color="#17212b", family="Avenir Next, PingFang TC, sans-serif"),
                        margin=dict(l=10, r=10, t=30, b=10),
                        title=dict(text="投資組合配置占比", font=dict(color="#0f766e", size=15)),
                        height=320,
                    )
                    st.plotly_chart(pie_fig, use_container_width=True)

            # Recalculate portfolio result with current portfolio
            if sim_results is not None and not sim_results.empty:
                port_result = portfolio_stress_test(port_dict, sim_results)
                st.session_state["portfolio_result"] = port_result

            # Risk metrics
            st.markdown('<div class="section-header" style="font-size:1rem;">📊 風險指標</div>', unsafe_allow_html=True)

            if port_result:
                m1, m2, m3, m4, m5 = st.columns(5)
                metrics = [
                    ("期望報酬", port_result["expected_return"], ""),
                    ("VaR (95%)", port_result["var_95"], "5%最壞情境"),
                    ("VaR (99%)", port_result["var_99"], "1%最壞情境"),
                    ("CVaR (ES)", port_result["expected_shortfall"], "尾端期望損失"),
                    ("最佳情境", port_result["best_case"], "P95"),
                ]
                for col, (label, val, help_text) in zip([m1, m2, m3, m4, m5], metrics):
                    with col:
                        color = "normal" if val >= 0 else "inverse"
                        st.metric(label, f"{val:.2%}", help=help_text)

                # Waterfall chart
                st.plotly_chart(
                    plot_portfolio_waterfall(port_result, port_dict),
                    use_container_width=True,
                )

                # Simulation histogram for portfolio
                port_paths = port_result.get("simulation_paths", np.array([0.0]))
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Histogram(
                    x=port_paths * 100,
                    nbinsx=60,
                    name="組合報酬模擬",
                    marker_color="#3f7cac",
                    opacity=0.7,
                ))
                fig_hist.add_vline(x=port_result["var_95"] * 100, line_dash="dash",
                                   line_color="#b4534a", annotation_text="  VaR 95%",
                                   annotation_font_color="#b4534a")
                fig_hist.add_vline(x=port_result["expected_return"] * 100, line_dash="dash",
                                   line_color="#0f766e", annotation_text="  期望值",
                                   annotation_font_color="#0f766e")
                fig_hist.update_layout(
                    plot_bgcolor="#f6f7f9", paper_bgcolor="#ffffff",
                    font=dict(color="#17212b"), height=280,
                    title=dict(text="投資組合報酬模擬分佈", font=dict(color="#0f766e", size=14)),
                    xaxis_title="報酬 (%)", showlegend=False,
                    margin=dict(l=40, r=20, t=50, b=40),
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            # Hedge suggestions
            st.markdown('<div class="section-header" style="font-size:1rem;">🛡️ 對沖建議</div>', unsafe_allow_html=True)
            hedges = get_hedge_suggestions(port_dict, sim_results, current_event["category"])
            for h in hedges:
                asset_name = ASSET_UNIVERSE.get(h["asset"], {}).get("name_zh", h["asset"])
                eff_pct = int(h["hedge_effectiveness"] * 100)
                ret_color = "#2f8f68" if h["expected_return"] >= 0 else "#b4534a"
                already = "（已持有）" if h.get("already_in_portfolio") else ""
                st.markdown(
                    f"""
                    <div class="event-card" style="border-left-color:#2f8f68;">
                      <h4>🛡️ {asset_name} ({h['asset']}) {already}</h4>
                      <p>{h['reason_zh']}</p>
                      <div style="margin-top:8px; font-size:0.85rem;">
                        <span style="color:#8ca0b8;">預期報酬：</span>
                        <span style="color:{ret_color}; font-weight:600;">{h['expected_return']:.2%}</span>
                        &nbsp;&nbsp;
                        <span style="color:#8ca0b8;">對沖有效性：</span>
                        <span style="color:#2f8f68; font-weight:600;">{eff_pct}%</span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    elif not st.session_state.get("analysis_done"):
        st.markdown(
            """
            <div class="info-box" style="text-align:center; padding:30px;">
              👆 完成上方步驟後，點擊「🚀 執行分析」開始模擬
            </div>
            """,
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════════════════
# PAGE 3: 事件資料庫 / Event Database
# ════════════════════════════════════════════════════════════════════════════

elif page == "📚 事件資料庫":
    st.markdown('<div class="hero-title" style="font-size:2rem;">📚 事件資料庫</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle" style="text-align:left; margin-bottom:20px;">瀏覽與搜尋 2000–2025 年重大金融事件</div>', unsafe_allow_html=True)

    # Timeline
    st.plotly_chart(plot_event_timeline(HISTORICAL_EVENTS), use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Filters
    f1, f2, f3 = st.columns(3)
    with f1:
        filter_cat = st.selectbox("類別篩選", ["全部"] + EVENT_CATEGORIES)
    with f2:
        filter_search = st.text_input("搜尋事件名稱", placeholder="例如：聯準會、比特幣...")
    with f3:
        filter_mag = st.slider("最低嚴重程度", 1.0, 5.0, 1.0, 0.5)

    # Filter events
    display_events = HISTORICAL_EVENTS.copy()
    if filter_cat != "全部":
        display_events = [e for e in display_events if e["category"] == filter_cat]
    if filter_search:
        q = filter_search.lower()
        display_events = [
            e for e in display_events
            if q in e["name_zh"].lower() or q in e["name_en"].lower() or q in e["description_zh"].lower()
        ]
    display_events = [e for e in display_events if e["magnitude"] >= filter_mag]
    display_events = sorted(display_events, key=lambda x: x["date"], reverse=True)

    st.markdown(f"**找到 {len(display_events)} 個事件**", unsafe_allow_html=True)

    # Table view
    df_display = pd.DataFrame([
        {
            "日期": e["date"],
            "類別": e["category"],
            "事件名稱（中）": e["name_zh"],
            "事件名稱（英）": e["name_en"],
            "嚴重程度": e["magnitude"],
            "主要衝擊": e["primary_shock"],
        }
        for e in display_events
    ])

    st.dataframe(df_display, use_container_width=True, hide_index=True, height=320)

    # Detail cards
    st.markdown('<div class="section-header">事件詳情</div>', unsafe_allow_html=True)
    for ev in display_events[:10]:  # Show top 10 to keep UI manageable
        cat_color = CAT_COLORS.get(ev["category"], "#888")
        mag_stars = "★" * round(ev["magnitude"]) + "☆" * (5 - round(ev["magnitude"]))
        with st.expander(f"📌 {ev['date']} — {ev['name_zh']}"):
            dc1, dc2 = st.columns([3, 1])
            with dc1:
                st.markdown(
                    f"""
                    <div style="color:#b0c4d8; line-height:1.8; font-size:0.9rem;">
                    <b style="color:#f0b90b;">中文描述：</b>{ev['description_zh']}<br>
                    <b style="color:#f0b90b;">English：</b>{ev['description_en']}<br>
                    <b style="color:#f0b90b;">主要衝擊資產：</b><span style="color:{cat_color};">{ev['primary_shock']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with dc2:
                st.markdown(
                    f"""
                    <div style="text-align:center; padding:10px; background:#0d1f3c; border-radius:10px; border:1px solid #1e3050;">
                    <div style="font-size:2rem; color:{cat_color};">{mag_stars}</div>
                    <div style="color:#8ca0b8; font-size:0.8rem; margin-top:4px;">嚴重程度 {ev['magnitude']}/5</div>
                    <div style="margin-top:8px;">
                      <span class="badge" style="background:{cat_color}22; color:{cat_color}; padding:4px 10px; border-radius:20px; font-size:0.8rem;">
                        {ev['category']}
                      </span>
                    </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ════════════════════════════════════════════════════════════════════════════
# PAGE 4: 方法論說明 / Methodology
# ════════════════════════════════════════════════════════════════════════════

elif page == "📖 方法論說明":
    st.markdown('<div class="hero-title" style="font-size:2rem;">📖 方法論說明</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle" style="text-align:left; margin-bottom:20px;">EventScope 核心分析方法的學術基礎與實作說明</div>', unsafe_allow_html=True)

    # ── 1. Event Study ────────────────────────────────────────────────────
    with st.expander("📊 一、事件研究法（Event Study）", expanded=True):
        st.markdown(
            """
            <div style="color:#b0c4d8; line-height:1.9; font-size:0.92rem;">

            <b style="color:#f0b90b; font-size:1.05rem;">理論基礎</b><br>
            事件研究法由 Fama et al.（1969）提出，用於衡量特定事件對資產價格的異常影響。
            其核心假設是效率市場假說：若市場有效，資產價格應即時反映所有公開訊息，
            因此「異常報酬」（Abnormal Return）代表事件帶來的超額影響。

            <br><br><b style="color:#f0b90b;">估計窗口（Estimation Window）</b><br>
            以事件日前的資料（本平台使用 120 個交易日）建立基準模型，
            排除事件期間的「汙染」。

            <br><br><b style="color:#f0b90b;">市場模型（Market Model）</b><br>
            透過 OLS 回歸，估計資產報酬與市場報酬的關係：<br>
            <code style="background:#0d1f3c; padding:4px 8px; border-radius:4px; color:#17becf;">
              R_i,t = α + β × R_m,t + ε_t
            </code>
            <br>其中 α 為截距（超額報酬），β 為系統性風險係數。

            <br><br><b style="color:#f0b90b;">異常報酬（Abnormal Return, AR）</b><br>
            <code style="background:#0d1f3c; padding:4px 8px; border-radius:4px; color:#17becf;">
              AR_t = R_i,t − (α̂ + β̂ × R_m,t)
            </code>
            <br>事件窗口（Event Window）內的實際報酬與模型預測報酬之差。

            <br><br><b style="color:#f0b90b;">累積異常報酬（Cumulative Abnormal Return, CAR）</b><br>
            <code style="background:#0d1f3c; padding:4px 8px; border-radius:4px; color:#17becf;">
              CAR(t₁, t₂) = Σ AR_t，t₁ ≤ t ≤ t₂
            </code>
            <br>本平台預設使用 [-1, +10] 交易日的 CAR，捕捉事件前後兩週的衝擊。

            <br><br><b style="color:#f0b90b;">顯著性檢定</b><br>
            使用 t 統計量：t = CAR / (σ × √n)，
            其中 σ 為估計窗口的殘差標準差，n 為事件窗口長度。
            p < 0.10 視為統計顯著。

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── 2. Granger Causality & Transfer Entropy ───────────────────────────
    with st.expander("🕸️ 二、Granger 因果性與轉移熵（Causality Network）"):
        st.markdown(
            """
            <div style="color:#b0c4d8; line-height:1.9; font-size:0.92rem;">

            <b style="color:#f0b90b; font-size:1.05rem;">Granger 因果性檢定</b><br>
            Granger（1969）提出：若 X 的過去值能顯著預測 Y 的未來值（在控制 Y 自身歷史後），
            則稱「X Granger-causes Y」。這是一種預測因果性，非哲學上的因果關係。

            <br><br>實作方式：對所有資產對進行逐對 VAR 模型 F 檢定，
            測試滯後期 1–5 期，取最小 p 值（最顯著的滯後）。

            <br><br><b style="color:#f0b90b; font-size:1.05rem;">轉移熵（Transfer Entropy, TE）</b><br>
            Shannon（1948）資訊理論框架，Schreiber（2000）將其應用於時間序列：<br>
            <code style="background:#0d1f3c; padding:4px 8px; border-radius:4px; color:#17becf;">
              TE(X→Y) = H(Y_t | Y_{t-1}) − H(Y_t | Y_{t-1}, X_{t-1})
            </code>
            <br>量化「在已知 Y 的歷史後，X 的歷史提供多少關於 Y 未來的額外資訊」。
            透過分箱離散化方法估計，單位為 bits。

            <br><br><b style="color:#f0b90b;">傳導網路建構</b><br>
            將 Granger p 值（門檻 0.05）與 TE（門檻 0.01）的結果疊加，
            建立有向加權圖（Directed Weighted Graph）。
            節點大小代表出度中心性（Out-degree Centrality），
            代表該資產對其他資產的整體影響力。

            <br><br><b style="color:#f0b90b;">桑基圖（Sankey Diagram）</b><br>
            視覺化衝擊從源頭資產（主要受衝擊者）向其他資產的流量分佈，
            流量寬度反映蒙地卡羅模擬中的期望報酬絕對值。

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── 3. Monte Carlo ────────────────────────────────────────────────────
    with st.expander("🎲 三、蒙地卡羅模擬（Monte Carlo Simulation）"):
        st.markdown(
            """
            <div style="color:#b0c4d8; line-height:1.9; font-size:0.92rem;">

            <b style="color:#f0b90b; font-size:1.05rem;">Bootstrap 重抽樣</b><br>
            本平台使用非參數 Bootstrap 方法：從歷史相似事件的 CAR 樣本中，
            有放回地抽取 5,000 次，加上少量 Gaussian 雜訊（± 15% 標準差）以增加多樣性。
            「事件強度」倍數直接縮放每次抽樣結果。

            <br><br><b style="color:#f0b90b;">輸出統計量</b><br>
            <ul style="margin:8px 0; padding-left:20px;">
              <li><b>期望報酬（Mean）</b>：5,000 次模擬的平均值</li>
              <li><b>標準差（Std）</b>：波動程度量化</li>
              <li><b>P5 / P25 / P75 / P95</b>：分位數分佈</li>
              <li><b>下跌機率</b>：模擬結果為負值的比例</li>
            </ul>

            <br><b style="color:#f0b90b; font-size:1.05rem;">風險指標（Risk Metrics）</b><br>
            <b>在險值（Value at Risk, VaR）：</b><br>
            <code style="background:#0d1f3c; padding:4px 8px; border-radius:4px; color:#17becf;">
              VaR_α = 第 (1-α) 百分位數
            </code>
            <br>代表在給定信心水準下的最大可能損失。
            本平台提供 95% 及 99% VaR。

            <br><br><b>條件在險值（Expected Shortfall / CVaR）：</b><br>
            <code style="background:#0d1f3c; padding:4px 8px; border-radius:4px; color:#17becf;">
              ES_α = E[損失 | 損失 > VaR_α]
            </code>
            <br>尾部損失的期望值，比 VaR 更能捕捉極端風險。

            <br><br><b style="color:#f0b90b;">情境分析</b><br>
            <ul style="margin:8px 0; padding-left:20px;">
              <li><b>樂觀情境（Best Case）</b>：歷史 CAR 的 P90</li>
              <li><b>基準情境（Base Case）</b>：歷史 CAR 的中位數</li>
              <li><b>悲觀情境（Worst Case）</b>：歷史 CAR 的 P10</li>
            </ul>

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── 4. Portfolio Stress Test ──────────────────────────────────────────
    with st.expander("💼 四、投資組合壓力測試（Portfolio Stress Test）"):
        st.markdown(
            """
            <div style="color:#b0c4d8; line-height:1.9; font-size:0.92rem;">

            <b style="color:#f0b90b; font-size:1.05rem;">加權組合損益計算</b><br>
            <code style="background:#0d1f3c; padding:4px 8px; border-radius:4px; color:#17becf;">
              R_portfolio,s = Σ w_i × R_i,s
            </code>
            <br>對每一次蒙地卡羅模擬 s，計算加權後的組合報酬，
            得到 5,000 個組合情境報酬。

            <br><br><b style="color:#f0b90b;">資產貢獻分析</b><br>
            每個資產對組合期望損失的貢獻：<br>
            <code style="background:#0d1f3c; padding:4px 8px; border-radius:4px; color:#17becf;">
              Contribution_i = w_i × E[R_i]
            </code>

            <br><br><b style="color:#f0b90b;">瀑布圖（Waterfall Chart）</b><br>
            視覺化每個資產對組合總報酬的貢獻，
            正貢獻顯示為綠色，負貢獻顯示為紅色，組合總計以金色標示。

            <br><br><b style="color:#f0b90b;">對沖建議</b><br>
            根據事件類別與現有持倉，建議適合的對沖工具。
            對沖有效性（Hedge Effectiveness）基於歷史事件中的統計相關性，
            範圍 0–100%，越高代表該資產越能有效抵消組合風險。

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── 5. Data Sources ───────────────────────────────────────────────────
    with st.expander("📡 五、資料來源與技術架構"):
        st.markdown(
            """
            <div style="color:#b0c4d8; line-height:1.9; font-size:0.92rem;">

            <b style="color:#f0b90b; font-size:1.05rem;">主要資料來源</b>
            <ul style="margin:8px 0; padding-left:20px;">
              <li><b>Yahoo Finance (yfinance)</b>：股票、ETF、期貨、加密貨幣日收盤價</li>
              <li><b>FRED（聖路易聯準會資料庫）</b>：總體經濟指標（利率、殖利率曲線等）</li>
              <li><b>CoinGecko API</b>：加密貨幣備援資料源</li>
              <li><b>合成資料備援</b>：當 API 不可用時，基於歷史風格化事實（Stylized Facts）產生模擬資料</li>
            </ul>

            <br><b style="color:#f0b90b; font-size:1.05rem;">技術架構</b>
            <ul style="margin:8px 0; padding-left:20px;">
              <li><b>前端框架</b>：Streamlit 1.32+</li>
              <li><b>視覺化</b>：Plotly 5.18+（互動式圖表、網路圖、桑基圖）</li>
              <li><b>數值計算</b>：NumPy、SciPy</li>
              <li><b>統計模型</b>：statsmodels（Granger 因果性）</li>
              <li><b>網路分析</b>：NetworkX（中心性計算、最短路徑）</li>
              <li><b>資料處理</b>：pandas</li>
            </ul>

            <br><b style="color:#f0b90b;">快取策略</b><br>
            所有資料獲取與分析函式均使用 <code>@st.cache_data(ttl=3600)</code> 快取，
            避免重複計算，提升互動響應速度。

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── References ────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📚 主要參考文獻</div>', unsafe_allow_html=True)
    refs = [
        ("Fama et al. (1969)", "Adjustment of Stock Prices to New Information", "Journal of Finance"),
        ("Granger (1969)", "Investigating Causal Relations by Econometric Models", "Econometrica"),
        ("Schreiber (2000)", "Measuring Information Transfer", "Physical Review Letters"),
        ("MacKinlay (1997)", "Event Studies in Economics and Finance", "Journal of Economic Literature"),
        ("Jorion (2007)", "Value at Risk: The New Benchmark for Managing Financial Risk", "McGraw-Hill"),
    ]
    for author, title, journal in refs:
        st.markdown(
            f"<div style='margin:6px 0; color:#8ca0b8; font-size:0.87rem;'>"
            f"<b style='color:#f0b90b;'>{author}</b> — "
            f"<i>{title}</i>, {journal}</div>",
            unsafe_allow_html=True,
        )
