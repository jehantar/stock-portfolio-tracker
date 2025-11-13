# Dashboard Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Install & Run
```bash
./start_dashboard.sh
```
This script automatically:
- Creates a virtual environment
- Installs all dependencies
- Launches the dashboard at `http://localhost:8501`

### 2. Create Your First Portfolio

**In the dashboard:**

1. Set the **End Date** (e.g., today's date)

2. **Basket 1** (expand the section):
   - Tickers: `AAPL, MSFT, GOOGL`
   - Start Date: `2024-01-01`

3. Click **➕ Add New Basket**

4. **Basket 2**:
   - Tickers: `NVDA, AMD, TSM`
   - Start Date: `2024-06-01`

5. Click **🚀 Run Analysis**

6. Wait 30-60 seconds for data fetching

7. View your results!

### 3. Save & Share

**In the sidebar:**
- Enter name: `tech_portfolio`
- Click **💾 Save**
- Saved as `tech_portfolio.yaml` for future use

## 📊 Dashboard Features Overview

### Single Portfolio Mode
```
┌─────────────────────────────────────────┐
│  📊 Performance Metrics                 │
│  ┌────┬────┬────┬────┐                 │
│  │ TR │ AR │ SR │ DD │  (4 columns)    │
│  └────┴────┴────┴────┘                 │
│                                         │
│  📈 Interactive Performance Chart       │
│  (Plotly - zoom, pan, hover)           │
│                                         │
│  📉 Drawdown Chart | Returns Histogram  │
│  (2 columns)                            │
│                                         │
│  💾 Export: CSV Downloads               │
└─────────────────────────────────────────┘
```

### Portfolio Comparison Mode
```
┌─────────────────────────────────────────┐
│  Select 2-5 portfolios to compare       │
│  ☑ tech_portfolio.yaml                  │
│  ☑ value_stocks.yaml                    │
│  ☐ growth_portfolio.yaml                │
│                                         │
│  🚀 Compare Portfolios                  │
│                                         │
│  📊 Metrics Comparison Table            │
│  Portfolio  | TR | SR | DD | Vol       │
│  ────────────┼────┼────┼────┼────      │
│  Tech       | 38%| 1.2|-12%| 18%       │
│  Value      | 24%| 0.9| -8%| 14%       │
│                                         │
│  📈 Overlay Performance Chart           │
│  (All portfolios + S&P 500)            │
│                                         │
│  📋 Individual Portfolio Details        │
│  (Expandable sections)                  │
└─────────────────────────────────────────┘
```

## 🎯 Key Concepts

### What is a Basket?
A **basket** is a group of stocks held for a specific time period.

**Example:**
- **Basket 1**: Tech stocks (Jan-May 2024)
  - `AAPL, MSFT, GOOGL`
- **Basket 2**: Semiconductors (Jun-Dec 2024)
  - `NVDA, AMD, TSM`

### Rollover Returns
The portfolio carries forward gains/losses between baskets:
- Basket 1 ends at 115 (15% gain) → Basket 2 starts at 115, not 100
- This compounds returns across basket transitions

### Custom Timeframes
Each basket can have any start date:
- Weekly rebalancing: Every Monday
- Monthly rebalancing: 1st of each month
- Quarterly rebalancing: Jan 1, Apr 1, Jul 1, Oct 1
- Event-driven: Based on market conditions

## 💡 Pro Tips

### 1. Use Caching
Once data is fetched, it's cached for 1 hour:
- Edit baskets instantly without re-fetching
- Try different ticker combinations quickly
- Press `C` in browser to clear cache if needed

### 2. Save Configurations
Create multiple portfolios for different strategies:
- `tech_2024.yaml` - Technology stocks
- `value_stocks.yaml` - Value investing
- `dividend_growth.yaml` - Dividend aristocrats
- `momentum_q1.yaml` - Momentum strategy Q1

### 3. Compare Performance
Select 2-5 saved portfolios to compare:
- See which strategy performed best
- Analyze risk vs return (Sharpe ratio)
- Identify best timing for rebalancing

### 4. Export Data
Download CSV files for:
- Further analysis in Excel/Google Sheets
- Creating custom reports
- Sharing with others

## 🔧 Troubleshooting

### Dashboard Won't Start
```bash
# Check Python version (need 3.8+)
python3 --version

# Manually create venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run dashboard.py
```

### "No Module Named..." Error
```bash
# You're not in the virtual environment
source venv/bin/activate

# Then try again
streamlit run dashboard.py
```

### API Key Errors
```bash
# Check .env file exists
cat .env

# Should contain:
# NASDAQ_DATA_LINK_API_KEY=your_key_here
# FRED_API_KEY=your_key_here

# Verify keys loaded
python3 test_dashboard_setup.py
```

### Data Fetching Slow
- First fetch takes 30-60 seconds (normal)
- Subsequent edits are instant (cached)
- More tickers = longer fetch time
- Bulk export faster than SDK method

### Charts Not Showing
```bash
# Update Plotly
pip install --upgrade plotly

# Clear browser cache
# Press Ctrl+Shift+R (or Cmd+Shift+R on Mac)
```

## 📚 Learn More

- **Full Documentation**: `DASHBOARD_README.md`
- **Project Overview**: `CLAUDE.md`
- **Setup Verification**: `python3 test_dashboard_setup.py`

## 🎨 Customization Examples

### Weekly Rebalancing Strategy
```python
# Create 52 baskets for weekly rebalancing
# Use same tickers, different dates
baskets:
  - tickers: [AAPL, MSFT]
    start_date: "2024-01-01"
  - tickers: [AAPL, MSFT]
    start_date: "2024-01-08"
  - tickers: [AAPL, MSFT]
    start_date: "2024-01-15"
  # ... etc
```

### Sector Rotation
```python
baskets:
  # Q1: Technology
  - tickers: [AAPL, MSFT, NVDA]
    start_date: "2024-01-01"

  # Q2: Healthcare
  - tickers: [JNJ, PFE, UNH]
    start_date: "2024-04-01"

  # Q3: Energy
  - tickers: [XOM, CVX, COP]
    start_date: "2024-07-01"

  # Q4: Finance
  - tickers: [JPM, BAC, GS]
    start_date: "2024-10-01"
```

### Risk-Based Allocation
Create separate portfolios for comparison:
- `aggressive.yaml` - High beta tech stocks
- `moderate.yaml` - Mix of growth and value
- `conservative.yaml` - Low volatility blue chips

Then compare to see risk/return tradeoffs!

## 🚀 Next Steps

1. **Start simple**: 2 baskets, 3-5 tickers each, 1-2 year period
2. **Experiment**: Try different ticker combinations
3. **Compare**: Create multiple strategies and compare
4. **Analyze**: Look at Sharpe ratio and drawdown for risk-adjusted returns
5. **Iterate**: Refine your strategy based on results

**Happy tracking! 📈**
