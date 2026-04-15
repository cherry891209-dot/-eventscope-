# analysis/event_study.py
# Event Study: Market Model, Abnormal Returns, CAR

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats


def estimate_market_model(
    asset_returns: pd.Series,
    market_returns: pd.Series,
) -> dict:
    """
    OLS regression: R_i = alpha + beta * R_m + epsilon
    Returns dict with alpha, beta, r_squared, residual_std.
    """
    # Align series
    aligned = pd.concat([asset_returns, market_returns], axis=1).dropna()
    if aligned.shape[0] < 10:
        # Not enough data – return zeroed result
        return {"alpha": 0.0, "beta": 1.0, "r_squared": 0.0, "residual_std": 0.01}

    y = aligned.iloc[:, 0].values
    x = aligned.iloc[:, 1].values

    # Add intercept
    X = np.column_stack([np.ones(len(x)), x])
    try:
        beta_hat, residuals, rank, sv = np.linalg.lstsq(X, y, rcond=None)
    except np.linalg.LinAlgError:
        return {"alpha": 0.0, "beta": 1.0, "r_squared": 0.0, "residual_std": 0.01}

    alpha, beta = float(beta_hat[0]), float(beta_hat[1])
    y_pred = X @ beta_hat
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
    residual_std = float(np.sqrt(ss_res / max(1, len(y) - 2)))

    return {
        "alpha": alpha,
        "beta": beta,
        "r_squared": max(0.0, r_squared),
        "residual_std": residual_std,
    }


def calculate_abnormal_returns(
    asset_returns: pd.Series,
    market_returns: pd.Series,
    alpha: float,
    beta: float,
) -> pd.Series:
    """
    AR_t = R_i_t - (alpha + beta * R_m_t)
    """
    aligned = pd.concat([asset_returns, market_returns], axis=1).dropna()
    if aligned.empty:
        return pd.Series(dtype=float)

    r_i = aligned.iloc[:, 0]
    r_m = aligned.iloc[:, 1]
    expected = alpha + beta * r_m
    ar = r_i - expected
    ar.name = asset_returns.name
    return ar


def calculate_car(
    abnormal_returns: pd.Series,
    window_start: int = -1,
    window_end: int = 5,
) -> float:
    """
    Cumulative Abnormal Return over [window_start, window_end] relative to event.
    Assumes abnormal_returns is already sliced to the event window.
    """
    if abnormal_returns.empty:
        return 0.0

    n = len(abnormal_returns)
    # Determine the event day index (0-based centre)
    centre = abs(window_start)
    start_idx = max(0, centre + window_start)
    end_idx = min(n, centre + window_end + 1)

    sub = abnormal_returns.iloc[start_idx:end_idx]
    return float(sub.sum())


def run_event_study(
    returns_matrix: pd.DataFrame,
    event_date: str,
    estimation_window: int = 250,
    event_window: tuple = (-1, 10),
    market_ticker: str = "^GSPC",
) -> pd.DataFrame:
    """
    Full event study for all assets in returns_matrix.
    Returns DataFrame with columns:
        ticker, alpha, beta, r_squared, residual_std,
        CAR, t_stat, p_value, is_significant
    """
    results = []

    if market_ticker not in returns_matrix.columns:
        # Use first column as market proxy
        market_ticker = returns_matrix.columns[0]

    # Locate event day in returns index
    event_ts = pd.Timestamp(event_date)
    diffs = np.abs(returns_matrix.index - event_ts)
    if len(diffs) == 0:
        return pd.DataFrame()

    event_loc = int(diffs.argmin())
    pre = abs(event_window[0])
    post = event_window[1]

    # Estimation window slice (before event)
    est_start = max(0, event_loc - pre - estimation_window)
    est_end = max(0, event_loc - pre)
    estimation_rets = returns_matrix.iloc[est_start:est_end]

    # Event window slice
    ev_start = max(0, event_loc - pre)
    ev_end = min(len(returns_matrix), event_loc + post + 1)
    event_rets = returns_matrix.iloc[ev_start:ev_end]

    for ticker in returns_matrix.columns:
        asset_est = estimation_rets.get(ticker, pd.Series(dtype=float))
        asset_ev = event_rets.get(ticker, pd.Series(dtype=float))

        benchmark_ticker = market_ticker
        if ticker == market_ticker:
            alt_candidates = [col for col in returns_matrix.columns if col != ticker]
            if alt_candidates:
                benchmark_ticker = alt_candidates[0]

        market_est = estimation_rets.get(benchmark_ticker, pd.Series(dtype=float))
        market_ev = event_rets.get(benchmark_ticker, pd.Series(dtype=float))

        model = estimate_market_model(asset_est, market_est)
        alpha, beta = model["alpha"], model["beta"]
        residual_std = model["residual_std"]

        ar = calculate_abnormal_returns(asset_ev, market_ev, alpha, beta)
        car = float(ar.sum()) if not ar.empty else 0.0

        # t-statistic: CAR / (residual_std * sqrt(n_event))
        n_event = max(1, len(ar))
        se_car = residual_std * np.sqrt(n_event)
        t_stat = car / se_car if se_car > 0 else 0.0
        df_est = max(1, len(estimation_rets) - 2)
        p_value = float(2 * (1 - stats.t.cdf(abs(t_stat), df=df_est)))

        results.append(
            {
                "ticker": ticker,
                "alpha": round(alpha, 6),
                "beta": round(beta, 4),
                "r_squared": round(model["r_squared"], 4),
                "residual_std": round(residual_std, 6),
                "CAR": round(car, 6),
                "t_stat": round(t_stat, 4),
                "p_value": round(p_value, 4),
                "is_significant": p_value < 0.10,
            }
        )

    return pd.DataFrame(results)


def calculate_historical_cars(
    event: dict,
    similar_events: list,
    tickers: list,
) -> pd.DataFrame:
    """
    Calculate CARs for a list of similar historical events.
    Returns DataFrame: events (rows) × tickers (columns).
    Uses synthetic/stylized data when real fetch is too slow.
    """
    from data.fetcher import build_returns_matrix

    all_events = [event] + similar_events
    rows = []
    row_labels = []

    for ev in all_events:
        try:
            matrix_data = build_returns_matrix(
                ev["date"],
                tickers=tickers,
                estimation_window=120,
                event_window_pre=1,
                event_window_post=10,
                event_category=ev.get("category"),
            )
            study = run_event_study(
                matrix_data["returns"],
                ev["date"],
                estimation_window=120,
                event_window=(-1, 10),
            )
            if study.empty:
                raise ValueError("Empty event study")
            car_row = study.set_index("ticker")["CAR"].reindex(tickers).fillna(0.0)
        except Exception:
            # Stylised synthetic fallback
            from data.fetcher import SYNTHETIC_PATTERNS
            pattern = SYNTHETIC_PATTERNS.get(ev.get("category", "金融危機"), {})
            intensity = ev.get("magnitude", 3.0) / 3.0
            car_row = pd.Series(
                {t: pattern.get(t, -0.02) * intensity for t in tickers}
            )

        rows.append(car_row.values)
        row_labels.append(f"{ev['date']} {ev['name_zh']}")

    df = pd.DataFrame(rows, index=row_labels, columns=tickers)
    return df
