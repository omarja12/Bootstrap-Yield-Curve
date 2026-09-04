"""
Portfolio analysis fundamentals: returns, correlation, and Markowitz
mean-variance optimization.

Connects to the yield curve module to use bootstrapped risk-free rates in
Sharpe ratio calculations.
"""

from __future__ import annotations

import warnings
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Optional dependencies — raiser helpful message if missing
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

try:
    from scipy.optimize import minimize
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class PortfolioAnalyzer:
    """Daily-return-based portfolio analysis for a set of tickers.

    Parameters
    ----------
    prices : pd.DataFrame
        Panel of adjusted close prices, columns = tickers, index = dates.
    risk_free_rate : float, optional
        Annualized risk-free rate (as a decimal, e.g. 0.05 for 5%) used in
        Sharpe ratio calculations. Defaults to 0 (excess returns = raw returns).
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        risk_free_rate: float = 0.0,
    ) -> None:
        self.prices = prices.copy()
        self.risk_free_rate = risk_free_rate
        self._returns: Optional[pd.DataFrame] = None
        self._mean_returns: Optional[pd.Series] = None
        self._cov_matrix: Optional[pd.DataFrame] = None

    @property
    def returns(self) -> pd.DataFrame:
        if self._returns is None:
            self._returns = self.prices.pct_change().dropna()
            self._mean_returns = self._returns.mean() * 252
            self._cov_matrix = self._returns.cov() * 252
        return self._returns

    @property
    def mean_returns(self) -> pd.Series:
        _ = self.returns  # ensure computed
        return self._mean_returns

    @property
    def cov_matrix(self) -> pd.DataFrame:
        _ = self.returns
        return self._cov_matrix

    def annualized_return(self, weights: np.ndarray) -> float:
        """Annualized portfolio return for a weight vector."""
        return float(np.dot(weights, self.mean_returns))

    def annualized_volatility(self, weights: np.ndarray) -> float:
        """Annualized portfolio volatility for a weight vector."""
        return float(np.sqrt(weights @ self.cov_matrix.values @ weights))

    def sharpe_ratio(self, weights: np.ndarray) -> float:
        """Annualized Sharpe ratio."""
        ret = self.annualized_return(weights)
        vol = self.annualized_volatility(weights)
        if vol == 0:
            return 0.0
        return (ret - self.risk_free_rate) / vol

    def efficient_frontier(
        self,
        n_points: int = 50,
        ret_range: Optional[Tuple[float, float]] = None,
    ) -> pd.DataFrame:
        """Compute the efficient frontier via quadratic optimization.

        Parameters
        ----------
        n_points : int
            Number of points on the frontier.
        ret_range : tuple, optional
            (min_return, max_return) range to scan. Defaults to min/max
            mean returns across assets.

        Returns
        -------
        df : pd.DataFrame
            Columns: volatility, return, sharpe. One row per efficient point.
        """
        if not HAS_SCIPY:
            raise ImportError("scipy is required for efficient_frontier()")

        n_assets = len(self.mean_returns)
        means = self.mean_returns.values
        cov = self.cov_matrix.values

        if ret_range is None:
            ret_range = (means.min(), means.max())

        target_returns = np.linspace(ret_range[0], ret_range[1], n_points)
        results = []

        init_guess = np.ones(n_assets) / n_assets

        def portfolio_variance(w):
            return w @ cov @ w

        def portfolio_return(w):
            return w @ means

        def weight_constraint():
            return {"type": "eq", "fun": lambda w: np.sum(w) - 1}

        for target in target_returns:
            cons = [
                weight_constraint(),
                {"type": "eq", "fun": lambda w, t=target: portfolio_return(w) - t},
            ]
            res = minimize(
                portfolio_variance,
                init_guess,
                method="SLSQP",
                constraints=cons,
                bounds=[(0, 1)] * n_assets,
                options={"ftol": 1e-9, "disp": False},
            )
            if res.success:
                w = res.x
                results.append({
                    "volatility": float(np.sqrt(portfolio_variance(w))),
                    "return": float(portfolio_return(w)),
                    "sharpe": float((portfolio_return(w) - self.risk_free_rate) /
                                    np.sqrt(portfolio_variance(w))),
                    "weights": w,
                })

        return pd.DataFrame(results)

    def max_sharpe_portfolio(self) -> dict:
        """Find weights that maximize the Sharpe ratio."""
        if not HAS_SCIPY:
            raise ImportError("scipy is required for max_sharpe_portfolio()")

        n_assets = len(self.mean_returns)
        means = self.mean_returns.values
        cov = self.cov_matrix.values

        def neg_sharpe(w):
            vol = np.sqrt(w @ cov @ w)
            if vol == 0:
                return 0.0
            return -(w @ means - self.risk_free_rate) / vol

        cons = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
        res = minimize(
            neg_sharpe,
            np.ones(n_assets) / n_assets,
            method="SLSQP",
            constraints=cons,
            bounds=[(0, 1)] * n_assets,
        )
        if not res.success:
            raise RuntimeError("Optimization did not converge")
        w = res.x
        return {
            "weights": w,
            "volatility": float(np.sqrt(w @ cov @ w)),
            "return": float(w @ means),
            "sharpe": float((w @ means - self.risk_free_rate) / np.sqrt(w @ cov @ w)),
        }

    def correlation_heatmap(
        self,
        title: str = "Correlation of Daily Returns",
        cmap: str = "viridis",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> plt.Figure:
        """Plot the correlation matrix of daily returns."""
        fig, ax = plt.subplots()
        corr = self.returns.corr()
        cax = ax.imshow(corr.values, cmap=cmap, vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.index)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right")
        ax.set_yticklabels(corr.index)
        ax.set_title(title)
        fig.colorbar(cax, ax=ax)
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        if show:
            plt.show()
        return fig

    def cumulative_returns_plot(
        self,
        title: str = "Cumulative Returns",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> plt.Figure:
        """Plot cumulative returns of each asset."""
        fig, ax = plt.subplots(figsize=(12, 6))
        (self.returns + 1).cumprod().plot(ax=ax, title=title)
        ax.set_ylabel("Cumulative return")
        ax.grid(alpha=0.3)
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        if show:
            plt.show()
        return fig


def fetch_prices_from_yfinance(
    tickers: List[str],
    start: str = "2012-01-01",
    end: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch adjusted close prices from yfinance.

    Parameters
    ----------
    tickers : list of str
        Ticker symbols.
    start : str
        Start date (inclusive), e.g. "2012-01-01".
    end : str or None
        End date (exclusive). Defaults to today.

    Returns
    -------
    prices : pd.DataFrame
        Adjusted close prices, columns = tickers, index = dates.
    """
    if not HAS_YFINANCE:
        raise ImportError(
            "yfinance is required for fetch_prices_from_yfinance(). Install with "
            "`pip install yfinance`."
        )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        data = yf.download(
            tickers, start=start, end=end, progress=False, auto_adjust=True
        )
    if isinstance(data.columns, pd.MultiIndex):
        # yfinance dropped "Adj Close" once auto_adjust became the default, so
        # prefer it when present and fall back to the adjusted "Close".
        level = data.columns.get_level_values(0)
        field = "Adj Close" if "Adj Close" in level else "Close"
        prices = data[field]
    elif "Close" in data.columns:
        prices = data[["Close"]]
        prices.columns = list(tickers)[:1]
    else:
        prices = data
    return prices.dropna(how="all").sort_index()
