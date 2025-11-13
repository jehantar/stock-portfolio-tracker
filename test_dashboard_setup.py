#!/usr/bin/env python3
"""
Dashboard Setup Verification Script

Checks if all dashboard dependencies and configurations are ready.
"""

import sys
import os

def check_dashboard_setup():
    """Check if dashboard setup is complete."""

    print("=" * 60)
    print("DASHBOARD SETUP VERIFICATION")
    print("=" * 60)
    print()

    issues = []

    # Check Python version
    print("1. Checking Python version...")
    if sys.version_info < (3, 8):
        print("   ❌ Python 3.8+ required")
        issues.append("Python version too old")
    else:
        print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    print()

    # Check core dependencies
    print("2. Checking core dependencies...")
    core_deps = [
        'pandas',
        'matplotlib',
        'requests',
        'yaml',
        'dotenv',
        'nasdaqdatalink',
        'pandas_datareader',
        'fredapi'
    ]

    for dep in core_deps:
        try:
            if dep == 'yaml':
                __import__('yaml')
            elif dep == 'dotenv':
                __import__('dotenv')
            elif dep == 'nasdaqdatalink':
                __import__('nasdaqdatalink')
            else:
                __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} not installed")
            issues.append(f"{dep} missing")
    print()

    # Check dashboard dependencies
    print("3. Checking dashboard-specific dependencies...")
    dashboard_deps = [
        ('streamlit', 'Streamlit'),
        ('plotly', 'Plotly')
    ]

    for module, name in dashboard_deps:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ⚠️  {name} not installed (required for dashboard)")
            print(f"      Run: pip install {module}")
            issues.append(f"{name} missing")
    print()

    # Check environment variables
    print("4. Checking environment variables...")
    from dotenv import load_dotenv
    load_dotenv()

    nasdaq_key = os.getenv('NASDAQ_DATA_LINK_API_KEY')
    fred_key = os.getenv('FRED_API_KEY')

    if nasdaq_key:
        print(f"   ✅ NASDAQ_DATA_LINK_API_KEY found (length: {len(nasdaq_key)})")
    else:
        print("   ❌ NASDAQ_DATA_LINK_API_KEY not found in .env")
        issues.append("NASDAQ API key missing")

    if fred_key:
        print(f"   ✅ FRED_API_KEY found (length: {len(fred_key)})")
    else:
        print("   ⚠️  FRED_API_KEY not found (optional, but recommended)")
    print()

    # Check required files
    print("5. Checking required files...")
    required_files = [
        'portfolio_tracker.py',
        'dashboard.py',
        'requirements.txt',
        'DASHBOARD_README.md',
        'start_dashboard.sh'
    ]

    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} not found")
            issues.append(f"{file} missing")
    print()

    # Check for example configs
    print("6. Checking for example configurations...")
    if os.path.exists('portfolio_config.example.yaml'):
        print("   ✅ portfolio_config.example.yaml found")
    else:
        print("   ⚠️  portfolio_config.example.yaml not found")

    yaml_files = [f for f in os.listdir('.') if f.endswith('.yaml') or f.endswith('.yml')]
    yaml_files = [f for f in yaml_files if f != 'portfolio_config.example.yaml']

    if yaml_files:
        print(f"   ✅ Found {len(yaml_files)} portfolio config(s): {', '.join(yaml_files[:3])}")
    else:
        print("   ℹ️  No saved portfolios yet (create them in the dashboard)")
    print()

    # Summary
    print("=" * 60)
    if issues:
        print(f"❌ SETUP INCOMPLETE - {len(issues)} issue(s) found:")
        for issue in issues:
            print(f"   • {issue}")
        print()
        print("To fix:")
        print("1. Ensure you're in a virtual environment or use:")
        print("   ./start_dashboard.sh")
        print()
        print("2. Install missing packages:")
        print("   pip install -r requirements.txt")
        print()
        print("3. Create .env file with API keys (see README)")
        print("=" * 60)
        return False
    else:
        print("✅ DASHBOARD READY!")
        print()
        print("Start the dashboard with:")
        print("   ./start_dashboard.sh")
        print()
        print("Or manually:")
        print("   streamlit run dashboard.py")
        print("=" * 60)
        return True


if __name__ == '__main__':
    success = check_dashboard_setup()
    sys.exit(0 if success else 1)
