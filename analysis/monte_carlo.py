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

        prob_neg = float(np.mean(simulated < 0))
        prob_pos = float(np.mean(simulated > 0))

        results.append(
            {
                "ticker": ticker,
                "mean_return": float(np.mean(simulated)),
                "median_return": float(np.median(simulated)),
                "std_return": float(np.std(simulated)),
                "sharpe_ratio": _safe_sharpe(float(np.mean(simulated)), float(np.std(simulated))),
                "p5": float(np.percentile(simulated, 5)),
                "p25": float(np.percentile(simulated, 25)),
                "p75": float(np.percentile(simulated, 75)),
                "p95": float(np.percentile(simulated, 95)),
                "prob_negative": round(prob_neg, 4),
                "prob_positive": round(prob_pos, 4),
                "_simulated": simulated,  # Store for portfolio use
            }
        )

    return pd.DataFrame(results)


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

    return {
        "expected_return": round(expected_return, 6),
        "volatility": round(volatility, 6),
        "sharpe_ratio": round(_safe_sharpe(expected_return, volatility), 6),
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
