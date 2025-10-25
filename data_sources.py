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

    def fetch_coingecko_data(self, symbol: str, days: int = 3650) -> pd.DataFrame:
        """
        Fetch cryptocurrency data from CoinGecko (free, no API key needed)
        Returns DataFrame with OHLCV data
        """
        try:
            coin_id = self.crypto_map.get(symbol)
            if not coin_id:
                logger.warning(f"Symbol {symbol} not found in crypto mapping")
                return None

            logger.info(f"Fetching {symbol} from CoinGecko...")

            # Fetch price data
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': min(days, 3650),  # CoinGecko limit
                'interval': 'daily'
            }

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()
            prices = data.get('prices', [])

            if not prices:
                logger.warning(f"No price data received from CoinGecko for {symbol}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(prices, columns=['timestamp', 'Close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # CoinGecko only provides close prices, so we'll use them for OHLC
            df['Open'] = df['Close']
            df['High'] = df['Close']
            df['Low'] = df['Close']
            df['Volume'] = 0  # Not available in this endpoint

            logger.info(f"✓ CoinGecko: {len(df)} records for {symbol}")
            return df

        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API error for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {symbol} from CoinGecko: {str(e)}")
            return None

    def fetch_alternative_stock_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch stock data using alternative free sources
        Currently using: Financial Modeling Prep (limited free tier)
        """
        try:
            # Note: This is a free tier with limits
            # You can add API key for higher limits: https://financialmodelingprep.com
            logger.info(f"Attempting alternative source for {symbol}...")

            end_date = datetime.now()
            start_date = end_date - timedelta(days=3650)  # 10 years

            # Free tier FMP endpoint (limited to 250 requests/day)
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
            params = {
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }

            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                historical = data.get('historical', [])

                if historical:
                    df = pd.DataFrame(historical)
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    df.sort_index(inplace=True)

                    # Rename columns to match yfinance format
                    df = df.rename(columns={
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    })

                    logger.info(f"✓ FMP: {len(df)} records for {symbol}")
                    return df[['Open', 'High', 'Low', 'Close', 'Volume']]

            logger.warning(f"FMP returned status {response.status_code} for {symbol}")
            return None

        except Exception as e:
            logger.warning(f"Alternative stock fetch failed for {symbol}: {str(e)}")
            return None

    def fetch_with_fallback(self, symbol: str) -> tuple:
        """
        Fetch data with automatic fallback between sources
        Returns (DataFrame, source_name)
        """
        # Strategy 1: For crypto, try CoinGecko first (most reliable)
        if '-USD' in symbol:
            logger.info(f"Crypto detected: {symbol}")
            df = self.fetch_coingecko_data(symbol)
            if df is not None and not df.empty:
                return df, "CoinGecko API"

        # Strategy 2: For stocks/ETFs, try alternative source
        if not symbol.endswith('=X') and '-USD' not in symbol:
            logger.info(f"Stock/ETF detected: {symbol}")
            df = self.fetch_alternative_stock_data(symbol)
            if df is not None and not df.empty:
                return df, "Financial Modeling Prep"

        # Strategy 3: yfinance as fallback (may be rate-limited)
        logger.info(f"Trying yfinance for {symbol}...")
        try:
            import yfinance as yf
            time.sleep(0.5)  # Rate limiting

            ticker = yf.Ticker(symbol)

            # Try with period parameter
            for period in ['10y', '5y', '3y']:
                try:
                    hist = ticker.history(period=period)
                    if not hist.empty:
                        logger.info(f"✓ yfinance ({period}): {len(hist)} records for {symbol}")
                        return hist, f"yfinance ({period})"
                except:
                    continue

        except Exception as e:
            logger.warning(f"yfinance failed for {symbol}: {str(e)}")

        logger.error(f"❌ All data sources failed for {symbol}")
        return None, None


# Global instance
data_source_manager = DataSourceManager()


def get_historical_data(symbol: str):
    """
    Main function to get historical data with automatic fallback
    Returns (DataFrame, source_name)
    """
    return data_source_manager.fetch_with_fallback(symbol)
