#!/usr/bin/env python3
"""
Stock Portfolio Tracker with Basket Rebalancing

Tracks portfolio performance across multiple basket rebalances,
calculating rollover returns and comparing against S&P 500 benchmark.
"""

import os
import sys
import time
import io
import zipfile
import gzip
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests
import yaml
import nasdaqdatalink as ndl
from dotenv import load_dotenv
from fredapi import Fred


@dataclass
class Basket:
    """Represents a stock basket for a specific time period."""
    tickers: List[str]
    start_date: str

    def __post_init__(self):
        self.tickers = [t.upper() for t in self.tickers]


@dataclass
class PortfolioConfig:
    """Portfolio configuration with multiple baskets."""
    baskets: List[Basket]
    end_date: str

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML export."""
        return {
            'baskets': [
                {'tickers': b.tickers, 'start_date': b.start_date}
                for b in self.baskets
            ],
            'end_date': self.end_date
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PortfolioConfig':
        """Load from dictionary (YAML import)."""
        baskets = [Basket(**b) for b in data['baskets']]
        return cls(baskets=baskets, end_date=data['end_date'])


def download_nasdaq_prices_sdk(api_key: str, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
    """
    Download daily stock prices using NASDAQ Data Link SDK (fallback method).

    Args:
        api_key: NASDAQ Data Link API key
        tickers: List of ticker symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        DataFrame with columns: ticker, date, close
    """
    print(f"Fetching prices for {len(tickers)} tickers using SDK...")
    ndl.ApiConfig.api_key = api_key

    all_data = []

    for i, ticker in enumerate(tickers):
        try:
            print(f"  Fetching {ticker}...", end=" ", flush=True)
            params = {
                "ticker": ticker,
                "date": {"gte": start_date, "lte": end_date},
                "qopts": {"columns": ["ticker", "date", "close"]}
            }

            df = ndl.get_table("SHARADAR/SEP", paginate=True, **params)

            if not df.empty:
                all_data.append(df)
                print(f"✓ ({len(df)} rows)")
            else:
                print(f"⚠ No data")

            # Small delay to avoid rate limiting (except for last ticker)
            if i < len(tickers) - 1:
                time.sleep(0.2)

        except Exception as e:
            print(f"✗ Error: {e}")
            continue

    if not all_data:
        raise ValueError("No data could be downloaded for any ticker")

    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df['date'] = pd.to_datetime(combined_df['date'])

    print(f"Downloaded {len(combined_df)} rows for {combined_df['ticker'].nunique()} tickers")
    return combined_df


def download_nasdaq_prices(api_key: str, start_date: str, end_date: str,
                           timeout: int = 300, poll_interval: int = 5) -> pd.DataFrame:
    """
    Download daily stock prices using NASDAQ Data Link bulk export API.

    Mimics the pattern from momentum/data/prices.py with async polling.

    Args:
        api_key: NASDAQ Data Link API key
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        timeout: Maximum time to wait for export (seconds)
        poll_interval: Time between status checks (seconds)

    Returns:
        DataFrame with columns: ticker, date, close
    """
    export_url = "https://data.nasdaq.com/api/v3/datatables/SHARADAR/SEP"
    columns = ["ticker", "date", "close"]

    params = {
        "qopts.export": "true",
        "api_key": api_key,
        "qopts.columns": ",".join(columns),
        "date.gte": start_date,
        "date.lte": end_date,
    }

    print(f"Initiating NASDAQ bulk export for {start_date} to {end_date}...")
    resp = requests.get(export_url, params=params, timeout=30)
    resp.raise_for_status()

    response_json = resp.json()

    # Check for error message in response
    if "datatable_bulk_download" not in response_json:
        print(f"Error: Unexpected response from NASDAQ API: {response_json}")
        raise ValueError("NASDAQ API did not return bulk download information")

    job = response_json["datatable_bulk_download"]
    status_url = job.get("status")
    download_link = job.get("link") or (job.get("file") or {}).get("link")

    # Poll until ready
    start_time = time.time()
    while download_link is None and status_url:
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Bulk export timeout after {timeout}s")

        time.sleep(poll_interval)
        status_resp = requests.get(status_url, timeout=10)
        status_resp.raise_for_status()
        status_json = status_resp.json()

        if "datatable_bulk_download" not in status_json:
            print(f"Error: Unexpected status response: {status_json}")
            break

        status = status_json["datatable_bulk_download"]
        download_link = status.get("link") or (status.get("file") or {}).get("link")
        print(".", end="", flush=True)

    if download_link is None:
        raise ValueError("Could not obtain download link from NASDAQ API. The bulk export may have failed.")

    print(f"\nDownloading data from {download_link}...")
    csv_resp = requests.get(download_link, timeout=60)
    csv_resp.raise_for_status()

    # Handle compression (mimic momentum/data/prices.py)
    content = csv_resp.content
    content_type = csv_resp.headers.get("content-type", "").lower()
    is_zip = "zip" in content_type or download_link.endswith(".zip") or content.startswith(b"PK")

    if is_zip:
        print("Extracting CSV from ZIP archive...")
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            names = [name for name in zf.namelist() if name.endswith(".csv")]
            if not names:
                raise RuntimeError("Export zip did not contain a CSV file.")
            with zf.open(names[0]) as zipped_csv:
                df = pd.read_csv(zipped_csv, encoding="latin1", encoding_errors="replace")
    elif content.startswith(b"\x1f\x8b"):
        print("Decompressing gzipped data...")
        with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz:
            decompressed = gz.read()
        df = pd.read_csv(io.BytesIO(decompressed), encoding="latin1", encoding_errors="replace")
    else:
        try:
            df = pd.read_csv(io.BytesIO(content))
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(content), encoding="latin1", encoding_errors="replace")
    df['date'] = pd.to_datetime(df['date'])

    print(f"Downloaded {len(df)} rows for {df['ticker'].nunique()} tickers")
    return df


def download_sp500_benchmark(fred_api_key: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Download S&P 500 index data from FRED (daily data) using fredapi.

    Args:
        fred_api_key: FRED API key
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        DataFrame with columns: date, close
    """
    print(f"Downloading S&P 500 benchmark data from FRED...")

    try:
        # Use fredapi to get daily S&P 500 data from FRED
        fred = Fred(api_key=fred_api_key)
        daily_data = fred.get_series('SP500', observation_start=start_date, observation_end=end_date)

        if daily_data.empty:
            print("Warning: No S&P 500 data returned")
            return pd.DataFrame(columns=['date', 'close'])

        # Convert Series to DataFrame
        daily_data = daily_data.to_frame(name='close')

        # Forward fill NaNs for holidays/weekends
        daily_data['close'] = daily_data['close'].ffill()

        # Also backfill in case the first entries are NaN
        daily_data['close'] = daily_data['close'].bfill()

        # Reset index to make date a column
        daily_data = daily_data.reset_index()
        daily_data = daily_data.rename(columns={'index': 'date'})

        # Ensure date column is datetime
        daily_data['date'] = pd.to_datetime(daily_data['date'])

        # Remove any remaining NaN values
        daily_data = daily_data.dropna(subset=['close'])

        print(f"Downloaded {len(daily_data)} days of S&P 500 data")
        return daily_data[['date', 'close']]

    except Exception as e:
        print(f"Error downloading S&P 500 data: {e}")
        print("Benchmark comparison will be skipped")
        return pd.DataFrame(columns=['date', 'close'])


def calculate_portfolio_returns(prices_df: pd.DataFrame, config: PortfolioConfig) -> pd.DataFrame:
    """
    Calculate portfolio returns with rollover across basket transitions.

    Args:
        prices_df: DataFrame with ticker, date, close
        config: Portfolio configuration with baskets

    Returns:
        DataFrame with date, portfolio_value, basket_index columns
    """
    results = []
    portfolio_value = 100.0  # Start with normalized value of 100

    for i, basket in enumerate(config.baskets):
        # Determine end date for this basket
        if i < len(config.baskets) - 1:
            basket_end_date = config.baskets[i + 1].start_date
        else:
            basket_end_date = config.end_date

        # Filter prices for this basket's tickers and date range
        basket_prices = prices_df[
            (prices_df['ticker'].isin(basket.tickers)) &
            (prices_df['date'] >= basket.start_date) &
            (prices_df['date'] < basket_end_date)
        ].copy()

        if basket_prices.empty:
            print(f"Warning: No data for basket {i+1} ({basket.tickers})")
            continue

        # Calculate equal-weighted portfolio for this basket
        # Pivot to get ticker columns
        basket_pivot = basket_prices.pivot(index='date', columns='ticker', values='close')

        # Get initial prices (first date of this basket)
        initial_prices = basket_pivot.iloc[0]

        # Calculate normalized prices (starting at 1.0)
        normalized = basket_pivot / initial_prices

        # Equal-weighted average across tickers
        basket_performance = normalized.mean(axis=1)

        # Apply to current portfolio value
        basket_values = basket_performance * portfolio_value

        # Store results
        for date, value in basket_values.items():
            results.append({
                'date': date,
                'portfolio_value': value,
                'basket_index': i
            })

        # Update portfolio value for next basket (rollover)
        portfolio_value = basket_values.iloc[-1]

        print(f"Basket {i+1} ({basket.start_date} to {basket_end_date}): "
              f"{len(basket.tickers)} stocks, "
              f"Return: {(basket_performance.iloc[-1] - 1) * 100:.2f}%")

    return pd.DataFrame(results)


def calculate_benchmark_returns(benchmark_df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Calculate benchmark returns normalized to start at 100.

    Args:
        benchmark_df: DataFrame with date, close
        start_date: Portfolio start date
        end_date: Portfolio end date

    Returns:
        DataFrame with date, benchmark_value
    """
    # Ensure dates are datetime
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    # Filter to portfolio date range
    benchmark = benchmark_df[
        (benchmark_df['date'] >= start_dt) &
        (benchmark_df['date'] <= end_dt)
    ].copy()

    if benchmark.empty:
        print("Warning: No benchmark data available for date range")
        return pd.DataFrame(columns=['date', 'benchmark_value'])

    # Remove NaN values and normalize to start at 100
    benchmark = benchmark.dropna(subset=['close'])

    if benchmark.empty:
        print("Warning: No valid benchmark data after removing NaN values")
        return pd.DataFrame(columns=['date', 'benchmark_value'])

    initial_value = benchmark.iloc[0]['close']
    if initial_value == 0:
        print("Warning: Invalid initial benchmark value (zero)")
        return pd.DataFrame(columns=['date', 'benchmark_value'])

    benchmark['benchmark_value'] = (benchmark['close'] / initial_value) * 100

    print(f"Benchmark: {len(benchmark)} days, Initial: {initial_value:.2f}, Final: {benchmark.iloc[-1]['close']:.2f}")

    return benchmark[['date', 'benchmark_value']]


def visualize_portfolio(portfolio_df: pd.DataFrame, benchmark_df: pd.DataFrame,
                       config: PortfolioConfig, output_path: str = 'charts/portfolio_performance.png'):
    """
    Create visualization of portfolio performance vs benchmark.

    Args:
        portfolio_df: DataFrame with date, portfolio_value, basket_index
        benchmark_df: DataFrame with date, benchmark_value
        config: Portfolio configuration
        output_path: Path to save chart
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot portfolio value
    ax.plot(portfolio_df['date'], portfolio_df['portfolio_value'],
            linewidth=2, label='Portfolio', color='#2E86AB')

    # Plot benchmark
    if not benchmark_df.empty:
        ax.plot(benchmark_df['date'], benchmark_df['benchmark_value'],
                linewidth=2, label='S&P 500', color='#A23B72', linestyle='--')

    # Add vertical lines for basket transitions
    basket_colors = ['#F18F01', '#C73E1D', '#6A994E', '#BC4B51']
    for i, basket in enumerate(config.baskets):
        color = basket_colors[i % len(basket_colors)]
        ax.axvline(pd.to_datetime(basket.start_date), color=color,
                   linestyle=':', alpha=0.7, linewidth=1.5)

        # Add annotation for basket composition
        basket_label = ', '.join(basket.tickers[:3])
        if len(basket.tickers) > 3:
            basket_label += f' +{len(basket.tickers)-3}'

        # Position annotation
        y_pos = ax.get_ylim()[1] * 0.95
        ax.text(pd.to_datetime(basket.start_date), y_pos,
                f'  {basket_label}', rotation=0, verticalalignment='top',
                fontsize=9, color=color, fontweight='bold')

    # Formatting
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Portfolio Value (Base = 100)', fontsize=12, fontweight='bold')
    ax.set_title('Portfolio Performance with Basket Rebalancing',
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)

    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()

    # Add metrics text box with advanced metrics
    final_value = portfolio_df.iloc[-1]['portfolio_value']
    total_return = ((final_value - 100) / 100) * 100

    start = pd.to_datetime(config.baskets[0].start_date)
    end = pd.to_datetime(config.end_date)
    days = (end - start).days
    years = days / 365.25
    annualized_return = ((final_value / 100) ** (1 / years) - 1) * 100 if years > 0 else 0

    benchmark_final = benchmark_df.iloc[-1]['benchmark_value'] if not benchmark_df.empty else 100
    benchmark_return = ((benchmark_final - 100) / 100) * 100

    # Calculate advanced metrics
    advanced_metrics = calculate_advanced_metrics(portfolio_df, benchmark_df)

    metrics_text = f'Total Return: {total_return:.2f}%\n'
    metrics_text += f'Annualized Return: {annualized_return:.2f}%\n'
    metrics_text += f'Sharpe Ratio: {advanced_metrics["sharpe_ratio"]:.2f}\n'
    metrics_text += f'Max Drawdown: {advanced_metrics["max_drawdown"]:.2f}%\n'
    metrics_text += f'Volatility: {advanced_metrics["volatility"]:.2f}%\n'
    metrics_text += f'Win Rate: {advanced_metrics["win_rate"]:.1f}%\n'
    metrics_text += f'Days Held: {days}\n'
    if not benchmark_df.empty:
        metrics_text += f'S&P 500: {benchmark_return:.2f}%\n'
        metrics_text += f'Outperformance: {total_return - benchmark_return:.2f}%'

    ax.text(0.02, 0.02, metrics_text, transform=ax.transAxes,
            fontsize=9, verticalalignment='bottom',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nChart saved to: {output_path}")

    plt.show()


def interactive_basket_input() -> PortfolioConfig:
    """
    Interactively collect basket information from user.

    Returns:
        PortfolioConfig with all baskets
    """
    print("\n" + "="*60)
    print("STOCK PORTFOLIO TRACKER - Interactive Mode")
    print("="*60)
    print("\nEnter your stock baskets. You can add multiple baskets to track")
    print("rebalancing over time. Press Ctrl+C to cancel.\n")

    baskets = []
    basket_num = 1

    while True:
        print(f"\n--- Basket {basket_num} ---")

        # Get tickers
        while True:
            tickers_input = input(f"Enter stock tickers for basket {basket_num} (comma-separated, e.g., AAPL,MSFT,GOOGL): ").strip()
            if tickers_input:
                tickers = [t.strip().upper() for t in tickers_input.split(',')]
                if tickers:
                    break
            print("Please enter at least one ticker.")

        # Get start date
        while True:
            if basket_num == 1:
                date_input = input(f"Enter start date for basket {basket_num} (YYYY-MM-DD): ").strip()
            else:
                date_input = input(f"Enter transition date to basket {basket_num} (YYYY-MM-DD): ").strip()

            try:
                pd.to_datetime(date_input)
                start_date = date_input
                break
            except:
                print("Invalid date format. Please use YYYY-MM-DD.")

        baskets.append(Basket(tickers=tickers, start_date=start_date))
        print(f"✓ Added basket {basket_num}: {', '.join(tickers)} starting {start_date}")

        # Ask for more baskets
        more = input("\nAdd another basket? (y/n): ").strip().lower()
        if more != 'y':
            break

        basket_num += 1

    # Get end date
    while True:
        end_input = input("\nEnter end date for analysis (YYYY-MM-DD, or press Enter for today): ").strip()
        if not end_input:
            end_date = datetime.now().strftime('%Y-%m-%d')
            break
        try:
            pd.to_datetime(end_input)
            end_date = end_input
            break
        except:
            print("Invalid date format. Please use YYYY-MM-DD.")

    config = PortfolioConfig(baskets=baskets, end_date=end_date)

    print(f"\n✓ Portfolio configured with {len(baskets)} basket(s)")
    print(f"  Date range: {baskets[0].start_date} to {end_date}")

    return config


def save_config(config: PortfolioConfig, filepath: str = 'portfolio_config.yaml'):
    """Save portfolio configuration to YAML file."""
    with open(filepath, 'w') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False)
    print(f"\n✓ Configuration saved to: {filepath}")


def load_config(filepath: str = 'portfolio_config.yaml') -> PortfolioConfig:
    """Load portfolio configuration from YAML file."""
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    return PortfolioConfig.from_dict(data)


def calculate_advanced_metrics(portfolio_df: pd.DataFrame, benchmark_df: pd.DataFrame = None) -> Dict[str, float]:
    """
    Calculate advanced portfolio metrics.

    Args:
        portfolio_df: DataFrame with portfolio_value column
        benchmark_df: Optional DataFrame with benchmark_value column

    Returns:
        Dictionary of metrics
    """
    metrics = {}

    # Calculate daily returns
    portfolio_df = portfolio_df.copy()
    portfolio_df['daily_return'] = portfolio_df['portfolio_value'].pct_change()

    # Volatility (annualized standard deviation)
    daily_volatility = portfolio_df['daily_return'].std()
    metrics['volatility'] = daily_volatility * (252 ** 0.5) * 100  # Annualized %

    # Maximum Drawdown
    rolling_max = portfolio_df['portfolio_value'].expanding().max()
    drawdown = (portfolio_df['portfolio_value'] - rolling_max) / rolling_max
    metrics['max_drawdown'] = drawdown.min() * 100  # %

    # Sharpe Ratio (assuming 0% risk-free rate for simplicity)
    mean_return = portfolio_df['daily_return'].mean()
    if daily_volatility > 0:
        metrics['sharpe_ratio'] = (mean_return / daily_volatility) * (252 ** 0.5)
    else:
        metrics['sharpe_ratio'] = 0

    # Win rate (percentage of positive return days)
    positive_days = (portfolio_df['daily_return'] > 0).sum()
    total_days = portfolio_df['daily_return'].notna().sum()
    metrics['win_rate'] = (positive_days / total_days * 100) if total_days > 0 else 0

    return metrics


def compare_portfolios(config_files: List[str]):
    """
    Compare multiple portfolio configurations.

    Args:
        config_files: List of paths to configuration files
    """
    if len(config_files) < 2:
        print("Error: Comparison requires at least 2 configuration files")
        sys.exit(1)

    # Load environment variables
    load_dotenv()
    nasdaq_key = os.getenv('NASDAQ_DATA_LINK_API_KEY')
    fred_key = os.getenv('FRED_API_KEY')

    if not nasdaq_key:
        print("Error: NASDAQ_DATA_LINK_API_KEY not found in .env file")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"PORTFOLIO COMPARISON - {len(config_files)} Portfolios")
    print(f"{'='*60}\n")

    portfolios = []
    all_tickers = set()
    min_start_date = None
    max_end_date = None

    # Load all configurations
    for i, config_file in enumerate(config_files, 1):
        if not os.path.exists(config_file):
            print(f"Error: Config file '{config_file}' not found")
            sys.exit(1)

        config = load_config(config_file)
        name = os.path.basename(config_file).replace('.yaml', '').replace('_', ' ').title()

        print(f"Portfolio {i}: {name}")
        print(f"  - Baskets: {len(config.baskets)}")
        print(f"  - Period: {config.baskets[0].start_date} to {config.end_date}")

        portfolios.append({
            'name': name,
            'config': config,
            'file': config_file
        })

        # Collect all tickers and date ranges
        for basket in config.baskets:
            all_tickers.update(basket.tickers)

        start = pd.to_datetime(config.baskets[0].start_date)
        end = pd.to_datetime(config.end_date)
        if min_start_date is None or start < min_start_date:
            min_start_date = start
        if max_end_date is None or end > max_end_date:
            max_end_date = end

    print(f"\nTotal unique tickers across all portfolios: {len(all_tickers)}")
    print(f"Overall date range: {min_start_date.date()} to {max_end_date.date()}")

    # Download all price data once
    print(f"\n{'='*60}")
    print(f"Fetching data for {len(all_tickers)} unique tickers...")
    print(f"{'='*60}\n")

    try:
        prices_df = download_nasdaq_prices(nasdaq_key,
                                          min_start_date.strftime('%Y-%m-%d'),
                                          max_end_date.strftime('%Y-%m-%d'))
    except Exception as e:
        print(f"Bulk export failed: {e}")
        print("Falling back to SDK method (slower but more reliable)...\n")
        prices_df = download_nasdaq_prices_sdk(nasdaq_key, list(all_tickers),
                                              min_start_date.strftime('%Y-%m-%d'),
                                              max_end_date.strftime('%Y-%m-%d'))

    # Download benchmark once
    benchmark_df = pd.DataFrame(columns=['date', 'benchmark_value'])
    if fred_key:
        try:
            sp500_df = download_sp500_benchmark(fred_key,
                                               min_start_date.strftime('%Y-%m-%d'),
                                               max_end_date.strftime('%Y-%m-%d'))
            benchmark_df = calculate_benchmark_returns(sp500_df,
                                                      min_start_date.strftime('%Y-%m-%d'),
                                                      max_end_date.strftime('%Y-%m-%d'))
        except Exception as e:
            print(f"Warning: Could not fetch benchmark data: {e}")

    # Calculate returns for each portfolio
    print(f"\n{'='*60}")
    print("Calculating returns for all portfolios...")
    print(f"{'='*60}\n")

    for portfolio in portfolios:
        portfolio_df = calculate_portfolio_returns(prices_df, portfolio['config'])
        portfolio['returns'] = portfolio_df

        # Calculate metrics
        portfolio['metrics'] = calculate_advanced_metrics(portfolio_df, benchmark_df)

        final_value = portfolio_df.iloc[-1]['portfolio_value']
        total_return = ((final_value - 100) / 100) * 100
        portfolio['total_return'] = total_return

        print(f"{portfolio['name']}: {total_return:.2f}%")

    # Create comparison visualization
    visualize_comparison(portfolios, benchmark_df)

    # Print comparison summary
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}\n")

    # Sort by total return
    sorted_portfolios = sorted(portfolios, key=lambda x: x['total_return'], reverse=True)

    for i, portfolio in enumerate(sorted_portfolios, 1):
        metrics = portfolio['metrics']
        print(f"{i}. {portfolio['name']}")
        print(f"   Total Return: {portfolio['total_return']:.2f}%")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"   Volatility: {metrics['volatility']:.2f}%")
        print(f"   Win Rate: {metrics['win_rate']:.1f}%")
        print()

    print("✓ Comparison complete!")


def visualize_comparison(portfolios: List[Dict], benchmark_df: pd.DataFrame,
                        output_path: str = 'charts/portfolio_comparison.png'):
    """
    Create comparison visualization for multiple portfolios.

    Args:
        portfolios: List of portfolio dictionaries with returns and metadata
        benchmark_df: DataFrame with benchmark data
        output_path: Path to save the chart
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    # Color palette
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

    # Plot each portfolio
    for i, portfolio in enumerate(portfolios):
        df = portfolio['returns']
        color = colors[i % len(colors)]
        ax.plot(df['date'], df['portfolio_value'], label=portfolio['name'],
               color=color, linewidth=2)

    # Plot benchmark
    if not benchmark_df.empty:
        ax.plot(benchmark_df['date'], benchmark_df['benchmark_value'],
               label='S&P 500', linestyle='--', color='gray', linewidth=2, alpha=0.7)

    # Formatting
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Portfolio Value (Base 100)', fontsize=12)
    ax.set_title('Portfolio Performance Comparison', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45)

    plt.tight_layout()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nComparison chart saved to: {output_path}")


def main():
    """Main execution function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Stock Portfolio Tracker with Basket Rebalancing')
    parser.add_argument('-c', '--config', default='portfolio_config.yaml',
                       help='Path to portfolio configuration file (default: portfolio_config.yaml)')
    parser.add_argument('-a', '--auto', action='store_true',
                       help='Automatically load config file if it exists (non-interactive mode)')
    parser.add_argument('--compare', nargs='+', metavar='CONFIG',
                       help='Compare multiple portfolios (provide 2+ config file paths)')
    args = parser.parse_args()

    # If compare mode, use different flow
    if args.compare:
        compare_portfolios(args.compare)
        return

    # Load environment variables
    load_dotenv()

    nasdaq_key = os.getenv('NASDAQ_DATA_LINK_API_KEY')
    fred_key = os.getenv('FRED_API_KEY')

    if not nasdaq_key:
        print("Error: NASDAQ_DATA_LINK_API_KEY not found in .env file")
        sys.exit(1)

    if not fred_key:
        print("Warning: FRED_API_KEY not found in .env file. Benchmark comparison will be skipped.")

    # Check for config file
    config_path = args.config
    if os.path.exists(config_path):
        if args.auto:
            # Auto mode: just load the config
            config = load_config(config_path)
            print(f"✓ Loaded configuration with {len(config.baskets)} basket(s) from {config_path}")
        else:
            # Interactive mode: ask user
            load_existing = input(f"\nFound existing config ({config_path}). Load it? (y/n): ").strip().lower()
            if load_existing == 'y':
                config = load_config(config_path)
                print(f"✓ Loaded configuration with {len(config.baskets)} basket(s)")
            else:
                config = interactive_basket_input()
                save_config(config, config_path)
    else:
        if args.auto:
            print(f"Error: Config file '{config_path}' not found. Cannot run in auto mode without config.")
            sys.exit(1)
        config = interactive_basket_input()

        save_choice = input("\nSave this configuration for future use? (y/n): ").strip().lower()
        if save_choice == 'y':
            save_config(config, config_path)

    # Get all unique tickers
    all_tickers = set()
    for basket in config.baskets:
        all_tickers.update(basket.tickers)

    print(f"\n{'='*60}")
    print(f"Fetching data for {len(all_tickers)} unique tickers...")
    print(f"{'='*60}\n")

    # Download stock prices
    start_date = config.baskets[0].start_date

    # Try bulk export first, fall back to SDK if it fails
    try:
        prices_df = download_nasdaq_prices(nasdaq_key, start_date, config.end_date)
        # Filter to only our tickers
        prices_df = prices_df[prices_df['ticker'].isin(all_tickers)]
    except Exception as e:
        print(f"Bulk export failed: {e}")
        print("Falling back to SDK method (slower but more reliable)...\n")
        prices_df = download_nasdaq_prices_sdk(nasdaq_key, list(all_tickers), start_date, config.end_date)

    # Download benchmark
    benchmark_df = pd.DataFrame(columns=['date', 'benchmark_value'])
    if fred_key:
        try:
            sp500_df = download_sp500_benchmark(fred_key, start_date, config.end_date)
            benchmark_df = calculate_benchmark_returns(sp500_df, start_date, config.end_date)
        except Exception as e:
            print(f"Warning: Could not fetch benchmark data: {e}")

    # Calculate portfolio returns
    print(f"\n{'='*60}")
    print("Calculating portfolio returns...")
    print(f"{'='*60}\n")

    portfolio_df = calculate_portfolio_returns(prices_df, config)

    # Display summary
    print(f"\n{'='*60}")
    print("PORTFOLIO SUMMARY")
    print(f"{'='*60}\n")

    final_value = portfolio_df.iloc[-1]['portfolio_value']
    total_return = ((final_value - 100) / 100) * 100

    print(f"Initial Value: $100.00")
    print(f"Final Value: ${final_value:.2f}")
    print(f"Total Return: {total_return:.2f}%")

    if not benchmark_df.empty:
        benchmark_final = benchmark_df.iloc[-1]['benchmark_value']
        if pd.notna(benchmark_final) and benchmark_final > 0:
            benchmark_return = ((benchmark_final - 100) / 100) * 100
            print(f"\nS&P 500 Return: {benchmark_return:.2f}%")
            print(f"Outperformance: {total_return - benchmark_return:.2f}%")
        else:
            print(f"\nWarning: Invalid benchmark data (final value: {benchmark_final})")

    # Visualize
    print(f"\n{'='*60}")
    print("Generating visualization...")
    print(f"{'='*60}\n")

    visualize_portfolio(portfolio_df, benchmark_df, config)

    print("\n✓ Analysis complete!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
