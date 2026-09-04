#!/usr/bin/env python3
"""
Yield curve bootstrapping and portfolio analysis — script version.

Mirrors Yield_Curve_And_Portfolio_Analysis.ipynb, executing end-to-end so
it can be run headless (no Jupyter required).

Run:
    python notebooks/run_analysis.py

Requires: numpy, scipy, pandas, matplotlib, seaborn, numpy-financial,
          optionally yfinance (falls back to synthetic data if absent).
"""

from __future__ import annotations

import sys
import os

# Make the package importable when run from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless — save PNGs without a GUI backend
import matplotlib.pyplot as plt
import seaborn as sns

from yield_curve import YieldCurve, NelsonSiegel, PortfolioAnalyzer, fetch_prices_from_yfinance

sns.set_theme(style="whitegrid", palette="dark")
np.set_printoptions(suppress=True, formatter={"float_kind": "{:0.4f}".format})


def run() -> None:
    print("=" * 78)
    print("Bootstrap Yield Curve — Package Demo")
    print("=" * 78)

    # ------------------------------------------------------------------
    # 1. Treasury yield curve — bootstrapping three ways
    # ------------------------------------------------------------------
    print("\n[1] Treasury yield curve — bootstrapping")

    maturities = np.arange(1, 11)
    prices = np.array(
        [96.60, 93.71, 91.56, 90.24, 89.74, 90.04, 91.09, 92.82, 95.19, 98.14]
    )
    coupons = np.linspace(0.015, 0.0375, num=10)
    bonds = np.column_stack((maturities, prices, coupons))

    print("Bonds (maturity, price, coupon):")
    print(bonds)
    print()

    yc = YieldCurve(bonds)

    print("Discount factors — Matrix operations:")
    print(yc.discount_factors("Matrix operations"))
    print()
    print("Discount factors — Global Solver:")
    print(yc.discount_factors("Global Solver"))
    print()
    print("Discount factors — Iterative procedure:")
    print(yc.discount_factors("Iterative Procedure"))
    print()

    df_m = yc.discount_factors("Matrix operations")
    df_s = yc.discount_factors("Global Solver")
    df_i = yc.discount_factors("Iterative Procedure")

    print("Consistency check (max abs diff):")
    print("  matrix vs solver   :", np.max(np.abs(df_m - df_s)))
    print("  matrix vs iterative:", np.max(np.abs(df_m - df_i)))
    print("Prices recovered from cash flows @ DF:")
    print(yc.cash_flows @ df_m)
    print()

    # ------------------------------------------------------------------
    # 2. Spot rates, YTM, and forward rates
    # ------------------------------------------------------------------
    print("[2] Derived rates")

    spot = yc.spot_rates()
    ytm = yc.bonds_ytm()
    fwd = yc.forward_rates()

    print("Spot rates (%):  ", np.round(100 * spot, 2))
    print("YTM (%):         ", np.round(100 * ytm, 2))
    print("1y Forward (%):  ", np.round(100 * fwd, 2))
    print()

    # Save the combined rate plot
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(repo_root, "docs", "images")
    os.makedirs(out_dir, exist_ok=True)
    yc.plot_rates(
        title="US Treasury Yield Curve — Spot, YTM, and Forward Rates",
        save_path=os.path.join(out_dir, "yield_curve_overview.png"),
        show=False,
    )
    print("Saved: yield_curve_overview.png")
    plt.close("all")

    # ------------------------------------------------------------------
    # 3. Nelson-Siegel parametric fit
    # ------------------------------------------------------------------
    print("\n[3] Nelson-Siegel parametric fit")

    ns = NelsonSiegel(
        maturities=bonds[:, 0].astype(float),
        discount_factors=yc.discount_factors("Matrix operations"),
    )
    ns.fit()

    beta0, beta1, beta2, tau = ns.params
    print("Fitted Nelson-Siegel parameters:")
    print(f"  beta0 (level)     = {beta0:.6f}")
    print(f"  beta1 (slope)     = {beta1:.6f}")
    print(f"  beta2 (curvature) = {beta2:.6f}")
    print(f"  tau (decay)       = {tau:.4f}")
    print()

    ns.plot(
        title="Nelson-Siegel fit vs bootstrapped discount factors",
        save_path=os.path.join(out_dir, "nelson_siegel_fit.png"),
        show=False,
    )
    print("Saved: nelson_siegel_fit.png")
    plt.close("all")

    # ------------------------------------------------------------------
    # 4. Portfolio analysis
    # ------------------------------------------------------------------
    print("\n[4] Portfolio analysis")

    tickers = ["AAPL", "IBM", "MSFT", "GOOG", "AMZN"]
    is_synthetic = False

    try:
        prices = fetch_prices_from_yfinance(tickers, start="2019-01-01")
        # yfinance may return an empty panel (network/cache issues, ticker
        # name changes, etc.) — fall through to synthetic data in that case.
        if prices is None or prices.empty or len(prices) < 20:
            raise ValueError(
                f"yfinance returned {len(prices) if prices is not None else 0} rows"
            )
        print(f"Fetched {len(prices)} daily observations for {len(tickers)} tickers")
        print("Date range:", prices.index.min().date(), "to", prices.index.max().date())
    except Exception as e:
        print(f"yfinance unavailable or returned no data ({type(e).__name__}: {e})")
        print("Falling back to synthetic data — the numbers below are NOT market data.")
        is_synthetic = True
        # Neutral labels: this panel is simulated, so it must not be presented
        # under real ticker symbols.
        tickers = ["ASSET_A", "ASSET_B", "ASSET_C", "ASSET_D", "ASSET_E"]
        np.random.seed(42)
        dates = pd.bdate_range("2019-01-02", periods=504)  # ~2 years of trading days
        mu = np.array([0.0005, 0.0003, 0.0006, 0.0005, 0.0007])  # ~12-18% annualized
        vols = np.array([0.018, 0.016, 0.017, 0.019, 0.021])  # daily vol
        corr = np.array([
            [1.00, 0.45, 0.60, 0.55, 0.50],
            [0.45, 1.00, 0.50, 0.42, 0.30],
            [0.60, 0.50, 1.00, 0.65, 0.56],
            [0.55, 0.42, 0.65, 1.00, 0.60],
            [0.50, 0.30, 0.56, 0.60, 1.00],
        ])
        L = np.linalg.cholesky(corr)
        Z = np.random.randn(len(dates), 5)
        returns = Z @ L.T * vols + mu / 252
        prices = pd.DataFrame(
            100 * np.exp(np.cumsum(returns, axis=0)),
            index=dates,
            columns=tickers,
        )
        print(f"Generated {len(prices)} synthetic daily prices for {len(tickers)} assets")
        print("Synthetic panel:", prices.shape)

    # Suffix carried onto every chart title so an exported image cannot be
    # mistaken for an analysis of real market data.
    src_note = " (synthetic sample data)" if is_synthetic else ""

    # Label everything off the frame's own columns: yfinance returns them
    # alphabetically, which is not the order `tickers` was written in.
    names = list(prices.columns)

    print()
    print("First rows of price panel:")
    print(prices.head())
    print()

    risk_free = float(spot[0])
    pa = PortfolioAnalyzer(prices, risk_free_rate=risk_free)

    print(f"Risk-free rate used: {risk_free:.4f} ({100 * risk_free:.2f}%)")
    print(f"Observation period: {len(pa.returns)} trading days")
    print("Annualized mean returns (sorted):")
    print(pa.mean_returns.sort_values(ascending=False))
    print()

    pa.cumulative_returns_plot(
        title=(
            f"Cumulative returns ({prices.index.min().date()} "
            f"to {prices.index.max().date()}){src_note}"
        ),
        save_path=os.path.join(out_dir, "cumulative_returns.png"),
        show=False,
    )
    print("Saved: cumulative_returns.png")
    plt.close("all")

    pa.correlation_heatmap(
        title=f"Correlation of Daily Returns{src_note}",
        save_path=os.path.join(out_dir, "correlation_heatmap.png"),
        show=False,
    )
    print("Saved: correlation_heatmap.png")
    plt.close("all")

    frontier = pa.efficient_frontier(n_points=100)
    max_sharpe = pa.max_sharpe_portfolio()

    print("Maximum Sharpe portfolio:")
    for ticker, w in zip(names, max_sharpe["weights"]):
        if w > 1e-6:
            print(f"  {ticker:6s}: {w * 100:6.2f}%")
    print(f"  Volatility : {max_sharpe['volatility'] * 100:.2f}%")
    print(f"  Return     : {max_sharpe['return'] * 100:.2f}%")
    print(f"  Sharpe     : {max_sharpe['sharpe']:.3f}")
    print()

    # Efficient frontier plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        frontier["volatility"] * 100,
        frontier["return"] * 100,
        "b-",
        alpha=0.5,
        label="Efficient frontier",
    )
    ax.scatter(
        [max_sharpe["volatility"] * 100],
        [max_sharpe["return"] * 100],
        color="red",
        s=150,
        zorder=5,
        label=f"Max Sharpe ({max_sharpe['sharpe']:.2f})",
    )
    for ticker, ret, vol in zip(
        names,
        pa.mean_returns,
        np.sqrt(np.diag(pa.cov_matrix)),
    ):
        ax.scatter(vol * 100, ret * 100, alpha=0.6, label=ticker)

    ax.set_xlabel("Annualized volatility (%)")
    ax.set_ylabel("Annualized return (%)")
    ax.set_title(f"Markowitz Efficient Frontier{src_note}")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.savefig(os.path.join(out_dir, "efficient_frontier.png"), dpi=150, bbox_inches="tight")
    print("Saved: efficient_frontier.png")
    plt.close("all")

    # ------------------------------------------------------------------
    # 5. Summary
    # ------------------------------------------------------------------
    print("\n[5] Done — all outputs saved to", out_dir)
    print("=" * 78)


if __name__ == "__main__":
    run()
