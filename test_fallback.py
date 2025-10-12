"""
Test the new fallback methods for data loading
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend import ProbabilityAnalyzer

def test_data_loading():
    """Test data loading with new fallback methods"""

    test_symbols = [
        ("GC=F", "Gold"),
        ("^GSPC", "S&P 500"),
        ("EURUSD=X", "EUR/USD"),
    ]

    analyzer = ProbabilityAnalyzer()

    print("=" * 60)
    print("DATA LOADING FALLBACK TEST")
    print("=" * 60)

    for symbol, name in test_symbols:
        print(f"\n[*] Testing {name} ({symbol})...")
        print("-" * 60)

        try:
            data = analyzer.load_data(symbol, timeframe='1d', period='1y')

            if not data.empty:
                print(f"[+] SUCCESS: Loaded {len(data)} candles")
                print(f"    Date range: {data.index[0]} to {data.index[-1]}")
                print(f"    Last close: {data['Close'].iloc[-1]:.2f}")
            else:
                print(f"[-] FAILED: No data loaded")

        except Exception as e:
            print(f"[-] ERROR: {str(e)}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_data_loading()
