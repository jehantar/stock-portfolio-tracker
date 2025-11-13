#!/usr/bin/env python3
"""
Interactive Stock Portfolio Tracker Dashboard

Streamlit-based dashboard for creating, editing, and analyzing stock portfolios
with basket rebalancing and performance metrics.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import traceback

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yaml
from dotenv import load_dotenv

# Import functions from portfolio_tracker
from portfolio_tracker import (
    Basket, PortfolioConfig,
    download_nasdaq_prices, download_nasdaq_prices_sdk,
    download_sp500_benchmark,
    calculate_portfolio_returns, calculate_benchmark_returns,
    calculate_advanced_metrics
)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Stock Portfolio Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for compact styling
st.markdown("""
<style>
    /* Reduce overall font sizes and top padding */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem;
        max-width: 100%;
    }

    /* Remove Streamlit default toolbar space */
    .stApp > header {
        background-color: transparent;
    }

    section[data-testid="stSidebar"] {
        top: 0;
    }

    /* Reduce top padding aggressively */
    div[data-testid="stVerticalBlock"] > div:first-child {
        padding-top: 0 !important;
    }

    .main-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.3rem;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* Target first element to remove top space */
    .main .block-container > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* Tighter spacing for all elements */
    .element-container {
        margin-bottom: 0.5rem !important;
    }

    /* Compact form elements */
    .stTextInput > label, .stDateInput > label, .stSelectbox > label {
        font-size: 0.85rem !important;
        margin-bottom: 0.2rem !important;
    }

    .stTextInput > div > div > input,
    .stDateInput > div > div > input,
    .stSelectbox > div > div {
        font-size: 0.9rem !important;
        padding: 0.3rem 0.5rem !important;
    }

    /* Compact buttons */
    .stButton > button {
        font-size: 0.9rem !important;
        padding: 0.35rem 0.75rem !important;
    }

    /* Compact expanders */
    .streamlit-expanderHeader {
        font-size: 0.95rem !important;
        padding: 0.5rem !important;
    }

    /* Compact metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
    }

    /* Reduce heading sizes */
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 0.5rem !important;
    }

    h2 {
        font-size: 1.4rem !important;
        margin-bottom: 0.4rem !important;
        margin-top: 0.8rem !important;
    }

    h3 {
        font-size: 1.1rem !important;
        margin-bottom: 0.3rem !important;
        margin-top: 0.6rem !important;
    }

    /* Tighter dividers */
    hr {
        margin: 0.5rem 0 !important;
    }

    .metric-card {
        background-color: #f0f2f6;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.3rem 0;
    }

    .basket-card {
        background-color: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin: 0.3rem 0;
    }

    /* Make date input more compact */
    .stDateInput {
        max-width: 100%;
    }

    /* Align metrics in the header row */
    div[data-testid="column"] .stMetric {
        margin-top: 0;
    }
</style>
""", unsafe_allow_html=True)


# Session state initialization
if 'config' not in st.session_state:
    st.session_state.config = None
if 'prices_df' not in st.session_state:
    st.session_state.prices_df = None
if 'benchmark_df' not in st.session_state:
    st.session_state.benchmark_df = None
if 'portfolio_returns' not in st.session_state:
    st.session_state.portfolio_returns = None
if 'configs' not in st.session_state:
    st.session_state.configs = {}  # For comparison mode


@st.cache_data(ttl=3600)
def fetch_stock_prices(api_key: str, start_date: str, end_date: str, tickers: List[str]) -> pd.DataFrame:
    """
    Cached function to fetch stock prices.

    Args:
        api_key: NASDAQ API key
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        tickers: List of ticker symbols

    Returns:
        DataFrame with stock prices
    """
    try:
        # Try bulk export first
        prices_df = download_nasdaq_prices(api_key, start_date, end_date)
        # Filter to only requested tickers
        prices_df = prices_df[prices_df['ticker'].isin(tickers)]
        return prices_df
    except Exception as e:
        st.warning(f"Bulk export failed: {e}. Falling back to SDK method...")
        # Fallback to SDK method
        return download_nasdaq_prices_sdk(api_key, tickers, start_date, end_date)


@st.cache_data(ttl=3600)
def fetch_benchmark(fred_key: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Cached function to fetch S&P 500 benchmark data.

    Args:
        fred_key: FRED API key
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        DataFrame with benchmark data
    """
    try:
        sp500_df = download_sp500_benchmark(fred_key, start_date, end_date)
        return calculate_benchmark_returns(sp500_df, start_date, end_date)
    except Exception as e:
        st.warning(f"Could not fetch benchmark data: {e}")
        return pd.DataFrame(columns=['date', 'benchmark_value'])


def create_interactive_chart(portfolio_df: pd.DataFrame, benchmark_df: pd.DataFrame,
                             config: PortfolioConfig, show_baskets: bool = True) -> go.Figure:
    """
    Create interactive Plotly chart for portfolio performance.

    Args:
        portfolio_df: Portfolio returns DataFrame
        benchmark_df: Benchmark returns DataFrame
        config: Portfolio configuration
        show_baskets: Whether to show basket transition lines

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Add portfolio line
    fig.add_trace(go.Scatter(
        x=portfolio_df['date'],
        y=portfolio_df['portfolio_value'],
        mode='lines',
        name='Portfolio',
        line=dict(color='#2E86AB', width=3),
        hovertemplate='<b>Portfolio</b><br>Date: %{x|%Y-%m-%d}<br>Value: %{y:.2f}<extra></extra>'
    ))

    # Add benchmark line
    if not benchmark_df.empty:
        fig.add_trace(go.Scatter(
            x=benchmark_df['date'],
            y=benchmark_df['benchmark_value'],
            mode='lines',
            name='S&P 500',
            line=dict(color='#A23B72', width=2, dash='dash'),
            hovertemplate='<b>S&P 500</b><br>Date: %{x|%Y-%m-%d}<br>Value: %{y:.2f}<extra></extra>'
        ))

    # Add basket transition lines
    if show_baskets:
        basket_colors = ['#F18F01', '#C73E1D', '#6A994E', '#BC4B51', '#FF6B6B', '#4ECDC4']
        for i, basket in enumerate(config.baskets):
            color = basket_colors[i % len(basket_colors)]
            basket_label = ', '.join(basket.tickers[:3])
            if len(basket.tickers) > 3:
                basket_label += f' +{len(basket.tickers)-3}'

            fig.add_vline(
                x=pd.to_datetime(basket.start_date).timestamp() * 1000,
                line=dict(color=color, width=2, dash='dot'),
                annotation=dict(
                    text=f"Basket {i+1}: {basket_label}",
                    textangle=-90,
                    yshift=10
                )
            )

    # Update layout
    fig.update_layout(
        title='Portfolio Performance Over Time',
        xaxis_title='Date',
        yaxis_title='Portfolio Value (Base = 100)',
        hovermode='x unified',
        template='plotly_white',
        height=600,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    return fig


def create_metrics_dashboard(portfolio_df: pd.DataFrame, benchmark_df: pd.DataFrame,
                             config: PortfolioConfig) -> Dict:
    """
    Calculate and display portfolio metrics.

    Args:
        portfolio_df: Portfolio returns DataFrame
        benchmark_df: Benchmark returns DataFrame
        config: Portfolio configuration

    Returns:
        Dictionary of calculated metrics
    """
    final_value = portfolio_df.iloc[-1]['portfolio_value']
    total_return = ((final_value - 100) / 100) * 100

    start = pd.to_datetime(config.baskets[0].start_date)
    end = pd.to_datetime(config.end_date)
    days = (end - start).days
    years = days / 365.25
    annualized_return = ((final_value / 100) ** (1 / years) - 1) * 100 if years > 0 else 0

    # Get advanced metrics
    advanced_metrics = calculate_advanced_metrics(portfolio_df, benchmark_df)

    # Benchmark metrics
    benchmark_return = 0
    outperformance = 0
    if not benchmark_df.empty:
        benchmark_final = benchmark_df.iloc[-1]['benchmark_value']
        benchmark_return = ((benchmark_final - 100) / 100) * 100
        outperformance = total_return - benchmark_return

    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'sharpe_ratio': advanced_metrics['sharpe_ratio'],
        'max_drawdown': advanced_metrics['max_drawdown'],
        'volatility': advanced_metrics['volatility'],
        'win_rate': advanced_metrics['win_rate'],
        'days_held': days,
        'benchmark_return': benchmark_return,
        'outperformance': outperformance
    }


def create_drawdown_chart(portfolio_df: pd.DataFrame) -> go.Figure:
    """Create drawdown chart."""
    portfolio_df = portfolio_df.copy()
    rolling_max = portfolio_df['portfolio_value'].expanding().max()
    drawdown = (portfolio_df['portfolio_value'] - rolling_max) / rolling_max * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=portfolio_df['date'],
        y=drawdown,
        fill='tozeroy',
        name='Drawdown',
        line=dict(color='#E63946'),
        hovertemplate='Date: %{x|%Y-%m-%d}<br>Drawdown: %{y:.2f}%<extra></extra>'
    ))

    fig.update_layout(
        title='Portfolio Drawdown Over Time',
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        template='plotly_white',
        height=400,
        hovermode='x unified'
    )

    return fig


def create_returns_distribution(portfolio_df: pd.DataFrame) -> go.Figure:
    """Create daily returns distribution chart."""
    portfolio_df = portfolio_df.copy()
    portfolio_df['daily_return'] = portfolio_df['portfolio_value'].pct_change() * 100

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=portfolio_df['daily_return'].dropna(),
        nbinsx=50,
        name='Daily Returns',
        marker=dict(color='#457B9D')
    ))

    fig.update_layout(
        title='Distribution of Daily Returns',
        xaxis_title='Daily Return (%)',
        yaxis_title='Frequency',
        template='plotly_white',
        height=400,
        showlegend=False
    )

    return fig


def load_yaml_configs() -> List[str]:
    """Load all YAML config files in the current directory."""
    configs = []
    for file in os.listdir('.'):
        if file.endswith('.yaml') or file.endswith('.yml'):
            if file not in ['portfolio_config.example.yaml']:
                configs.append(file)
    return sorted(configs)


def basket_editor():
    """Interactive basket editor component."""
    st.subheader("Portfolio Configuration")

    # Initialize config if not exists
    if st.session_state.config is None:
        st.session_state.config = PortfolioConfig(
            baskets=[Basket(tickers=['AAPL'], start_date=datetime.now().strftime('%Y-%m-%d'))],
            end_date=datetime.now().strftime('%Y-%m-%d')
        )

    config = st.session_state.config

    # End date
    col1, col2 = st.columns([2, 1])
    with col1:
        end_date = st.date_input(
            "Portfolio End Date",
            value=pd.to_datetime(config.end_date),
            key="end_date_input",
            format="MM/DD/YYYY"
        )
        config.end_date = end_date.strftime('%Y-%m-%d')

    with col2:
        st.markdown("")  # Align with input field
        st.metric("Number of Baskets", len(config.baskets))

    # Basket editor
    st.markdown("---")
    st.markdown("### Baskets")

    baskets_to_remove = []

    for i, basket in enumerate(config.baskets):
        with st.expander(f"📊 Basket {i+1}: {', '.join(basket.tickers[:3])}" +
                        (f" +{len(basket.tickers)-3}" if len(basket.tickers) > 3 else ""),
                        expanded=(i == len(config.baskets) - 1)):

            col1, col2 = st.columns([3, 2])

            with col1:
                tickers_input = st.text_input(
                    "Tickers (comma-separated)",
                    value=', '.join(basket.tickers),
                    key=f"basket_{i}_tickers",
                    label_visibility="visible"
                )
                basket.tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]

            with col2:
                start_date = st.date_input(
                    "Start Date" if i == 0 else "Transition Date",
                    value=pd.to_datetime(basket.start_date),
                    key=f"basket_{i}_start",
                    label_visibility="visible",
                    format="MM/DD/YYYY"
                )
                basket.start_date = start_date.strftime('%Y-%m-%d')

            # Remove button on its own row
            if st.button("🗑️ Remove Basket", key=f"remove_basket_{i}", type="secondary"):
                baskets_to_remove.append(i)

    # Remove baskets (after iteration to avoid modification during iteration)
    for i in reversed(baskets_to_remove):
        if len(config.baskets) > 1:  # Keep at least one basket
            config.baskets.pop(i)
            st.rerun()

    # Add new basket button
    if st.button("➕ Add New Basket"):
        # Default start date is after the last basket
        last_date = config.baskets[-1].start_date if config.baskets else config.end_date
        next_date = (pd.to_datetime(last_date) + timedelta(days=90)).strftime('%Y-%m-%d')
        config.baskets.append(Basket(tickers=['AAPL'], start_date=next_date))
        st.rerun()


def save_load_configs():
    """Save and load configuration management."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Configuration Management")

    # Save configuration
    save_name = st.sidebar.text_input("Config Name", value="my_portfolio")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("💾 Save"):
            if st.session_state.config:
                filename = f"{save_name}.yaml"
                with open(filename, 'w') as f:
                    yaml.dump(st.session_state.config.to_dict(), f, default_flow_style=False)
                st.sidebar.success(f"Saved to {filename}")
                st.rerun()
            else:
                st.sidebar.error("No configuration to save")

    with col2:
        if st.button("🔄 New"):
            st.session_state.config = PortfolioConfig(
                baskets=[Basket(tickers=['AAPL'], start_date=datetime.now().strftime('%Y-%m-%d'))],
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            st.session_state.prices_df = None
            st.session_state.portfolio_returns = None
            st.rerun()

    # Load configuration
    yaml_files = load_yaml_configs()
    if yaml_files:
        selected_file = st.sidebar.selectbox("Load Configuration", [""] + yaml_files)

        if selected_file:
            if st.sidebar.button("📂 Load"):
                try:
                    with open(selected_file, 'r') as f:
                        data = yaml.safe_load(f)
                    st.session_state.config = PortfolioConfig.from_dict(data)
                    st.session_state.prices_df = None  # Reset cached data
                    st.session_state.portfolio_returns = None
                    st.sidebar.success(f"Loaded {selected_file}")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Error loading config: {e}")


def main():
    """Main dashboard application."""

    # Header - with negative margin to reduce top space
    st.markdown('<div style="margin-top: -4rem;"><p class="main-header" style="margin-top: 0; padding-top: 0;">📈 Stock Portfolio Tracker</p></div>', unsafe_allow_html=True)
    st.markdown("Interactive dashboard for portfolio analysis with basket rebalancing")

    # Sidebar
    st.sidebar.title("Settings")

    # API Keys
    nasdaq_key = os.getenv('NASDAQ_DATA_LINK_API_KEY')
    fred_key = os.getenv('FRED_API_KEY')

    if not nasdaq_key:
        st.error("⚠️ NASDAQ_DATA_LINK_API_KEY not found in .env file")
        st.stop()

    if not fred_key:
        st.warning("⚠️ FRED_API_KEY not found. Benchmark comparison will be skipped.")

    st.sidebar.success("✅ API Keys Loaded")

    # Save/Load configs
    save_load_configs()

    st.sidebar.markdown("---")

    # View mode selector
    view_mode = st.sidebar.radio(
        "View Mode",
        ["Single Portfolio", "Portfolio Comparison"],
        key="view_mode"
    )

    # Main content
    if view_mode == "Single Portfolio":
        show_single_portfolio(nasdaq_key, fred_key)
    else:
        show_portfolio_comparison(nasdaq_key, fred_key)


def show_single_portfolio(nasdaq_key: str, fred_key: str):
    """Show single portfolio analysis."""

    # Basket editor
    basket_editor()

    st.markdown("---")

    # Run analysis button
    if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
        with st.spinner("Fetching data and calculating returns..."):
            try:
                config = st.session_state.config

                # Get all tickers
                all_tickers = set()
                for basket in config.baskets:
                    all_tickers.update(basket.tickers)

                start_date = config.baskets[0].start_date

                # Fetch prices
                st.info(f"Fetching prices for {len(all_tickers)} tickers...")
                prices_df = fetch_stock_prices(nasdaq_key, start_date, config.end_date, list(all_tickers))
                st.session_state.prices_df = prices_df

                # Fetch benchmark
                if fred_key:
                    st.info("Fetching S&P 500 benchmark...")
                    benchmark_df = fetch_benchmark(fred_key, start_date, config.end_date)
                    st.session_state.benchmark_df = benchmark_df
                else:
                    st.session_state.benchmark_df = pd.DataFrame(columns=['date', 'benchmark_value'])

                # Calculate returns
                st.info("Calculating portfolio returns...")
                portfolio_df = calculate_portfolio_returns(prices_df, config)
                st.session_state.portfolio_returns = portfolio_df

                st.success("✅ Analysis complete!")

            except Exception as e:
                st.error(f"Error during analysis: {e}")
                st.code(traceback.format_exc())

    # Display results if available
    if st.session_state.portfolio_returns is not None:
        portfolio_df = st.session_state.portfolio_returns
        benchmark_df = st.session_state.benchmark_df if st.session_state.benchmark_df is not None else pd.DataFrame()
        config = st.session_state.config

        # Metrics
        st.markdown("---")
        st.subheader("📊 Performance Metrics")

        metrics = create_metrics_dashboard(portfolio_df, benchmark_df, config)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Return", f"{metrics['total_return']:.2f}%")
            st.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")

        with col2:
            st.metric("Annualized Return", f"{metrics['annualized_return']:.2f}%")
            st.metric("Max Drawdown", f"{metrics['max_drawdown']:.2f}%")

        with col3:
            st.metric("Volatility (Annual)", f"{metrics['volatility']:.2f}%")
            st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")

        with col4:
            st.metric("Days Held", metrics['days_held'])
            if not benchmark_df.empty:
                st.metric("Outperformance vs S&P 500", f"{metrics['outperformance']:.2f}%")

        # Charts
        st.markdown("---")
        st.subheader("📈 Portfolio Performance")

        show_baskets = st.checkbox("Show Basket Transitions", value=True)
        fig = create_interactive_chart(portfolio_df, benchmark_df, config, show_baskets)
        st.plotly_chart(fig, use_container_width=True)

        # Additional analytics
        col1, col2 = st.columns(2)

        with col1:
            st.plotly_chart(create_drawdown_chart(portfolio_df), use_container_width=True)

        with col2:
            st.plotly_chart(create_returns_distribution(portfolio_df), use_container_width=True)

        # Data export
        st.markdown("---")
        st.subheader("💾 Export Data")

        col1, col2 = st.columns(2)

        with col1:
            csv = portfolio_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Portfolio Returns (CSV)",
                data=csv,
                file_name=f"portfolio_returns_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        with col2:
            metrics_df = pd.DataFrame([metrics])
            metrics_csv = metrics_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Metrics (CSV)",
                data=metrics_csv,
                file_name=f"portfolio_metrics_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )


def show_portfolio_comparison(nasdaq_key: str, fred_key: str):
    """Show portfolio comparison view."""

    st.subheader("📊 Portfolio Comparison")

    # Select portfolios to compare
    yaml_files = load_yaml_configs()

    if not yaml_files:
        st.warning("No saved portfolio configurations found. Please create and save portfolios first.")
        return

    selected_files = st.multiselect(
        "Select portfolios to compare (2-5 portfolios)",
        yaml_files,
        default=yaml_files[:min(2, len(yaml_files))]
    )

    if len(selected_files) < 2:
        st.info("Please select at least 2 portfolios to compare")
        return

    if len(selected_files) > 5:
        st.warning("Please select at most 5 portfolios for better visualization")
        return

    # Run comparison
    if st.button("🚀 Compare Portfolios", type="primary", use_container_width=True):
        with st.spinner("Loading and analyzing portfolios..."):
            try:
                portfolios = []
                all_tickers = set()
                min_start_date = None
                max_end_date = None

                # Load all configs
                for config_file in selected_files:
                    with open(config_file, 'r') as f:
                        data = yaml.safe_load(f)
                    config = PortfolioConfig.from_dict(data)
                    name = config_file.replace('.yaml', '').replace('_', ' ').title()

                    portfolios.append({
                        'name': name,
                        'config': config,
                        'file': config_file
                    })

                    # Collect tickers and dates
                    for basket in config.baskets:
                        all_tickers.update(basket.tickers)

                    start = pd.to_datetime(config.baskets[0].start_date)
                    end = pd.to_datetime(config.end_date)

                    if min_start_date is None or start < min_start_date:
                        min_start_date = start
                    if max_end_date is None or end > max_end_date:
                        max_end_date = end

                st.info(f"Fetching data for {len(all_tickers)} unique tickers...")

                # Fetch data once
                prices_df = fetch_stock_prices(
                    nasdaq_key,
                    min_start_date.strftime('%Y-%m-%d'),
                    max_end_date.strftime('%Y-%m-%d'),
                    list(all_tickers)
                )

                if fred_key:
                    benchmark_df = fetch_benchmark(
                        fred_key,
                        min_start_date.strftime('%Y-%m-%d'),
                        max_end_date.strftime('%Y-%m-%d')
                    )
                else:
                    benchmark_df = pd.DataFrame(columns=['date', 'benchmark_value'])

                # Calculate returns for each portfolio
                st.info("Calculating returns for all portfolios...")
                for portfolio in portfolios:
                    portfolio_df = calculate_portfolio_returns(prices_df, portfolio['config'])
                    portfolio['returns'] = portfolio_df
                    portfolio['metrics'] = create_metrics_dashboard(
                        portfolio_df, benchmark_df, portfolio['config']
                    )

                st.session_state.comparison_portfolios = portfolios
                st.session_state.comparison_benchmark = benchmark_df

                st.success("✅ Comparison complete!")

            except Exception as e:
                st.error(f"Error during comparison: {e}")
                st.code(traceback.format_exc())

    # Display comparison results
    if 'comparison_portfolios' in st.session_state:
        portfolios = st.session_state.comparison_portfolios
        benchmark_df = st.session_state.comparison_benchmark

        # Metrics comparison table
        st.markdown("---")
        st.subheader("📊 Metrics Comparison")

        metrics_data = []
        for p in portfolios:
            metrics_data.append({
                'Portfolio': p['name'],
                'Total Return (%)': f"{p['metrics']['total_return']:.2f}",
                'Annual Return (%)': f"{p['metrics']['annualized_return']:.2f}",
                'Sharpe Ratio': f"{p['metrics']['sharpe_ratio']:.2f}",
                'Max Drawdown (%)': f"{p['metrics']['max_drawdown']:.2f}",
                'Volatility (%)': f"{p['metrics']['volatility']:.2f}",
                'Win Rate (%)': f"{p['metrics']['win_rate']:.1f}"
            })

        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(metrics_df, use_container_width=True)

        # Comparison chart
        st.markdown("---")
        st.subheader("📈 Performance Comparison")

        fig = go.Figure()

        colors = px.colors.qualitative.Set2

        for i, p in enumerate(portfolios):
            fig.add_trace(go.Scatter(
                x=p['returns']['date'],
                y=p['returns']['portfolio_value'],
                mode='lines',
                name=p['name'],
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=f"<b>{p['name']}</b><br>Date: %{{x|%Y-%m-%d}}<br>Value: %{{y:.2f}}<extra></extra>"
            ))

        # Add benchmark
        if not benchmark_df.empty:
            fig.add_trace(go.Scatter(
                x=benchmark_df['date'],
                y=benchmark_df['benchmark_value'],
                mode='lines',
                name='S&P 500',
                line=dict(color='gray', width=2, dash='dash'),
                hovertemplate='<b>S&P 500</b><br>Date: %{x|%Y-%m-%d}<br>Value: %{y:.2f}<extra></extra>'
            ))

        fig.update_layout(
            title='Portfolio Performance Comparison',
            xaxis_title='Date',
            yaxis_title='Portfolio Value (Base = 100)',
            hovermode='x unified',
            template='plotly_white',
            height=600,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # Individual portfolio details
        st.markdown("---")
        st.subheader("📋 Portfolio Details")

        for p in portfolios:
            with st.expander(f"📊 {p['name']} - {p['metrics']['total_return']:.2f}% Return"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown("**Baskets:**")
                    for i, basket in enumerate(p['config'].baskets):
                        st.write(f"{i+1}. {', '.join(basket.tickers)} (from {basket.start_date})")

                with col2:
                    st.markdown("**Key Metrics:**")
                    st.write(f"Sharpe: {p['metrics']['sharpe_ratio']:.2f}")
                    st.write(f"Max DD: {p['metrics']['max_drawdown']:.2f}%")
                    st.write(f"Volatility: {p['metrics']['volatility']:.2f}%")


if __name__ == '__main__':
    main()
