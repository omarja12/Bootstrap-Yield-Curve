# Bootstrap-Yield-Curve

A 2022 coursework notebook that bootstraps a yield curve from ten government bonds three ways, then looks at returns and correlation for five tech stocks. Everything is in one notebook: [`Bootstrapping_Yield_Curve.ipynb`](Bootstrapping_Yield_Curve.ipynb).

**This repository is archived.** The notebook has known defects (listed below) and is kept unchanged as a dated record of the original work. A corrected rebuild lives in [curve-and-portfolio](https://github.com/omarja12/curve-and-portfolio).

## What the notebook does

**Part one: the curve.** A `YieldCurve` class takes an `n x 3` array of bonds (maturity, dirty price, coupon rate), builds the cash-flow matrix and bootstraps the discount factors. The input is ten bonds with maturities of 1 to 10 years and par value 100. From the discount factors it derives spot rates, yield to maturity and one-year forward rates.

The discount factors are computed three ways:

- matrix operations (solving the linear system directly);
- a global optimiser that minimises the squared pricing error;
- forward substitution.

**Part two: returns and correlation.** Daily prices for AAPL, IBM, MSFT, GOOG and AMZN from Yahoo Finance, from 1 January 2012. The data was downloaded in 2026 for this part, and the script that fetched it is not in the repository.

## Known issues

- The matrix and forward-substitution methods solve the same triangular system, so their agreement to machine precision is expected and does not show that the bootstrap is right. The global optimiser differs from them by about 5.8e-9.
- `YieldCurve` uses a global variable `y`. A second instance silently returns the first curve's solver result, and if `y` is undefined the solver raises a `NameError`.
- The forward rates in the notebook use an approximation that is off by up to 1.7 bp.
- Plot year labels and a ticker label do not match the data.
- The notebook was written against 2022 library versions and may not run unchanged today.

## Licence

See [LICENSE](LICENSE).
