# Bootstrap Yield Curve

A quantitative finance toolkit for **bootstrapping yield curves** from coupon-bearing bonds and **analyzing equity portfolios**, built and maintained by [Omar J](https://github.com/omarja12).

- **Package:** `yield_curve` — pure-Python, minimal dependencies, well-tested.
- **Origin:** a Computational Finance exercise (August 2022), refactored into a maintainable Python package (September 2026).
- **Right now:** bootstrapping discount factors three ways + Nelson-Siegel fitting + Markowitz efficient frontier.

---

## What's in the box

### 1. Yield curve bootstrapping (the original exercise, elevated)

The core `YieldCurve` class takes a set of Treasury bonds (maturity, price, coupon) and bootstraps:

| What | How |
|------|-----|
| **Discount factors** | matrix solve (`np.linalg.solve`), global optimum (`scipy.optimize.minimize`), and an iterative forward-substitution procedure |
| **Spot rates** | from discount factors, annual compounding |
| **Yield to maturity** | per bond via `numpy_financial.irr` |
| **Forward rates** | 1-year forward rates from the spot curve |

Plus a **Nelson-Siegel** parametric fit (`NelsonSiegel` class) — the industry-standard curve model, implemented from scratch and fitted by least squares.

### 2. Portfolio analysis (the "what's next" on the original stock-data exercise)

The `PortfolioAnalyzer` class works with daily price panels to compute:

| What | How |
|------|-----|
| Daily / annualized returns, volatility, Sharpe ratio | from a price DataFrame |
| Efficient frontier | quadratic optimization over target returns |
| Maximum-Sharpe portfolio | direct optimization |
| Correlation heatmap | seaborn-style |
| Cumulative returns plot | matplotlib |

It can pull market data from **yfinance** if you want live prices, or you can pass in your own DataFrame.

---

## Quick start

```bash
# Clone this repo
git clone https://github.com/omarja12/Bootstrap-Yield-Curve.git
cd Bootstrap-Yield-Curve

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# Install the package + dev tools
pip install -e ".[dev]"

# Run the tests
pytest tests/ -v

# Open the demo notebook
jupyter lab notebooks/demo.ipynb
```

### As a package (in your own project)

```python
from yield_curve import YieldCurve, NelsonSiegel
import numpy as np

# --- Example: bootstrap a yield curve from Treasury bonds ---

bonds = np.array([
    [1, 96.60, 0.0150],
    [2, 93.71, 0.0175],
    [3, 91.56, 0.0200],
    [4, 90.24, 0.0225],
    [5, 89.74, 0.0250],
    [6, 90.04, 0.0275],
    [7, 91.09, 0.0300],
    [8, 92.82, 0.0325],
    [9, 95.19, 0.0350],
    [10, 98.14, 0.0375],
], dtype=float)

yc = YieldCurve(bonds)

# Three ways — they all agree
df_matrix   = yc.discount_factors("Matrix operations")
df_solver   = yc.discount_factors("Global Solver")
df_iter     = yc.discount_factors("Iterative Procedure")

# Derived quantities
spot_rates  = yc.spot_rates()
ytm         = yc.bonds_ytm()
forward_rates = yc.forward_rates()

# Visualize
fig = yc.plot_rates(title="US Treasury Yield Curve (bootstrap)")
# fig.savefig("yield_curve.png", dpi=150)

# --- Example: Nelson-Siegel fit ---

ns = NelsonSiegel(
    maturities=np.array([1, 2, 3, 5, 7, 10], dtype=float),
    discount_factors=df_matrix,
)
ns.fit()
fig2 = ns.plot()
# fig2.savefig("nelson_siegel_fit.png", dpi=150)

# --- Example: portfolio analysis ---

from yield_curve import PortfolioAnalyzer

prices = <your DataFrame: columns=tickers, index=dates>
pa = PortfolioAnalyzer(prices, risk_free_rate=0.045)

frontier = pa.efficient_frontier(n_points=50)
max_sharpe = pa.max_sharpe_portfolio()

print(f"Max Sharpe: {max_sharpe['sharpe']:.3f}")
print("Weights:", max_sharpe["weights"])
```

---

## Package structure

```
Bootstrap-Yield-Curve/
├── notebooks/
│   └── Bootstrapping_Yield_Curve.ipynb   # original exercise (2022) — preserved for the record
│   └── demo.ipynb                        # modern demo using the package
├── src/
│   └── yield_curve/
│       ├── __init__.py
│       ├── bootstrap.py        # YieldCurve, NelsonSiegel
│       └── portfolio.py        # PortfolioAnalyzer, yfinance helper
├── tests/
│   └── test_bootstrap.py       # pytest suite
├── LICENSE
├── pyproject.toml
├── requirements.txt
└── README.md
```

The original Jupyter notebook (`notebooks/Bootstrapping_Yield_Curve.ipynb`) is kept as-is: it documents the step-by-step exploration that the package now encapsulates. The new `demo.ipynb` shows how to use the package API directly.

---

## Requirements

| Package | Version | Purpose |
|---------|---------|---------|
| `numpy` | ≥ 1.20 | array ops, linear algebra |
| `scipy` | ≥ 1.7 | optimization (solver, efficient frontier) |
| `pandas` | ≥ 1.3 | DataFrame plumbing |
| `matplotlib` | ≥ 3.4 | plotting |
| `seaborn` | ≥ 0.11 | styling |
| `numpy-financial` | ≥ 0.2 | IRR for YTM |

**Optional:**
- `yfinance` — live market data for the portfolio module

---

## Background (why this exists)

### Bootstrap, in plain terms

Given the price of a bond that pays coupons at known times, what is the "fair" discount factor for each future date? If you have bonds of different maturities, you can solve for the discount factor curve piece by piece: the 1-year bond pins down the 1-year discount factor; the 2-year bond then pins down the 2-year factor given the 1-year factor you already have. That's **bootstrapping** — building the curve from the ground up, instrument by instrument.

Three computational routes to the same answer:
1. **Matrix operations** — set up the cash-flow matrix and solve the linear system directly. Fast, exact, and the baseline.
2. **Global solver** — minimize the squared error between model prices and market prices. Useful when the system isn't perfectly determined.
3. **Iterative procedure** — a step-by-step forward substitution that mirrors how a trader would actually build the curve by hand.

### Why Nelson-Siegel?

The bootstrapped curve from a handful of bonds is jagged and depends on the instruments you happened to have. Nelson-Siegel (and its extension, Svensson) gives a **smooth, parametric** curve with only a few parameters (level, slope, curvature, decay). It's the workhorse of central banks and dealers for exactly this reason. Implementing it from scratch here gives the bootstrapping exercise a real-world counterpart.

### Portfolio analysis — where it fits

Once you have a yield curve, you have a risk-free rate. Plug that into a mean-variance framework and you can measure Sharpe ratios, draw an efficient frontier, and find the tangency portfolio. That's the bridge between the yield-curve work and the equity-data work in this repo.

---

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).

---

## History

This repo began in **August 2022** as a single Jupyter notebook (`Bootstrapping_Yield_Curve.ipynb`) documenting a Computational Finance assignment. The notebook is preserved in `notebooks/` for the record — it still runs, and the original plots are in its output cells.

In **September 2026**, the code was extracted into a proper Python package (`src/yield_curve/`), tested, given CI, and extended with Nelson-Siegel fitting and Markowitz portfolio analysis. The original notebook is untouched; the package is the upgraded surface.

---

## Contributing

Issues and PRs welcome — especially:
- Adding Nelson-Siegel-Svensson (three-factor extension with an extra decay term)
- Adding cubic-spline / monotonic-spline bootstrapping options
- Broader market-data connectors (FRED, Treasury.gov, etc.)
- More tests (arbitrage-free checks, monotonicity, integration tests with live data)

---

*Built as a portfolio piece for quant / data-science roles. If you use this in your own work, consider dropping a note in the issues — always good to know where these things end up.*
