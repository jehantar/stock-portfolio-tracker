#!/bin/bash
# Dashboard Launcher (skips Streamlit onboarding prompt)

set -e

echo "🚀 Stock Portfolio Tracker - Dashboard"
echo "======================================"
echo ""

# Activate existing venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./run_dashboard.sh first to set up."
    exit 1
fi

source venv/bin/activate

# Create Streamlit config to skip email prompt
mkdir -p ~/.streamlit
if [ ! -f ~/.streamlit/config.toml ]; then
    cat > ~/.streamlit/config.toml <<EOF
[general]
email = ""

[browser]
gatherUsageStats = false
EOF
    echo "✅ Streamlit config created"
fi

echo "🌐 Starting dashboard at http://localhost:8501"
echo "Press Ctrl+C to stop"
echo ""

# Run dashboard
streamlit run dashboard.py
