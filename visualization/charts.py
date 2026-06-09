# visualization/charts.py
# Plotly chart functions for EventScope

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─── Earth-tone color palette ───────────────────────────────────────────────
BG_COLOR = "#F5EFE6"
PAPER_BG = "#FFF9F0"
GRID_COLOR = "#D9C8B3"
TEXT_COLOR = "#2E2922"
ACCENT = "#8A5A3B"
POSITIVE_COLOR = "#6F7F4F"
NEGATIVE_COLOR = "#A45F45"
OCHRE_COLOR = "#B88A45"

_LAYOUT_BASE = dict(
    plot_bgcolor=BG_COLOR,
    paper_bgcolor=PAPER_BG,
    font=dict(color=TEXT_COLOR, family="Avenir Next, PingFang TC, Microsoft JhengHei, sans-serif"),
    xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
    yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
    margin=dict(l=60, r=40, t=60, b=50),
)

CATEGORY_COLORS = {
    "美國股市": "#8A5A3B",
    "台灣股市": "#B88A45",
    "亞洲股市": "#9D7652",
    "歐洲股市": "#7A6D5F",
    "拉丁美洲": "#A45F45",
    "商品": "#7A845D",
    "固定收益": "#8F9A76",
    "外匯": "#71665A",
    "加密貨幣": "#9A694E",
    "新興市場": "#9B8061",
}

EVENT_CATEGORY_COLORS = {
    "貨幣政策": "#7A845D",
    "地緣政治": "#A45F45",
    "金融危機": "#8A5A3B",
    "商品衝擊": "#B88A45",
    "科技產業": "#9B8061",
    "自然災害": "#8F9A76",
}


# ─── Network Chart ───────────────────────────────────────────────────────────

def plot_impact_network(
    network: dict,
    event_name: str,
    asset_info: dict,
) -> go.Figure:
    """
    Readable directed route map showing the strongest contagion paths.
    """
    nodes = network.get("nodes", [])
    edges = network.get("edges", [])
    centrality = network.get("centrality", {})

    if not nodes or not edges:
        fig = go.Figure()
        fig.update_layout(**_LAYOUT_BASE, title="無足夠資料建立網路圖")
        return fig

    top_edges = sorted(edges, key=lambda e: e.get("weight", 0), reverse=True)[:10]
    max_weight = max([float(e.get("weight", 0)) for e in top_edges] + [1.0])
    row_count = len(top_edges)

    fig = go.Figure()
    y_values = list(range(row_count, 0, -1))

    for y, edge in zip(y_values, top_edges):
        src = edge["source"]
        tgt = edge["target"]
        weight = float(edge.get("weight", 0))
        src_info = asset_info.get(src, {})
        tgt_info = asset_info.get(tgt, {})
        src_name = src_info.get("name_zh", src)
        tgt_name = tgt_info.get("name_zh", tgt)
        src_cat = src_info.get("category", "其他")
        tgt_cat = tgt_info.get("category", "其他")
        source_color = CATEGORY_COLORS.get(src_cat, "#9B8061")
        target_color = CATEGORY_COLORS.get(tgt_cat, "#9B8061")
        line_color = OCHRE_COLOR if weight >= 0.55 else ACCENT
        line_width = 2.5 + 7.5 * (weight / max_weight)

        fig.add_trace(
            go.Scatter(
                x=[0.34, 0.66],
                y=[y, y],
                mode="lines",
                line=dict(color=line_color, width=line_width),
                hovertemplate=(
                    f"<b>{src_name} → {tgt_name}</b><br>"
                    f"來源：{src}｜{src_cat}<br>"
                    f"目標：{tgt}｜{tgt_cat}<br>"
                    f"傳導強度：{weight:.2f}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )
        fig.add_annotation(
            x=0.66,
            y=y,
            ax=0.58,
            ay=y,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=3,
            arrowsize=1.1,
            arrowwidth=max(1.4, line_width * 0.55),
            arrowcolor=line_color,
        )
        fig.add_trace(
            go.Scatter(
                x=[0.28],
                y=[y],
                mode="markers",
                marker=dict(size=22, color=source_color, line=dict(width=2, color=PAPER_BG)),
                hovertemplate=f"<b>{src_name}</b><br>{src_cat}<br>中心度：{centrality.get(src, 0):.2f}<extra></extra>",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[0.72],
                y=[y],
                mode="markers",
                marker=dict(size=22, color=target_color, line=dict(width=2, color=PAPER_BG)),
                hovertemplate=f"<b>{tgt_name}</b><br>{tgt_cat}<br>中心度：{centrality.get(tgt, 0):.2f}<extra></extra>",
                showlegend=False,
            )
        )
        fig.add_annotation(
            x=0.04,
            y=y,
            text=(
                f"<b>{src_name}</b><br>"
                f"<span style='font-size:10px;color:#71665A'>{src_cat}｜{src}</span>"
            ),
            xanchor="left",
            yanchor="middle",
            showarrow=False,
            align="left",
            font=dict(size=11, color=TEXT_COLOR),
        )
        fig.add_annotation(
            x=0.96,
            y=y,
            text=(
                f"<b>{tgt_name}</b><br>"
                f"<span style='font-size:10px;color:#71665A'>{tgt_cat}｜{tgt}</span>"
            ),
            xanchor="right",
            yanchor="middle",
            showarrow=False,
            align="right",
            font=dict(size=11, color=TEXT_COLOR),
        )
        fig.add_annotation(
            x=0.50,
            y=y + 0.23,
            text=f"{weight:.2f}",
            showarrow=False,
            font=dict(size=11, color=TEXT_COLOR),
            bgcolor="#FFF4E6",
            bordercolor=GRID_COLOR,
            borderpad=3,
        )

    fig.add_annotation(
        x=0.04,
        y=row_count + 0.95,
        text="<b>來源資產</b>",
        showarrow=False,
        xanchor="left",
        font=dict(size=13, color=ACCENT),
    )
    fig.add_annotation(
        x=0.50,
        y=row_count + 0.95,
        text="<b>傳導強度</b><br><span style='font-size:11px;color:#71665A'>線越粗，模型推估的傳導越強</span>",
        showarrow=False,
        xanchor="center",
        font=dict(size=13, color=ACCENT),
    )
    fig.add_annotation(
        x=0.96,
        y=row_count + 0.95,
        text="<b>受影響資產</b>",
        showarrow=False,
        xanchor="right",
        font=dict(size=13, color=ACCENT),
    )

    net_layout = dict(**_LAYOUT_BASE)
    net_layout["xaxis"] = dict(range=[0, 1], showgrid=False, zeroline=False, showticklabels=False, fixedrange=True)
    net_layout["yaxis"] = dict(range=[0.35, row_count + 1.35], showgrid=False, zeroline=False, showticklabels=False, fixedrange=True)
    net_layout["margin"] = dict(l=28, r=28, t=74, b=28)
    fig.update_layout(
        **net_layout,
        title=dict(text=f"主要傳導路徑 — {event_name}", font=dict(color=ACCENT, size=16)),
        height=max(500, 62 * row_count),
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
        (mean, "期望值", ACCENT),
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


def plot_risk_adjusted_rankings(
    simulation_results: pd.DataFrame,
    asset_info: dict,
) -> go.Figure:
    """Grouped bar chart for Sharpe and Sortino rankings."""
    if simulation_results.empty:
        return go.Figure()

    df = simulation_results.copy()
    df["name_zh"] = df["ticker"].apply(lambda t: asset_info.get(t, {}).get("name_zh", t))
    df = df.sort_values("sortino_ratio", ascending=False).head(8)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df["name_zh"],
            x=df["sharpe_ratio"],
            orientation="h",
            name="Sharpe",
            marker_color=ACCENT,
            hovertemplate="<b>%{y}</b><br>Sharpe: %{x:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            y=df["name_zh"],
            x=df["sortino_ratio"],
            orientation="h",
            name="Sortino",
            marker_color=OCHRE_COLOR,
            hovertemplate="<b>%{y}</b><br>Sortino: %{x:.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="風險調整後報酬排行", font=dict(color=ACCENT, size=16)),
        xaxis_title="比率",
        yaxis_title="",
        barmode="group",
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_taiwan_indicator_panel(indicators: dict) -> go.Figure:
    """Compact dashboard chart for Taiwan-specific metrics."""
    if not indicators:
        return go.Figure()

    labels = ["台灣事件密度", "半導體比重", "政策風險比重", "平均強度"]
    values = [
        indicators.get("event_density_score", 0.0),
        indicators.get("semiconductor_share", 0.0) * 100,
        indicators.get("policy_risk_share", 0.0) * 100,
        indicators.get("avg_magnitude", 0.0) * 20,
    ]
    colors = ["#B88A45", "#8F9A76", "#A45F45", "#9B8061"]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[f"{v:.0f}" for v in values],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>指標分數: %{y:.1f}<extra></extra>",
        )
    )
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="台灣市場專屬指標", font=dict(color=ACCENT, size=16)),
        yaxis_title="指標分數",
        xaxis_title="",
        height=340,
        margin=dict(l=50, r=30, t=60, b=60),
    )
    return fig


def plot_market_snapshot(snapshot_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart for global market pulse."""
    if snapshot_df.empty:
        return go.Figure()

    df = snapshot_df.copy().sort_values("one_week")
    layout = dict(_LAYOUT_BASE, margin=dict(l=70, r=70, t=60, b=45))
    colors = [POSITIVE_COLOR if v >= 0 else NEGATIVE_COLOR for v in df["one_week"]]
    fig = go.Figure(
        go.Bar(
            x=df["one_week"] * 100,
            y=df["name_zh"],
            orientation="h",
            marker_color=colors,
            text=[f"{v:.2f}%" for v in df["one_week"] * 100],
            textposition="auto",
            textfont=dict(size=11, color=TEXT_COLOR),
            cliponaxis=False,
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
        **layout,
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
    z_abs = np.nanpercentile(np.abs(z), 92) if np.isfinite(z).any() else 8
    z_range = max(3.0, min(12.0, float(z_abs)))

    # Truncate long row labels
    row_labels = [str(r)[:35] for r in historical_cars.index]
    col_labels = historical_cars.columns.tolist()

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=col_labels,
            y=row_labels,
            colorscale=[
                [0.0, "#8F3E2F"],
                [0.30, "#D39A85"],
                [0.50, "#FFF8EE"],
                [0.70, "#A8B682"],
                [1.0, "#53663B"],
            ],
            zmin=-z_range,
            zmax=z_range,
            zmid=0,
            text=[[f"{v:.1f}%" for v in row] for row in z],
            texttemplate="%{text}",
            textfont=dict(size=10, color=TEXT_COLOR),
            hovertemplate="事件: %{y}<br>資產: %{x}<br>CAR: %{z:.2f}%<extra></extra>",
            colorbar=dict(
                title=dict(text="CAR (%)", font=dict(color=TEXT_COLOR)),
                tickfont=dict(color=TEXT_COLOR),
                ticksuffix="%",
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
    fig.add_annotation(
        x=0,
        y=1.08,
        xref="paper",
        yref="paper",
        text=(
            "<b>讀法：</b>紅色代表該事件下資產累積異常報酬（CAR）偏負，"
            "綠色代表偏正，米白接近 0。顏色越深，偏離越大。"
        ),
        showarrow=False,
        align="left",
        font=dict(size=12, color="#4B4036"),
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
        "貨幣政策": "#7A845D",
        "地緣政治": "#A45F45",
        "金融危機": "#8A5A3B",
        "商品衝擊": "#B88A45",
        "科技產業": "#9B8061",
        "自然災害": "#8F9A76",
    }

    df = pd.DataFrame(events)
    df["date"] = pd.to_datetime(df["date"])
    df["color"] = df["category"].map(cat_color_map).fillna("#9B8061")
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
                    color=cat_color_map.get(cat, "#9B8061"),
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
            bgcolor="rgba(255,255,255,0.86)",
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
    asset_info: dict | None = None,
) -> go.Figure:
    """Sankey diagram showing how impact flows from source to other assets."""
    asset_info = asset_info or {}
    edges = network.get("edges", [])
    if not edges:
        return go.Figure(layout=dict(**_LAYOUT_BASE, title="無傳導路徑資料"))

    sorted_edges = sorted(edges, key=lambda e: e.get("weight", 0), reverse=True)
    direct_edges = [e for e in sorted_edges if e["source"] == source_asset][:6]
    direct_targets = {e["target"] for e in direct_edges}
    second_hop_edges = [
        e for e in sorted_edges
        if e["source"] in direct_targets and e["target"] != source_asset
    ][:5]
    relevant_edges = direct_edges + second_hop_edges
    if not relevant_edges:
        direct_edges = sorted_edges[:6]
        if direct_edges:
            source_asset = direct_edges[0]["source"]
        direct_targets = {e["target"] for e in direct_edges}
        second_hop_edges = []
        relevant_edges = direct_edges

    node_set = []
    node_map = {}
    for edge in relevant_edges:
        for ticker in [edge["source"], edge["target"]]:
            if ticker not in node_map:
                node_map[ticker] = len(node_set)
                node_set.append(ticker)

    sim_indexed: dict[str, float] = {}
    if not simulation_results.empty:
        for _, row in simulation_results.iterrows():
            sim_indexed[row["ticker"]] = float(row.get("mean_return", 0.0))

    def asset_name(ticker: str) -> str:
        return asset_info.get(ticker, {}).get("name_zh", ticker)

    def asset_category(ticker: str) -> str:
        return asset_info.get(ticker, {}).get("category", "其他")

    def short_label(ticker: str) -> str:
        name = asset_name(ticker)
        if len(name) > 6:
            name = name[:6] + "..."
        return f"{name} ({ticker})"

    def hover_label(ticker: str) -> str:
        impact = sim_indexed.get(ticker)
        impact_text = "來源資產" if ticker == source_asset else ("n/a" if impact is None else f"{impact:+.2%}")
        return f"{asset_name(ticker)}<br>{asset_category(ticker)}｜{ticker}<br>預期報酬：{impact_text}"

    def node_color(ticker: str) -> str:
        if ticker == source_asset:
            return ACCENT
        return CATEGORY_COLORS.get(asset_category(ticker), "#9B8061")

    def link_color(target: str) -> str:
        impact = sim_indexed.get(target, 0.0)
        if impact > 0.0005:
            return "rgba(111,127,79,0.66)"
        if impact < -0.0005:
            return "rgba(164,95,69,0.62)"
        return "rgba(138,90,59,0.46)"

    link_sources, link_targets, link_values, link_colors, link_labels = [], [], [], [], []
    for edge in relevant_edges:
        source_idx = node_map.get(edge["source"])
        target_idx = node_map.get(edge["target"])
        if source_idx is None or target_idx is None:
            continue
        weight = abs(float(edge.get("weight", 0.5)))
        target_impact = abs(sim_indexed.get(edge["target"], 0.0)) * 100
        link_sources.append(source_idx)
        link_targets.append(target_idx)
        link_values.append(max(0.2, weight * 3.2 + target_impact * 0.65))
        link_colors.append(link_color(edge["target"]))
        link_labels.append(
            f"{asset_name(edge['source'])} → {asset_name(edge['target'])}<br>"
            f"傳導強度：{weight:.2f}<br>"
            f"目標預期報酬：{sim_indexed.get(edge['target'], 0.0):+.2%}"
        )

    node_labels = [short_label(ticker) for ticker in node_set]
    node_colors = [node_color(ticker) for ticker in node_set]
    node_hover = [hover_label(ticker) for ticker in node_set]

    def node_layer(ticker: str) -> float:
        if ticker == source_asset:
            return 0.02
        if ticker in direct_targets:
            return 0.46
        return 0.82

    buckets: dict[float, list[str]] = {}
    for ticker in node_set:
        buckets.setdefault(node_layer(ticker), []).append(ticker)

    node_x, node_y = [], []
    for ticker in node_set:
        layer = node_layer(ticker)
        bucket = buckets[layer]
        index = bucket.index(ticker)
        y = 0.50 if len(bucket) == 1 else 0.08 + index * (0.84 / (len(bucket) - 1))
        node_x.append(layer)
        node_y.append(y)

    fig = go.Figure(
        go.Sankey(
            arrangement="fixed",
            textfont=dict(size=15, color=TEXT_COLOR, family="Microsoft JhengHei, PingFang TC, Arial, sans-serif"),
            node=dict(
                pad=26,
                thickness=26,
                label=node_labels,
                color=node_colors,
                customdata=node_hover,
                line=dict(color=TEXT_COLOR, width=0.7),
                x=node_x,
                y=node_y,
                hovertemplate="%{customdata}<extra></extra>",
            ),
            link=dict(
                source=link_sources,
                target=link_targets,
                value=link_values,
                color=link_colors,
                customdata=link_labels,
                hovertemplate="%{customdata}<extra></extra>",
            ),
        )
    )

    fig.add_annotation(
        x=0.0,
        y=1.08,
        xref="paper",
        yref="paper",
        text=(
            "<b>讀法：</b>左邊是事件衝擊來源，中間是直接受影響資產，右邊是二次傳導。 "
            "線越粗代表傳導越強；綠線偏正向、紅線偏負向、棕線接近中性。"
        ),
        showarrow=False,
        align="left",
        font=dict(size=13, color="#4B4036"),
    )
    for x, title in [(0.02, "衝擊來源"), (0.46, "直接受影響"), (0.82, "二次傳導")]:
        fig.add_annotation(
            x=x,
            y=1.0,
            xref="paper",
            yref="paper",
            text=f"<b>{title}</b>",
            showarrow=False,
            font=dict(size=14, color=ACCENT),
        )

    sankey_layout = dict(**_LAYOUT_BASE)
    sankey_layout["margin"] = dict(l=34, r=120, t=118, b=42)
    fig.update_layout(
        **sankey_layout,
        title=dict(
            text=f"衝擊傳導桑基圖 — 從 {asset_name(source_asset)} 擴散",
            font=dict(color=ACCENT, size=16),
        ),
        height=620,
    )
    return fig
