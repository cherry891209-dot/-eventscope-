# portfolio/stress_test.py
# Portfolio stress testing utilities

import re
import numpy as np
import pandas as pd

DEFAULT_PORTFOLIO = {
    "^GSPC": 0.30,    # S&P 500
    "^IXIC": 0.20,    # Nasdaq
    "^TWII": 0.20,    # Taiwan Stock
    "GLD": 0.15,      # Gold
    "BTC-USD": 0.10,  # Bitcoin
    "^TNX": 0.05,     # 10Y Treasury
}

# Known valid tickers (from ASSET_UNIVERSE + common ones)
VALID_TICKERS = {
    "^GSPC", "^IXIC", "^TWII", "2330.TW", "GLD", "GC=F",
    "CL=F", "^TNX", "^DXY", "BTC-USD", "ETH-USD", "EEM",
    # Additional common tickers
    "AAPL", "TSLA", "MSFT", "AMZN", "NVDA", "GOOG", "META",
    "SPY", "QQQ", "IEF", "TLT", "USO", "IAU",
}

# Hedging suggestions by event category
HEDGE_CATALOG = {
    "金融危機": [
        {"asset": "GLD",    "reason_zh": "黃金在金融危機中通常作為避險資產升值", "expected_return": 0.04, "hedge_effectiveness": 0.75},
        {"asset": "^TNX",   "reason_zh": "美國國債殖利率下跌（債券價格上漲）提供保護", "expected_return": 0.03, "hedge_effectiveness": 0.70},
        {"asset": "^DXY",   "reason_zh": "美元指數在危機時期往往升值（避險貨幣）", "expected_return": 0.02, "hedge_effectiveness": 0.60},
    ],
    "地緣政治": [
        {"asset": "GLD",    "reason_zh": "黃金在地緣政治緊張時期為傳統避險資產", "expected_return": 0.03, "hedge_effectiveness": 0.70},
        {"asset": "CL=F",   "reason_zh": "能源衝突往往推升油價，原油可作對沖", "expected_return": 0.05, "hedge_effectiveness": 0.65},
        {"asset": "^DXY",   "reason_zh": "美元在不確定性上升時獲得避險買盤", "expected_return": 0.01, "hedge_effectiveness": 0.55},
    ],
    "貨幣政策": [
        {"asset": "GLD",    "reason_zh": "升息週期中通脹預期下降，金價短期承壓但長期保值", "expected_return": -0.01, "hedge_effectiveness": 0.40},
        {"asset": "^DXY",   "reason_zh": "升息通常推升美元指數，可作外匯對沖", "expected_return": 0.02, "hedge_effectiveness": 0.65},
        {"asset": "EEM",    "reason_zh": "新興市場在升息時期受壓，可透過反向ETF對沖", "expected_return": -0.04, "hedge_effectiveness": 0.60},
    ],
    "商品衝擊": [
        {"asset": "CL=F",   "reason_zh": "直接持有原油期貨可對沖能源價格上漲風險", "expected_return": 0.08, "hedge_effectiveness": 0.80},
        {"asset": "GC=F",   "reason_zh": "黃金期貨在通膨衝擊中保值效果佳", "expected_return": 0.04, "hedge_effectiveness": 0.70},
        {"asset": "^DXY",   "reason_zh": "商品以美元計價，美元走強可抵銷部分成本上漲", "expected_return": 0.02, "hedge_effectiveness": 0.50},
    ],
    "科技產業": [
        {"asset": "GLD",    "reason_zh": "科技股大幅波動時，黃金提供穩定錨定效果", "expected_return": 0.02, "hedge_effectiveness": 0.55},
        {"asset": "^TNX",   "reason_zh": "科技股下跌時資金轉入債市，降低組合波動", "expected_return": 0.02, "hedge_effectiveness": 0.50},
        {"asset": "^DXY",   "reason_zh": "美元升值部分緩衝科技股損失", "expected_return": 0.01, "hedge_effectiveness": 0.40},
    ],
    "自然災害": [
        {"asset": "GLD",    "reason_zh": "災害引發不確定性，黃金提供避險功能", "expected_return": 0.02, "hedge_effectiveness": 0.60},
        {"asset": "CL=F",   "reason_zh": "供應鏈中斷往往推升能源價格", "expected_return": 0.03, "hedge_effectiveness": 0.55},
        {"asset": "^TNX",   "reason_zh": "央行寬鬆應對災害，債券受益", "expected_return": 0.01, "hedge_effectiveness": 0.45},
    ],
}


def parse_portfolio_input(text: str) -> dict:
    """
    Parse user text input like 'AAPL:30%, TSLA:20%, GLD:50%' into dict.
    Supports formats such as:
    - TICKER:30%
    - TICKER=30%
    - TICKER 30%
    - TICKER:0.30
    - TICKER 0.30
    Returns {ticker: weight} with weights as fractions (0-1).
    """
    portfolio = {}
    if not text:
        return portfolio

    # Accept comma-separated or line-separated entries.
    chunks = [chunk.strip() for chunk in re.split(r"[\n,]+", text) if chunk.strip()]
    pattern = re.compile(
        r"^\s*([A-Z0-9\^\.=\-]+)\s*(?::|=|\s)\s*(-?\d+(?:\.\d+)?)\s*(%)?\s*$",
        re.IGNORECASE,
    )

    for chunk in chunks:
        match = pattern.match(chunk)
        if not match:
            continue

        ticker = match.group(1).upper()
        raw_value = float(match.group(2))
        has_percent = bool(match.group(3))

        # Treat values <= 1 as decimal weights unless explicitly marked as percent.
        if has_percent:
            weight = raw_value / 100.0
        else:
            weight = raw_value if abs(raw_value) <= 1 else raw_value / 100.0

        portfolio[ticker] = weight

    return portfolio


def validate_portfolio(portfolio: dict) -> tuple:
    """
    Validate portfolio weights.
    Returns (is_valid: bool, message: str).
    """
    if not portfolio:
        return False, "投資組合為空，請輸入資產配置。"

    invalid_tickers = [ticker for ticker in portfolio if ticker not in VALID_TICKERS]
    if invalid_tickers:
        return False, f"以下資產代碼不支援：{', '.join(invalid_tickers)}。請使用平台支援的 ticker。"

    total_weight = sum(portfolio.values())

    if abs(total_weight - 1.0) > 0.02:
        return (
            False,
            f"權重總和為 {total_weight:.1%}，請確保總和為 100%（目前差距 {abs(total_weight-1)*100:.1f}%）。",
        )

    negative_weights = [t for t, w in portfolio.items() if w < 0]
    if negative_weights:
        return False, f"以下資產權重為負數：{', '.join(negative_weights)}。請輸入正數權重。"

    return True, f"✓ 投資組合有效 — {len(portfolio)} 個資產，總權重 {total_weight:.1%}"


def get_hedge_suggestions(
    portfolio: dict,
    simulation_results: pd.DataFrame,
    event_category: str,
) -> list:
    """
    Suggest hedging instruments based on portfolio and event type.
    Returns list of dicts: {asset, reason_zh, expected_return, hedge_effectiveness}.
    """
    suggestions = HEDGE_CATALOG.get(event_category, HEDGE_CATALOG["金融危機"])

    # Filter out assets already in portfolio
    existing_tickers = set(portfolio.keys())

    # Adjust expected returns based on simulation results if available
    enhanced = []
    sim_map = {}
    if not simulation_results.empty:
        for _, row in simulation_results.iterrows():
            sim_map[row["ticker"]] = float(row.get("mean_return", 0.0))

    for sug in suggestions:
        asset = sug["asset"]
        s = sug.copy()

        if asset in sim_map:
            # Use simulation result if positive (hedge is working)
            sim_return = sim_map[asset]
            if sim_return > 0:
                s["expected_return"] = round(sim_return, 4)
                s["hedge_effectiveness"] = min(0.95, sug["hedge_effectiveness"] + 0.1)

        s["already_in_portfolio"] = asset in existing_tickers
        enhanced.append(s)

    # Sort by hedge effectiveness descending
    enhanced.sort(key=lambda x: x["hedge_effectiveness"], reverse=True)
    return enhanced
