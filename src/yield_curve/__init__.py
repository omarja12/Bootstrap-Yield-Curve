"""
Yield curve analysis package.

Provides bootstrapping of discount factors, spot rates, and forward rates
from coupon-bearing bonds, plus Nelson-Siegel yield curve fitting, and
Markowitz mean-variance portfolio analysis on equity panels.
"""

from ._version import __version__
from .bootstrap import NelsonSiegel, YieldCurve
from .portfolio import PortfolioAnalyzer, fetch_prices_from_yfinance

__all__ = [
    "NelsonSiegel",
    "PortfolioAnalyzer",
    "YieldCurve",
    "__version__",
    "fetch_prices_from_yfinance",
]
