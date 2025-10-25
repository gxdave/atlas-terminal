"""
Alternative Data Sources for Atlas Terminal
Provides fallback mechanisms when yfinance is blocked or rate-limited
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
import os
from demo_data_generator import PREGENERATED_DATA, get_demo_data

logger = logging.getLogger(__name__)

class DataSourceManager:
    """Manages multiple data sources with automatic fallback"""

    def __init__(self):
        self.crypto_map = {
            'BTC-USD': 'bitcoin',
            'ETH-USD': 'ethereum',
            'BNB-USD': 'binancecoin',
            'XRP-USD': 'ripple',
            'ADA-USD': 'cardano',
            'SOL-USD': 'solana',
            'DOGE-USD': 'dogecoin',
            'MATIC-USD': 'matic-network',
            'DOT-USD': 'polkadot',
            'AVAX-USD': 'avalanche-2',
            'LINK-USD': 'chainlink'
        }

    def fetch_coincap_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch cryptocurrency data from CoinCap API (completely free, no API key)
        Returns DataFrame with OHLCV data
        """
        try:
            # Map to CoinCap IDs
            coincap_map = {
                'BTC-USD': 'bitcoin',
                'ETH-USD': 'ethereum',
                'BNB-USD': 'binance-coin',
                'XRP-USD': 'xrp',
                'ADA-USD': 'cardano',
                'SOL-USD': 'solana',
                'DOGE-USD': 'dogecoin',
                'MATIC-USD': 'polygon',
                'DOT-USD': 'polkadot',
                'AVAX-USD': 'avalanche',
                'LINK-USD': 'chainlink'
            }

            coin_id = coincap_map.get(symbol)
            if not coin_id:
                logger.warning(f"Symbol {symbol} not in CoinCap mapping")
                return None

            logger.info(f"Fetching {symbol} from CoinCap...")

            # CoinCap provides historical data
            url = f"https://api.coincap.io/v2/assets/{coin_id}/history"
            params = {
                'interval': 'd1',  # Daily
                'start': int((datetime.now() - timedelta(days=3650)).timestamp() * 1000),
                'end': int(datetime.now().timestamp() * 1000)
            }

            response = requests.get(url, params=params, timeout=15)

            if response.status_code != 200:
                logger.warning(f"CoinCap returned {response.status_code} for {symbol}")
                return None

            data = response.json().get('data', [])

            if not data:
                logger.warning(f"No data from CoinCap for {symbol}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['time'], unit='ms')
            df.set_index('date', inplace=True)
            df['priceUsd'] = pd.to_numeric(df['priceUsd'])

            # Create OHLC from single price
            df['Close'] = df['priceUsd']
            df['Open'] = df['Close']
            df['High'] = df['Close']
            df['Low'] = df['Close']
            df['Volume'] = 0

            logger.info(f"✓ CoinCap: {len(df)} records for {symbol}")
            return df[['Open', 'High', 'Low', 'Close', 'Volume']]

        except Exception as e:
            logger.error(f"CoinCap fetch error for {symbol}: {str(e)}")
            return None

    def fetch_twelve_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch data from Twelve Data API (800 requests/day free tier, no API key needed)
        Works for stocks, ETFs, forex, crypto
        """
        try:
            logger.info(f"Attempting Twelve Data for {symbol}...")

            # Twelve Data free tier endpoint
            url = "https://api.twelvedata.com/time_series"
            params = {
                'symbol': symbol,
                'interval': '1day',
                'outputsize': 5000,  # Max for free tier
                'format': 'JSON'
            }

            response = requests.get(url, params=params, timeout=15)

            if response.status_code != 200:
                logger.warning(f"Twelve Data returned {response.status_code}")
                return None

            data = response.json()

            if 'values' not in data or not data['values']:
                logger.warning(f"No data from Twelve Data for {symbol}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data['values'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)

            # Convert string values to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Rename columns
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })

            logger.info(f"✓ Twelve Data: {len(df)} records for {symbol}")
            return df[['Open', 'High', 'Low', 'Close', 'Volume']]

        except Exception as e:
            logger.warning(f"Twelve Data fetch failed for {symbol}: {str(e)}")
            return None

    def fetch_alpha_vantage_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch data from Alpha Vantage using API key from environment
        Works for stocks, ETFs, forex, commodities
        Uses the same key as Probability Analyzer
        """
        try:
            logger.info(f"Attempting Alpha Vantage for {symbol}...")

            # Get API key from environment (same as probability analyzer)
            api_key = os.environ.get("ALPHAVANTAGE_API_KEY", "demo")

            if api_key == "demo":
                logger.warning("Using demo API key - may have severe rate limits")

            # Determine if it's forex
            is_forex = symbol.endswith('=X') or '/' in symbol

            # Convert symbol format for forex
            if is_forex:
                # Convert EURUSD=X to EUR/USD format
                clean_symbol = symbol.replace('=X', '')
                if '/' not in clean_symbol and len(clean_symbol) == 6:
                    # EURUSD -> EUR/USD
                    forex_symbol = f"{clean_symbol[:3]}/{clean_symbol[3:]}"
                else:
                    forex_symbol = clean_symbol

                logger.info(f"Forex detected: {symbol} -> {forex_symbol}")

                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'FX_DAILY',
                    'from_symbol': forex_symbol.split('/')[0],
                    'to_symbol': forex_symbol.split('/')[1],
                    'outputsize': 'full',
                    'apikey': api_key
                }
            else:
                # Regular stocks/ETFs
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'TIME_SERIES_DAILY',
                    'symbol': symbol,
                    'outputsize': 'full',
                    'apikey': api_key
                }

            response = requests.get(url, params=params, timeout=20)

            if response.status_code != 200:
                logger.warning(f"Alpha Vantage HTTP {response.status_code}")
                return None

            data = response.json()

            # Check for rate limit message
            if 'Note' in data or 'Information' in data:
                logger.warning(f"Alpha Vantage rate limit or info: {data.get('Note', data.get('Information'))}")
                return None

            # Get the time series key (different for stocks vs forex)
            if is_forex:
                ts_key = 'Time Series FX (Daily)'
            else:
                ts_key = 'Time Series (Daily)'

            if ts_key not in data:
                logger.warning(f"No time series data from Alpha Vantage for {symbol}")
                logger.debug(f"Response keys: {list(data.keys())}")
                return None

            # Convert to DataFrame
            time_series = data[ts_key]
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)

            # Rename columns (different naming for stocks vs forex)
            if is_forex:
                df = df.rename(columns={
                    '1. open': 'Open',
                    '2. high': 'High',
                    '3. low': 'Low',
                    '4. close': 'Close'
                })
                df['Volume'] = 0  # Forex doesn't have volume
            else:
                df = df.rename(columns={
                    '1. open': 'Open',
                    '2. high': 'High',
                    '3. low': 'Low',
                    '4. close': 'Close',
                    '5. volume': 'Volume'
                })

            # Convert to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            logger.info(f"✅ Alpha Vantage: {len(df)} records for {symbol}")
            return df[['Open', 'High', 'Low', 'Close', 'Volume']]

        except Exception as e:
            logger.warning(f"Alpha Vantage fetch failed for {symbol}: {str(e)}")
            return None

    def fetch_with_fallback(self, symbol: str) -> tuple:
        """
        Fetch data using Alpha Vantage for everything (except crypto)
        Returns (DataFrame, source_name)
        """
        # Strategy 1: For crypto, use CoinCap (completely free, no API key)
        if '-USD' in symbol:
            logger.info(f"Crypto detected: {symbol}")
            df = self.fetch_coincap_data(symbol)
            if df is not None and not df.empty:
                return df, "CoinCap API"

        # Strategy 2: For EVERYTHING ELSE, use Alpha Vantage (has API key)
        # Works for: Stocks, ETFs, Forex, Commodities
        logger.info(f"Using Alpha Vantage for {symbol}")
        df = self.fetch_alpha_vantage_data(symbol)
        if df is not None and not df.empty and len(df) > 100:
            asset_type = "Forex" if symbol.endswith('=X') else "Stock"
            return df, f"Alpha Vantage API ({asset_type})"

        # Strategy 3: Try Twelve Data as fallback
        logger.info(f"Alpha Vantage failed, trying Twelve Data for {symbol}")
        df = self.fetch_twelve_data(symbol)
        if df is not None and not df.empty and len(df) > 100:
            return df, "Twelve Data API"

        # Strategy 4: Use demo data as final fallback (ALWAYS WORKS)
        logger.warning(f"All APIs failed for {symbol}, using demo data")

        # Check if we have pre-generated data
        if symbol in PREGENERATED_DATA:
            logger.info(f"✅ Using pre-generated demo data for {symbol}")
            return PREGENERATED_DATA[symbol], "Demo Data (Simulated)"

        # Generate on-the-fly for other symbols
        try:
            df = get_demo_data(symbol)
            logger.info(f"✅ Generated demo data for {symbol}")
            return df, "Demo Data (Generated)"
        except Exception as e:
            logger.error(f"Even demo data generation failed: {str(e)}")
            return None, None


# Global instance
data_source_manager = DataSourceManager()


def get_historical_data(symbol: str):
    """
    Main function to get historical data with automatic fallback
    Returns (DataFrame, source_name)
    """
    return data_source_manager.fetch_with_fallback(symbol)
