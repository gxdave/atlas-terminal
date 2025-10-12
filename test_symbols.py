"""
Test script for symbol conversion and data loading
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend import convert_symbol_for_source, SYMBOL_CONVERSIONS

def test_symbol_conversions():
    """Test symbol conversion for different data sources"""

    print("=" * 60)
    print("SYMBOL CONVERSION TEST")
    print("=" * 60)

    test_symbols = [
        "EURUSD=X",  # Forex
        "GC=F",      # Gold
        "^GSPC",     # S&P 500
        "^DJI",      # Dow Jones
        "AAPL",      # Stock
        "CL=F",      # Crude Oil
    ]

    sources = ["alphavantage", "twelvedata"]

    for symbol in test_symbols:
        print(f"\n{symbol}:")
        print(f"  Display Name: {SYMBOL_CONVERSIONS.get(symbol, {}).get('display', 'N/A')}")
        for source in sources:
            converted = convert_symbol_for_source(symbol, source)
            print(f"  {source:15s}: {converted}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_symbol_conversions()
