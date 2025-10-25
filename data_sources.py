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
        # Strategy 1: For crypto, try CoinCap first (completely free, no API key)
        if '-USD' in symbol:
            logger.info(f"Crypto detected: {symbol}")
            df = self.fetch_coincap_data(symbol)
            if df is not None and not df.empty:
                return df, "CoinCap API (Free)"

        # Strategy 2: For stocks/ETFs, try yfinance directly (most reliable for stocks)
        if not symbol.endswith('=X') and '-USD' not in symbol:
            logger.info(f"Stock/ETF detected: {symbol}")
            try:
                import yfinance as yf
                time.sleep(0.3)

                ticker = yf.Ticker(symbol)

                # Try different periods
                for period in ['10y', '5y', '3y', '2y']:
                    try:
                        hist = ticker.history(period=period)
                        if not hist.empty and len(hist) > 100:  # Ensure meaningful data
                            logger.info(f"✓ yfinance ({period}): {len(hist)} records for {symbol}")
                            return hist, f"yfinance ({period})"
                    except:
                        continue
            except Exception as e:
                logger.warning(f"yfinance failed for stock {symbol}: {str(e)}")

        # Strategy 3: yfinance as fallback for other assets
        logger.info(f"Trying yfinance fallback for {symbol}...")
        try:
            import yfinance as yf
            time.sleep(0.5)

            ticker = yf.Ticker(symbol)

            for period in ['max', '10y', '5y']:
                try:
                    hist = ticker.history(period=period)
                    if not hist.empty:
                        logger.info(f"✓ yfinance ({period}): {len(hist)} records for {symbol}")
                        return hist, f"yfinance ({period})"
                except:
                    continue

        except Exception as e:
            logger.warning(f"Final yfinance attempt failed for {symbol}: {str(e)}")

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
