#!/bin/bash
# Start Dashboard Script
# Automatically sets up virtual environment and runs the dashboard

set -e

VENV_DIR="venv"

echo "🚀 Stock Portfolio Tracker - Dashboard Launcher"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install/upgrade dependencies
echo "📥 Installing/upgrading dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✅ Dependencies ready"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create a .env file with your API keys:"
    echo ""
    echo "NASDAQ_DATA_LINK_API_KEY=your_key_here"
    echo "FRED_API_KEY=your_key_here"
    echo ""
    echo "Get keys from:"
    echo "- NASDAQ: https://data.nasdaq.com/sign-up"
    echo "- FRED: https://fred.stlouisfed.org/docs/api/api_key.html"
    echo ""
    exit 1
fi

echo "✅ API keys found"
echo ""

# Run the dashboard
echo "🌐 Starting dashboard..."
echo "Dashboard will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

streamlit run dashboard.py
