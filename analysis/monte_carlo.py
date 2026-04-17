# analysis/monte_carlo.py
# Monte Carlo simulation for event impact assessment

import numpy as np
import pandas as pd
from scipy import stats


def _safe_sharpe(mean_return: float, std_return: float, risk_free_rate: float = 0.0) -> float:
    """Return Sharpe ratio with a zero-safe denominator."""
    if std_return <= 1e-12:
        return 0.0
    return float((mean_return - risk_free_rate) / std_return)


def _safe_sortino(simulated: np.ndarray, risk_free_rate: float = 0.0) -> float:
    """Return Sortino ratio using downside deviation."""
    if simulated.size == 0:
        return 0.0
    excess = simulated - risk_free_rate
    downside = excess[excess < 0]
    downside_dev = float(np.sqrt(np.mean(np.square(downside)))) if downside.size else 0.0
    if downside_dev <= 1e-12:
        return 0.0
    return float(np.mean(excess) / downside_dev)


def _max_drawdown(simulated: np.ndarray) -> float:
    """Approximate max drawdown from a cumulative pseudo-path."""
    if simulated.size == 0:
        return 0.0
    wealth = np.cumprod(1 + simulated)
    running_peak = np.maximum.accumulate(wealth)
    drawdowns = wealth / np.maximum(running_peak, 1e-12) - 1
    return float(np.min(drawdowns))


def _safe_calmar(mean_return: float, max_drawdown: float) -> float:
    """Return Calmar ratio with a zero-safe denominator."""
    if abs(max_drawdown) <= 1e-12:
        return 0.0
    return float(mean_return / abs(max_drawdown))


def _profit_loss_ratio(simulated: np.ndarray) -> float:
    """Average positive outcome divided by average absolute loss."""
    wins = simulated[simulated > 0]
    losses = simulated[simulated < 0]
    if wins.size == 0 or losses.size == 0:
        return 0.0
    avg_loss = abs(float(np.mean(losses)))
    if avg_loss <= 1e-12:
        return 0.0
    return float(np.mean(wins) / avg_loss)


def _alpha_beta(target: np.ndarray, benchmark: np.ndarray) -> tuple[float, float]:
    """Return alpha and beta of target against benchmark."""
    if target.size == 0 or benchmark.size == 0:
        return 0.0, 0.0
    min_len = min(len(target), len(benchmark))
    if min_len == 0:
        return 0.0, 0.0
    tgt = target[:min_len]
    bench = benchmark[:min_len]
    bench_var = float(np.var(bench))
    beta = 0.0 if bench_var <= 1e-12 else float(np.cov(tgt, bench, ddof=0)[0, 1] / bench_var)
    alpha = float(np.mean(tgt) - beta * np.mean(bench))
    return alpha, beta


def classify_risk_grade(
    sharpe_ratio: float,
    max_drawdown: float,
    prob_negative: float,
) -> str:
    """Simple website-friendly risk grade."""
    score = 0
    if sharpe_ratio >= 1.0:
        score += 2
    elif sharpe_ratio >= 0.4:
        score += 1
    elif sharpe_ratio < 0:
        score -= 1

    if max_drawdown >= -0.08:
        score += 2
    elif max_drawdown >= -0.16:
        score += 1
    elif max_drawdown <= -0.28:
        score -= 1

    if prob_negative <= 0.4:
        score += 1
    elif prob_negative >= 0.62:
        score -= 1

    if score >= 4:
        return "A 穩健"
    if score >= 2:
        return "B 均衡"
    if score >= 0:
        return "C 波動"
    return "D 高風險"


def _select_benchmark_series(sim_indexed: pd.DataFrame) -> tuple[str, np.ndarray | None]:
    """Pick a reasonable benchmark simulation series from the available assets."""
    candidates = ["^GSPC", "^TWII", "^IXIC", "^DJI", "0050.TW"]
    for ticker in candidates:
        if ticker in sim_indexed.index:
            arr = sim_indexed.loc[ticker].get("_simulated")
            if isinstance(arr, np.ndarray):
                return ticker, arr
    for ticker in sim_indexed.index:
        arr = sim_indexed.loc[ticker].get("_simulated")
        if isinstance(arr, np.ndarray):
            return str(ticker), arr
    return "", None


def simulate_event_impact(
    historical_cars: pd.DataFrame,
    n_simulations: int = 10000,
    event_intensity: float = 1.0,
) -> pd.DataFrame:
    """
    Bootstrap from historical CAR distribution.

    Parameters
    ----------
    historical_cars : DataFrame (events × tickers) of CAR values
    n_simulations   : number of Monte Carlo draws
    event_intensity : severity multiplier (0.5 = mild, 1.0 = normal, 2.0 = severe)

    Returns
    -------
    DataFrame with one row per ticker and summary statistics columns.
    """
    if historical_cars.empty:
        return pd.DataFrame()

    results = []
    rng = np.random.default_rng(seed=2024)
    benchmark_draws: dict[str, np.ndarray] = {}

    for ticker in historical_cars.columns:
        obs = historical_cars[ticker].dropna().values

        if len(obs) == 0:
            obs = np.array([-0.02])

        # Bootstrap: sample with replacement + add small Gaussian noise
        mean_obs = float(np.mean(obs))
        std_obs = float(np.std(obs)) if len(obs) > 1 else abs(mean_obs) * 0.3 + 1e-4

        draws = rng.choice(obs, size=n_simulations, replace=True)
        noise = rng.normal(0, std_obs * 0.15, n_simulations)
        simulated = (draws + noise) * event_intensity
        benchmark_draws[ticker] = simulated

        prob_neg = float(np.mean(simulated < 0))
        prob_pos = float(np.mean(simulated > 0))
        mean_return = float(np.mean(simulated))
        std_return = float(np.std(simulated))
        max_drawdown = _max_drawdown(simulated)

        results.append(
            {
                "ticker": ticker,
                "mean_return": mean_return,
                "median_return": float(np.median(simulated)),
                "std_return": std_return,
                "sharpe_ratio": _safe_sharpe(mean_return, std_return),
                "sortino_ratio": _safe_sortino(simulated),
                "max_drawdown": max_drawdown,
                "calmar_ratio": _safe_calmar(mean_return, max_drawdown),
                "win_rate": prob_pos,
                "profit_loss_ratio": _profit_loss_ratio(simulated),
                "p5": float(np.percentile(simulated, 5)),
                "p25": float(np.percentile(simulated, 25)),
                "p75": float(np.percentile(simulated, 75)),
                "p95": float(np.percentile(simulated, 95)),
                "prob_negative": round(prob_neg, 4),
                "prob_positive": round(prob_pos, 4),
                "_simulated": simulated,  # Store for portfolio use
            }
        )
    df = pd.DataFrame(results)
    if df.empty:
        return df

    sim_indexed = df.set_index("ticker")
    benchmark_ticker, benchmark_series = _select_benchmark_series(sim_indexed)
    alphas, betas, grades, benchmark_labels = [], [], [], []
    for _, row in df.iterrows():
        simulated = row["_simulated"]
        alpha, beta = (0.0, 0.0)
        if isinstance(benchmark_series, np.ndarray):
            alpha, beta = _alpha_beta(simulated, benchmark_series)
        alphas.append(alpha)
        betas.append(beta)
        grades.append(classify_risk_grade(float(row["sharpe_ratio"]), float(row["max_drawdown"]), float(row["prob_negative"])))
        benchmark_labels.append(benchmark_ticker or "--")
    df["alpha"] = alphas
    df["beta"] = betas
    df["risk_grade"] = grades
    df["benchmark_ticker"] = benchmark_labels
    return df


def portfolio_stress_test(
    portfolio: dict,
    simulation_results: pd.DataFrame,
) -> dict:
    """
    Portfolio-level stress test using Monte Carlo simulation results.

    Parameters
    ----------
    portfolio          : {ticker: weight} – weights must sum to ~1
    simulation_results : output of simulate_event_impact

    Returns
    -------
    dict with VaR, ES, scenario metrics and per-asset contributions.
    """
    if simulation_results.empty or not portfolio:
        return {
            "expected_return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "calmar_ratio": 0.0,
            "alpha": 0.0,
            "beta": 0.0,
            "win_rate": 0.0,
            "profit_loss_ratio": 0.0,
            "risk_grade": "C 波動",
            "benchmark_ticker": "--",
            "var_95": 0.0,
            "var_99": 0.0,
            "expected_shortfall": 0.0,
            "best_case": 0.0,
            "worst_case": 0.0,
            "asset_contributions": {},
            "simulation_paths": np.array([0.0]),
        }

    n_sim = 10_000

    # Build per-ticker simulation arrays aligned on the same row
    # (reuse stored _simulated arrays if present, else bootstrap from stats)
    ticker_sims: dict[str, np.ndarray] = {}
    sim_indexed = simulation_results.set_index("ticker")

    rng = np.random.default_rng(seed=2025)

    for ticker, weight in portfolio.items():
        if ticker in sim_indexed.index:
            row = sim_indexed.loc[ticker]
            if "_simulated" in row.index and isinstance(row["_simulated"], np.ndarray):
                arr = row["_simulated"].copy()
                # Ensure arr is exactly n_sim length (resample if needed)
                if len(arr) < n_sim:
                    arr = rng.choice(arr, size=n_sim, replace=True)
                else:
                    arr = arr[:n_sim]
            else:
                # Reconstruct from summary stats
                mu = float(row.get("mean_return", 0.0))
                sigma = float(row.get("std_return", abs(mu) * 0.3 + 1e-4))
                arr = rng.normal(mu, sigma, n_sim)
            ticker_sims[ticker] = arr
        else:
            ticker_sims[ticker] = rng.normal(0.0, 0.02, n_sim)

    # Portfolio return per simulation
    port_sim = np.zeros(n_sim)
    asset_contributions: dict[str, float] = {}

    for ticker, weight in portfolio.items():
        arr = ticker_sims.get(ticker, np.zeros(n_sim))
        contribution = weight * arr
        port_sim += contribution
        asset_contributions[ticker] = round(float(np.mean(contribution)), 6)

    # Risk metrics
    var_95 = float(np.percentile(port_sim, 5))   # 5th percentile (loss side)
    var_99 = float(np.percentile(port_sim, 1))
    es_mask = port_sim <= var_95
    expected_shortfall = float(np.mean(port_sim[es_mask])) if es_mask.any() else var_95
    volatility = float(np.std(port_sim))
    expected_return = float(np.mean(port_sim))
    max_drawdown = _max_drawdown(port_sim)
    benchmark_ticker, benchmark_series = _select_benchmark_series(sim_indexed)
    alpha, beta = (0.0, 0.0)
    if isinstance(benchmark_series, np.ndarray):
        alpha, beta = _alpha_beta(port_sim, benchmark_series)
    win_rate = float(np.mean(port_sim > 0))
    prob_negative = float(np.mean(port_sim < 0))

    return {
        "expected_return": round(expected_return, 6),
        "volatility": round(volatility, 6),
        "sharpe_ratio": round(_safe_sharpe(expected_return, volatility), 6),
        "sortino_ratio": round(_safe_sortino(port_sim), 6),
        "max_drawdown": round(max_drawdown, 6),
        "calmar_ratio": round(_safe_calmar(expected_return, max_drawdown), 6),
        "alpha": round(alpha, 6),
        "beta": round(beta, 6),
        "win_rate": round(win_rate, 6),
        "profit_loss_ratio": round(_profit_loss_ratio(port_sim), 6),
        "risk_grade": classify_risk_grade(_safe_sharpe(expected_return, volatility), max_drawdown, prob_negative),
        "benchmark_ticker": benchmark_ticker or "--",
        "var_95": round(var_95, 6),
        "var_99": round(var_99, 6),
        "expected_shortfall": round(expected_shortfall, 6),
        "best_case": round(float(np.percentile(port_sim, 95)), 6),
        "worst_case": round(float(np.percentile(port_sim, 5)), 6),
        "asset_contributions": asset_contributions,
        "simulation_paths": port_sim,
    }


def generate_scenario_comparison(
    historical_cars: pd.DataFrame,
) -> dict:
    """
    Generate best/base/worst case scenarios from historical CAR distributions.

    Returns
    -------
    dict with keys 'best', 'base', 'worst',
    each containing a dict {ticker: expected_return}.
    """
    if historical_cars.empty:
        return {"best": {}, "base": {}, "worst": {}}

    best, base, worst = {}, {}, {}

    for ticker in historical_cars.columns:
        obs = historical_cars[ticker].dropna().values
        if len(obs) == 0:
            obs = np.array([0.0])

        # Best: 90th percentile of historical CARs
        best[ticker] = round(float(np.percentile(obs, 90)), 4)
        # Base: median
        base[ticker] = round(float(np.median(obs)), 4)
        # Worst: 10th percentile
        worst[ticker] = round(float(np.percentile(obs, 10)), 4)

    return {"best": best, "base": base, "worst": worst}
