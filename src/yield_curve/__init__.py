"""
Yield curve analysis package.

Provides bootstrapping of discount factors, spot rates, and forward rates
from coupon-bearing bonds, plus Nelson-Siegel yield curve fitting, and
Markowitz mean-variance portfolio analysis on equity panels.

Original exercise: August 2022.
Refactored into a package: September 2026.
"""

from .bootstrap import YieldCurve, NelsonSiegel
from .portfolio import PortfolioAnalyzer, fetch_prices_from_yfinance

__version__ = "2.0.0"

__all__ = ["YieldCurve", "NelsonSiegel", "PortfolioAnalyzer", "fetch_prices_from_yfinance"]
