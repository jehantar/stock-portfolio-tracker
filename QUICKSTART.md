# Quick Start Guide

## 1. Verify Setup

```bash
python3 test_setup.py
```

This will check that all dependencies and API keys are configured correctly.

## 2. Run the Portfolio Tracker

```bash
python3 portfolio_tracker.py
```

## 3. Example Usage

Here's a sample interactive session:

```
=================================================
STOCK PORTFOLIO TRACKER - Interactive Mode
=================================================

Enter your stock baskets...

--- Basket 1 ---
Enter stock tickers for basket 1: AAPL,MSFT,GOOGL
Enter start date for basket 1 (YYYY-MM-DD): 2024-01-01
✓ Added basket 1: AAPL, MSFT, GOOGL starting 2024-01-01

Add another basket? (y/n): y

--- Basket 2 ---
Enter stock tickers for basket 2: NVDA,AMD
Enter transition date to basket 2 (YYYY-MM-DD): 2024-07-01
✓ Added basket 2: NVDA, AMD starting 2024-07-01

Add another basket? (y/n): n

Enter end date (press Enter for today):

✓ Portfolio configured with 2 basket(s)
```

## 4. Understanding the Output

The script will:

1. **Download data** from NASDAQ (may take 1-2 minutes for bulk export)
2. **Calculate returns** for each basket with automatic rollover
3. **Generate a chart** saved to `charts/portfolio_performance.png`
4. **Display metrics**:
   - Total return %
   - Annualized return %
   - Days held
   - Number of rebalances
   - S&P 500 comparison
   - Outperformance vs. benchmark

## 5. Using Configuration Files

Save your portfolio for repeated analysis:

```bash
# After running interactively, choose 'y' to save config
Save this configuration for future use? (y/n): y
✓ Configuration saved to: portfolio_config.yaml

# Next time, the script will detect and offer to load it
Found existing config (portfolio_config.yaml). Load it? (y/n): y
```

Or manually create `portfolio_config.yaml`:

```yaml
baskets:
  - tickers: [AAPL, MSFT, GOOGL]
    start_date: "2024-01-01"
  - tickers: [NVDA, AMD]
    start_date: "2024-07-01"
end_date: "2024-12-31"
```

## 6. Interpreting the Chart

The chart shows:

- **Blue line**: Your portfolio value (starts at 100)
- **Purple dashed line**: S&P 500 benchmark
- **Vertical dotted lines**: Basket transition dates
- **Colored labels**: Which stocks were held in each period
- **Metrics box**: Performance statistics

## 7. Rollover Example

If you had:
- Basket 1 from Jan-Jun: +20% return → Portfolio goes from 100 to 120
- Basket 2 from Jun-Dec: +10% return → Portfolio goes from 120 to 132

Total return: 32% (not 30%!) due to compounding

## Troubleshooting

### "NASDAQ_DATA_LINK_API_KEY not found"
- Make sure you copied `.env.template` to `.env`
- Add your API key to the `.env` file

### "No data for basket"
- Check that ticker symbols are correct (must be US stocks)
- Ensure date range is valid (not too far in the past for NASDAQ free tier)
- Try with well-known tickers like AAPL, MSFT first

### "Module not found"
- Install dependencies: `pip3 install -r requirements.txt`

## Tips

1. **Start simple**: Test with 2-3 well-known stocks first (AAPL, MSFT, GOOGL)
2. **Recent dates**: Use dates within the last few years for best data availability
3. **Save configs**: Use YAML configs to quickly re-run analysis with different parameters
4. **Check charts**: Visual inspection of `charts/portfolio_performance.png` helps spot issues

## Next Steps

- Modify baskets and dates to track your actual investment decisions
- Compare different rebalancing strategies
- Track performance over longer time periods
- Consider expanding to a web application (Phase 3 in README.md)

Enjoy tracking your portfolio! 📈
