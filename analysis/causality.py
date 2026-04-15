# analysis/causality.py
# Granger Causality and Transfer Entropy

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats
import networkx as nx


# ---------------------------------------------------------------------------
# Granger Causality
# ---------------------------------------------------------------------------

def _granger_test_pair(cause: np.ndarray, effect: np.ndarray, max_lag: int) -> float:
    """
    Test whether `cause` Granger-causes `effect` up to `max_lag`.
    Returns minimum p-value across all tested lags.
    Uses manual F-test implementation to avoid statsmodels dependency issues.
    """
    try:
        from statsmodels.tsa.stattools import grangercausalitytests
        data = np.column_stack([effect, cause])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = grangercausalitytests(data, maxlag=max_lag, verbose=False)
        p_values = [res[lag][0]["ssr_ftest"][1] for lag in range(1, max_lag + 1)]
        return float(min(p_values))
    except Exception:
        # Manual lagged regression fallback
        try:
            n = len(effect)
            lag = min(max_lag, max(1, n // 10))

            # Restricted model: effect ~ lags of effect
            Y = effect[lag:]
            X_r = np.column_stack([effect[lag - k: n - k] for k in range(1, lag + 1)])
            X_r = np.column_stack([np.ones(len(Y)), X_r])

            # Unrestricted model: effect ~ lags of effect + lags of cause
            X_c = np.column_stack([cause[lag - k: n - k] for k in range(1, lag + 1)])
            X_u = np.column_stack([X_r, X_c])

            def ssr(X, y):
                beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
                resid = y - X @ beta
                return float(np.sum(resid ** 2))

            ssr_r = ssr(X_r, Y)
            ssr_u = ssr(X_u, Y)

            T = len(Y)
            k = lag  # number of restrictions
            df1, df2 = k, T - X_u.shape[1]
            if df2 <= 0 or ssr_u <= 0:
                return 0.5

            F = ((ssr_r - ssr_u) / k) / (ssr_u / df2)
            p = float(1 - stats.f.cdf(F, df1, df2))
            return p
        except Exception:
            return 0.5


def granger_causality_matrix(
    returns: pd.DataFrame,
    max_lag: int = 5,
    significance: float = 0.05,
) -> pd.DataFrame:
    """
    Run pairwise Granger causality tests for all asset pairs.
    Returns square DataFrame (rows=causes, cols=effects) with p-values.
    """
    cols = returns.columns.tolist()
    n = len(cols)
    matrix = pd.DataFrame(np.ones((n, n)), index=cols, columns=cols)

    for i, cause in enumerate(cols):
        for j, effect in enumerate(cols):
            if i == j:
                matrix.loc[cause, effect] = 1.0
                continue
            c_vals = returns[cause].dropna().values
            e_vals = returns[effect].dropna().values
            # Align lengths
            min_len = min(len(c_vals), len(e_vals))
            if min_len < max_lag + 5:
                matrix.loc[cause, effect] = 1.0
                continue
            c_vals = c_vals[-min_len:]
            e_vals = e_vals[-min_len:]
            p = _granger_test_pair(c_vals, e_vals, max_lag)
            matrix.loc[cause, effect] = p

    return matrix


# ---------------------------------------------------------------------------
# Transfer Entropy
# ---------------------------------------------------------------------------

def _discretize(series: np.ndarray, bins: int) -> np.ndarray:
    """Discretize a continuous series into `bins` integer categories."""
    # Use quantile-based binning for robustness
    quantiles = np.linspace(0, 100, bins + 1)
    thresholds = np.percentile(series, quantiles[1:-1])
    return np.digitize(series, thresholds)


def _joint_entropy(x: np.ndarray, y: np.ndarray) -> float:
    """H(X, Y) via empirical joint distribution."""
    xy = np.column_stack([x, y])
    unique, counts = np.unique(xy, axis=0, return_counts=True)
    probs = counts / counts.sum()
    return float(-np.sum(probs * np.log2(probs + 1e-12)))


def _entropy(x: np.ndarray) -> float:
    """H(X) via empirical distribution."""
    unique, counts = np.unique(x, return_counts=True)
    probs = counts / counts.sum()
    return float(-np.sum(probs * np.log2(probs + 1e-12)))


def _transfer_entropy(x: np.ndarray, y: np.ndarray, bins: int = 5) -> float:
    """
    TE(X→Y) = H(Y_t | Y_{t-1}) - H(Y_t | Y_{t-1}, X_{t-1})
             = H(Y_t, Y_{t-1}) - H(Y_{t-1}) - H(Y_t, Y_{t-1}, X_{t-1}) + H(Y_{t-1}, X_{t-1})
    """
    if len(x) < 10 or len(y) < 10:
        return 0.0

    xd = _discretize(x, bins)
    yd = _discretize(y, bins)

    yt = yd[1:]
    yt_lag = yd[:-1]
    xt_lag = xd[:-1]

    # TE = H(Y_t | Y_{t-1}) - H(Y_t | Y_{t-1}, X_{t-1})
    # H(A | B) = H(A, B) - H(B)
    h_yt_ytlag = _joint_entropy(yt, yt_lag)
    h_ytlag = _entropy(yt_lag)
    h_yt_given_ytlag = h_yt_ytlag - h_ytlag  # H(Y_t | Y_{t-1})

    h_yt_ytlag_xtlag = _joint_entropy(
        yt, np.column_stack([yt_lag, xt_lag]).view(np.int64).reshape(-1)
        if False else np.array([yt_lag[i] * bins + xt_lag[i] for i in range(len(yt_lag))])
    )
    h_ytlag_xtlag = _joint_entropy(yt_lag, xt_lag)
    h_yt_given_ytlag_xtlag = h_yt_ytlag_xtlag - h_ytlag_xtlag

    te = h_yt_given_ytlag - h_yt_given_ytlag_xtlag
    return max(0.0, float(te))


def transfer_entropy_matrix(
    returns: pd.DataFrame,
    bins: int = 5,
) -> pd.DataFrame:
    """
    Calculate pairwise transfer entropy for all asset pairs.
    Returns square DataFrame with TE values (rows=source, cols=target).
    """
    cols = returns.columns.tolist()
    n = len(cols)
    matrix = pd.DataFrame(np.zeros((n, n)), index=cols, columns=cols)

    for i, source in enumerate(cols):
        for j, target in enumerate(cols):
            if i == j:
                continue
            x = returns[source].dropna().values
            y = returns[target].dropna().values
            min_len = min(len(x), len(y))
            if min_len < 20:
                continue
            x = x[-min_len:]
            y = y[-min_len:]
            te = _transfer_entropy(x, y, bins=bins)
            matrix.loc[source, target] = te

    return matrix


# ---------------------------------------------------------------------------
# Network Construction
# ---------------------------------------------------------------------------

def build_causality_network(
    granger_matrix: pd.DataFrame,
    te_matrix: pd.DataFrame,
    granger_threshold: float = 0.05,
    te_threshold: float = 0.01,
) -> dict:
    """
    Combine Granger and TE results into a directed network.
    Returns dict with nodes, edges, centrality.
    """
    assets = granger_matrix.columns.tolist()

    # Compute correlation matrix for direction labeling
    # (We use returns if available; otherwise sign from TE is used)
    edges = []
    for source in assets:
        for target in assets:
            if source == target:
                continue
            g_p = granger_matrix.loc[source, target] if source in granger_matrix.index else 1.0
            te_val = te_matrix.loc[source, target] if source in te_matrix.index else 0.0

            if g_p < granger_threshold or te_val > te_threshold:
                # Weight: combine normalised p-value and TE score
                g_score = max(0.0, 1.0 - g_p)  # higher = more significant
                te_score = float(te_val)
                weight = 0.5 * g_score + 0.5 * min(te_score, 1.0)

                edges.append(
                    {
                        "source": source,
                        "target": target,
                        "granger_p": float(g_p),
                        "te_value": float(te_val),
                        "weight": round(weight, 4),
                        "direction": "positive" if weight > 0.3 else "negative",
                    }
                )

    # Build networkx DiGraph for centrality computation
    G = nx.DiGraph()
    G.add_nodes_from(assets)
    for e in edges:
        G.add_edge(e["source"], e["target"], weight=e["weight"])

    try:
        centrality = nx.out_degree_centrality(G)
    except Exception:
        centrality = {a: 0.0 for a in assets}

    return {
        "nodes": assets,
        "edges": edges,
        "centrality": {k: round(v, 4) for k, v in centrality.items()},
    }


def get_transmission_path(
    network: dict,
    source: str,
    targets: list,
) -> list:
    """
    Find the transmission path from source to each target using the network graph.
    Returns list of (from, to, weight) tuples representing the cascade.
    """
    G = nx.DiGraph()
    G.add_nodes_from(network["nodes"])
    for e in network["edges"]:
        G.add_edge(e["source"], e["target"], weight=e["weight"])

    paths = []
    for target in targets:
        if target == source:
            continue
        try:
            path_nodes = nx.shortest_path(G, source=source, target=target, weight=None)
            for i in range(len(path_nodes) - 1):
                u, v = path_nodes[i], path_nodes[i + 1]
                w = G[u][v].get("weight", 0.0) if G.has_edge(u, v) else 0.0
                paths.append((u, v, w))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # No path found; try adding a direct edge if it exists in edges
            for e in network["edges"]:
                if e["source"] == source and e["target"] == target:
                    paths.append((source, target, e["weight"]))
                    break

    # Deduplicate
    seen = set()
    unique_paths = []
    for p in paths:
        key = (p[0], p[1])
        if key not in seen:
            seen.add(key)
            unique_paths.append(p)

    return unique_paths
