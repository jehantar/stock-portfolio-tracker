#!/bin/bash
# Simple Dashboard Runner
# Uses existing system Python with minimal additional dependencies

set -e

echo "🚀 Stock Portfolio Tracker - Dashboard"
echo "======================================"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    exit 1
fi

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install only dashboard-specific deps (core deps already in system Python)
echo "📥 Installing dashboard dependencies..."
pip install -q --upgrade pip
pip install -q streamlit plotly 2>&1 || {
    echo "⚠️  Standard pip install failed. Trying with pre-built wheels..."
    pip install -q --only-binary=:all: streamlit plotly
}

echo "✅ Dependencies ready"
echo ""
echo "🌐 Starting dashboard at http://localhost:8501"
echo "Press Ctrl+C to stop"
echo ""

# Run dashboard
streamlit run dashboard.py
