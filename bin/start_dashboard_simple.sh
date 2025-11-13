#!/bin/bash
# Simplified Dashboard Launcher
# Uses pipx for installation (recommended by macOS for Python apps)

set -e

echo "🚀 Stock Portfolio Tracker - Dashboard Launcher"
echo "================================================"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create a .env file with your API keys:"
    echo ""
    echo "NASDAQ_DATA_LINK_API_KEY=your_key_here"
    echo "FRED_API_KEY=your_key_here"
    echo ""
    exit 1
fi

echo "✅ API keys found"
echo ""

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "📦 Installing pipx (Python application installer)..."
    brew install pipx
    pipx ensurepath
    echo "✅ pipx installed"
    echo ""
fi

# Install streamlit via pipx if not already installed
if ! command -v streamlit &> /dev/null; then
    echo "📦 Installing Streamlit..."
    pipx install streamlit
    echo "✅ Streamlit installed"
    echo ""
else
    echo "✅ Streamlit already installed"
    echo ""
fi

# Install plotly in pipx streamlit environment
echo "📦 Ensuring plotly is available..."
pipx inject streamlit plotly || echo "⚠️  Plotly may already be installed"
echo ""

# Run the dashboard
echo "🌐 Starting dashboard..."
echo "Dashboard will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

streamlit run dashboard.py
