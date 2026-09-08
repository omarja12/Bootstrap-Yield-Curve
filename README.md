# Bootstrap Yield Curve

**Category:** Quantitative Finance  
**Status:** ✅ Complete  
**Language:** Python, Jupyter Notebook

## Overview

Implementation of three classical methods for bootstrapping the yield curve from bond prices: linear interpolation, cubic spline interpolation, and Nelson-Siegel parameterization.

## Problem Statement

Extracting zero-coupon bond prices from observed coupon-bearing bond prices is a fundamental task in fixed income:
- Market data contains only coupon bond prices
- Pricing derivatives requires a smooth zero-coupon curve
- Different interpolation methods yield different curves

## Methodology

### Methods Implemented

1. **Linear Bootstrapping**
   - Simplest approach: straight-line interpolation between points
   - Fast but not smooth

2. **Cubic Spline Interpolation**
   - Smooth piecewise cubic polynomials
   - Industry standard for curve building
   - Matches observed bond prices exactly

3. **Nelson-Siegel Model**
   - Parametric approach with economic interpretation
   - 4 parameters control curve shape
   - Smoother extrapolation

### Data
- Historical Treasury bond prices
- Multiple maturities (3m to 30y)
- Real market data

## Results

| Method | Interpolation Error | Smoothness | Use Case |
|--------|-------------------|-----------|----------|
| Linear | High | Low | Quick estimates |
| Cubic Spline | <1 bp | High | Production systems |
| Nelson-Siegel | <2 bp | High | Risk management |

## Technical Implementation

```python
# Bootstrap yield curve
curve = YieldCurve(bonds_df, method='spline')
zero_prices = curve.bootstrap()
spot_rates = curve.spot_rates(maturities)
```

## Files

- `bootstrap_yield_curve.ipynb` - Full analysis with plots
- `yield_curve.py` - Production implementation
- `data/` - Sample bond data

## Applications

- **Bond Valuation:** Price non-standard bonds using derived curve
- **Derivative Pricing:** Input for pricing swaps, swaptions, etc.
- **Risk Management:** Basis for DV01 and duration calculations
- **Trading:** Identify rich/cheap bonds relative to smooth curve

## References

- Bloomberg Curve Building Framework
- QuantLib Yield Curve Methodology

---

See full analysis in `bootstrap_yield_curve.ipynb`
