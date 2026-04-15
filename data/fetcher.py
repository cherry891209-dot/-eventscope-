# data/fetcher.py
# Data fetching module for EventScope

import warnings
warnings.filterwarnings("ignore")

import contextlib
import io
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional

from data.events_db import ASSET_UNIVERSE

DEFAULT_TICKERS = list(ASSET_UNIVERSE.keys())
_YFINANCE_DISABLED = False
_COINGECKO_DISABLED = False

# ---------------------------------------------------------------------------
# Synthetic data helpers (fallback when APIs are unavailable)
# ---------------------------------------------------------------------------

# Known stylised return impacts by event category and primary shock
SYNTHETIC_PATTERNS = {
    "金融危機": {
        "^GSPC": -0.08, "^IXIC": -0.12, "^TWII": -0.07, "2330.TW": -0.10,
        "GLD": 0.04,   "GC=F": 0.04,   "CL=F": -0.05, "^TNX": -0.03,
        "^DXY": 0.02,  "BTC-USD": -0.15, "ETH-USD": -0.18, "EEM": -0.10,
    },
    "地緣政治": {
        "^GSPC": -0.04, "^IXIC": -0.05, "^TWII": -0.03, "2330.TW": -0.04,
        "GLD": 0.03,   "GC=F": 0.03,   "CL=F": 0.06,  "^TNX": -0.02,
        "^DXY": 0.01,  "BTC-USD": -0.05, "ETH-USD": -0.06, "EEM": -0.05,
    },
    "貨幣政策": {
        "^GSPC": -0.03, "^IXIC": -0.05, "^TWII": -0.02, "2330.TW": -0.04,
        "GLD": -0.01,  "GC=F": -0.01,  "CL=F": -0.02, "^TNX": 0.05,
        "^DXY": 0.02,  "BTC-USD": -0.06, "ETH-USD": -0.07, "EEM": -0.04,
    },
    "商品衝擊": {
        "^GSPC": -0.02, "^IXIC": -0.02, "^TWII": -0.02, "2330.TW": -0.01,
        "GLD": 0.05,   "GC=F": 0.05,   "CL=F": 0.10,  "^TNX": -0.01,
        "^DXY": 0.01,  "BTC-USD": -0.03, "ETH-USD": -0.03, "EEM": -0.03,
    },
    "科技產業": {
        "^GSPC": -0.03, "^IXIC": -0.08, "^TWII": -0.05, "2330.TW": -0.07,
        "GLD": 0.01,   "GC=F": 0.01,   "CL=F": 0.00,  "^TNX": -0.01,
        "^DXY": 0.01,  "BTC-USD": -0.12, "ETH-USD": -0.14, "EEM": -0.03,
    },
    "自然災害": {
        "^GSPC": -0.02, "^IXIC": -0.02, "^TWII": -0.05, "2330.TW": -0.06,
        "GLD": 0.02,   "GC=F": 0.02,   "CL=F": 0.03,  "^TNX": -0.01,
        "^DXY": 0.01,  "BTC-USD": -0.04, "ETH-USD": -0.05, "EEM": -0.04,
    },
}


def _generate_synthetic_prices(
    tickers: list,
    start: str,
    end: str,
    event_date: Optional[str] = None,
    category: Optional[str] = None,
) -> pd.DataFrame:
    """
    Generate synthetic but plausible price series.
    If event_date and category are given, embed a shock around that date.
    """
    dates = pd.bdate_range(start=start, end=end)
    if len(dates) == 0:
        dates = pd.bdate_range(start=start, periods=300)

    rng = np.random.default_rng(seed=42)
    base_prices = {
        "^GSPC": 4500.0, "^IXIC": 14000.0, "^TWII": 17000.0,
        "2330.TW": 600.0, "GLD": 185.0, "GC=F": 1900.0,
        "CL=F": 80.0, "^TNX": 4.0, "^DXY": 104.0,
        "BTC-USD": 40000.0, "ETH-USD": 2200.0, "EEM": 38.0,
    }

    shock_pattern = SYNTHETIC_PATTERNS.get(category, SYNTHETIC_PATTERNS["金融危機"]) if category else {}

    data = {}
    for ticker in tickers:
        if ticker not in base_prices:
            base_prices[ticker] = 100.0
        price = base_prices[ticker]
        prices = []
        event_idx = None
        if event_date:
            try:
                ed = pd.Timestamp(event_date)
                diffs = [(abs((d - ed).days), i) for i, d in enumerate(dates)]
                event_idx = min(diffs, key=lambda x: x[0])[1]
            except Exception:
                event_idx = None

        for i, _ in enumerate(dates):
            daily_vol = 0.01 if "^TNX" not in ticker else 0.005
            drift = rng.normal(0.0002, daily_vol)
            price = price * (1 + drift)

            # Apply shock
            if event_idx is not None and (0 <= i - event_idx <= 3):
                shock = shock_pattern.get(ticker, -0.02)
                price = price * (1 + shock / 4)  # spread shock over ~4 days

            prices.append(price)

        data[ticker] = prices

    df = pd.DataFrame(data, index=dates)
    return df


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_price_data(tickers: list, start: str, end: str) -> pd.DataFrame:
    """
    Fetch daily adjusted close prices for multiple tickers using yfinance.
    Falls back to synthetic data if yfinance is unavailable or fails.
    """
    global _YFINANCE_DISABLED

    if _YFINANCE_DISABLED:
        return _generate_synthetic_prices(tickers, start, end)

    try:
        import yfinance as yf
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            raw = yf.download(
                tickers,
                start=start,
                end=end,
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        if raw.empty:
            raise ValueError("Empty response from yfinance")

        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"] if "Close" in raw.columns.get_level_values(0) else raw.iloc[:, :len(tickers)]
        else:
            close = raw[["Close"]] if "Close" in raw.columns else raw

        # Reindex to requested tickers, fill missing with NaN
        if len(tickers) == 1:
            close.columns = tickers
        close = close.reindex(columns=tickers)
        close = close.dropna(how="all")
        if close.empty:
            raise ValueError("All tickers returned NaN")
        return close

    except Exception:
        _YFINANCE_DISABLED = True
        return _generate_synthetic_prices(tickers, start, end)


def fetch_event_window_data(
    ticker: str,
    event_date: str,
    pre_days: int = 250,
    post_days: int = 60,
) -> pd.DataFrame:
    """
    Fetch OHLCV data for a specific asset around an event date.
    Returns a DataFrame with standard OHLCV columns.
    """
    try:
        ed = datetime.strptime(event_date, "%Y-%m-%d")
    except ValueError:
        ed = datetime.now()

    start = (ed - timedelta(days=int(pre_days * 1.5))).strftime("%Y-%m-%d")
    end = (ed + timedelta(days=int(post_days * 1.5))).strftime("%Y-%m-%d")

    global _YFINANCE_DISABLED

    if _YFINANCE_DISABLED:
        raise RuntimeError("yfinance disabled for current session")

    try:
        import yfinance as yf
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
        if df.empty:
            raise ValueError("Empty yfinance response")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        _YFINANCE_DISABLED = True
        # Synthetic OHLCV
        dates = pd.bdate_range(start=start, end=end)
        rng = np.random.default_rng(42)
        prices = _generate_synthetic_prices([ticker], start, end, event_date=event_date)
        close = prices[ticker].values if ticker in prices.columns else prices.iloc[:, 0].values
        high = close * (1 + rng.uniform(0, 0.01, len(close)))
        low = close * (1 - rng.uniform(0, 0.01, len(close)))
        open_ = close * (1 + rng.normal(0, 0.005, len(close)))
        vol = rng.integers(1_000_000, 10_000_000, len(close)).astype(float)
        return pd.DataFrame(
            {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": vol},
            index=dates,
        )


def fetch_macro_data_fred(series_ids: list) -> pd.DataFrame:
    """
    Fetch macro indicator data from FRED.
    If FRED API key not set or fredapi unavailable, returns empty DataFrame gracefully.
    """
    try:
        import os
        from fredapi import Fred

        api_key = os.environ.get("FRED_API_KEY", "")
        if not api_key:
            return pd.DataFrame()

        fred = Fred(api_key=api_key)
        frames = {}
        for sid in series_ids:
            try:
                s = fred.get_series(sid)
                frames[sid] = s
            except Exception:
                frames[sid] = pd.Series(dtype=float)

        if not frames:
            return pd.DataFrame()

        df = pd.DataFrame(frames)
        df.index = pd.to_datetime(df.index)
        return df.sort_index()

    except Exception:
        return pd.DataFrame()


def get_crypto_data(symbol: str, start: str, end: str) -> pd.DataFrame:
    """
    Fetch crypto OHLCV from CoinGecko free API.
    Falls back to yfinance then synthetic.
    symbol: 'bitcoin' or 'ethereum'
    """
    # Map symbol → yfinance ticker
    yf_map = {"bitcoin": "BTC-USD", "ethereum": "ETH-USD"}
    yf_ticker = yf_map.get(symbol.lower(), symbol.upper() + "-USD")

    global _YFINANCE_DISABLED, _COINGECKO_DISABLED

    if not _YFINANCE_DISABLED:
        try:
            import yfinance as yf
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                df = yf.download(yf_ticker, start=start, end=end, auto_adjust=True, progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return df[["Close"]].rename(columns={"Close": "close"})
        except Exception:
            _YFINANCE_DISABLED = True

    if _COINGECKO_DISABLED:
        prices = _generate_synthetic_prices([yf_ticker], start, end)
        return prices[[yf_ticker]].rename(columns={yf_ticker: "close"})

    try:
        import yfinance as yf
        import requests
        cg_id = symbol.lower()
        url = (
            f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart/range"
        )
        start_ts = int(datetime.strptime(start, "%Y-%m-%d").timestamp())
        end_ts = int(datetime.strptime(end, "%Y-%m-%d").timestamp())
        resp = requests.get(url, params={"vs_currency": "usd", "from": start_ts, "to": end_ts}, timeout=10)
        if resp.status_code == 200:
            prices = resp.json().get("prices", [])
            if prices:
                df = pd.DataFrame(prices, columns=["timestamp", "close"])
                df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
                df.set_index("date", inplace=True)
                return df[["close"]]
    except Exception:
        _COINGECKO_DISABLED = True

    # Synthetic fallback
    prices = _generate_synthetic_prices([yf_ticker], start, end)
    return prices[[yf_ticker]].rename(columns={yf_ticker: "close"})


def build_returns_matrix(
    event_date: str,
    tickers: list = None,
    estimation_window: int = 250,
    event_window_pre: int = 5,
    event_window_post: int = 20,
    event_category: str = None,
) -> dict:
    """
    Build a complete returns matrix around an event.
    Returns a dict containing:
        'prices'             : full price DataFrame
        'returns'            : full daily-return DataFrame
        'estimation_returns' : returns in the estimation window
        'event_returns'      : returns in the event window
        'event_date'         : event date string
    """
    if tickers is None:
        tickers = DEFAULT_TICKERS

    try:
        ed = datetime.strptime(event_date, "%Y-%m-%d")
    except ValueError:
        ed = datetime.now()

    # Total fetch window: estimation window + buffer + event window
    total_back = int(estimation_window * 1.5) + event_window_pre + 30
    total_fwd = event_window_post + 30
    start_str = (ed - timedelta(days=total_back)).strftime("%Y-%m-%d")
    end_str = (ed + timedelta(days=total_fwd)).strftime("%Y-%m-%d")

    try:
        prices = fetch_price_data(tickers, start_str, end_str)
    except Exception:
        prices = _generate_synthetic_prices(tickers, start_str, end_str, event_date, event_category)

    if prices.empty:
        prices = _generate_synthetic_prices(tickers, start_str, end_str, event_date, event_category)

    # Fill forward, drop all-NaN rows
    prices = prices.ffill().dropna(how="all")

    returns = prices.pct_change().dropna(how="all")

    # Locate event date in index
    event_ts = pd.Timestamp(event_date)
    idx_array = returns.index.to_numpy()
    # Find the nearest trading day to event_date
    diffs = np.abs(returns.index - event_ts)
    if len(diffs) == 0:
        # Fallback synthetic
        prices = _generate_synthetic_prices(tickers, start_str, end_str, event_date, event_category)
        returns = prices.pct_change().dropna(how="all")
        diffs = np.abs(returns.index - event_ts)

    event_loc = diffs.argmin()

    est_start = max(0, event_loc - event_window_pre - estimation_window)
    est_end = max(0, event_loc - event_window_pre)
    ev_start = max(0, event_loc - event_window_pre)
    ev_end = min(len(returns), event_loc + event_window_post + 1)

    estimation_returns = returns.iloc[est_start:est_end]
    event_returns = returns.iloc[ev_start:ev_end]

    return {
        "prices": prices,
        "returns": returns,
        "estimation_returns": estimation_returns,
        "event_returns": event_returns,
        "event_date": event_date,
        "event_loc": event_loc,
    }
