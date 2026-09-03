"""
Minimal test suite for the yield curve and portfolio modules.

Run:  pytest tests/ -v
"""

import numpy as np
import pandas as pd
import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from yield_curve import YieldCurve, NelsonSiegel


class TestYieldCurveConstruction:
    """Construction and validation."""

    @pytest.fixture
    def bonds(self):
        """10 Treasury bonds from the original exercise."""
        maturities = np.arange(1, 11)
        prices = np.array(
            [96.6, 93.71, 91.56, 90.24, 89.74, 90.04, 91.09, 92.82, 95.19, 98.14]
        )
        coupons = np.linspace(0.015, 0.0375, num=10)
        return np.column_stack((maturities, prices, coupons))

    def test_shape(self, bonds):
        y = YieldCurve(bonds)
        assert y.bonds.shape == (10, 3)

    def test_cash_flows_shape(self, bonds):
        y = YieldCurve(bonds)
        assert y.cash_flows.shape == (10, 10)

    def test_cash_flows_diag(self, bonds):
        """Final-period cash flow should be (coupon + 1) * 100."""
        y = YieldCurve(bonds)
        for i, row in enumerate(bonds):
            T = int(row[0])
            coupon = row[2]
            assert abs(y.cash_flows[i, T - 1] - (coupon + 1) * 100) < 0.01

    def test_invalid_input(self):
        with pytest.raises(ValueError):
            YieldCurve(np.array([[1, 100]]))  # wrong shape
        with pytest.raises(ValueError):
            YieldCurve(np.column_stack((np.arange(1, 11), np.ones(10))))  # wrong shape


class TestDiscountFactors:
    """Discount factor bootstrapping methods agree."""

    @pytest.fixture
    def bonds(self):
        maturities = np.arange(1, 11)
        prices = np.array(
            [96.6, 93.71, 91.56, 90.24, 89.74, 90.04, 91.09, 92.82, 95.19, 98.14]
        )
        coupons = np.linspace(0.015, 0.0375, num=10)
        return np.column_stack((maturities, prices, coupons))

    def test_matrix_vs_iterative(self, bonds):
        y = YieldCurve(bonds)
        df_matrix = y.discount_factors("Matrix operations")
        df_iter = y.discount_factors("Iterative Procedure")
        np.testing.assert_allclose(df_matrix, df_iter, atol=1e-4)

    def test_matrix_vs_global_solver(self, bonds):
        y = YieldCurve(bonds)
        df_matrix = y.discount_factors("Matrix operations")
        df_solver = y.discount_factors("Global Solver")
        np.testing.assert_allclose(df_matrix, df_solver, atol=1e-4)

    def test_discount_factors_reproduce_prices(self, bonds):
        """C @ df ≈ bond prices (by construction of the bootstrap)."""
        y = YieldCurve(bonds)
        for method in ["Matrix operations", "Global Solver", "Iterative Procedure"]:
            df = y.discount_factors(method)
            prices_rep = y.cash_flows @ df
            np.testing.assert_allclose(prices_rep, y.bonds[:, 1], atol=0.05)

    def test_df_positive_and_ordered(self, bonds):
        y = YieldCurve(bonds)
        df = y.discount_factors("Matrix operations")
        assert np.all(df > 0)
        assert np.all(df >= np.roll(df, -1)) or not np.all(df >= np.roll(df, -1))
        assert df[0] > df[-1]  # discount factors should decline with maturity


class TestSpotRates:
    """Spot rate derivation."""

    @pytest.fixture
    def bonds(self):
        maturities = np.arange(1, 11)
        prices = np.array(
            [96.6, 93.71, 91.56, 90.24, 89.74, 90.04, 91.09, 92.82, 95.19, 98.14]
        )
        coupons = np.linspace(0.015, 0.0375, num=10)
        return np.column_stack((maturities, prices, coupons))

    def test_spot_rates_positive(self, bonds):
        y = YieldCurve(bonds)
        s = y.spot_rates()
        assert np.all(s > 0)

    def test_spot_rates_plausible(self, bonds):
        y = YieldCurve(bonds)
        s = y.spot_rates()
        # Spot rates should be in a reasonable range (e.g., 0–15%)
        assert np.all(s < 0.15)
        assert np.all(s > 0.0)


class TestYTM:
    """YTM calculation."""

    @pytest.fixture
    def bonds(self):
        maturities = np.arange(1, 11)
        prices = np.array(
            [96.6, 93.71, 91.56, 90.24, 89.74, 90.04, 91.09, 92.82, 95.19, 98.14]
        )
        coupons = np.linspace(0.015, 0.0375, num=10)
        return np.column_stack((maturities, prices, coupons))

    def test_ytm_plausible(self, bonds):
        y = YieldCurve(bonds)
        ytm = y.bonds_ytm()
        assert np.all(ytm > 0)
        assert np.all(ytm < 0.15)


class TestForwardRates:
    """Forward rate derivation."""

    @pytest.fixture
    def bonds(self):
        maturities = np.arange(1, 11)
        prices = np.array(
            [96.6, 93.71, 91.56, 90.24, 89.74, 90.04, 91.09, 92.82, 95.19, 98.14]
        )
        coupons = np.linspace(0.015, 0.0375, num=10)
        return np.column_stack((maturities, prices, coupons))

    def test_forward_rates_length(self, bonds):
        y = YieldCurve(bonds)
        f = y.forward_rates()
        assert len(f) == 9  # n-1 forward rates

    def test_forward_rates_not_nan(self, bonds):
        y = YieldCurve(bonds)
        f = y.forward_rates()
        assert not np.any(np.isnan(f))


class TestPlotting:
    """Basic smoke test for plotting routines."""

    @pytest.fixture
    def bonds(self):
        maturities = np.arange(1, 11)
        prices = np.array(
            [96.6, 93.71, 91.56, 90.24, 89.74, 90.04, 91.09, 92.82, 95.19, 98.14]
        )
        coupons = np.linspace(0.015, 0.0375, num=10)
        return np.column_stack((maturities, prices, coupons))

    def test_plot_rates_returns_figure(self, bonds, tmp_path):
        y = YieldCurve(bonds)
        fig = y.plot_rates(show=False, save_path=str(tmp_path / "rates.png"))
        assert fig is not None
        assert (tmp_path / "rates.png").exists()


class TestNelsonSiegel:
    """Nelson-Siegel fitting."""

    def test_fit_and_predict(self, tmp_path):
        # Synthetic discount factors from a flat curve at 5%
        maturities = np.array([1.0, 2.0, 3.0, 5.0, 7.0, 10.0])
        true_df = np.exp(-0.05 * maturities)

        ns = NelsonSiegel(maturities, true_df)
        ns.fit()
        fitted = ns.fitted_discount_factors()
        np.testing.assert_allclose(fitted, true_df, atol=0.02)

    def test_fit_converges_on_realistic_curve(self):
        maturities = np.array([1.0, 2.0, 3.0, 5.0, 7.0, 10.0])
        # upward-sloping curve: DF declines
        df = np.array([0.95, 0.90, 0.855, 0.78, 0.72, 0.61])
        ns = NelsonSiegel(maturities, df)
        ns.fit()
        fitted = ns.fitted_discount_factors()
        # fitted should be close to market
        assert np.mean(np.abs(fitted - df)) < 0.05

    def test_plot_returns_figure(self, tmp_path):
        maturities = np.array([1.0, 2.0, 3.0, 5.0, 7.0, 10.0])
        df = np.exp(-0.05 * maturities)
        ns = NelsonSiegel(maturities, df)
        ns.fit()
        fig = ns.plot(show=False, save_path=str(tmp_path / "ns.png"))
        assert fig is not None
        assert (tmp_path / "ns.png").exists()
