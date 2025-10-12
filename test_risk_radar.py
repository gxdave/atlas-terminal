"""
Test Script für Risk Radar API Endpoint
Testet die Backend-Integration des Risk Radars
"""

import requests
import json
from datetime import datetime

# API URL
API_URL = "http://127.0.0.1:8000"

def test_risk_radar():
    """Test Risk Radar API Endpoint"""
    print("=" * 60)
    print("RISK RADAR API TEST")
    print("=" * 60)
    print()

    # Test API Connection
    print("1. Testing API connection...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✓ API is running")
        else:
            print(f"   ✗ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ✗ Cannot connect to API. Make sure backend is running:")
        print("     python backend.py")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    print()

    # Test Risk Radar Endpoint
    print("2. Testing Risk Radar endpoint...")
    print("   (This may take 5-10 seconds to fetch FRED data...)")

    try:
        response = requests.get(f"{API_URL}/api/risk-radar", timeout=30)

        if response.status_code == 200:
            print("   ✓ Risk Radar endpoint is working")
            data = response.json()

            print()
            print("=" * 60)
            print("RISK RADAR RESULTS")
            print("=" * 60)
            print()

            # Current State
            if 'current_state' in data:
                current = data['current_state']
                print(f"Date:           {current.get('date', 'N/A')}")
                print(f"Regime:         {current.get('regime', 'N/A')}")
                print(f"Composite Z:    {current.get('composite_z', 0):.2f}")
                print()

                print("Components:")
                for name, values in current.get('components', {}).items():
                    print(f"  {name:<12}: {values.get('value', 0):6.2f} (Date: {values.get('date', 'N/A')})")
                print()

            # Alerts
            if 'alerts' in data:
                alerts = data['alerts']
                print(f"Recent Alerts: {len(alerts)}")
                if alerts:
                    print("Last 5 Alerts:")
                    for alert in alerts[-5:]:
                        print(f"  {alert.get('date', 'N/A')}: {alert.get('regime', 'N/A')} (Z={alert.get('composite_z', 0):.2f})")
                print()

            # Statistics
            if 'statistics' in data:
                stats = data['statistics']
                print("Regime Distribution (Last 12 Months):")
                regime_dist = stats.get('regime_distribution', {})
                total_days = stats.get('total_days', 1)
                for regime, count in regime_dist.items():
                    percentage = (count / total_days * 100) if total_days > 0 else 0
                    print(f"  {regime:<8}: {count:3d} days ({percentage:5.1f}%)")
                print()

                comp_stats = stats.get('composite_stats', {})
                print("Composite Z-Score Stats:")
                print(f"  Mean:    {comp_stats.get('mean', 0):6.2f}")
                print(f"  Std Dev: {comp_stats.get('std', 0):6.2f}")
                print(f"  Max:     {comp_stats.get('max', 0):6.2f}")
                print(f"  Min:     {comp_stats.get('min', 0):6.2f}")
                print()

            # Thresholds
            if 'thresholds' in data:
                print("Regime Thresholds:")
                for regime, threshold in data['thresholds'].items():
                    print(f"  {regime:<8}: {threshold}")
                print()

            print("=" * 60)
            print("✓ All tests passed successfully!")
            print("=" * 60)

            # Save full response to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"risk_radar_response_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\nFull response saved to: {filename}")

            return True

        else:
            print(f"   ✗ Risk Radar endpoint returned status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("   ✗ Request timeout. FRED API may be slow or unavailable.")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def test_direct_fredapi():
    """Test direct FRED API access"""
    print()
    print("=" * 60)
    print("DIRECT FRED API TEST")
    print("=" * 60)
    print()

    try:
        from fredapi import Fred
        import os

        # Use API key from environment or default
        api_key = os.environ.get("FRED_API_KEY", "a650cab7da43489ec04d1073446a338f")
        fred = Fred(api_key=api_key)

        print("Testing FRED API with VIX series...")
        vix = fred.get_series('VIXCLS')

        if vix is not None and len(vix) > 0:
            print(f"✓ Successfully loaded {len(vix)} VIX data points")
            print(f"  Latest VIX: {vix.iloc[-1]:.2f} (Date: {vix.index[-1].date()})")
            return True
        else:
            print("✗ No VIX data received")
            return False

    except ImportError:
        print("✗ fredapi not installed. Run: pip install fredapi")
        return False
    except Exception as e:
        print(f"✗ Error accessing FRED API: {e}")
        print("  This might be due to:")
        print("  - Invalid API key")
        print("  - Rate limit exceeded")
        print("  - Network issues")
        return False

if __name__ == "__main__":
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "ATLAS TERMINAL - RISK RADAR TEST" + " " * 11 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    # Test 1: Direct FRED API
    fred_ok = test_direct_fredapi()

    print()

    # Test 2: Risk Radar API
    if fred_ok:
        api_ok = test_risk_radar()
    else:
        print("Skipping Risk Radar API test due to FRED API issues.")
        api_ok = False

    print()
    print("=" * 60)
    if fred_ok and api_ok:
        print("✓ ALL TESTS PASSED")
        print()
        print("Next steps:")
        print("1. Open terminal.html in your browser")
        print("2. Navigate to 'Risk Radar' in the sidebar")
        print("3. Click 'REFRESH' to load current data")
    else:
        print("✗ SOME TESTS FAILED")
        print()
        print("Troubleshooting:")
        if not fred_ok:
            print("- Install fredapi: pip install fredapi")
            print("- Check FRED API key in environment or code")
        if not api_ok:
            print("- Make sure backend is running: python backend.py")
            print("- Check backend logs for errors")
    print("=" * 60)
    print()
