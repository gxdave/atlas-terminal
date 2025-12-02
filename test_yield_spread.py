"""
Test script for Yield Spread Analyzer
Validates the analyzer functionality without running the full backend
"""

import sys
import logging
from yield_spread_analyzer import YieldSpreadAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_analyzer():
    """Test the yield spread analyzer"""
    print("\n" + "="*60)
    print("YIELD SPREAD ANALYZER TEST")
    print("="*60 + "\n")

    analyzer = YieldSpreadAnalyzer()

    # Test 1: Fetch Treasury Yields
    print("TEST 1: Fetching US Treasury Yields...")
    yields = analyzer.fetch_treasury_yields(period="1mo")

    if not yields.empty:
        print(f"✓ SUCCESS: Fetched {len(yields)} data points")
        print(f"  Columns: {list(yields.columns)}")
        print(f"  Date range: {yields.index[0]} to {yields.index[-1]}")
        print(f"  Latest values:")
        for col in yields.columns:
            print(f"    {col}: {yields[col].iloc[-1]:.2f}%")
    else:
        print("✗ FAILED: No yield data fetched")
        return False

    # Test 2: Fetch FX Data
    print("\nTEST 2: Fetching FX and Risk Data...")
    fx_data = analyzer.fetch_fx_data(period="1mo")

    if not fx_data.empty:
        print(f"✓ SUCCESS: Fetched {len(fx_data)} data points")
        print(f"  Columns: {list(fx_data.columns)}")
        print(f"  Latest values:")
        for col in fx_data.columns:
            print(f"    {col}: {fx_data[col].iloc[-1]:.2f}")
    else:
        print("✗ FAILED: No FX data fetched")
        return False

    # Test 3: Calculate Spreads
    print("\nTEST 3: Calculating Yield Spreads...")
    spreads = analyzer.calculate_spreads(yields)

    if not spreads.empty:
        print(f"✓ SUCCESS: Calculated {len(spreads.columns)} spreads")
        print(f"  Spreads: {list(spreads.columns)}")
        print(f"  Latest values:")
        for col in spreads.columns:
            print(f"    {col}: {spreads[col].iloc[-1]:.2f} bp")
    else:
        print("✗ FAILED: No spreads calculated")
        return False

    # Test 4: Calculate Z-Scores
    print("\nTEST 4: Calculating Z-Scores...")
    z_scores = analyzer.calculate_z_scores(spreads, window=20)

    if not z_scores.empty:
        print(f"✓ SUCCESS: Calculated Z-scores")
        print(f"  Latest Z-scores:")
        for col in z_scores.columns:
            z = z_scores[col].iloc[-1]
            if not pd.isna(z):
                print(f"    {col}: {z:.2f}σ")
    else:
        print("✗ FAILED: No Z-scores calculated")
        return False

    # Test 5: Rolling Correlation
    print("\nTEST 5: Testing Rolling Correlation...")
    returns_spread = analyzer.calculate_returns(spreads)
    returns_fx = analyzer.calculate_returns(fx_data)

    if not returns_spread.empty and not returns_fx.empty:
        if 'US_10Y_2Y' in returns_spread.columns and 'DXY' in returns_fx.columns:
            correlations = analyzer.calculate_rolling_correlation(
                returns_spread['US_10Y_2Y'],
                returns_fx['DXY'],
                windows=[30]
            )

            if correlations:
                print(f"✓ SUCCESS: Calculated rolling correlations")
                for window, series in correlations.items():
                    if not series.empty:
                        latest = series.iloc[-1]
                        print(f"  {window} correlation: {latest:.3f}")
            else:
                print("⚠ WARNING: Not enough data for correlation")
        else:
            print("⚠ WARNING: Required columns not available for correlation")
    else:
        print("✗ FAILED: No returns calculated")
        return False

    # Test 6: Lead/Lag Analysis
    print("\nTEST 6: Testing Lead/Lag Analysis...")
    if not returns_spread.empty and not returns_fx.empty:
        if 'US_10Y_2Y' in returns_spread.columns and 'DXY' in returns_fx.columns:
            lead_lag = analyzer.calculate_lead_lag(
                returns_spread['US_10Y_2Y'],
                returns_fx['DXY'],
                max_lag=10
            )

            if lead_lag:
                print(f"✓ SUCCESS: Calculated lead/lag")
                print(f"  Lag: {lead_lag['lag']} days")
                print(f"  Correlation: {lead_lag['correlation']:.3f}")

                if lead_lag['lag'] < 0:
                    print(f"  → Spread leads DXY by {abs(lead_lag['lag'])} days")
                elif lead_lag['lag'] > 0:
                    print(f"  → DXY leads Spread by {lead_lag['lag']} days")
                else:
                    print(f"  → Synchronous movement")
            else:
                print("✗ FAILED: Lead/lag calculation failed")
                return False
        else:
            print("⚠ WARNING: Required columns not available for lead/lag")
    else:
        print("✗ FAILED: No returns available for lead/lag")
        return False

    # Test 7: Quick Summary
    print("\nTEST 7: Testing Quick Summary...")
    summary = analyzer.get_summary()

    if summary.get('status') == 'success':
        print(f"✓ SUCCESS: Summary generated")
        if 'yields' in summary:
            print(f"  Yields available: {list(summary['yields']['current'].keys())}")
        if 'fx' in summary:
            print(f"  FX data available: {list(summary['fx']['current'].keys())}")
        if 'spreads' in summary:
            print(f"  Spreads available: {list(summary['spreads']['current'].keys())}")
    else:
        print(f"✗ FAILED: {summary.get('error', 'Unknown error')}")
        return False

    # Test 8: Full Analysis
    print("\nTEST 8: Testing Full Analysis (6 months)...")
    print("  This may take 10-20 seconds...\n")

    analysis = analyzer.analyze(period="6mo")

    if analysis.get('status') == 'success':
        print(f"✓ SUCCESS: Full analysis completed")

        # Check components
        components = ['current', 'correlations', 'lead_lag', 'historical', 'alerts']
        for comp in components:
            if comp in analysis:
                print(f"  ✓ {comp} available")
            else:
                print(f"  ✗ {comp} missing")

        # Show alerts
        if analysis.get('alerts'):
            print(f"\n  ALERTS ({len(analysis['alerts'])}):")
            for alert in analysis['alerts']:
                print(f"    [{alert['severity']}] {alert['type']}: {alert['message']}")
        else:
            print(f"\n  No alerts triggered")

        # Show correlation summary
        if 'correlations' in analysis:
            print(f"\n  CORRELATION SUMMARY:")
            for spread, fx_pairs in analysis['correlations'].items():
                for fx, windows in fx_pairs.items():
                    if '180d' in windows:
                        corr = windows['180d']
                        print(f"    {spread} vs {fx} (180d): {corr:.3f}")
    else:
        print(f"✗ FAILED: {analysis.get('error', 'Unknown error')}")
        return False

    print("\n" + "="*60)
    print("ALL TESTS PASSED ✓")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    try:
        import pandas as pd
        import numpy as np

        success = test_analyzer()
        sys.exit(0 if success else 1)

    except ImportError as e:
        print(f"\n✗ IMPORT ERROR: {e}")
        print("\nPlease install required dependencies:")
        print("  pip install pandas numpy yfinance scipy")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
