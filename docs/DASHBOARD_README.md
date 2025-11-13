# Stock Portfolio Tracker - Interactive Dashboard

Interactive Streamlit dashboard for creating, editing, and analyzing stock portfolios with basket rebalancing.

## Features

### 📊 Live Portfolio Editing
- Add/remove/modify baskets in real-time
- Drag-and-drop interface for ticker input
- Custom timeframes for each basket
- Instant validation of configuration

### 💾 Configuration Management
- Save multiple portfolio configurations
- Load and switch between portfolios
- Export configurations as YAML files
- Quick "New" button to start fresh

### 📈 Interactive Charting
- Plotly-powered interactive charts with zoom, pan, and hover
- Toggle basket transition markers
- Real-time benchmark comparison (S&P 500)
- Downloadable chart data

### 📉 Advanced Analytics
- **Performance Metrics**: Total return, annualized return, Sharpe ratio
- **Risk Metrics**: Maximum drawdown, volatility, win rate
- **Drawdown Chart**: Visualize peak-to-trough declines
- **Returns Distribution**: Histogram of daily returns

### 🔄 Portfolio Comparison
- Compare 2-5 portfolios side-by-side
- Unified metrics table
- Overlay performance charts
- Rank by total return

### ⚡ Performance Optimization
- Built-in caching (1-hour TTL) for API calls
- Bulk data fetching for multiple portfolios
- Automatic fallback to SDK if bulk export fails

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys** (if not already done):
   ```bash
   # Create .env file
   echo "NASDAQ_DATA_LINK_API_KEY=your_key_here" >> .env
   echo "FRED_API_KEY=your_key_here" >> .env
   ```

## Usage

### Running the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Basic Workflow

1. **Configure Portfolio**:
   - Set the end date for your analysis
   - Add baskets with tickers and start dates
   - Use the expanders to edit each basket

2. **Run Analysis**:
   - Click "🚀 Run Analysis" button
   - Wait for data fetching (cached for 1 hour)
   - View metrics and charts

3. **Save Configuration**:
   - Enter a name in the sidebar
   - Click "💾 Save" to persist your portfolio
   - Saved as `{name}.yaml` in the current directory

4. **Compare Portfolios**:
   - Switch to "Portfolio Comparison" mode in sidebar
   - Select 2-5 saved configurations
   - Click "🚀 Compare Portfolios"
   - View side-by-side metrics and overlay chart

### Example: Creating a Tech Portfolio

1. Start the dashboard: `streamlit run dashboard.py`
2. In the main area:
   - Set end date to today
   - Expand "Basket 1"
   - Enter tickers: `AAPL, MSFT, GOOGL`
   - Set start date: `2024-01-01`
3. Click "➕ Add New Basket"
4. Expand "Basket 2":
   - Enter tickers: `NVDA, AMD, INTC`
   - Set start date: `2024-06-01`
5. Click "🚀 Run Analysis"
6. In sidebar:
   - Enter name: `tech_portfolio`
   - Click "💾 Save"

### Keyboard Shortcuts

- **Streamlit Native**:
  - `R` - Rerun the app
  - `C` - Clear cache
  - `?` - Show keyboard shortcuts

## Dashboard Sections

### 📊 Performance Metrics
Four-column layout showing:
- Total Return & Sharpe Ratio
- Annualized Return & Max Drawdown
- Volatility & Win Rate
- Days Held & Outperformance vs S&P 500

### 📈 Portfolio Performance Chart
- Interactive Plotly line chart
- Portfolio value vs S&P 500 benchmark
- Basket transition markers (toggle on/off)
- Hover for exact values and dates
- Zoom, pan, and export to PNG

### 📉 Additional Analytics
Two-column layout:
- **Drawdown Chart**: Shows portfolio decline from peaks
- **Returns Distribution**: Histogram of daily returns

### 💾 Export Data
Download buttons for:
- Portfolio returns (CSV with date, value, basket_index)
- Metrics summary (CSV with all calculated metrics)

## Configuration Files

### YAML Format
```yaml
baskets:
  - tickers: [AAPL, MSFT, GOOGL]
    start_date: "2024-01-01"
  - tickers: [NVDA, AMD, TSM]
    start_date: "2024-06-01"
end_date: "2024-12-31"
```

### Saved Locations
- All `.yaml` files in current directory are auto-detected
- Exclude `portfolio_config.example.yaml` from dropdown
- Use descriptive names: `tech_2024.yaml`, `value_stocks.yaml`

## Caching Strategy

The dashboard uses Streamlit's `@st.cache_data` with 1-hour TTL:

```python
@st.cache_data(ttl=3600)
def fetch_stock_prices(...):
    # Cached for 1 hour
```

**Benefits**:
- Instant re-renders when editing baskets
- No redundant API calls during same session
- Automatic refresh after 1 hour

**Clear Cache**:
- Click "C" in the browser
- Or use "Clear Cache" from hamburger menu (☰)

## Troubleshooting

### Dashboard won't start
```bash
# Check Streamlit installation
pip install --upgrade streamlit

# Run with verbose output
streamlit run dashboard.py --logger.level=debug
```

### "No module named 'portfolio_tracker'"
```bash
# Ensure you're in the correct directory
cd /path/to/stock
python -c "import portfolio_tracker"  # Should work
```

### Charts not displaying
```bash
# Update Plotly
pip install --upgrade plotly
```

### API errors
```bash
# Verify API keys
python3 test_setup.py

# Check .env file
cat .env
```

### Cache issues
- Press `C` in browser to clear cache
- Or restart the dashboard

## Customization

### Change Chart Colors
Edit `dashboard.py:142-151` (basket colors):
```python
basket_colors = ['#F18F01', '#C73E1D', '#6A994E', '#BC4B51', '#FF6B6B', '#4ECDC4']
```

### Adjust Cache Duration
Edit `dashboard.py:79` and `dashboard.py:108`:
```python
@st.cache_data(ttl=7200)  # 2 hours instead of 1
```

### Modify Metrics Display
Edit `show_single_portfolio()` function around line 550-570 to add/remove metrics.

## Migration to Flask + Plotly Dash

The dashboard is designed to make migration easier:

**What's portable**:
- All calculation logic (imports from `portfolio_tracker.py`)
- Plotly chart functions (`create_interactive_chart`, etc.)
- Data fetching and caching patterns

**What needs rewriting**:
- Layout (Streamlit → Dash layout components)
- State management (session_state → dcc.Store)
- Callbacks (Streamlit reruns → Dash callbacks)

**Recommended approach**:
1. Keep `dashboard.py` as-is
2. Create `dashboard_flask.py` alongside it
3. Copy chart functions and calculation logic
4. Rewrite UI with Dash components

## Performance Tips

1. **Use comparison mode wisely**: Comparing 5 portfolios with 100+ tickers can take 2-3 minutes
2. **Save configurations**: Avoid re-entering baskets each session
3. **Limit date ranges**: Start with 1-2 years for testing, expand later
4. **Cache is your friend**: Editing baskets after initial fetch is instant
5. **Use YAML configs**: Easier to version control and share

## Next Steps

Ideas for future enhancements:
- Add momentum-based basket suggestions
- Export to PDF reports
- Email/Slack notifications for portfolio updates
- Real-time price updates (WebSocket)
- Multi-user support with authentication
- Database backend for portfolio versioning
- Automated rebalancing alerts

## Support

For issues or questions:
1. Check `CLAUDE.md` for project details
2. Run `python3 test_setup.py` to verify setup
3. Check the console for error messages
4. Ensure API keys are valid and have quota remaining
