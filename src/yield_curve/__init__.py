"""
Yield curve analysis package.

Provides bootstrapping of discount factors, spot rates, and forward rates
from coupon-bearing bonds, plus Nelson-Siegel yield curve fitting.

Original exercise: August 2022.
Refactored into a package: September 2026.
"""

from .bootstrap import YieldCurve, NelsonSiegel

__all__ = ["YieldCurve", "NelsonSiegel"]
