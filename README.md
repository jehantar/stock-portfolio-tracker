# 📈 Stock Portfolio Tracker

Interactive portfolio tracking with basket rebalancing, performance analytics, and S&P 500 benchmarking.

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd stock

# 2. Configure API keys
cp config/.env.template .env
# Edit .env and add your API keys

# 3. Run the dashboard
./portfolio dashboard
```

The dashboard will open at `http://localhost:8501`

## ✨ Features

### Interactive Web Dashboard
- **Live Basket Editing** - Add/remove/modify baskets with custom tickers and timeframes
- **Interactive Charts** - Plotly-powered charts with zoom, pan, and hover details
- **Portfolio Comparison** - Compare 2-5 portfolios side-by-side
- **Advanced Metrics** - Sharpe ratio, max drawdown, volatility, win rate
- **Save/Load Configs** - Manage multiple portfolio strategies
- **Data Export** - Download returns and metrics as CSV

### Command-Line Interface
- Batch processing for automation
- Config file support (YAML)
- Portfolio comparison mode
- Chart generation

## 📋 Requirements

- Python 3.8+ (tested on 3.13)
- NASDAQ Data Link API key ([sign up](https://data.nasdaq.com/sign-up))
- FRED API key ([sign up](https://fred.stlouisfed.org/docs/api/api_key.html)) - optional

## 🎯 Usage

### Interactive Dashboard (Recommended)

```bash
./portfolio dashboard
```

Features:
- Create portfolios with multiple baskets
- Set custom start dates for each basket (rebalancing points)
- Run analysis with one click
- View performance metrics and charts
- Save configurations for later use
- Compare different strategies

### Command-Line Mode

```bash
# Interactive mode (prompts for input)
./portfolio cli

# Auto mode (load existing config)
./portfolio cli --auto

# Use specific config file
./portfolio cli --config config/portfolio_config.example.yaml

# Compare multiple portfolios
./portfolio cli --compare portfolio1.yaml portfolio2.yaml
```

### Verify Setup

```bash
./portfolio test
```

## 📁 Project Structure

```
stock/
├── portfolio              # Unified launcher script
├── .env                   # API keys (create from template)
├── portfolio_config.yaml  # Your portfolio (auto-created)
│
├── src/                   # Source code
│   ├── portfolio_tracker.py  # Core tracker logic
│   └── dashboard.py           # Web dashboard
│
├── config/                # Example configurations
│   ├── .env.template          # API keys template
│   ├── portfolio_config.example.yaml
│   └── portfolio_config_alt.yaml
│
├── docs/                  # Documentation
│   ├── README.md              # Original README
│   ├── QUICKSTART.md          # CLI quick start
│   ├── DASHBOARD_README.md    # Complete dashboard guide
│   └── DASHBOARD_QUICKSTART.md
│
├── bin/                   # Helper scripts (legacy)
│   ├── start_dashboard.sh
│   ├── run_dashboard.sh
│   └── launch_dashboard.sh
│
├── tests/                 # Test utilities
├── charts/                # Generated charts (gitignored)
└── venv/                  # Virtual environment (auto-created)
```

## 🎨 Configuration Format

Create a YAML file with one or more baskets:

```yaml
baskets:
  # First basket - Tech stocks (Jan-May)
  - tickers: [AAPL, MSFT, GOOGL]
    start_date: "2024-01-01"

  # Second basket - Semiconductors (Jun-Dec)
  - tickers: [NVDA, AMD, TSM]
    start_date: "2024-06-01"

# End date for analysis
end_date: "2024-12-31"
```

**Key Concepts:**
- **Basket**: Group of stocks held for a specific period
- **Rebalancing**: Portfolio transitions to next basket at its start_date
- **Rollover Returns**: Gains/losses compound across basket transitions

## 📊 How It Works

1. **Equal-Weighted Baskets** - Each stock contributes equally to basket performance
2. **Rollover Compounding** - Basket 1 ends at 115 → Basket 2 starts at 115 (not 100)
3. **S&P 500 Benchmark** - Compare your strategy against the market
4. **Advanced Metrics** - Risk-adjusted returns (Sharpe ratio), drawdowns, volatility

## 🔧 Advanced Usage

### Custom Strategies

**Sector Rotation:**
```yaml
baskets:
  - tickers: [AAPL, MSFT, GOOGL]  # Q1: Tech
    start_date: "2024-01-01"
  - tickers: [JNJ, PFE, UNH]      # Q2: Healthcare
    start_date: "2024-04-01"
  - tickers: [XOM, CVX, COP]      # Q3: Energy
    start_date: "2024-07-01"
  - tickers: [JPM, BAC, GS]       # Q4: Finance
    start_date: "2024-10-01"
end_date: "2024-12-31"
```

**Momentum Strategy:**
```yaml
baskets:
  - tickers: [NVDA, AMD, SMCI]  # High momentum
    start_date: "2024-01-01"
  - tickers: [TSLA, META, AMZN] # Rebalance monthly
    start_date: "2024-02-01"
  # ... continue monthly
end_date: "2024-12-31"
```

### Portfolio Comparison

Create multiple configs and compare:
```bash
./portfolio dashboard
# Select "Portfolio Comparison" mode
# Choose 2-5 saved configurations
# Click "Compare Portfolios"
```

## 🛠️ Development

### Setup Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install setuptools  # Python 3.13+ compatibility

# Run tests
python3 test_setup.py
python3 test_dashboard_setup.py
```

### Running from Source

```bash
# Dashboard
source venv/bin/activate
streamlit run src/dashboard.py

# CLI
python3 src/portfolio_tracker.py --auto
```

## 📚 Documentation

- **[Quick Start](docs/QUICKSTART.md)** - Get started with CLI in 5 minutes
- **[Dashboard Guide](docs/DASHBOARD_README.md)** - Complete dashboard documentation
- **[Dashboard Quick Start](docs/DASHBOARD_QUICKSTART.md)** - Dashboard in 3 steps
- **[CLAUDE.md](CLAUDE.md)** - Developer guide for Claude Code

## 🤝 Contributing

This project uses:
- **NASDAQ Data Link** - Stock price data
- **FRED** - S&P 500 benchmark data
- **Streamlit** - Interactive dashboards
- **Plotly** - Interactive charts
- **pandas** - Data processing

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- NASDAQ Data Link for stock price data
- FRED for benchmark data
- Streamlit for the amazing dashboard framework

## 💡 Tips

1. **Start Simple** - Begin with 2 baskets, 3-5 tickers, 1-2 year period
2. **Use Examples** - Check `config/` for ready-to-use configurations
3. **Save Configs** - Name them descriptively (e.g., `tech_2024.yaml`, `value_stocks.yaml`)
4. **Compare Strategies** - Test different approaches side-by-side
5. **Export Data** - Download CSV for further analysis in Excel/Google Sheets

## 🐛 Troubleshooting

**"Module not found" errors:**
```bash
source venv/bin/activate
pip install -r requirements.txt
pip install setuptools
```

**API key errors:**
```bash
# Verify .env file exists
cat .env

# Should contain:
# NASDAQ_DATA_LINK_API_KEY=your_key
# FRED_API_KEY=your_key
```

**Dashboard won't start:**
```bash
# Kill any existing instances
pkill -f "streamlit run"

# Restart
./portfolio dashboard
```

**Data fetching slow:**
- First fetch: 30-60 seconds (normal)
- Cached for 1 hour after that
- More tickers = longer initial fetch

## 🌐 Deployment

### Deploy as Live Website (FREE!)

Deploy your dashboard to Streamlit Community Cloud in under 5 minutes:

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select this repository: `jehantar/stock-portfolio-tracker`
5. Set main file: `src/dashboard.py`
6. Add your API keys in the Secrets section:
```toml
NASDAQ_DATA_LINK_API_KEY = "your_key"
FRED_API_KEY = "your_key"
```
7. Click "Deploy"

**Your dashboard will be live at: `https://your-app.streamlit.app`**

📖 Full deployment guide: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

**Security Note:** Your API keys are stored securely in Streamlit Cloud and are NOT exposed in your code or repository.

## 📞 Support

- Check documentation in `docs/`
- Run `./portfolio test` to verify setup
- See `CLAUDE.md` for development details

---

**Made with Claude Code** 🤖
