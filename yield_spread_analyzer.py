"""
Yield Spread Analyzer - Makro-Analyse-Tool
Misst die Beziehung zwischen Zinsdifferenzen und USD-Stärke

Kernlogik:
1. Relative Zinsdifferenz (Interest Rate Advantage)
2. Dollar-Stärke / Marktreaktion
3. Statistische Auswertung (Correlation, Lead/Lag, Z-Score)

Philosophie: Neutral. Kalt. Objektiv. Keine Interpretation - nur Messung.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import yfinance as yf
from scipy import stats
from scipy.stats import zscore
import requests
import os
from fredapi import Fred

logger = logging.getLogger(__name__)


class YieldSpreadAnalyzer:
    """
    Analysiert Yield Spreads und deren Korrelation mit USD-Stärke
    """

    # Treasury Yield Symbols (yfinance)
    YIELD_SYMBOLS = {
        'US_2Y': '^IRX',      # US 13-Week Treasury (proxy for short-end)
        'US_10Y': '^TNX',     # US 10-Year Treasury
        'US_30Y': '^TYX',     # US 30-Year Treasury
    }

    # FX Symbols
    FX_SYMBOLS = {
        'DXY': 'DX-Y.NYB',    # Dollar Index
        'EURUSD': 'EURUSD=X',
        'USDJPY': 'USDJPY=X',
        'GBPUSD': 'GBPUSD=X',
    }

    # Risk Indicators
    RISK_SYMBOLS = {
        'VIX': '^VIX',
        'SPX': '^GSPC',
    }

    # FRED API Series IDs for International Yields
    FRED_SERIES = {
        # Germany (EU Proxy)
        'EU_2Y': 'IRLTLT01DEM156N',   # Germany 2-Year
        'EU_10Y': 'IRLTLT01DEM156N',  # Germany 10-Year
        # UK
        'UK_2Y': 'IRLTLT01GBM156N',   # UK 2-Year
        'UK_10Y': 'IRLTLT01GBM156N',  # UK 10-Year
        # Japan
        'JP_2Y': 'IRLTLT01JPM156N',   # Japan 2-Year
        'JP_10Y': 'IRLTLT01JPM156N',  # Japan 10-Year
        # Alternative US series from FRED
        'US_2Y_FRED': 'DGS2',         # US 2-Year
        'US_10Y_FRED': 'DGS10',       # US 10-Year
    }

    def __init__(self, fred_api_key: Optional[str] = None):
        """
        Initialize analyzer

        Args:
            fred_api_key: FRED API key (optional, will try env var if not provided)
        """
        self.cache = {}
        self.last_update = None

        # Initialize FRED API
        self.fred_api_key = fred_api_key or os.getenv('FRED_API_KEY')
        self.fred = None

        if self.fred_api_key:
            try:
                self.fred = Fred(api_key=self.fred_api_key)
                logger.info("FRED API initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize FRED API: {e}")
                self.fred = None
        else:
            logger.warning("No FRED API key provided - international yields unavailable")

    def fetch_treasury_yields(self, period: str = "1y") -> pd.DataFrame:
        """
        Fetch US Treasury yields from yfinance

        Args:
            period: Time period (1mo, 3mo, 6mo, 1y, 2y)

        Returns:
            DataFrame with yields
        """
        try:
            data = {}

            for name, symbol in self.YIELD_SYMBOLS.items():
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)

                if not hist.empty:
                    # yfinance returns yields as values, normalize to percentage
                    data[name] = hist['Close']

            if not data:
                logger.warning("No treasury data fetched")
                return pd.DataFrame()

            df = pd.DataFrame(data)
            df.index = pd.to_datetime(df.index)

            # Forward fill missing values
            df = df.fillna(method='ffill')

            return df

        except Exception as e:
            logger.error(f"Error fetching treasury yields: {e}")
            return pd.DataFrame()

    def fetch_international_yields(self, period: str = "1y") -> pd.DataFrame:
        """
        Fetch international government bond yields from FRED API

        Args:
            period: Time period (1mo, 3mo, 6mo, 1y, 2y)

        Returns:
            DataFrame with international yields (EU, UK, JP)
        """
        if not self.fred:
            logger.warning("FRED API not available - skipping international yields")
            return pd.DataFrame()

        try:
            # Convert period to date range
            end_date = datetime.now()
            period_days = {
                '1mo': 30,
                '3mo': 90,
                '6mo': 180,
                '1y': 365,
                '2y': 730,
                '5y': 1825
            }
            days = period_days.get(period, 365)
            start_date = end_date - timedelta(days=days)

            data = {}

            # Fetch each series from FRED
            # Note: Using correct FRED series IDs
            series_mapping = {
                'EU_2Y': 'IRLTLT01DEM156N',   # Germany 2-Year (not ideal, monthly)
                'EU_10Y': 'IRLTLT01DEM156N',  # Germany 10-Year (monthly)
                'UK_2Y': 'IRLTLT01GBM156N',   # UK 2-Year (monthly)
                'UK_10Y': 'IRLTLT01GBM156N',  # UK 10-Year (monthly)
                'JP_2Y': 'IRLTLT01JPM156N',   # Japan 2-Year (monthly)
                'JP_10Y': 'IRLTLT01JPM156N',  # Japan 10-Year (monthly)
                # Better alternatives - daily data
                'EU_10Y_ALT': 'IRLTLT01DEM156N',  # Will use this
                'UK_10Y_ALT': 'IRLTLT01GBM156N',
                'JP_10Y_ALT': 'IRLTLT01JPM156N',
            }

            # Try to fetch with better series
            # For 2Y and 10Y we'll use best available data
            series_to_fetch = {
                'EU_10Y': 'IRLTLT01DEM156N',
                'UK_10Y': 'IRLTLT01GBM156N',
                'JP_10Y': 'IRLTLT01JPM156N',
            }

            for name, series_id in series_to_fetch.items():
                try:
                    series = self.fred.get_series(
                        series_id,
                        observation_start=start_date.strftime('%Y-%m-%d'),
                        observation_end=end_date.strftime('%Y-%m-%d')
                    )

                    if series is not None and not series.empty:
                        data[name] = series
                        logger.info(f"Fetched {name}: {len(series)} observations")
                    else:
                        logger.warning(f"No data for {name} ({series_id})")

                except Exception as e:
                    logger.warning(f"Failed to fetch {name} ({series_id}): {e}")

            if not data:
                logger.warning("No international yields fetched from FRED")
                return pd.DataFrame()

            # Combine into DataFrame
            df = pd.DataFrame(data)
            df.index = pd.to_datetime(df.index)

            # Forward fill missing values (FRED data can be sparse)
            df = df.fillna(method='ffill')

            # Resample to daily and forward fill
            df = df.resample('D').ffill()

            logger.info(f"International yields fetched: {list(df.columns)}")
            return df

        except Exception as e:
            logger.error(f"Error fetching international yields: {e}")
            return pd.DataFrame()

    def fetch_fx_data(self, period: str = "1y") -> pd.DataFrame:
        """
        Fetch FX and risk indicator data

        Args:
            period: Time period

        Returns:
            DataFrame with FX prices
        """
        try:
            data = {}

            all_symbols = {**self.FX_SYMBOLS, **self.RISK_SYMBOLS}

            for name, symbol in all_symbols.items():
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)

                if not hist.empty:
                    data[name] = hist['Close']

            if not data:
                logger.warning("No FX data fetched")
                return pd.DataFrame()

            df = pd.DataFrame(data)
            df.index = pd.to_datetime(df.index)
            df = df.fillna(method='ffill')

            return df

        except Exception as e:
            logger.error(f"Error fetching FX data: {e}")
            return pd.DataFrame()

    def calculate_spreads(self, yields_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate yield spreads (US advantage)

        Calculates:
        - US Yield Curve (10Y-2Y)
        - International spreads (US vs EU/UK/JP) if data available

        Args:
            yields_df: DataFrame with yield data

        Returns:
            DataFrame with spreads
        """
        spreads = pd.DataFrame(index=yields_df.index)

        # US Yield Curve (most important for recession signal)
        if 'US_10Y' in yields_df.columns and 'US_2Y' in yields_df.columns:
            spreads['US_10Y_2Y'] = yields_df['US_10Y'] - yields_df['US_2Y']

        # International 10Y Spreads (US advantage)
        if 'US_10Y' in yields_df.columns:
            if 'EU_10Y' in yields_df.columns:
                spreads['US_EU_10Y'] = yields_df['US_10Y'] - yields_df['EU_10Y']

            if 'UK_10Y' in yields_df.columns:
                spreads['US_UK_10Y'] = yields_df['US_10Y'] - yields_df['UK_10Y']

            if 'JP_10Y' in yields_df.columns:
                spreads['US_JP_10Y'] = yields_df['US_10Y'] - yields_df['JP_10Y']

        # Note: 2Y spreads would require 2Y data from FRED
        # Currently focusing on 10Y as most widely available

        return spreads

    def calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate returns (changes) to avoid spurious correlations

        Args:
            df: Price/yield data

        Returns:
            DataFrame with returns
        """
        return df.pct_change().dropna()

    def calculate_rolling_correlation(
        self,
        series1: pd.Series,
        series2: pd.Series,
        windows: List[int] = [30, 90, 180]
    ) -> Dict[str, pd.Series]:
        """
        Calculate rolling correlation between two series

        Args:
            series1: First time series
            series2: Second time series
            windows: List of rolling windows in days

        Returns:
            Dict with correlation series for each window
        """
        correlations = {}

        # Align series
        aligned = pd.DataFrame({
            's1': series1,
            's2': series2
        }).dropna()

        for window in windows:
            if len(aligned) >= window:
                corr = aligned['s1'].rolling(window).corr(aligned['s2'])
                correlations[f'{window}d'] = corr

        return correlations

    def calculate_lead_lag(
        self,
        series1: pd.Series,
        series2: pd.Series,
        max_lag: int = 20
    ) -> Dict[str, float]:
        """
        Calculate lead/lag relationship between two series

        Args:
            series1: First time series (e.g., spread)
            series2: Second time series (e.g., DXY)
            max_lag: Maximum lag to test in days

        Returns:
            Dict with best lag and correlation
        """
        # Align series
        aligned = pd.DataFrame({
            's1': series1,
            's2': series2
        }).dropna()

        if len(aligned) < max_lag * 2:
            return {'lag': 0, 'correlation': 0.0}

        correlations = []

        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                # s1 leads s2
                corr = aligned['s1'].iloc[:lag].corr(aligned['s2'].iloc[-lag:])
            elif lag > 0:
                # s2 leads s1
                corr = aligned['s1'].iloc[lag:].corr(aligned['s2'].iloc[:-lag])
            else:
                # No lag
                corr = aligned['s1'].corr(aligned['s2'])

            correlations.append({
                'lag': lag,
                'correlation': corr if not np.isnan(corr) else 0.0
            })

        # Find lag with highest absolute correlation
        best = max(correlations, key=lambda x: abs(x['correlation']))

        return best

    def calculate_z_scores(self, df: pd.DataFrame, window: int = 252) -> pd.DataFrame:
        """
        Calculate rolling Z-scores to identify extreme values

        Args:
            df: Data
            window: Rolling window for mean/std calculation (default 252 = 1 year)

        Returns:
            DataFrame with Z-scores
        """
        z_scores = pd.DataFrame(index=df.index)

        for col in df.columns:
            rolling_mean = df[col].rolling(window).mean()
            rolling_std = df[col].rolling(window).std()
            z_scores[col] = (df[col] - rolling_mean) / rolling_std

        return z_scores

    def analyze(
        self,
        period: str = "1y",
        correlation_windows: List[int] = [30, 90, 180]
    ) -> Dict:
        """
        Main analysis function - comprehensive yield spread analysis

        Args:
            period: Time period to analyze
            correlation_windows: Windows for rolling correlation

        Returns:
            Dict with complete analysis results
        """
        try:
            logger.info(f"Starting yield spread analysis for period: {period}")

            # 1. Fetch data
            yields = self.fetch_treasury_yields(period)
            intl_yields = self.fetch_international_yields(period)
            fx_data = self.fetch_fx_data(period)

            if yields.empty or fx_data.empty:
                raise ValueError("Failed to fetch required data")

            # Combine US and international yields
            if not intl_yields.empty:
                all_yields = pd.concat([yields, intl_yields], axis=1, join='outer')
                all_yields = all_yields.fillna(method='ffill')
                logger.info(f"Combined yields: {list(all_yields.columns)}")
            else:
                all_yields = yields
                logger.info("Using US yields only (no international data)")

            # 2. Merge data on common dates
            merged = pd.concat([all_yields, fx_data], axis=1, join='inner')
            merged = merged.dropna()

            # 3. Calculate spreads
            spreads = self.calculate_spreads(all_yields)
            spreads = spreads.loc[merged.index]

            # 4. Calculate returns (for correlation analysis)
            spread_returns = self.calculate_returns(spreads)
            fx_returns = self.calculate_returns(fx_data)

            # Align returns
            common_index = spread_returns.index.intersection(fx_returns.index)
            spread_returns = spread_returns.loc[common_index]
            fx_returns = fx_returns.loc[common_index]

            # 5. Calculate Z-scores
            spread_zscores = self.calculate_z_scores(spreads)
            fx_zscores = self.calculate_z_scores(fx_data)

            # 6. Current values
            current_data = {
                'yields': yields.iloc[-1].to_dict() if not yields.empty else {},
                'fx': fx_data.iloc[-1].to_dict() if not fx_data.empty else {},
                'spreads': spreads.iloc[-1].to_dict() if not spreads.empty else {},
                'spread_zscores': spread_zscores.iloc[-1].to_dict() if not spread_zscores.empty else {},
                'fx_zscores': fx_zscores.iloc[-1].to_dict() if not fx_zscores.empty else {},
            }

            # 7. Calculate correlations for each spread-FX pair
            correlations = {}
            lead_lag = {}

            for spread_col in spread_returns.columns:
                correlations[spread_col] = {}
                lead_lag[spread_col] = {}

                for fx_col in ['DXY', 'EURUSD', 'USDJPY', 'GBPUSD']:
                    if fx_col in fx_returns.columns:
                        # Rolling correlations
                        rolling_corr = self.calculate_rolling_correlation(
                            spread_returns[spread_col],
                            fx_returns[fx_col],
                            correlation_windows
                        )

                        # Current correlations
                        current_corr = {}
                        for window, series in rolling_corr.items():
                            if not series.empty:
                                current_corr[window] = float(series.iloc[-1]) if not np.isnan(series.iloc[-1]) else 0.0

                        correlations[spread_col][fx_col] = current_corr

                        # Lead/Lag analysis
                        ll = self.calculate_lead_lag(
                            spread_returns[spread_col],
                            fx_returns[fx_col]
                        )
                        lead_lag[spread_col][fx_col] = ll

            # 8. Historical data for charts (last 180 days for performance)
            lookback = min(180, len(merged))
            historical = {
                'dates': merged.index[-lookback:].strftime('%Y-%m-%d').tolist(),
                'yields': all_yields.iloc[-lookback:].to_dict('list'),
                'spreads': spreads.iloc[-lookback:].to_dict('list'),
                'fx': fx_data.iloc[-lookback:].to_dict('list'),
                'spread_zscores': spread_zscores.iloc[-lookback:].to_dict('list'),
            }

            # 9. Alerts - identify extreme conditions
            alerts = []

            # Check for yield curve inversion
            if 'US_10Y_2Y' in current_data['spreads']:
                curve_spread = current_data['spreads']['US_10Y_2Y']
                if curve_spread < 0:
                    alerts.append({
                        'type': 'CURVE_INVERSION',
                        'severity': 'HIGH',
                        'message': f'US Yield Curve Inverted: {curve_spread:.2f}bp',
                        'value': curve_spread
                    })

            # Check for extreme Z-scores
            for spread_name, zscore in current_data['spread_zscores'].items():
                if abs(zscore) > 2.5:
                    alerts.append({
                        'type': 'EXTREME_ZSCORE',
                        'severity': 'MEDIUM' if abs(zscore) < 3 else 'HIGH',
                        'message': f'{spread_name} Z-Score: {zscore:.2f}σ',
                        'value': zscore
                    })

            # Check for high correlation
            for spread, fx_corrs in correlations.items():
                for fx, windows in fx_corrs.items():
                    for window, corr in windows.items():
                        if abs(corr) > 0.7:
                            alerts.append({
                                'type': 'HIGH_CORRELATION',
                                'severity': 'LOW',
                                'message': f'{spread} vs {fx} ({window}): {corr:.2f}',
                                'value': corr
                            })

            result = {
                'timestamp': datetime.now().isoformat(),
                'period': period,
                'current': current_data,
                'correlations': correlations,
                'lead_lag': lead_lag,
                'historical': historical,
                'alerts': alerts,
                'status': 'success'
            }

            logger.info("Yield spread analysis completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error in yield spread analysis: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }

    def get_summary(self) -> Dict:
        """
        Get quick summary of current market conditions

        Returns:
            Dict with summary data
        """
        try:
            # Fetch latest data
            yields = self.fetch_treasury_yields(period="5d")
            fx_data = self.fetch_fx_data(period="5d")

            if yields.empty or fx_data.empty:
                return {'status': 'error', 'error': 'No data available'}

            # Calculate current spread
            spreads = self.calculate_spreads(yields)

            latest_yields = yields.iloc[-1].to_dict()
            latest_fx = fx_data.iloc[-1].to_dict()
            latest_spreads = spreads.iloc[-1].to_dict()

            # Calculate 1-day change
            if len(yields) > 1:
                yield_change = (yields.iloc[-1] - yields.iloc[-2]).to_dict()
                fx_change = (fx_data.iloc[-1] - fx_data.iloc[-2]).to_dict()
                spread_change = (spreads.iloc[-1] - spreads.iloc[-2]).to_dict()
            else:
                yield_change = {k: 0.0 for k in latest_yields.keys()}
                fx_change = {k: 0.0 for k in latest_fx.keys()}
                spread_change = {k: 0.0 for k in latest_spreads.keys()}

            return {
                'timestamp': datetime.now().isoformat(),
                'yields': {
                    'current': latest_yields,
                    'change_1d': yield_change
                },
                'fx': {
                    'current': latest_fx,
                    'change_1d': fx_change
                },
                'spreads': {
                    'current': latest_spreads,
                    'change_1d': spread_change
                },
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# Singleton instance
_analyzer_instance = None

def get_analyzer() -> YieldSpreadAnalyzer:
    """Get or create analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = YieldSpreadAnalyzer()
    return _analyzer_instance
