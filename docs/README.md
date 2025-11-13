# Stock Portfolio Tracker with Basket Rebalancing

Track your stock portfolio performance over time with support for rebalancing across multiple baskets. Compare your returns against the S&P 500 benchmark.

## Features

- **Multiple Basket Support**: Track portfolio performance across different stock selections over time
- **Rollover Returns**: Automatically calculates cumulative returns when transitioning between baskets
- **Benchmark Comparison**: Compare your portfolio against S&P 500 performance
- **Interactive Input**: Easy-to-use prompts for entering baskets and dates
- **Configuration Files**: Save and load portfolio configurations for repeated analysis
- **Professional Visualization**: Charts with transition markers, performance metrics, and annotations

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your API keys:
   - Copy `.env.template` to `.env`
   - Add your NASDAQ Data Link API key (required)
   - Add your FRED API key (optional, for S&P 500 benchmark)

```bash
cp .env.template .env
# Edit .env and add your keys
```

## Usage

### Interactive Mode

Run the script and follow the prompts:

```bash
python portfolio_tracker.py
```

The script will ask you to:
1. Enter stock tickers for each basket (comma-separated)
2. Enter the start date for each basket
3. Optionally add more baskets (for rebalancing)
4. Enter the end date for analysis (or use today)

### Example Session

```
--- Basket 1 ---
Enter stock tickers for basket 1: AAPL,MSFT,GOOGL
Enter start date for basket 1 (YYYY-MM-DD): 2024-01-01

Add another basket? (y/n): y

--- Basket 2 ---
Enter stock tickers for basket 2: NVDA,AMD,TSM
Enter transition date to basket 2 (YYYY-MM-DD): 2024-06-01

Add another basket? (y/n): n

Enter end date for analysis (YYYY-MM-DD, or press Enter for today): 2024-12-31
```

### Configuration File

Save your portfolio configuration for repeated analysis:

```yaml
baskets:
  - tickers: [AAPL, MSFT, GOOGL]
    start_date: "2024-01-01"
  - tickers: [NVDA, AMD, TSM]
    start_date: "2024-06-01"
  - tickers: [META, AMZN]
    start_date: "2024-09-01"
end_date: "2024-12-31"
```

The script will automatically detect and offer to load `portfolio_config.yaml` if it exists.

## How It Works

### Rollover Return Calculation

When you transition from one basket to another, the script:

1. Calculates the equal-weighted return of Basket 1 from its start date to the transition date
2. Applies this return to the initial portfolio value (100)
3. Uses the ending value as the starting point for Basket 2
4. Continues this process for all baskets

**Example:**
- Basket 1 (AAPL, MSFT): Jan 1 → Jun 1, gains 15%
  - Portfolio: 100 → 115
- Basket 2 (NVDA, AMD): Jun 1 → Dec 31, gains 20%
  - Portfolio: 115 → 138
- Total return: 38%

### Equal-Weighted Baskets

Each stock in a basket contributes equally to the basket's performance. This is calculated by:

1. Normalizing each stock's price to 1.0 at the basket's start date
2. Averaging the normalized prices across all stocks in the basket
3. Applying the average performance to the portfolio value

## Output

The script generates:

1. **Console Output**:
   - Download progress
   - Basket-by-basket performance
   - Final summary statistics

2. **Performance Chart** (`charts/portfolio_performance.png`):
   - Portfolio value over time
   - S&P 500 benchmark (if FRED API key provided)
   - Vertical lines marking basket transitions
   - Annotations showing which stocks were held in each period
   - Metrics box with returns, annualized returns, and outperformance

## API Keys

### NASDAQ Data Link API Key (Required)

Get your free API key at: https://data.nasdaq.com/sign-up

The free tier includes:
- 50 API calls per day
- Access to SHARADAR equity prices
- Sufficient for most portfolio tracking needs

### FRED API Key (Optional)

Get your free API key at: https://fred.stlouisfed.org/docs/api/api_key.html

Used for fetching S&P 500 benchmark data.

## Data Source

Stock prices are sourced from NASDAQ Data Link (formerly Quandl) using the SHARADAR/SEP dataset, which provides:
- Daily closing prices for all US equities
- High-quality, survivorship-bias-free data
- Historical data going back decades

## Limitations

- Requires NASDAQ Data Link subscription for comprehensive historical data
- Equal-weighted baskets only (no custom position sizing)
- Does not account for dividends, splits, or trading costs
- Weekend/holiday prices are interpolated from benchmark data

## Future Enhancements

- Web application interface (Flask + Plotly)
- Custom position sizing (dollar amounts per stock)
- Dividend reinvestment modeling
- Multiple portfolio comparison
- Export to CSV/Excel
- Real-time price updates

## License

MIT License - Feel free to modify and use as needed!
