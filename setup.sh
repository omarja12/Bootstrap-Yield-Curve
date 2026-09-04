#******************************************************************************
# Bootstrap Yield Curve — environment bootstrap
#******************************************************************************
#
# One-command setup so a reviewer (or CI) can spin up the full environment
# from a fresh clone in under a minute.
#
# Usage (POSIX shell — bash/zsh/MSYS2):
#     bash setup.sh
#
# What it does:
#   1. Creates a virtual environment in .venv/
#   2. Upgrades pip and installs the package + dev dependencies from
#      pyproject.toml (editable mode).
#   3. Installs the optional yfinance extra (for live market data).
#   4. Runs the test suite to prove everything is wired correctly.
#   5. Runs the demo notebook via nbconvert (headless, no browser needed)
#      so all five PNG outputs are produced on first run.
#
# Requirements:
#   - Python 3.8+
#   - A POSIX-compatible shell (bash, zsh, MSYS2 on Windows)
#   - Network access to PyPI (and Yahoo Finance if you want live data)
#
# After running:
#   - Activate the venv:  source .venv/bin/activate   (Windows: .venv\\Scripts\\activate)
#   - Open the notebook:  jupyter lab notebooks/Yield_Curve_And_Portfolio_Analysis.ipynb
#   - Or run headless:     python notebooks/run_analysis.py
#   - Read the docs:      cat README.md
#   - Open the webpage:   open index.html      (macOS)
#                          start index.html     (Windows)
#                          xdg-open index.html  (Linux)
#
# If you only want the core package (no yfinance, no notebook execution):
#     pip install -e ".[dev]"
#
#******************************************************************************

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
PYTHON="${PYTHON:-python3}"

echo "==> Bootstrap Yield Curve — environment setup"
echo "    Repo root: $REPO_ROOT"
echo ""

# --- 0. Detect Python -------------------------------------------------------

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "ERROR: '$PYTHON' not found on PATH."
    echo "       Set the PYTHON environment variable to a working python3, e.g."
    echo "           PYTHON=/usr/bin/python3 bash setup.sh"
    exit 1
fi

PY_VERSION=$("$PYTHON" --version 2>&1)
echo "    Using: $PY_VERSION at $(command -v "$PYTHON")"

# --- 1. Virtual environment -------------------------------------------------

if [ -d "$VENV_DIR" ]; then
    echo "==> Virtual environment already exists at $VENV_DIR"
    echo "    (delete it manually with: rm -rf $VENV_DIR)"
else
    echo ""
    echo "==> Creating virtual environment in .venv/ ..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# Activate without relying on the caller's shell
# (some CI runners do not source .venv/bin/activate for you)
ACTIVATE="$VENV_DIR/bin/activate"
if [ -f "$ACTIVATE" ]; then
    # shellcheck disable=SC1091
    . "$ACTIVATE"
else
    echo "ERROR: activate script not found at $ACTIVATE"
    exit 1
fi

# Make sure we use the venv python from here on
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

# --- 2. Upgrade core tooling -----------------------------------------------

echo ""
echo "==> Upgrading pip, setuptools, wheel ..."
"$PIP" install --quiet --upgrade pip setuptools wheel

# --- 3. Install the package (editable) + dev + yfinance -------------------

echo ""
echo "==> Installing yield-curve (editable) with dev + yfinance extras ..."
echo "    (this may take a minute on first run)"
"$PIP" install --quiet --upgrade -e ".[dev,yfinance]"

# --- 4. Run the test suite -------------------------------------------------

echo ""
echo "==> Running test suite ..."
"$PYTHON" -m pytest tests/ -v --tb=short

# --- 5. Execute the analysis notebook (headless) --------------------------

echo ""
echo "==> Executing the analysis notebook (headless, produces PNGs) ..."
if ! command -v jupyter >/dev/null 2>&1; then
    echo "    WARNING: 'jupyter' not on PATH — skipping notebook execution."
    echo "    Install it with:  pip install jupyterlab nbconvert"
else
    "$PYTHON" -m nbconvert \
        --to notebook \
        --execute \
        --ExecutePreprocessor.timeout=180 \
        --output Yield_Curve_And_Portfolio_Analysis.ipynb \
        --allow-errors \
        notebooks/Yield_Curve_And_Portfolio_Analysis.ipynb
    echo "    Done. Outputs:"
    for png in yield_curve_overview.png nelson_siegel_fit.png cumulative_returns.png correlation_heatmap.png efficient_frontier.png; do
        if [ -f "$REPO_ROOT/$png" ]; then
            echo "      ✓ $png"
        else
            echo "      ✗ $png (missing)"
        fi
    done
fi

# --- 6. Lint (optional, non-fatal) ----------------------------------------

echo ""
echo "==> Quick lint check (ruff, non-fatal) ..."
if command -v ruff >/dev/null 2>&1; then
    ruff check src/ tests/ || echo "    (ruff found issues — see above)"
else
    echo "    (ruff not installed — skipping; add it with: pip install ruff)"
fi

# --- Done ------------------------------------------------------------------

echo ""
echo "==========================================================================="
echo "  Setup complete."
echo ""
echo "  Next steps:"
echo "    1. Activate the venv:  source .venv/bin/activate"
echo "    2. Open the notebook:  jupyter lab notebooks/Yield_Curve_And_Portfolio_Analysis.ipynb"
echo "    3. Or run headless:     python notebooks/run_analysis.py"
echo "    4. Read the docs:       cat README.md"
echo "    5. Open the webpage:    open index.html"
echo ""
echo "  Package API (import from any script after activating the venv):"
echo ""
echo "      from yield_curve import YieldCurve, NelsonSiegel, PortfolioAnalyzer"
echo ""
echo "==========================================================================="
