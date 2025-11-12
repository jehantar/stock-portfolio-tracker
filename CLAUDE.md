# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stock Portfolio Tracker with basket rebalancing - tracks portfolio performance across multiple time periods with different stock selections, calculating rollover returns and comparing against S&P 500 benchmark.

## Development Commands

### Setup and Testing
```bash
# Verify setup (checks dependencies and API keys)
python3 test_setup.py

# Install dependencies
pip install -r requirements.txt
```

### Running the Tracker

```bash
# Interactive mode (prompts for basket input)
python3 portfolio_tracker.py

# Auto mode (loads existing portfolio_config.yaml)
python3 portfolio_tracker.py --auto

# Use custom config file
python3 portfolio_tracker.py --config my_portfolio.yaml

# Compare multiple portfolios
python3 portfolio_tracker.py --compare portfolio_config.yaml portfolio_config_alt.yaml
```

### Testing Specific Features

```bash
# Test with minimal config for debugging
python3 portfolio_tracker.py --config portfolio_config.example.yaml --auto

# Run with unbuffered output (useful for debugging)
python3 -u portfolio_tracker.py --auto
```

## Architecture

### Data Flow

1. **Configuration** → `PortfolioConfig` dataclass with multiple `Basket` objects
2. **Data Download** → Bulk export from NASDAQ Data Link API (or SDK fallback)
3. **Benchmark** → S&P 500 data from FRED using pandas_datareader
4. **Calculation** → Equal-weighted basket returns with rollover compounding
5. **Visualization** → matplotlib charts with metrics and annotations

### Key Components

**portfolio_tracker.py:264-327** (`calculate_portfolio_returns`)
- Core logic for basket rebalancing and rollover calculations
- Normalizes each stock to 1.0 at basket start, averages performance
- Carries forward ending value as next basket's starting value (compounding)

**portfolio_tracker.py:117-212** (`download_nasdaq_prices`)
- Bulk export API with async polling pattern (mimics Projects/momentum/data/prices.py)
- Handles ZIP/GZIP compression with latin1 encoding fallback
- Downloads ALL market tickers (7k+) but filters to needed ones - faster than SDK individual requests

**portfolio_tracker.py:215-262** (`download_sp500_benchmark`)
- Uses pandas_datareader with FRED 'SP500' series
- Forward fill + backfill for NaN handling on holidays/weekends
- Pattern from Projects/momentum/data/benchmarks.py

**portfolio_tracker.py:556-594** (`calculate_advanced_metrics`)
- Sharpe ratio (252 trading days for annualization, assumes 0% risk-free rate)
- Maximum drawdown (peak-to-trough decline)
- Annualized volatility (daily std * sqrt(252))
- Win rate (% of positive return days)

**portfolio_tracker.py:597-728** (`compare_portfolios`)
- Loads multiple configs, downloads data ONCE for all portfolios
- Calculates metrics for each, creates comparison chart
- Sorts by total return for ranking

### Configuration Format

YAML files with structure:
```yaml
baskets:
  - tickers: [TICKER1, TICKER2, ...]
    start_date: "YYYY-MM-DD"
  - tickers: [TICKER3, TICKER4, ...]
    start_date: "YYYY-MM-DD"  # Next basket starts here (previous ends)
end_date: "YYYY-MM-DD"
```

Multiple baskets create rebalancing points where portfolio transitions from one set of stocks to another with cumulative returns.

## API Integration Patterns

### NASDAQ Data Link (Bulk Export)
- Async pattern: request export → poll status URL → download when ready
- Handles compression: ZIP (multiple files) or GZIP (single file)
- Encoding fallback: UTF-8 → latin1 with error replacement
- Timeout: 300s polling with 5s intervals
- Mimics: `Projects/momentum/data/prices.py`

### FRED (Benchmark Data)
- Uses pandas_datareader, NOT fredapi.Fred directly
- Series: 'SP500' for daily S&P 500 index values
- Normalizes to portfolio start at 100 for comparison
- Handles missing data with forward/backfill
- Mimics: `Projects/momentum/data/benchmarks.py`

## Important Implementation Details

### Rollover Return Calculation
When transitioning between baskets:
1. Basket 1: Start at 100, calculate equal-weighted return, end at (e.g.) 115
2. Basket 2: Start at 115 (not 100!), calculate return, end at (e.g.) 138
3. Total return: 38%, NOT sum of individual returns (compounding effect)

### Equal-Weighted Baskets
- Each stock normalized to 1.0 at basket's start_date
- Average normalized performance across all tickers
- No custom position sizing (all stocks contribute equally)

### Date Handling
- Basket end_date = next basket's start_date (OR final end_date for last basket)
- Benchmark filtered to exact portfolio date range
- Date filtering uses >= start and < end (exclusive end for transitions)

## Common Issues and Fixes

### UnicodeDecodeError in Bulk Export
- Issue: NASDAQ CSV sometimes has non-UTF-8 characters
- Fix: Use `encoding="latin1", encoding_errors="replace"` when reading CSV
- See: portfolio_tracker.py:198-208

### S&P 500 Showing NaN
- Issue: FRED data has holidays/weekends as NaN
- Fix: Use both `ffill()` and `bfill()`, then `dropna()` before normalization
- Validate initial value != 0
- See: portfolio_tracker.py:240-253

### Bulk Export Timeout/Failure
- Issue: NASDAQ API occasionally fails or times out
- Fix: Automatic fallback to SDK method (slower, ticker-by-ticker)
- See: portfolio_tracker.py:845-853

### Process Hanging (No Output)
- Issue: Python buffering prevents real-time output
- Fix: Run with `python3 -u` flag for unbuffered output
- See usage in background bash processes

## Output Files

- `charts/portfolio_performance.png` - Single portfolio chart with metrics
- `charts/portfolio_comparison.png` - Multi-portfolio comparison chart
- `portfolio_config.yaml` - User's portfolio configuration (gitignored)
- `.env` - API keys (gitignored)

## Testing Approach

When testing changes:
1. Use `portfolio_config.example.yaml` or create minimal test config
2. Start with recent dates (last 1-2 years) for faster data download
3. Use 2-3 well-known tickers (AAPL, MSFT, GOOGL) for reliable data
4. Check both console output and generated charts
5. For comparison feature, create 2+ configs with overlapping date ranges

## Environment Variables

Required:
- `NASDAQ_DATA_LINK_API_KEY` - Get from https://data.nasdaq.com/sign-up (free tier: 50 calls/day)

Optional:
- `FRED_API_KEY` - Get from https://fred.stlouisfed.org/docs/api/api_key.html (for benchmark data)

If FRED key missing, script runs but skips S&P 500 comparison.
