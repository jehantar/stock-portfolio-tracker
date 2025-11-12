#!/usr/bin/env python3
"""
Quick setup test to verify all dependencies and API keys are configured.
"""

import sys
import os
from dotenv import load_dotenv


def test_imports():
    """Test that all required packages are installed."""
    print("Testing imports...")
    required_packages = [
        ('pandas', 'pandas'),
        ('matplotlib', 'matplotlib'),
        ('requests', 'requests'),
        ('yaml', 'PyYAML'),
        ('dotenv', 'python-dotenv'),
        ('pandas_datareader', 'pandas-datareader'),
        ('fredapi', 'fredapi'),
    ]

    missing = []
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name} - NOT FOUND")
            missing.append(package_name)

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False

    print("\n✓ All packages installed successfully!")
    return True


def test_api_keys():
    """Test that API keys are configured."""
    print("\nTesting API keys...")

    load_dotenv()

    nasdaq_key = os.getenv('NASDAQ_DATA_LINK_API_KEY')
    fred_key = os.getenv('FRED_API_KEY')

    if nasdaq_key and nasdaq_key != 'your_nasdaq_api_key_here':
        print(f"  ✓ NASDAQ_DATA_LINK_API_KEY found ({nasdaq_key[:8]}...)")
    else:
        print("  ✗ NASDAQ_DATA_LINK_API_KEY not configured")
        print("    Add your key to .env file")
        return False

    if fred_key and fred_key != 'your_fred_api_key_here':
        print(f"  ✓ FRED_API_KEY found ({fred_key[:8]}...)")
    else:
        print("  ⚠ FRED_API_KEY not configured (optional - S&P 500 benchmark will be skipped)")

    print("\n✓ API keys configured!")
    return True


def test_directories():
    """Test that required directories exist."""
    print("\nTesting directories...")

    if os.path.exists('charts'):
        print("  ✓ charts/ directory exists")
    else:
        os.makedirs('charts')
        print("  ✓ charts/ directory created")

    return True


def main():
    """Run all tests."""
    print("="*60)
    print("STOCK PORTFOLIO TRACKER - Setup Test")
    print("="*60)
    print()

    all_passed = True

    if not test_imports():
        all_passed = False

    if not test_api_keys():
        all_passed = False

    if not test_directories():
        all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("✓ Setup complete! Ready to run portfolio_tracker.py")
    else:
        print("✗ Setup incomplete. Please fix the errors above.")
        sys.exit(1)
    print("="*60)


if __name__ == '__main__':
    main()
