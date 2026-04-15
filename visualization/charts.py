# visualization/charts.py
# Plotly chart functions for EventScope

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─── Color palette ──────────────────────────────────────────────────────────
BG_COLOR = "#f7f3ee"
PAPER_BG = "#fffaf5"
GRID_COLOR = "#ddd3ca"
TEXT_COLOR = "#3f4b4a"
ACCENT = "#7f998f"
POSITIVE_COLOR = "#8ea6a0"
NEGATIVE_COLOR = "#c48f87"

_LAYOUT_BASE = dict(
    plot_bgcolor=BG_COLOR,
    paper_bgcolor=PAPER_BG,
    font=dict(color=TEXT_COLOR, family="Avenir Next, PingFang TC, Microsoft JhengHei, sans-serif"),
    xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
    yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
    margin=dict(l=60, r=40, t=60, b=50),
)

CATEGORY_COLORS = {
    "美國股市": "#9bb2ba",
    "亞洲股市": "#c6a892",
    "歐洲股市": "#9eb0b4",
    "拉丁美洲": "#b69982",
    "商品": "#9eb5ae",
    "固定收益": "#b7c3ad",
    "外匯": "#c9cfb8",
    "加密貨幣": "#d2b29e",
    "新興市場": "#a9b7c5",
}

EVENT_CATEGORY_COLORS = {
    "貨幣政策": "#8fa89d",
    "地緣政治": "#b98b81",
    "金融危機": "#a87068",
    "商品衝擊": "#b59b74",
    "科技產業": "#819daf",
    "自然災害": "#9aa287",
}


# ─── Network Chart ───────────────────────────────────────────────────────────

def plot_impact_network(
    network: dict,
    event_name: str,
    asset_info: dict,
) -> go.Figure:
    """
    Interactive directed network graph showing contagion paths.
    """
    import math

    nodes = network.get("nodes", [])
    edges = network.get("edges", [])
    centrality = network.get("centrality", {})

    if not nodes:
        fig = go.Figure()
        fig.update_layout(**_LAYOUT_BASE, title="無足夠資料建立網路圖")
        return fig

    # Position nodes in a circle
    n = len(nodes)
    positions = {}
    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / n
        positions[node] = (math.cos(angle), math.sin(angle))

    # Draw edges
    edge_traces = []
    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        if src not in positions or tgt not in positions:
            continue
        x0, y0 = positions[src]
        x1, y1 = positions[tgt]
        color = POSITIVE_COLOR if edge.get("direction") == "positive" else NEGATIVE_COLOR
        width = max(1, min(6, edge.get("weight", 0.5) * 8))

        edge_traces.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(width=width, color=color),
                hoverinfo="none",
                showlegend=False,
            )
        )

    # Draw nodes
    node_x, node_y, node_text, node_size, node_color, hover_text = [], [], [], [], [], []
    for node in nodes:
        x, y = positions[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

        # Size by centrality
        c = centrality.get(node, 0.1)
        node_size.append(max(15, int(c * 80) + 20))

        # Color by asset category
        info = asset_info.get(node, {})
        cat = info.get("category", "其他")
        node_color.append(CATEGORY_COLORS.get(cat, "#aaaaaa"))

        name_zh = info.get("name_zh", node)
        hover_text.append(f"{name_zh}<br>中心度: {c:.3f}")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=2, color=TEXT_COLOR),
        ),
        text=node_text,
        textposition="top center",
        textfont=dict(size=10, color=TEXT_COLOR),
        hovertext=hover_text,
        hoverinfo="text",
        showlegend=False,
    )

    fig = go.Figure(data=edge_traces + [node_trace])
    net_layout = dict(**_LAYOUT_BASE)
    net_layout["xaxis"] = dict(showgrid=False, zeroline=False, showticklabels=False)
    net_layout["yaxis"] = dict(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_layout(
        **net_layout,
        title=dict(text=f"衝擊傳導網路 — {event_name}", font=dict(color=ACCENT, size=16)),
        height=500,
    )
    return fig


# ─── CAR Distribution ────────────────────────────────────────────────────────

def plot_car_distribution(
    simulation_results: pd.DataFrame,
    ticker: str,
) -> go.Figure:
    """Histogram of simulated returns for one asset with VaR lines."""
    if simulation_results.empty:
        return go.Figure()

    row = simulation_results[simulation_results["ticker"] == ticker]
    if row.empty:
        return go.Figure()

    row = row.iloc[0]
    mean = float(row["mean_return"])
    p5 = float(row["p5"])
    p95 = float(row["p95"])
    std = float(row["std_return"])

    # Re-create plausible distribution from summary stats
    rng = np.random.default_rng(42)
    sims = rng.normal(mean, std, 5000)

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=sims,
            nbinsx=60,
            name="模擬報酬",
            marker_color=ACCENT,
            opacity=0.7,
        )
    )
    for val, label, color in [
        (p5, "VaR 95%", NEGATIVE_COLOR),
        (mean, "期望值", "#00bfff"),
        (p95, "P95", POSITIVE_COLOR),
    ]:
        fig.add_vline(
            x=val,
            line_dash="dash",
            line_color=color,
            annotation_text=f"  {label}: {val:.2%}",
            annotation_font_color=color,
        )

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text=f"{ticker} 模擬報酬分佈", font=dict(color=ACCENT, size=15)),
        xaxis_title="累積異常報酬 (CAR)",
        yaxis_title="頻率",
        showlegend=False,
        height=350,
    )
    return fig


# ─── Multi-asset Forecast ─────────────────────────────────────────────────────

def plot_multi_asset_forecast(
    simulation_results: pd.DataFrame,
    asset_info: dict,
) -> go.Figure:
    """Bar chart with error bars showing expected return ± std for each asset."""
    if simulation_results.empty:
        return go.Figure()

    df = simulation_results.copy()
    df["name_zh"] = df["ticker"].apply(
        lambda t: asset_info.get(t, {}).get("name_zh", t)
    )
    df = df.sort_values("mean_return")

    colors = [
        POSITIVE_COLOR if v >= 0 else NEGATIVE_COLOR
        for v in df["mean_return"]
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["name_zh"],
            y=df["mean_return"] * 100,
            error_y=dict(
                type="data",
                array=(df["std_return"] * 100).tolist(),
                color=TEXT_COLOR,
                thickness=1.5,
                width=4,
            ),
            marker_color=colors,
            text=[f"{v:.2f}%" for v in df["mean_return"] * 100],
            textposition="outside",
            textfont=dict(size=10, color=TEXT_COLOR),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "期望報酬: %{y:.2f}%<br>"
                "<extra></extra>"
            ),
        )
    )
    fig.add_hline(y=0, line_color=TEXT_COLOR, line_width=1)
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="各資產衝擊預測（期望 CAR）", font=dict(color=ACCENT, size=16)),
        xaxis_title="資產",
        yaxis_title="期望報酬 (%)",
        height=450,
        bargap=0.3,
    )
    return fig


def plot_market_snapshot(snapshot_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart for global market pulse."""
    if snapshot_df.empty:
        return go.Figure()

    df = snapshot_df.copy().sort_values("one_week")
    colors = [POSITIVE_COLOR if v >= 0 else NEGATIVE_COLOR for v in df["one_week"]]
    fig = go.Figure(
        go.Bar(
            x=df["one_week"] * 100,
            y=df["name_zh"],
            orientation="h",
            marker_color=colors,
            text=[f"{v:.2f}%" for v in df["one_week"] * 100],
            textposition="outside",
            customdata=np.column_stack([df["one_day"] * 100, df["ticker"]]),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Ticker: %{customdata[1]}<br>"
                "近一週: %{x:.2f}%<br>"
                "近一日: %{customdata[0]:.2f}%<extra></extra>"
            ),
        )
    )
    fig.add_vline(x=0, line_color=GRID_COLOR, line_width=1)
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="全球市場快照", font=dict(color=ACCENT, size=16)),
        xaxis_title="近一週變化 (%)",
        yaxis_title="",
        height=420,
    )
    return fig


def plot_world_event_map(events_df: pd.DataFrame) -> go.Figure:
    """World map showing event coverage and severity by region."""
    if events_df.empty:
        return go.Figure()

    fig = go.Figure()
    for category, grp in events_df.groupby("category"):
        fig.add_trace(
            go.Scattergeo(
                lon=grp["lon"],
                lat=grp["lat"],
                text=grp["name_zh"],
                customdata=np.column_stack([grp["region"], grp["date"], grp["magnitude"]]),
                mode="markers",
                name=category,
                marker=dict(
                    size=(grp["magnitude"] * 5 + 8).tolist(),
                    color=EVENT_CATEGORY_COLORS.get(category, ACCENT),
                    line=dict(color=PAPER_BG, width=1),
                    opacity=0.85,
                ),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "地區: %{customdata[0]}<br>"
                    "日期: %{customdata[1]}<br>"
                    "強度: %{customdata[2]} / 5<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        font=dict(color=TEXT_COLOR, family="Avenir Next, PingFang TC, Microsoft JhengHei, sans-serif"),
        title=dict(text="全球事件分布地圖", font=dict(color=ACCENT, size=16)),
        geo=dict(
            projection_type="natural earth",
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#ccbfb3",
            showland=True,
            landcolor="#f1e7dd",
            showocean=True,
            oceancolor="#faf4ee",
            bgcolor=PAPER_BG,
        ),
        height=420,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.98,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,250,245,0.7)",
        ),
    )
    return fig


# ─── Historical Comparison Heatmap ───────────────────────────────────────────

def plot_historical_comparison(
    historical_cars: pd.DataFrame,
    event_name: str,
) -> go.Figure:
    """Heatmap of historical CARs: events × assets."""
    if historical_cars.empty:
        return go.Figure()

    z = historical_cars.values * 100  # Convert to %

    # Truncate long row labels
    row_labels = [str(r)[:35] for r in historical_cars.index]
    col_labels = historical_cars.columns.tolist()

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=col_labels,
            y=row_labels,
            colorscale=[
                [0.0, NEGATIVE_COLOR],
                [0.5, "#1e3050"],
                [1.0, POSITIVE_COLOR],
            ],
            zmid=0,
            text=[[f"{v:.1f}%" for v in row] for row in z],
            texttemplate="%{text}",
            textfont=dict(size=9),
            hovertemplate="事件: %{y}<br>資產: %{x}<br>CAR: %{z:.2f}%<extra></extra>",
            colorbar=dict(
                title=dict(text="CAR (%)", font=dict(color=TEXT_COLOR)),
                tickfont=dict(color=TEXT_COLOR),
            ),
        )
    )
    heat_layout = dict(**_LAYOUT_BASE)
    heat_layout["xaxis"] = dict(tickfont=dict(size=10), gridcolor=GRID_COLOR)
    heat_layout["yaxis"] = dict(tickfont=dict(size=9), gridcolor=GRID_COLOR)
    fig.update_layout(
        **heat_layout,
        title=dict(text=f"歷史相似事件 CAR 熱力圖 — {event_name}", font=dict(color=ACCENT, size=15)),
        height=max(350, len(row_labels) * 30 + 100),
    )
    return fig


# ─── Portfolio Waterfall ──────────────────────────────────────────────────────

def plot_portfolio_waterfall(
    portfolio_result: dict,
    portfolio: dict,
) -> go.Figure:
    """Waterfall chart showing portfolio VaR breakdown by asset."""
    if not portfolio_result or not portfolio:
        return go.Figure()

    contributions = portfolio_result.get("asset_contributions", {})
    expected_return = portfolio_result.get("expected_return", 0.0)

    tickers = list(contributions.keys())
    values = [contributions[t] * 100 for t in tickers]
    total = expected_return * 100

    measure = ["relative"] * len(tickers) + ["total"]
    x_labels = tickers + ["組合總計"]
    y_values = values + [total]

    colors = [
        POSITIVE_COLOR if v >= 0 else NEGATIVE_COLOR for v in y_values
    ]

    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=measure,
            x=x_labels,
            y=y_values,
            text=[f"{v:.2f}%" for v in y_values],
            textposition="outside",
            increasing=dict(marker_color=POSITIVE_COLOR),
            decreasing=dict(marker_color=NEGATIVE_COLOR),
            totals=dict(marker_color=ACCENT),
            connector=dict(line=dict(color=GRID_COLOR, dash="dot")),
        )
    )
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="投資組合壓力測試 — 各資產貢獻瀑布圖", font=dict(color=ACCENT, size=15)),
        yaxis_title="貢獻報酬 (%)",
        height=400,
    )
    return fig


# ─── Event Timeline ───────────────────────────────────────────────────────────

def plot_event_timeline(events: list) -> go.Figure:
    """Timeline scatter plot of historical events by category and magnitude."""
    if not events:
        return go.Figure()

    cat_color_map = {
        "貨幣政策": "#8fa89d",
        "地緣政治": "#b98b81",
        "金融危機": "#a87068",
        "商品衝擊": "#b59b74",
        "科技產業": "#819daf",
        "自然災害": "#9aa287",
    }

    df = pd.DataFrame(events)
    df["date"] = pd.to_datetime(df["date"])
    df["color"] = df["category"].map(cat_color_map).fillna("#aaaaaa")
    df["size"] = df["magnitude"] * 8

    fig = go.Figure()

    for cat, grp in df.groupby("category"):
        fig.add_trace(
            go.Scatter(
                x=grp["date"],
                y=grp["magnitude"],
                mode="markers",
                name=cat,
                marker=dict(
                    size=grp["size"].tolist(),
                    color=cat_color_map.get(cat, "#aaaaaa"),
                    line=dict(width=1, color=TEXT_COLOR),
                    opacity=0.85,
                ),
                text=grp["name_zh"] + "<br>" + grp["date"].dt.strftime("%Y-%m-%d"),
                hoverinfo="text",
            )
        )

    layout = dict(**_LAYOUT_BASE)
    layout["yaxis"] = dict(range=[0.5, 5.5], gridcolor=GRID_COLOR)
    fig.update_layout(
        **layout,
        title=dict(text="歷史金融事件時間軸", font=dict(color=ACCENT, size=16)),
        xaxis_title="日期",
        yaxis_title="事件影響程度 (1-5)",
        legend=dict(
            bgcolor="rgba(13,31,60,0.8)",
            bordercolor=GRID_COLOR,
            font=dict(color=TEXT_COLOR),
        ),
        height=480,
    )
    return fig


# ─── Propagation Cascade (Sankey) ────────────────────────────────────────────

def plot_propagation_cascade(
    network: dict,
    source_asset: str,
    simulation_results: pd.DataFrame,
) -> go.Figure:
    """Sankey diagram showing how impact flows from source to other assets."""
    edges = network.get("edges", [])
    if not edges:
        return go.Figure(layout=dict(**_LAYOUT_BASE, title="無傳導路徑資料"))

    # Filter edges originating from source_asset or passing through
    relevant_edges = [e for e in edges if e["source"] == source_asset]
    if not relevant_edges:
        relevant_edges = edges[:10]  # Fallback: show top edges

    # Build node list
    node_set = []
    node_map = {}
    for e in relevant_edges:
        for n in [e["source"], e["target"]]:
            if n not in node_map:
                node_map[n] = len(node_set)
                node_set.append(n)

    # Build link values from simulation expected returns
    sim_indexed = {}
    if not simulation_results.empty:
        for _, row in simulation_results.iterrows():
            sim_indexed[row["ticker"]] = abs(float(row.get("mean_return", 0.02))) * 100

    link_sources, link_targets, link_values, link_colors = [], [], [], []
    for e in relevant_edges:
        s_idx = node_map.get(e["source"])
        t_idx = node_map.get(e["target"])
        if s_idx is None or t_idx is None:
            continue
        val = sim_indexed.get(e["target"], abs(e.get("weight", 0.5)) * 5)
        link_sources.append(s_idx)
        link_targets.append(t_idx)
        link_values.append(max(0.1, val))
        color = "rgba(255,61,61,0.5)" if e.get("direction") != "positive" else "rgba(0,200,83,0.5)"
        link_colors.append(color)

    node_colors = [ACCENT if n == source_asset else "#5588bb" for n in node_set]

    fig = go.Figure(
        go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                label=node_set,
                color=node_colors,
                line=dict(color=TEXT_COLOR, width=0.5),
            ),
            link=dict(
                source=link_sources,
                target=link_targets,
                value=link_values,
                color=link_colors,
            ),
        )
    )
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(
            text=f"衝擊傳導桑基圖 — 從 {source_asset} 擴散",
            font=dict(color=ACCENT, size=15),
        ),
        height=420,
    )
    return fig
