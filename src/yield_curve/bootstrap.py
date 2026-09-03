"""
Yield curve bootstrapping: matrix operations, global solver, and iterative
procedure, plus Nelson-Siegel parametric fitting.

Original exercise: August 2022 (see `notebooks/`).
Refactored into a package: September 2026.
"""

from __future__ import annotations

import numpy as np
import numpy_financial as npf
from scipy.optimize import minimize
from typing import Tuple, Optional, List, Dict

import matplotlib.pyplot as plt
import seaborn as sns


class YieldCurve:
    """Bootstraps discount factors, spot rates, YTM, and forward rates from
    coupon-bearing bonds.

    Parameters
    ----------
    bonds : np.ndarray, shape (n, 3)
        Columns: (maturity_years, dirty_price, annual_coupon_rate).
        Maturities are assumed to be positive integers and sorted ascending.
        Face value is assumed to be 100.
    """

    def __init__(self, bonds: np.ndarray) -> None:
        self.bonds = np.asarray(bonds, dtype=float)
        if self.bonds.ndim != 2 or self.bonds.shape[1] != 3:
            raise ValueError("bonds must be an (n, 3) array")
        self._cash_flows = self._build_cash_flows()

    def _build_cash_flows(self) -> np.ndarray:
        """Build the cash-flows matrix C (n x n) where C[i, j] is the cash flow
        of bond i at year j+1 (1-indexed)."""
        n = self.bonds.shape[0]
        cash_flows = np.zeros((n, n))
        for i, (mat, price, coupon) in enumerate(self.bonds):
            T = int(mat)
            if T <= 0 or T > n:
                raise ValueError(f"Maturity {T} out of range for bond {i}")
            for j in range(1, T + 1):
                if j < T:
                    cash_flows[i, j - 1] = np.round(100 * coupon, 2)
                else:
                    cash_flows[i, j - 1] = np.round((coupon + 1) * 100, 2)
        return cash_flows

    @property
    def cash_flows(self) -> np.ndarray:
        return self._cash_flows

    def discount_factors(
        self, method: str = "Matrix operations"
    ) -> np.ndarray:
        """Bootstrap discount factors using the specified method.

        Parameters
        ----------
        method : str
            One of 'Matrix operations', 'Global Solver', 'Iterative Procedure'.

        Returns
        -------
        df : np.ndarray, shape (n,)
            Discount factors for each year 1..n.
        """
        n = self.bonds.shape[0]

        if method == "Matrix operations":
            return np.linalg.solve(self._cash_flows, self.bonds[:, 1])

        elif method == "Global Solver":
            def bond_prices(cfs, DF):
                return cfs @ DF

            def error(dfs, cfs, p):
                return ((bond_prices(cfs, dfs) - p) ** 2).sum()

            dfs0 = np.ones(n)
            res = minimize(
                error, dfs0, args=(self._cash_flows, self.bonds[:, 1])
            )
            if not res.success:
                raise RuntimeError("Global solver did not converge")
            return res.x

        elif method == "Iterative Procedure":
            tmp = []
            for row in self.bonds:
                T = int(row[0])
                coupon = row[2]
                price = row[1]
                # PV of coupons for years 1..T-1 using already computed DFs
                pv_coupons = 100 * coupon * sum(tmp)
                # Final cash flow at year T: coupon + face value
                df_T = (price - pv_coupons) / (100 * (coupon + 1))
                tmp.append(df_T)
            return np.array(tmp)

        else:
            raise ValueError(f"Unknown method: {method}")

    def spot_rates(self) -> np.ndarray:
        """Compute annual-compounded spot rates from matrix-operation discount
        factors.

        Returns
        -------
        s : np.ndarray, shape (n,)
            Spot rate for each year 1..n.
        """
        df = self.discount_factors("Matrix operations")
        n = self.bonds.shape[0]
        years = np.arange(1, n + 1)
        s = np.power(1.0 / df, 1.0 / years) - 1.0
        return s

    def bonds_ytm(self) -> np.ndarray:
        """Yield to maturity for each bond using numpy_financial.irr.

        Returns
        -------
        ytm : np.ndarray, shape (n,)
            YTM for each bond.
        """
        ytm = []
        for row in self.bonds:
            T = int(row[0])
            coupon = row[2]
            price = row[1]
            # cash flows: initial outflow = -price, then coupon*100 for years
            # 1..T-1, and (coupon+1)*100 at year T
            flows = [-price]
            for t in range(1, T + 1):
                if t < T:
                    flows.append(coupon * 100)
                else:
                    flows.append((coupon + 1) * 100)
            ytm.append(npf.irr(flows))
        return np.array(ytm)

    def forward_rates(self) -> np.ndarray:
        """One-year forward rates starting at each year 1..n-1.

        Returns
        -------
        f : np.ndarray, shape (n-1,)
            Forward rate f(t, t+1) for t = 1..n-1.
        """
        s = self.spot_rates()
        maturities = self.bonds[:, 0]
        # f(t, t+1) = ( (1+s_{t+1})^{t+1} ) / ( (1+s_t)^{t} ) - 1
        # Using approximation from the original: based on spot rates and maturities
        n = self.bonds.shape[0]
        f = np.zeros(n - 1)
        for t in range(1, n):
            # (1 + s_t)^t and (1 + s_{t+1})^{t+1}
            num = (1 + s[t]) ** maturities[t]  # s[t] is spot for year t+1? careful
            den = (1 + s[t - 1]) ** maturities[t - 1]
            f[t - 1] = (num / den) - 1
        return f

    # ------------------------------------------------------------------
    # Plotting helpers
    # ------------------------------------------------------------------

    def plot_rates(
        self,
        title: str = "Yield Curve Analysis",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> plt.Figure:
        """Plot spot rates, YTM, and forward rates on a single figure.

        Returns the Figure for further customization or saving.
        """
        sns.set_theme(style="whitegrid", palette="dark")
        s = self.spot_rates()
        ytm = self.bonds_ytm()
        f = self.forward_rates()
        maturities = self.bonds[:, 0]

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(maturities, 100 * s, color="black", marker="o", label="Spot Rate")
        ax.plot(maturities, 100 * ytm, color="green", marker="o", label="YTM")
        ax.plot(maturities[1:], 100 * f, color="red", marker="o", label="Forward Rate")
        ax.set_xlabel("Maturity (years)")
        ax.set_ylabel("Rate (%)")
        ax.set_title(title)
        ax.legend()
        ax.grid(alpha=0.3)

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        if show:
            plt.show()
        return fig


class NelsonSiegel:
    """Nelson-Siegel yield curve fitting.

    Fits the parametric form:

        f(t) = β0 + β1 * exp(-t/τ) + β2 * (t/τ) * exp(-t/τ)

    to market discount factors (or spot rates) by minimizing squared error.

    Parameters
    ----------
    maturities : array-like
        Maturities in years (may be non-integer).
    discount_factors : array-like
        Market discount factors for each maturity.
    """

    def __init__(
        self,
        maturities: np.ndarray,
        discount_factors: np.ndarray,
    ) -> None:
        self.maturities = np.asarray(maturities, dtype=float)
        self.discount_factors = np.asarray(discount_factors, dtype=float)
        self.params: Optional[np.ndarray] = None
        self._fitted_df: Optional[np.ndarray] = None

    def _discount_factor(self, t: float, beta0, beta1, beta2, tau) -> float:
        """Model discount factor at time t given parameters."""
        if tau <= 0:
            return np.nan
        # spot rate at t
        exp_neg = np.exp(-t / tau)
        if t == 0:
            s = beta0
        else:
            s = beta0 + (beta1 + beta2) * (1 - exp_neg) / (t / tau) - beta2 * exp_neg
        return np.exp(-s * t)

    def _objective(
        self, params, maturities, df_market
    ) -> float:
        beta0, beta1, beta2, tau = params
        df_model = np.array([self._discount_factor(t, beta0, beta1, beta2, tau) for t in maturities])
        return np.sum((df_model - df_market) ** 2)

    def fit(
        self,
        initial_guess: Optional[np.ndarray] = None,
        bounds: Optional[List[Tuple]] = None,
    ) -> "NelsonSiegel":
        """Fit parameters by minimizing squared error against market discount
        factors.

        Returns self for chaining.
        """
        if initial_guess is None:
            # typical starting values
            initial_guess = np.array([0.05, -0.02, -0.02, 2.0])
        if bounds is None:
            bounds = [(None, None), (None, None), (None, None), (0.1, 20.0)]

        res = minimize(
            self._objective,
            initial_guess,
            args=(self.maturities, self.discount_factors),
            bounds=bounds,
            method="L-BFGS-B",
        )
        if not res.success:
            raise RuntimeError("Nelson-Siegel fitting did not converge")
        self.params = res.x
        self._fitted_df = np.array([
            self._discount_factor(t, *self.params) for t in self.maturities
        ])
        return self

    def fitted_discount_factors(self) -> np.ndarray:
        """Return the fitted discount factors (after calling fit)."""
        if self._fitted_df is None:
            raise RuntimeError("Call fit() first")
        return self._fitted_df

    def plot(
        self,
        market_df: Optional[np.ndarray] = None,
        title: str = "Nelson-Siegel Fit",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> plt.Figure:
        """Plot market vs fitted discount factors (or spot rates if market_df
        is not provided)."""
        if self.params is None:
            raise RuntimeError("Call fit() first")
        t = self.maturities
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(t, self.discount_factors, "o", color="black", label="Market DF")
        ax.plot(t, self._fitted_df, "-", color="red", label="Nelson-Siegel DF")
        ax.set_xlabel("Maturity (years)")
        ax.set_ylabel("Discount Factor")
        ax.set_title(title)
        ax.legend()
        ax.grid(alpha=0.3)
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        if show:
            plt.show()
        return fig
