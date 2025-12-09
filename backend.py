"""
Atlas Terminal Backend - FastAPI Integration
Integriert den Probability Analyzer für das Atlas Terminal
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import io
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
import yfinance as yf
import logging
from datetime import datetime, timedelta
import sys
import os
import json
import sqlite3

# Import authentication module
from auth import (
    Token, User, UserCreate, UserLogin, TokenData,
    authenticate_user, create_access_token, get_current_active_user,
    get_current_admin_user, create_user, get_all_users, delete_user,
    get_user_settings, update_user_settings, init_database,
    ACCESS_TOKEN_EXPIRE_MINUTES, DB_PATH
)

# Import data sources
from data_sources import get_historical_data

# Import yield spread analyzer
from yield_spread_analyzer import get_analyzer

# Add Prob_Analyzer path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../Prob_Analyzer'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Atlas Terminal API",
    description="Backend API für Atlas Terminal mit Probability Analyzer",
    version="1.1.2"
)

# CORS Middleware - Allow all origins for public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for public deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Symbol Mapping for different data sources
SYMBOL_ALIASES = {
    # Forex pairs
    "EURUSD=X": ["EURUSD=X", "EUR=X"],
    "GBPUSD=X": ["GBPUSD=X", "GBP=X"],
    "USDJPY=X": ["USDJPY=X", "JPY=X"],
    "AUDUSD=X": ["AUDUSD=X", "AUD=X"],
    "USDCHF=X": ["USDCHF=X", "CHF=X"]
}

# Symbol conversion for alternative data sources
SYMBOL_CONVERSIONS = {
    # Commodities
    "GC=F": {  # Gold
        "alphavantage": "GC",
        "twelvedata": "GC",
        "display": "Gold Futures"
    },
    "CL=F": {  # Crude Oil
        "alphavantage": "CL",
        "twelvedata": "CL",
        "display": "Crude Oil Futures"
    },
    "SI=F": {  # Silver
        "alphavantage": "SI",
        "twelvedata": "SI",
        "display": "Silver Futures"
    },
    # Indices
    "^GSPC": {  # S&P 500
        "alphavantage": "SPX",
        "twelvedata": "SPX",
        "display": "S&P 500"
    },
    "^NDX": {  # Nasdaq 100
        "alphavantage": "NDX",
        "twelvedata": "NDX",
        "display": "Nasdaq 100"
    },
    "^DJI": {  # Dow Jones
        "alphavantage": "DJI",
        "twelvedata": "DJI",
        "display": "Dow Jones"
    },
    "^DAX": {  # DAX
        "alphavantage": "DAX",
        "twelvedata": "DAX",
        "display": "DAX"
    },
    # Forex (for completeness)
    "EURUSD=X": {
        "alphavantage": "EURUSD",
        "twelvedata": "EUR/USD",
        "display": "EUR/USD"
    },
    "GBPUSD=X": {
        "alphavantage": "GBPUSD",
        "twelvedata": "GBP/USD",
        "display": "GBP/USD"
    },
    "USDJPY=X": {
        "alphavantage": "USDJPY",
        "twelvedata": "USD/JPY",
        "display": "USD/JPY"
    },
    "AUDUSD=X": {
        "alphavantage": "AUDUSD",
        "twelvedata": "AUD/USD",
        "display": "AUD/USD"
    },
    "USDCHF=X": {
        "alphavantage": "USDCHF",
        "twelvedata": "USD/CHF",
        "display": "USD/CHF"
    }
}

def convert_symbol_for_source(symbol: str, source: str) -> str:
    """Convert Yahoo Finance symbol to format needed by alternative source"""
    if symbol in SYMBOL_CONVERSIONS:
        return SYMBOL_CONVERSIONS[symbol].get(source, symbol)

    # Fallback: Basic conversion logic
    clean_symbol = symbol.replace('=X', '').replace('=F', '').replace('^', '')

    if source == "alphavantage":
        return clean_symbol
    elif source == "twelvedata":
        # Forex pairs need special format for Twelve Data
        if len(clean_symbol) == 6 and symbol.endswith('=X'):
            return f"{clean_symbol[:3]}/{clean_symbol[3:]}"
        return clean_symbol

    return symbol

# Assets Configuration
ASSETS = {
    "FX-Paare": {
        "EURUSD=X": "EUR/USD",
        "GBPUSD=X": "GBP/USD",
        "USDJPY=X": "USD/JPY",
        "AUDUSD=X": "AUD/USD",
        "USDCHF=X": "USD/CHF"
    },
    "Commodities": {
        "GC=F": "Gold",
        "CL=F": "Crude Oil",
        "SI=F": "Silver"
    },
    "Indizes": {
        "^GSPC": "S&P 500",
        "^NDX": "Nasdaq 100",
        "^DJI": "Dow Jones",
        "^DAX": "DAX"
    },
    "Aktien": {
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "TSLA": "Tesla",
        "META": "Meta",
        "NVDA": "NVIDIA",
        "GOOGL": "Google"
    }
}

TIMEFRAMES = {
    "1d": "Daily",
    "1wk": "Weekly",
    "1mo": "Monthly"
}

# Pydantic Models
class PatternRequest(BaseModel):
    pattern: List[str]
    symbol: str
    timeframe: str = "1d"
    period: str = "5y"

class AnalysisResponse(BaseModel):
    total_matches: int
    next_bullish: int
    next_bearish: int
    bullish_probability: float
    bearish_probability: float
    symbol: str
    timeframe: str
    pattern: List[str]
    data_info: Dict[str, Any]

# Global Analyzer Instance
analyzer_instance = None

class ProbabilityAnalyzer:
    """Probability Analyzer für Candlestick Patterns"""

    def __init__(self):
        self.data = None
        self.symbol = None
        self.timeframe = None

    def _try_alternative_source(self, symbol: str, timeframe: str, period: str) -> pd.DataFrame:
        """Try alternative data sources as fallback"""
        try:
            import requests

            # Try different free APIs (pass original symbol, each method handles conversion)
            sources = [
                self._try_yahoo_csv,  # Direct CSV download (best fallback)
                self._try_yahoo_finance_v8,  # Yahoo v8 API endpoint
                self._try_investing_com,  # Symbol variations
                self._try_twelvedata,  # Good for forex and indices (needs API key)
                self._try_alphavantage,  # Free tier with API key
            ]

            for source_func in sources:
                try:
                    logger.info(f"Trying alternative source: {source_func.__name__}")
                    data = source_func(symbol, timeframe, period)
                    if not data.empty:
                        logger.info(f"✓ SUCCESS with {source_func.__name__}")
                        return data
                except Exception as e:
                    logger.error(f"Alternative source {source_func.__name__} failed: {e}")
                    continue

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"All alternative sources failed: {e}")
            return pd.DataFrame()

    def _try_yahoo_finance_v8(self, symbol: str, timeframe: str, period: str) -> pd.DataFrame:
        """Try Yahoo Finance v8 API endpoint (sometimes works when others fail)"""
        import requests
        from datetime import datetime, timedelta

        try:
            # Calculate dates
            end_date = datetime.now()
            period_map = {'1y': 365, '2y': 730, '5y': 1825, '10y': 3650}
            days = period_map.get(period, 1825)
            start_date = end_date - timedelta(days=days)

            # Convert to Unix timestamps
            start_ts = int(start_date.timestamp())
            end_ts = int(end_date.timestamp())

            # Map timeframe
            interval_map = {'1d': '1d', '1wk': '1wk', '1mo': '1mo'}
            interval = interval_map.get(timeframe, '1d')

            # v8 chart API endpoint
            url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'period1': start_ts,
                'period2': end_ts,
                'interval': interval,
                'includePrePost': 'false',
                'events': 'div,splits'
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }

            logger.info(f"Yahoo v8 API: Trying {symbol}")
            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                json_data = response.json()

                if 'chart' in json_data and 'result' in json_data['chart']:
                    result = json_data['chart']['result'][0]

                    if 'timestamp' in result and 'indicators' in result:
                        timestamps = result['timestamp']
                        quote = result['indicators']['quote'][0]

                        data = pd.DataFrame({
                            'Open': quote.get('open', []),
                            'High': quote.get('high', []),
                            'Low': quote.get('low', []),
                            'Close': quote.get('close', []),
                            'Volume': quote.get('volume', [])
                        }, index=pd.to_datetime(timestamps, unit='s'))

                        data.dropna(subset=['Open', 'High', 'Low', 'Close'], inplace=True)

                        if not data.empty:
                            logger.info(f"Yahoo v8 API: SUCCESS - {len(data)} rows")
                            return data

            logger.warning(f"Yahoo v8 API: Failed with status {response.status_code}")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Yahoo v8 API failed: {e}")
            return pd.DataFrame()

    def _try_investing_com(self, symbol: str, timeframe: str, period: str) -> pd.DataFrame:
        """Try alternate symbol variations as last resort"""
        import requests

        try:
            # Try common symbol variations for Yahoo Finance
            variations = []

            if symbol == "GC=F":
                variations = ["GC=F", "GC.F", "GOLD"]
            elif symbol == "^GSPC":
                variations = ["^GSPC", "SPX", "INX"]
            elif symbol == "^DJI":
                variations = ["^DJI", "DJI", "INDU"]
            elif symbol == "^NDX":
                variations = ["^NDX", "NDX"]
            elif symbol == "^DAX":
                variations = ["^GDAXI", "^DAX", "DAX"]

            if not variations:
                return pd.DataFrame()

            logger.info(f"Trying symbol variations: {variations}")

            # Try Yahoo CSV with each variation
            for var_symbol in variations:
                try:
                    data = self._try_yahoo_csv(var_symbol, timeframe, period)
                    if not data.empty:
                        logger.info(f"✓ SUCCESS with variation: {var_symbol}")
                        return data
                except:
                    continue

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Symbol variations failed: {e}")
            return pd.DataFrame()

    def _try_twelvedata(self, symbol: str, timeframe: str, period: str) -> pd.DataFrame:
        """Try Twelve Data free tier (no API key needed for some endpoints)"""
        import requests

        # Twelve Data free endpoint
        url = f"https://api.twelvedata.com/time_series"

        # Map timeframe
        interval_map = {'1d': '1day', '1wk': '1week', '1mo': '1month'}
        interval = interval_map.get(timeframe, '1day')

        # Convert symbol format for Twelve Data using our conversion function
        api_symbol = convert_symbol_for_source(symbol, "twelvedata")
        logger.info(f"Converted {symbol} to Twelve Data format: {api_symbol}")

        params = {
            'symbol': api_symbol,
            'interval': interval,
            'outputsize': 5000,
            'format': 'JSON'
        }

        logger.info(f"Twelve Data request: {url} with params: {params}")
        response = requests.get(url, params=params, timeout=10)
        logger.info(f"Twelve Data response status: {response.status_code}")

        if response.status_code == 200:
            json_data = response.json()
            logger.info(f"Twelve Data JSON keys: {json_data.keys()}")

            if 'values' in json_data:
                df = pd.DataFrame(json_data['values'])
                logger.info(f"Twelve Data: Loaded {len(df)} rows")

                df['datetime'] = pd.to_datetime(df['datetime'])
                df.set_index('datetime', inplace=True)
                df = df.sort_index()

                # Rename columns to match yfinance format
                df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }, inplace=True)

                # Convert to numeric
                for col in ['Open', 'High', 'Low', 'Close']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                df.dropna(inplace=True)
                return df
            else:
                logger.error(f"Twelve Data error: {json_data.get('message', 'Unknown error')}")

        return pd.DataFrame()

    def _try_yahoo_csv(self, symbol: str, timeframe: str, period: str) -> pd.DataFrame:
        """Try Yahoo Finance CSV endpoint directly (bypasses some blocks)"""
        try:
            import requests
            from datetime import datetime, timedelta
            import time

            # Calculate dates
            end_date = datetime.now()
            period_map = {'1y': 365, '2y': 730, '5y': 1825, '10y': 3650}
            days = period_map.get(period, 1825)
            start_date = end_date - timedelta(days=days)

            # Convert to Unix timestamps
            start_ts = int(start_date.timestamp())
            end_ts = int(end_date.timestamp())

            # Map timeframe to Yahoo interval
            interval_map = {'1d': '1d', '1wk': '1wk', '1mo': '1mo'}
            interval = interval_map.get(timeframe, '1d')

            # Yahoo Finance CSV download URL
            url = f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}"
            params = {
                'period1': start_ts,
                'period2': end_ts,
                'interval': interval,
                'events': 'history',
                'includeAdjustedClose': 'true'
            }

            # Enhanced headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            logger.info(f"Yahoo CSV direct: Trying {symbol} via CSV endpoint")

            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200 and len(response.text) > 100:
                # Parse CSV
                from io import StringIO
                csv_data = StringIO(response.text)
                data = pd.read_csv(csv_data)

                if not data.empty and 'Date' in data.columns:
                    data['Date'] = pd.to_datetime(data['Date'])
                    data.set_index('Date', inplace=True)
                    data.sort_index(inplace=True)

                    # Ensure required columns exist
                    required_cols = ['Open', 'High', 'Low', 'Close']
                    if all(col in data.columns for col in required_cols):
                        logger.info(f"Yahoo CSV direct: SUCCESS - {len(data)} rows")
                        return data
                    else:
                        logger.warning(f"Yahoo CSV: Missing columns. Found: {data.columns.tolist()}")
            else:
                logger.warning(f"Yahoo CSV direct: HTTP {response.status_code}, content length: {len(response.text)}")

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Yahoo CSV direct failed: {e}")
            return pd.DataFrame()

    def _try_alphavantage(self, symbol: str, timeframe: str, period: str) -> pd.DataFrame:
        """Try Alpha Vantage (free tier: 25 requests/day, no credit card needed)"""
        import requests

        try:
            # Get API key from environment or use demo key
            api_key = os.environ.get("ALPHAVANTAGE_API_KEY", "demo")

            # Convert symbol format using our conversion function
            api_symbol = convert_symbol_for_source(symbol, "alphavantage")

            # Map function based on timeframe
            function_map = {
                '1d': 'TIME_SERIES_DAILY',
                '1wk': 'TIME_SERIES_WEEKLY',
                '1mo': 'TIME_SERIES_MONTHLY'
            }
            function = function_map.get(timeframe, 'TIME_SERIES_DAILY')

            # For Forex pairs - detect if it's a 6-char forex symbol (EURUSD, GBPUSD, etc.)
            if len(api_symbol) == 6 and symbol.endswith('=X'):  # EURUSD
                from_currency = api_symbol[:3]
                to_currency = api_symbol[3:]
                function = 'FX_DAILY' if timeframe == '1d' else 'FX_WEEKLY' if timeframe == '1wk' else 'FX_MONTHLY'

                url = "https://www.alphavantage.co/query"
                params = {
                    'function': function,
                    'from_symbol': from_currency,
                    'to_symbol': to_currency,
                    'apikey': api_key,
                    'outputsize': 'full'
                }
            else:
                # For stocks, indices, commodities
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': function,
                    'symbol': api_symbol,
                    'apikey': api_key,
                    'outputsize': 'full'
                }

            logger.info(f"Alpha Vantage: Trying {api_symbol} with function {function}")
            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                json_data = response.json()

                # Find the time series key
                ts_key = None
                for key in json_data.keys():
                    if 'Time Series' in key:
                        ts_key = key
                        break

                if ts_key and ts_key in json_data:
                    time_series = json_data[ts_key]
                    df = pd.DataFrame.from_dict(time_series, orient='index')

                    # Rename columns
                    df.rename(columns={
                        '1. open': 'Open',
                        '2. high': 'High',
                        '3. low': 'Low',
                        '4. close': 'Close',
                        '5. volume': 'Volume'
                    }, inplace=True)

                    df.index = pd.to_datetime(df.index)
                    df = df.sort_index()

                    # Convert to numeric
                    for col in ['Open', 'High', 'Low', 'Close']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')

                    df.dropna(inplace=True)

                    if not df.empty:
                        logger.info(f"Alpha Vantage: SUCCESS - {len(df)} rows")
                        return df

                logger.error(f"Alpha Vantage error: {json_data.get('Note', json_data.get('Information', 'Unknown'))}")

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Alpha Vantage failed: {e}")
            return pd.DataFrame()

    def load_data(self, symbol: str, timeframe: str, period: str = "5y") -> pd.DataFrame:
        """Load historical OHLC data from yfinance"""
        try:
            logger.info(f"Loading data for {symbol} with timeframe {timeframe}")

            # Enhanced headers to avoid Yahoo Finance blocking (Railway fix)
            import requests
            import random

            # Rotate User-Agents for better success rate
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
            ]

            session = requests.Session()
            session.headers.update({
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
                'DNT': '1'
            })
            logger.info("Using enhanced headers for Railway compatibility")

            # Try different symbol variations if available
            symbols_to_try = SYMBOL_ALIASES.get(symbol, [symbol])
            data = pd.DataFrame()

            # Retry configuration
            max_retries = 3
            retry_delay = 2  # seconds

            for try_symbol in symbols_to_try:
                logger.info(f"Attempting to load: {try_symbol}")

                for retry in range(max_retries):
                    try:
                        if retry > 0:
                            import time
                            logger.info(f"Retry {retry}/{max_retries} after {retry_delay}s delay")
                            time.sleep(retry_delay)

                        # Set timeout for requests
                        session.request = lambda *args, **kwargs: requests.Session.request(
                            session, *args, **{**kwargs, 'timeout': 10}
                        )

                        ticker = yf.Ticker(try_symbol, session=session)

                        # Method 1: With auto_adjust
                        logger.info(f"Method 1: period={period}, interval={timeframe}, auto_adjust=True")
                        data = ticker.history(
                            period=period,
                            interval=timeframe,
                            auto_adjust=True,
                            prepost=False,
                            actions=False,
                            timeout=10
                        )
                        logger.info(f"Method 1 result: {len(data)} rows, empty={data.empty}")

                        if not data.empty:
                            logger.info(f"✓ SUCCESS with {try_symbol} (Method 1)")
                            logger.info(f"Date range: {data.index[0]} to {data.index[-1]}")
                            break

                        # Method 2: Without auto_adjust
                        logger.info(f"Method 2: Trying without auto_adjust")
                        data = ticker.history(
                            period=period,
                            interval=timeframe,
                            auto_adjust=False,
                            prepost=False,
                            timeout=10
                        )
                        logger.info(f"Method 2 result: {len(data)} rows, empty={data.empty}")

                        if not data.empty:
                            logger.info(f"✓ SUCCESS with {try_symbol} (Method 2)")
                            logger.info(f"Date range: {data.index[0]} to {data.index[-1]}")
                            break

                    except Exception as e:
                        logger.error(f"✗ Exception for {try_symbol} (attempt {retry + 1}/{max_retries}): {str(e)}")
                        if retry == max_retries - 1:
                            continue

                if not data.empty:
                    break

            if data.empty:
                # Fallback: Try alternative data source (Alpha Vantage Free API)
                logger.warning(f"Yahoo Finance failed for {symbol}. Trying alternative source...")
                data = self._try_alternative_source(symbol, timeframe, period)

                if data.empty:
                    error_msg = f"No data for {symbol}. Tried: {', '.join(symbols_to_try)} + alternative sources"
                    logger.error(f"✗ FAILED: {error_msg}")
                    raise ValueError(error_msg)

            # Round to appropriate decimal places
            decimal_places = 5 if any(fx in symbol for fx in ['=X', 'USD', 'EUR', 'GBP', 'JPY']) else 2

            data['Open'] = data['Open'].round(decimal_places)
            data['High'] = data['High'].round(decimal_places)
            data['Low'] = data['Low'].round(decimal_places)
            data['Close'] = data['Close'].round(decimal_places)

            # Calculate price change and candle type
            data['Price_Change'] = (data['Close'] - data['Open']).round(decimal_places)
            data['Candle_Type'] = np.where(
                data['Price_Change'] > 0, 'Bullish',
                np.where(data['Price_Change'] < 0, 'Bearish', 'Doji')
            )

            self.data = data
            self.symbol = symbol
            self.timeframe = timeframe

            logger.info(f"Successfully loaded {len(data)} candles")
            return data

        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    def find_patterns(self, pattern: List[str]) -> List[int]:
        """Find all occurrences of the specified pattern"""
        if self.data is None or len(self.data) < len(pattern) + 1:
            return []

        matches = []
        pattern_length = len(pattern)

        for i in range(len(self.data) - pattern_length):
            match = True
            for j in range(pattern_length):
                if self.data.iloc[i + j]['Candle_Type'] != pattern[j]:
                    match = False
                    break

            if match:
                matches.append(i + pattern_length - 1)

        return matches

    def calculate_probabilities(self, pattern: List[str]) -> Dict:
        """Calculate probabilities for next candle after pattern"""
        matches = self.find_patterns(pattern)

        if not matches:
            return {
                'total_matches': 0,
                'next_bullish': 0,
                'next_bearish': 0,
                'bullish_probability': 0,
                'bearish_probability': 0,
                'pattern_details': []
            }

        next_bullish = 0
        next_bearish = 0
        valid_matches = []
        pattern_details = []

        for match_idx in matches:
            if match_idx + 1 < len(self.data):
                next_candle_type = self.data.iloc[match_idx + 1]['Candle_Type']
                valid_matches.append(match_idx)

                pattern_start = match_idx - len(pattern) + 1
                pattern_dates = [
                    self.data.index[pattern_start + i].strftime('%Y-%m-%d')
                    for i in range(len(pattern))
                ]

                pattern_details.append({
                    'pattern_dates': pattern_dates,
                    'next_date': self.data.index[match_idx + 1].strftime('%Y-%m-%d'),
                    'next_candle': next_candle_type
                })

                if next_candle_type == 'Bullish':
                    next_bullish += 1
                else:
                    next_bearish += 1

        total_valid = len(valid_matches)

        return {
            'total_matches': total_valid,
            'next_bullish': next_bullish,
            'next_bearish': next_bearish,
            'bullish_probability': (next_bullish / total_valid * 100) if total_valid > 0 else 0,
            'bearish_probability': (next_bearish / total_valid * 100) if total_valid > 0 else 0,
            'pattern_details': pattern_details
        }

# Initialize authentication database
init_database()

# Auto-create admin user if none exists
try:
    from auth import get_user, create_user, UserCreate

    if not get_user("admin"):
        logger.info("No admin user found - creating default admin...")
        admin_password = os.environ.get("ADMIN_PASSWORD", "Atlas2025!")

        admin_user = create_user(UserCreate(
            username="admin",
            password=admin_password,
            email="admin@atlas.com",
            full_name="Admin User",
            is_admin=True
        ))

        logger.info("=" * 60)
        logger.info("  ATLAS TERMINAL - Admin User Created!")
        logger.info("=" * 60)
        logger.info(f"  Username: {admin_user.username}")
        logger.info(f"  Password: {admin_password}")
        logger.info("  Login at: /login.html")
        logger.info("  IMPORTANT: Change this password after first login!")
        logger.info("=" * 60)
    else:
        logger.info("Admin user already exists")
except Exception as e:
    logger.warning(f"Admin auto-creation failed: {e}")

# API Endpoints

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.post("/api/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    """Login endpoint - returns JWT token"""
    user = authenticate_user(user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current logged in user"""
    return current_user

@app.post("/api/auth/register", response_model=User)
async def register_user(
    user_create: UserCreate,
    current_admin: User = Depends(get_current_admin_user)
):
    """Register new user (admin only)"""
    try:
        user = create_user(user_create)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.get("/api/admin/users", response_model=List[User])
async def list_users(current_admin: User = Depends(get_current_admin_user)):
    """List all users (admin only)"""
    return get_all_users()

@app.delete("/api/admin/users/{username}")
async def remove_user(
    username: str,
    current_admin: User = Depends(get_current_admin_user)
):
    """Delete user (admin only)"""
    if username == current_admin.username:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    try:
        delete_user(username)
        return {"message": f"User {username} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# USER WATCHLIST & SETTINGS ENDPOINTS
# ============================================

@app.get("/api/user/watchlist")
async def get_user_watchlist(current_user: User = Depends(get_current_active_user)):
    """Get user's watchlist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT symbol, category, added_at
        FROM watchlist
        WHERE username = ?
        ORDER BY added_at DESC
    """, (current_user.username,))

    watchlist = []
    for row in cursor.fetchall():
        watchlist.append({
            "symbol": row[0],
            "category": row[1],
            "added_at": row[2]
        })

    conn.close()
    return {"username": current_user.username, "watchlist": watchlist}

@app.post("/api/user/watchlist")
async def add_to_watchlist(
    symbol: str,
    category: str,
    current_user: User = Depends(get_current_active_user)
):
    """Add asset to watchlist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO watchlist (username, symbol, category)
            VALUES (?, ?, ?)
        """, (current_user.username, symbol, category))

        conn.commit()
        return {"message": f"Added {symbol} to watchlist"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Symbol already in watchlist")
    finally:
        conn.close()

@app.delete("/api/user/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_active_user)
):
    """Remove asset from watchlist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM watchlist
        WHERE username = ? AND symbol = ?
    """, (current_user.username, symbol))

    conn.commit()
    conn.close()

    return {"message": f"Removed {symbol} from watchlist"}

@app.get("/api/user/settings")
async def get_settings(current_user: User = Depends(get_current_active_user)):
    """Get user settings"""
    settings = get_user_settings(current_user.username)
    return {"username": current_user.username, "settings": settings}

@app.post("/api/user/settings")
async def update_settings(
    settings: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Update user settings"""
    update_user_settings(current_user.username, settings)
    return {"message": "Settings updated successfully"}

# ============================================
# USER WIDGETS MANAGEMENT
# ============================================

@app.get("/api/user/widgets")
async def get_user_widgets(current_user: User = Depends(get_current_active_user)):
    """Get user's dashboard widgets"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, widget_type, widget_config, position_x, position_y, width, height
        FROM user_widgets
        WHERE username = ?
        ORDER BY id
    """, (current_user.username,))

    widgets = []
    for row in cursor.fetchall():
        config = json.loads(row[2]) if row[2] else {}
        widgets.append({
            "id": row[0],
            "widget_type": row[1],
            "widget_config": config,
            "position_x": row[3],
            "position_y": row[4],
            "width": row[5],
            "height": row[6]
        })

    conn.close()
    return {"widgets": widgets}

class WidgetCreate(BaseModel):
    widget_type: str
    widget_config: dict = {}
    position_x: int = 0
    position_y: int = 0
    width: int = 400
    height: int = 300

@app.post("/api/user/widgets")
async def add_widget(
    widget_data: WidgetCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Add widget to user's dashboard"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO user_widgets
            (username, widget_type, widget_config, position_x, position_y, width, height)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            current_user.username,
            widget_data.widget_type,
            json.dumps(widget_data.widget_config),
            widget_data.position_x,
            widget_data.position_y,
            widget_data.width,
            widget_data.height
        ))

        widget_id = cursor.lastrowid
        conn.commit()

        logger.info(f"Widget created for {current_user.username}: ID={widget_id}, Type={widget_data.widget_type}")

        return {"message": "Widget added successfully", "widget_id": widget_id}

    except Exception as e:
        logger.error(f"Error adding widget: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding widget: {str(e)}")
    finally:
        conn.close()

@app.put("/api/user/widgets/{widget_id}")
async def update_widget(
    widget_id: int,
    widget_config: Optional[dict] = None,
    position_x: Optional[int] = None,
    position_y: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Update widget configuration"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updates = []
    params = []

    if widget_config is not None:
        updates.append("widget_config = ?")
        params.append(json.dumps(widget_config))

    if position_x is not None:
        updates.append("position_x = ?")
        params.append(position_x)

    if position_y is not None:
        updates.append("position_y = ?")
        params.append(position_y)

    if width is not None:
        updates.append("width = ?")
        params.append(width)

    if height is not None:
        updates.append("height = ?")
        params.append(height)

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    params.extend([current_user.username, widget_id])

    cursor.execute(f"""
        UPDATE user_widgets
        SET {', '.join(updates)}
        WHERE username = ? AND id = ?
    """, params)

    conn.commit()
    conn.close()

    return {"message": "Widget updated successfully"}

@app.delete("/api/user/widgets/{widget_id}")
async def delete_widget(
    widget_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete widget from dashboard"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM user_widgets
        WHERE username = ? AND id = ?
    """, (current_user.username, widget_id))

    conn.commit()
    conn.close()

    return {"message": "Widget deleted successfully"}

# ============================================
# EXISTING ENDPOINTS
# ============================================

@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "message": "Atlas Terminal API v1.1.1",
        "status": "running",
        "endpoints": [
            "/api/auth/login",
            "/api/auth/me",
            "/api/assets",
            "/api/timeframes",
            "/api/analyze",
            "/api/user/watchlist",
            "/api/user/widgets"
        ]
    }

@app.get("/api/assets")
async def get_assets():
    """Get all available assets"""
    return ASSETS

@app.get("/api/timeframes")
async def get_timeframes():
    """Get available timeframes"""
    return TIMEFRAMES

@app.post("/api/analyze")
async def analyze_pattern(request: PatternRequest):
    """Analyze candlestick pattern probabilities"""
    global analyzer_instance

    try:
        logger.info(f"Analyzing pattern {request.pattern} for {request.symbol}")

        # Initialize analyzer
        analyzer_instance = ProbabilityAnalyzer()

        # Load data
        data = analyzer_instance.load_data(
            symbol=request.symbol,
            timeframe=request.timeframe,
            period=request.period
        )

        if len(data) < 10:
            raise HTTPException(
                status_code=400,
                detail="Nicht genügend historische Daten verfügbar"
            )

        # Calculate probabilities
        results = analyzer_instance.calculate_probabilities(request.pattern)

        # Prepare response
        response = {
            'total_matches': results['total_matches'],
            'next_bullish': results['next_bullish'],
            'next_bearish': results['next_bearish'],
            'bullish_probability': round(results['bullish_probability'], 2),
            'bearish_probability': round(results['bearish_probability'], 2),
            'symbol': request.symbol,
            'timeframe': request.timeframe,
            'pattern': request.pattern,
            'data_info': {
                'total_candles': len(data),
                'date_range': {
                    'start': data.index[0].strftime('%Y-%m-%d'),
                    'end': data.index[-1].strftime('%Y-%m-%d')
                },
                'candle_types': {
                    'bullish': int(sum(data['Candle_Type'] == 'Bullish')),
                    'bearish': int(sum(data['Candle_Type'] == 'Bearish')),
                    'doji': int(sum(data['Candle_Type'] == 'Doji'))
                }
            }
        }

        logger.info(f"Analysis complete: {results['total_matches']} matches found")
        return response

    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analyse fehlgeschlagen: {str(e)}")

@app.post("/api/upload-csv")
async def upload_csv_data(file: UploadFile = File(...)):
    """Upload CSV file with OHLC data for custom analysis"""
    global analyzer_instance

    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")

        # Read file content
        content = await file.read()
        csv_buffer = io.BytesIO(content)

        # Load CSV into analyzer
        analyzer_instance = ProbabilityAnalyzer()

        # Read CSV with pandas
        data = pd.read_csv(csv_buffer)

        # Validate required columns
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close']
        missing_columns = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}. Required: Date, Open, High, Low, Close"
            )

        # Process data
        data['Date'] = pd.to_datetime(data['Date'])
        data.set_index('Date', inplace=True)
        data.sort_index(inplace=True)

        # Convert to numeric
        for col in ['Open', 'High', 'Low', 'Close']:
            data[col] = pd.to_numeric(data[col], errors='coerce')

        data.dropna(inplace=True)

        if data.empty:
            raise HTTPException(status_code=400, detail="No valid data in CSV file")

        # Calculate candle types
        decimal_places = 5 if data['Close'].median() < 10 else 2
        data['Open'] = data['Open'].round(decimal_places)
        data['High'] = data['High'].round(decimal_places)
        data['Low'] = data['Low'].round(decimal_places)
        data['Close'] = data['Close'].round(decimal_places)

        data['Price_Change'] = (data['Close'] - data['Open']).round(decimal_places)
        data['Candle_Type'] = np.where(
            data['Price_Change'] > 0, 'Bullish',
            np.where(data['Price_Change'] < 0, 'Bearish', 'Doji')
        )

        # Store in analyzer
        analyzer_instance.data = data
        analyzer_instance.symbol = f"Custom: {file.filename}"
        analyzer_instance.timeframe = "Custom"

        logger.info(f"CSV uploaded: {file.filename}, {len(data)} candles")

        return {
            "message": "CSV uploaded successfully",
            "filename": file.filename,
            "total_candles": len(data),
            "date_range": {
                "start": data.index[0].strftime('%Y-%m-%d'),
                "end": data.index[-1].strftime('%Y-%m-%d')
            },
            "candle_types": {
                "bullish": int(sum(data['Candle_Type'] == 'Bullish')),
                "bearish": int(sum(data['Candle_Type'] == 'Bearish')),
                "doji": int(sum(data['Candle_Type'] == 'Doji'))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")

@app.post("/api/analyze-csv")
async def analyze_csv_pattern(pattern: List[str]):
    """Analyze pattern using uploaded CSV data"""
    global analyzer_instance

    try:
        if analyzer_instance is None or analyzer_instance.data is None:
            raise HTTPException(
                status_code=400,
                detail="No CSV data loaded. Please upload a CSV file first."
            )

        # Calculate probabilities
        results = analyzer_instance.calculate_probabilities(pattern)

        response = {
            'total_matches': results['total_matches'],
            'next_bullish': results['next_bullish'],
            'next_bearish': results['next_bearish'],
            'bullish_probability': round(results['bullish_probability'], 2),
            'bearish_probability': round(results['bearish_probability'], 2),
            'symbol': analyzer_instance.symbol,
            'timeframe': analyzer_instance.timeframe,
            'pattern': pattern,
            'data_info': {
                'total_candles': len(analyzer_instance.data),
                'date_range': {
                    'start': analyzer_instance.data.index[0].strftime('%Y-%m-%d'),
                    'end': analyzer_instance.data.index[-1].strftime('%Y-%m-%d')
                },
                'candle_types': {
                    'bullish': int(sum(analyzer_instance.data['Candle_Type'] == 'Bullish')),
                    'bearish': int(sum(analyzer_instance.data['Candle_Type'] == 'Bearish')),
                    'doji': int(sum(analyzer_instance.data['Candle_Type'] == 'Doji'))
                }
            }
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing CSV data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get current market data for a symbol - Alpha Vantage primary, yfinance fallback"""
    try:
        import requests
        import random

        # Try Alpha Vantage FIRST (more reliable for quotes)
        api_key = os.environ.get("ALPHAVANTAGE_API_KEY", "demo")

        # Only try Alpha Vantage if we have a valid API key (not demo)
        if api_key and api_key != "demo":
            try:
                # Convert symbol for Alpha Vantage
                api_symbol = convert_symbol_for_source(symbol, "alphavantage")

                # Determine if it's forex
                is_forex = len(api_symbol) == 6 and symbol.endswith('=X')

                if is_forex:
                    # Forex endpoint - use FX_DAILY for historical data to calculate proper change
                    from_currency = api_symbol[:3]
                    to_currency = api_symbol[3:]
                    url = "https://www.alphavantage.co/query"
                    params = {
                        'function': 'FX_DAILY',
                        'from_symbol': from_currency,
                        'to_symbol': to_currency,
                        'apikey': api_key,
                        'outputsize': 'compact'  # Last 100 days
                    }

                    logger.info(f"Alpha Vantage Forex Quote: {from_currency}/{to_currency}")
                    response = requests.get(url, params=params, timeout=10)

                    if response.status_code == 200:
                        data = response.json()

                        # Check for API limit message
                        if 'Note' in data or 'Information' in data:
                            logger.warning(f"Alpha Vantage rate limit: {data.get('Note', data.get('Information'))}")
                        elif 'Time Series FX (Daily)' in data:
                            time_series = data['Time Series FX (Daily)']

                            # Get the two most recent trading days
                            dates = sorted(time_series.keys(), reverse=True)
                            if len(dates) >= 2:
                                latest_date = dates[0]
                                prev_date = dates[1]

                                current_price = float(time_series[latest_date]['4. close'])
                                prev_close = float(time_series[prev_date]['4. close'])

                                change = current_price - prev_close
                                change_percent = (change / prev_close * 100) if prev_close > 0 else 0

                                logger.info(f"✓ Alpha Vantage Forex success: {symbol} = {current_price} ({change_percent:+.2f}%)")
                                return {
                                    'symbol': symbol,
                                    'price': round(current_price, 5),
                                    'change': round(change, 5),
                                    'changePercent': round(change_percent, 2),
                                    'volume': 0,
                                    'source': 'Alpha Vantage'
                                }
                else:
                    # Stock/Index/Commodity endpoint
                    url = "https://www.alphavantage.co/query"
                    params = {
                        'function': 'GLOBAL_QUOTE',
                        'symbol': api_symbol,
                        'apikey': api_key
                    }

                    logger.info(f"Alpha Vantage Quote: {api_symbol}")
                    response = requests.get(url, params=params, timeout=10)

                    if response.status_code == 200:
                        data = response.json()

                        # Check for API limit message
                        if 'Note' in data or 'Information' in data:
                            logger.warning(f"Alpha Vantage rate limit: {data.get('Note', data.get('Information'))}")
                        elif 'Global Quote' in data and data['Global Quote']:
                            quote = data['Global Quote']
                            current_price = float(quote.get('05. price', 0))

                            if current_price > 0:
                                change_percent = float(quote.get('10. change percent', '0').replace('%', ''))
                                change = float(quote.get('09. change', 0))
                                volume = int(float(quote.get('06. volume', 0)))

                                logger.info(f"✓ Alpha Vantage success: {symbol} = {current_price}")
                                return {
                                    'symbol': symbol,
                                    'price': round(current_price, 2),
                                    'change': round(change, 2),
                                    'changePercent': round(change_percent, 2),
                                    'volume': volume,
                                    'source': 'Alpha Vantage'
                                }
            except Exception as e:
                logger.warning(f"Alpha Vantage failed for {symbol}: {e}")
        else:
            logger.info(f"No valid Alpha Vantage API key, skipping to fallback sources")

        # Fallback 1: Yahoo Finance v8 API (most reliable fallback)
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5)
            start_ts = int(start_date.timestamp())
            end_ts = int(end_date.timestamp())

            url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'period1': start_ts,
                'period2': end_ts,
                'interval': '1d',
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'application/json'
            }

            logger.info(f"Trying Yahoo v8 API for {symbol}")
            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                json_data = response.json()

                if 'chart' in json_data and 'result' in json_data['chart']:
                    result = json_data['chart']['result'][0]

                    if 'timestamp' in result and 'indicators' in result:
                        quote = result['indicators']['quote'][0]
                        closes = [c for c in quote.get('close', []) if c is not None]
                        volumes = [v for v in quote.get('volume', []) if v is not None]

                        if len(closes) >= 2:
                            current_price = float(closes[-1])
                            prev_price = float(closes[-2])
                            change = current_price - prev_price
                            change_percent = (change / prev_price) * 100

                            logger.info(f"✓ Yahoo v8 API success: {symbol} = {current_price}")
                            return {
                                'symbol': symbol,
                                'price': round(current_price, 5 if '=X' in symbol else 2),
                                'change': round(change, 5 if '=X' in symbol else 2),
                                'changePercent': round(change_percent, 2),
                                'volume': int(volumes[-1]) if volumes else 0,
                                'source': 'Yahoo Finance'
                            }
        except Exception as e:
            logger.warning(f"Yahoo v8 API failed for {symbol}: {e}")

        # Fallback 2: yfinance library
        try:
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            ]

            session = requests.Session()
            session.headers.update({
                'User-Agent': random.choice(user_agents),
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
            })

            logger.info(f"Trying yfinance library for {symbol}")
            ticker = yf.Ticker(symbol, session=session)
            hist = ticker.history(period="5d", timeout=10)

            if len(hist) >= 2:
                current_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[-2])
                change = current_price - prev_price
                change_percent = (change / prev_price) * 100

                logger.info(f"✓ yfinance success: {symbol} = {current_price}")
                return {
                    'symbol': symbol,
                    'price': round(current_price, 5 if '=X' in symbol else 2),
                    'change': round(change, 5 if '=X' in symbol else 2),
                    'changePercent': round(change_percent, 2),
                    'volume': int(hist['Volume'].iloc[-1]) if hist['Volume'].iloc[-1] > 0 else 0,
                    'source': 'yfinance'
                }
        except Exception as e:
            logger.warning(f"yfinance failed for {symbol}: {e}")

        # Fallback 3: Static mock data for demo purposes
        logger.warning(f"All data sources failed for {symbol}. Using mock data.")

        # Generate realistic mock data based on symbol type
        base_price = 100.0
        if '=X' in symbol:  # Forex
            base_price = 1.08 if 'EUR' in symbol else 1.25
        elif '=F' in symbol:  # Commodities
            base_price = 2000.0 if 'GC' in symbol else 80.0
        elif '^' in symbol:  # Indices
            base_price = 5000.0

        mock_change_percent = random.uniform(-2.0, 2.0)
        mock_price = base_price * (1 + mock_change_percent / 100)

        return {
            'symbol': symbol,
            'price': round(mock_price, 2),
            'change': round(mock_price * mock_change_percent / 100, 2),
            'changePercent': round(mock_change_percent, 2),
            'volume': 0,
            'source': 'Demo data',
            'note': 'Live feed temporarily unavailable'
        }

    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news")
async def get_financial_news():
    """Get latest financial news from NewsAPI"""
    try:
        import requests

        # ========================================
        # NEWS API KEY - Wird aus Environment Variable gelesen
        # ========================================
        NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")  # Liest aus Railway Environment Variable

        # Versuche echte News von NewsAPI zu laden
        if NEWS_API_KEY and NEWS_API_KEY != "":
            try:
                url = "https://newsapi.org/v2/top-headlines"
                params = {
                    "category": "business",
                    "language": "en",
                    "pageSize": 20,
                    "apiKey": NEWS_API_KEY
                }

                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    if data.get("status") == "ok":
                        logger.info(f"Loaded {len(data.get('articles', []))} articles from NewsAPI")
                        return {
                            "status": "success",
                            "totalResults": data.get("totalResults", 0),
                            "articles": data.get("articles", [])
                        }
                    else:
                        logger.warning(f"NewsAPI returned error: {data.get('message', 'Unknown error')}")
                else:
                    logger.warning(f"NewsAPI HTTP error: {response.status_code}")

            except Exception as e:
                logger.warning(f"Error fetching from NewsAPI: {str(e)}")

        # Fallback: Mock-Daten wenn API Key fehlt oder API fehlschlägt
        logger.info("Using mock news data")
        mock_articles = [
            {
                "source": {"name": "Financial Times"},
                "title": "Global Markets Rally on Strong Economic Data",
                "description": "Major stock indices surge as investors digest positive employment figures and corporate earnings.",
                "url": "#",
                "publishedAt": datetime.now().isoformat(),
            },
            {
                "source": {"name": "Bloomberg"},
                "title": "Fed Holds Interest Rates Steady",
                "description": "Federal Reserve maintains current interest rate policy, signaling cautious approach to inflation.",
                "url": "#",
                "publishedAt": (datetime.now() - timedelta(hours=2)).isoformat(),
            },
            {
                "source": {"name": "Reuters"},
                "title": "Tech Sector Leads Market Gains",
                "description": "Technology stocks outperform as AI investments drive growth expectations.",
                "url": "#",
                "publishedAt": (datetime.now() - timedelta(hours=4)).isoformat(),
            },
            {
                "source": {"name": "Wall Street Journal"},
                "title": "Oil Prices Fluctuate Amid Supply Concerns",
                "description": "Crude oil markets show volatility as geopolitical tensions affect supply chains.",
                "url": "#",
                "publishedAt": (datetime.now() - timedelta(hours=6)).isoformat(),
            },
            {
                "source": {"name": "CNBC"},
                "title": "Dollar Strengthens Against Major Currencies",
                "description": "US dollar gains ground in forex markets as economic indicators surprise to upside.",
                "url": "#",
                "publishedAt": (datetime.now() - timedelta(hours=8)).isoformat(),
            },
            {
                "source": {"name": "MarketWatch"},
                "title": "European Markets Close Higher",
                "description": "European stocks end trading session with gains across major indices.",
                "url": "#",
                "publishedAt": (datetime.now() - timedelta(hours=10)).isoformat(),
            },
            {
                "source": {"name": "Yahoo Finance"},
                "title": "Gold Reaches New Highs",
                "description": "Precious metals rally as investors seek safe-haven assets.",
                "url": "#",
                "publishedAt": (datetime.now() - timedelta(hours=12)).isoformat(),
            },
            {
                "source": {"name": "Barron's"},
                "title": "Earnings Season Kicks Off with Strong Results",
                "description": "Major corporations report better-than-expected quarterly earnings.",
                "url": "#",
                "publishedAt": (datetime.now() - timedelta(hours=14)).isoformat(),
            }
        ]

        return {
            "status": "success",
            "totalResults": len(mock_articles),
            "articles": mock_articles
        }

    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/economic/{country}")
async def get_economic_data(country: str):
    """Get economic indicators for a specific country"""
    try:
        import requests
        from datetime import datetime

        # Economic indicators mapping for different countries
        ECONOMIC_INDICATORS = {
            "USA": [
                {"name": "Interest Rate (Fed Funds)", "fred_id": "FEDFUNDS", "unit": "%"},
                {"name": "Inflation Rate (CPI YoY)", "fred_id": "CPIAUCSL", "unit": "%", "transform": "pc1"},
                {"name": "Unemployment Rate", "fred_id": "UNRATE", "unit": "%"},
                {"name": "GDP Growth Rate (QoQ)", "fred_id": "A191RL1Q225SBEA", "unit": "%"},
                {"name": "Manufacturing PMI", "fred_id": "MANEMP", "unit": "Index"},
                {"name": "Retail Sales (MoM)", "fred_id": "RSXFS", "unit": "%", "transform": "pc1"},
                {"name": "Consumer Confidence", "fred_id": "UMCSENT", "unit": "Index"},
            ],
            "EUR": [
                {"name": "ECB Interest Rate", "value": "4.00", "previous": "4.50", "change": -11.1, "lastUpdated": "2025-01"},
                {"name": "Inflation Rate (HICP)", "value": "2.4%", "previous": "2.7%", "change": -11.1, "lastUpdated": "2025-09"},
                {"name": "Unemployment Rate", "value": "6.4%", "previous": "6.5%", "change": -1.5, "lastUpdated": "2025-08"},
                {"name": "GDP Growth Rate", "value": "0.4%", "previous": "0.2%", "change": 100, "lastUpdated": "2025-Q3"},
                {"name": "Manufacturing PMI", "value": "46.1", "previous": "45.2", "change": 2.0, "lastUpdated": "2025-09"},
            ],
            "GBR": [
                {"name": "BoE Interest Rate", "value": "4.75%", "previous": "5.00%", "change": -5.0, "lastUpdated": "2025-02"},
                {"name": "Inflation Rate (CPI)", "value": "2.6%", "previous": "2.3%", "change": 13.0, "lastUpdated": "2025-09"},
                {"name": "Unemployment Rate", "value": "4.0%", "previous": "4.0%", "change": 0, "lastUpdated": "2025-08"},
                {"name": "GDP Growth Rate", "value": "0.1%", "previous": "0.5%", "change": -80.0, "lastUpdated": "2025-Q3"},
                {"name": "Manufacturing PMI", "value": "48.6", "previous": "51.5", "change": -5.6, "lastUpdated": "2025-09"},
            ],
            "JPN": [
                {"name": "BoJ Interest Rate", "value": "0.25%", "previous": "0.10%", "change": 150.0, "lastUpdated": "2025-07"},
                {"name": "Inflation Rate (Core CPI)", "value": "2.4%", "previous": "2.8%", "change": -14.3, "lastUpdated": "2025-09"},
                {"name": "Unemployment Rate", "value": "2.5%", "previous": "2.5%", "change": 0, "lastUpdated": "2025-08"},
                {"name": "GDP Growth Rate", "value": "0.7%", "previous": "0.5%", "change": 40.0, "lastUpdated": "2025-Q3"},
                {"name": "Manufacturing PMI", "value": "49.0", "previous": "49.8", "change": -1.6, "lastUpdated": "2025-09"},
            ],
            "CAN": [
                {"name": "BoC Interest Rate", "value": "3.25%", "previous": "3.75%", "change": -13.3, "lastUpdated": "2025-03"},
                {"name": "Inflation Rate (CPI)", "value": "1.6%", "previous": "2.0%", "change": -20.0, "lastUpdated": "2025-09"},
                {"name": "Unemployment Rate", "value": "6.6%", "previous": "6.5%", "change": 1.5, "lastUpdated": "2025-09"},
                {"name": "GDP Growth Rate", "value": "0.0%", "previous": "0.2%", "change": -100.0, "lastUpdated": "2025-Q3"},
                {"name": "Manufacturing PMI", "value": "51.1", "previous": "49.5", "change": 3.2, "lastUpdated": "2025-09"},
            ],
            "AUS": [
                {"name": "RBA Interest Rate", "value": "4.35%", "previous": "4.35%", "change": 0, "lastUpdated": "2025-09"},
                {"name": "Inflation Rate (CPI)", "value": "2.8%", "previous": "3.8%", "change": -26.3, "lastUpdated": "2025-Q3"},
                {"name": "Unemployment Rate", "value": "4.1%", "previous": "4.1%", "change": 0, "lastUpdated": "2025-09"},
                {"name": "GDP Growth Rate", "value": "1.0%", "previous": "1.1%", "change": -9.1, "lastUpdated": "2025-Q2"},
                {"name": "Manufacturing PMI", "value": "47.3", "previous": "48.7", "change": -2.9, "lastUpdated": "2025-09"},
            ],
            "NZL": [
                {"name": "RBNZ Interest Rate", "value": "4.25%", "previous": "4.75%", "change": -10.5, "lastUpdated": "2025-02"},
                {"name": "Inflation Rate (CPI)", "value": "2.2%", "previous": "3.3%", "change": -33.3, "lastUpdated": "2025-Q3"},
                {"name": "Unemployment Rate", "value": "4.8%", "previous": "4.6%", "change": 4.3, "lastUpdated": "2025-Q3"},
                {"name": "GDP Growth Rate", "value": "-0.2%", "previous": "0.2%", "change": -200.0, "lastUpdated": "2025-Q2"},
                {"name": "Manufacturing PMI", "value": "46.9", "previous": "44.9", "change": 4.5, "lastUpdated": "2025-09"},
            ],
            "CHE": [
                {"name": "SNB Interest Rate", "value": "1.00%", "previous": "1.25%", "change": -20.0, "lastUpdated": "2025-03"},
                {"name": "Inflation Rate (CPI)", "value": "0.8%", "previous": "1.1%", "change": -27.3, "lastUpdated": "2025-09"},
                {"name": "Unemployment Rate", "value": "2.6%", "previous": "2.5%", "change": 4.0, "lastUpdated": "2025-09"},
                {"name": "GDP Growth Rate", "value": "0.7%", "previous": "0.5%", "change": 40.0, "lastUpdated": "2025-Q2"},
                {"name": "Manufacturing PMI", "value": "50.8", "previous": "47.4", "change": 7.2, "lastUpdated": "2025-09"},
            ],
            "CHN": [
                {"name": "PBoC Interest Rate (1Y LPR)", "value": "3.10%", "previous": "3.45%", "change": -10.1, "lastUpdated": "2025-02"},
                {"name": "Inflation Rate (CPI)", "value": "0.4%", "previous": "0.6%", "change": -33.3, "lastUpdated": "2025-09"},
                {"name": "Unemployment Rate", "value": "5.1%", "previous": "5.2%", "change": -1.9, "lastUpdated": "2025-08"},
                {"name": "GDP Growth Rate", "value": "4.6%", "previous": "4.7%", "change": -2.1, "lastUpdated": "2025-Q3"},
                {"name": "Manufacturing PMI", "value": "49.8", "previous": "49.1", "change": 1.4, "lastUpdated": "2025-09"},
            ],
            "DEU": [
                {"name": "ECB Interest Rate", "value": "4.00%", "previous": "4.50%", "change": -11.1, "lastUpdated": "2025-01"},
                {"name": "Inflation Rate (CPI)", "value": "2.0%", "previous": "1.7%", "change": 17.6, "lastUpdated": "2025-09"},
                {"name": "Unemployment Rate", "value": "6.1%", "previous": "6.0%", "change": 1.7, "lastUpdated": "2025-09"},
                {"name": "GDP Growth Rate", "value": "-0.1%", "previous": "0.1%", "change": -200.0, "lastUpdated": "2025-Q3"},
                {"name": "Manufacturing PMI", "value": "42.6", "previous": "42.4", "change": 0.5, "lastUpdated": "2025-09"},
            ],
        }

        if country not in ECONOMIC_INDICATORS:
            raise HTTPException(status_code=404, detail=f"Country {country} not found")

        indicators_config = ECONOMIC_INDICATORS[country]
        result_indicators = []

        # For USA, try to fetch from FRED API (if available)
        if country == "USA":
            fred_api_key = os.environ.get("FRED_API_KEY", "")

            if fred_api_key:
                logger.info("Fetching real-time data from FRED API")
                for indicator in indicators_config:
                    try:
                        fred_id = indicator.get("fred_id")
                        url = f"https://api.stlouisfed.org/fred/series/observations"
                        params = {
                            "series_id": fred_id,
                            "api_key": fred_api_key,
                            "file_type": "json",
                            "limit": 2,
                            "sort_order": "desc"
                        }

                        response = requests.get(url, params=params, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            observations = data.get("observations", [])

                            if len(observations) >= 2:
                                current_val = float(observations[0]["value"])
                                previous_val = float(observations[1]["value"])
                                change_pct = ((current_val - previous_val) / previous_val * 100) if previous_val != 0 else 0

                                result_indicators.append({
                                    "name": indicator["name"],
                                    "current": f"{current_val:.2f}{indicator.get('unit', '')}",
                                    "previous": f"{previous_val:.2f}{indicator.get('unit', '')}",
                                    "change": change_pct,
                                    "lastUpdated": observations[0]["date"]
                                })
                            else:
                                logger.warning(f"Not enough data for {indicator['name']}")
                    except Exception as e:
                        logger.error(f"Error fetching {indicator.get('name')}: {e}")
                        continue

                if result_indicators:
                    return {
                        "country": country,
                        "indicators": result_indicators,
                        "timestamp": datetime.now().isoformat(),
                        "source": "FRED API"
                    }

        # Fallback to static data (for all countries or if FRED fails)
        for indicator in indicators_config:
            if "value" in indicator:
                result_indicators.append({
                    "name": indicator["name"],
                    "current": indicator["value"],
                    "previous": indicator.get("previous", "N/A"),
                    "change": indicator.get("change", 0),
                    "lastUpdated": indicator.get("lastUpdated", "N/A")
                })

        return {
            "country": country,
            "indicators": result_indicators,
            "timestamp": datetime.now().isoformat(),
            "source": "Static Data (Update: Consider FRED API key for live USA data)"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching economic data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cot-data")
async def get_cot_data():
    """Get COT (Commitment of Traders) data for institutional positioning - V1.1.2"""
    try:
        import requests

        # Get optional NASDAQ API key from environment
        nasdaq_api_key = os.environ.get("NASDAQ_API_KEY", "")

        # NASDAQ/Quandl CFTC codes for major instruments
        # Format: CFTC/CODE_FO_ALL (Futures Only, All data)
        nasdaq_instruments = {
            'EURUSD': {'code': '099741', 'name': 'EUR'},
            'GBPUSD': {'code': '096742', 'name': 'GBP'},
            'USDJPY': {'code': '097741', 'name': 'JPY'},
            'AUDUSD': {'code': '232741', 'name': 'AUD'},
            'USDCAD': {'code': '090741', 'name': 'CAD'},
            'USDCHF': {'code': '092741', 'name': 'CHF'},
            'GOLD': {'code': '088691', 'name': 'Gold'},
            'SILVER': {'code': '084691', 'name': 'Silver'},
            'CRUDE_OIL': {'code': '067651', 'name': 'Oil'},
            'SP500': {'code': '13874A', 'name': 'SPX'},
            'NASDAQ': {'code': '209742', 'name': 'NASDAQ'},
            'DOW': {'code': '124603', 'name': 'DOW'},
            'NIKKEI': {'code': '240741', 'name': 'NIKKEI'},
            'USD_INDEX': {'code': '098662', 'name': 'USD'}
        }

        cot_results = []

        # Try CFTC Direct API first (most reliable and free)
        logger.info("Fetching COT data from CFTC direct API...")

        try:
            # CFTC Disaggregated Futures API
            base_url = "https://publicreporting.cftc.gov/resource/jun7-fc8e.json"

            params = {
                '$limit': 500,
                '$order': 'report_date_as_yyyy_mm_dd DESC'
            }

            response = requests.get(base_url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()

                # Map CFTC market names to display names (exact match patterns)
                cftc_map = {
                    'EURO FX': 'EUR',
                    'BRITISH POUND': 'GBP',
                    'JAPANESE YEN': 'JPY',
                    'SWISS FRANC': 'CHF',
                    'CANADIAN DOLLAR': 'CAD',
                    'AUSTRALIAN DOLLAR': 'AUD',
                    'GOLD': 'Gold',
                    'SILVER': 'Silver',
                    'CRUDE OIL': 'Oil',
                    'E-MINI S&P 500 - CHICAGO MERCANTILE': 'SPX',  # Precise match for S&P 500
                    'NASDAQ': 'NASDAQ',
                    'DOW': 'DOW',
                    'USD INDEX': 'USD'
                }

                for cftc_pattern, display_name in cftc_map.items():
                    matching = [r for r in data if cftc_pattern in r.get('market_and_exchange_names', '').upper()]

                    if len(matching) >= 2:
                        latest = matching[0]
                        previous = matching[1]

                        nc_long_latest = float(latest.get('noncomm_positions_long_all', 0))
                        nc_short_latest = float(latest.get('noncomm_positions_short_all', 0))
                        nc_long_prev = float(previous.get('noncomm_positions_long_all', 0))
                        nc_short_prev = float(previous.get('noncomm_positions_short_all', 0))

                        net_latest = nc_long_latest - nc_short_latest
                        net_previous = nc_long_prev - nc_short_prev
                        net_change = net_latest - net_previous

                        open_interest = float(latest.get('open_interest_all', 1))

                        cot_results.append({
                            'instrument': display_name,
                            'report_date': latest.get('report_date_as_yyyy_mm_dd', ''),
                            'non_commercial': {
                                'long': int(nc_long_latest),
                                'short': int(nc_short_latest),
                                'net': int(net_latest),
                                'net_percent_of_oi': round((net_latest / open_interest * 100) if open_interest > 0 else 0, 2)
                            },
                            'change_from_previous': {
                                'net': int(net_change),
                                'net_percent_change': round((net_change / abs(net_previous) * 100) if net_previous != 0 else 0, 2)
                            },
                            'open_interest': int(open_interest)
                        })

                if cot_results:
                    logger.info(f"✓ COT data fetched from CFTC: {len(cot_results)} instruments")

        except Exception as e:
            logger.error(f"CFTC API error: {e}")

        # Try NASDAQ Data Link API as alternative (if CFTC failed and API key available)
        if not cot_results and nasdaq_api_key:
            logger.info("Fetching COT data from NASDAQ Data Link API...")

            try:
                for instrument_key, info in nasdaq_instruments.items():
                    try:
                        # NASDAQ Data Link API endpoint
                        url = f"https://data.nasdaq.com/api/v3/datasets/CFTC/{info['code']}_FO_ALL.json"
                        params = {
                            'api_key': nasdaq_api_key,
                            'limit': 2,  # Get latest 2 weeks for comparison
                            'order': 'desc'
                        }

                        response = requests.get(url, params=params, timeout=10)

                        if response.status_code == 200:
                            data = response.json()
                            dataset = data.get('dataset', {})
                            dataset_data = dataset.get('data', [])

                            if len(dataset_data) >= 2:
                                latest = dataset_data[0]
                                previous = dataset_data[1]

                                # Column indices (NASDAQ format)
                                # [0]=Date, [1]=Open Interest, [2]=Dealer Long, [3]=Dealer Short,
                                # [4]=Asset Manager Long, [5]=Asset Manager Short,
                                # [6]=Leveraged Long, [7]=Leveraged Short, etc.

                                # Non-Commercial = Leveraged Funds (speculative positions)
                                nc_long_latest = float(latest[6] if len(latest) > 6 else 0)
                                nc_short_latest = float(latest[7] if len(latest) > 7 else 0)
                                nc_long_prev = float(previous[6] if len(previous) > 6 else 0)
                                nc_short_prev = float(previous[7] if len(previous) > 7 else 0)

                                open_interest = float(latest[1] if len(latest) > 1 else 1)

                                # Calculate net positioning
                                net_latest = nc_long_latest - nc_short_latest
                                net_previous = nc_long_prev - nc_short_prev
                                net_change = net_latest - net_previous

                                cot_results.append({
                                    'instrument': info['name'],
                                    'report_date': latest[0],
                                    'non_commercial': {
                                        'long': int(nc_long_latest),
                                        'short': int(nc_short_latest),
                                        'net': int(net_latest),
                                        'net_percent_of_oi': round((net_latest / open_interest * 100) if open_interest > 0 else 0, 2)
                                    },
                                    'change_from_previous': {
                                        'net': int(net_change),
                                        'net_percent_change': round((net_change / abs(net_previous) * 100) if net_previous != 0 else 0, 2)
                                    },
                                    'open_interest': int(open_interest)
                                })

                    except Exception as e:
                        logger.warning(f"Failed to fetch {info['name']} from NASDAQ: {e}")
                        continue

                if cot_results:
                    logger.info(f"✓ COT data fetched from NASDAQ: {len(cot_results)} instruments")

            except Exception as e:
                logger.error(f"NASDAQ API error: {e}")


        # Transform to frontend format
        if cot_results:
            assets = []
            for item in cot_results:
                nc = item['non_commercial']
                change = item['change_from_previous']

                total_positions = nc['long'] + nc['short']
                long_pct = (nc['long'] / total_positions * 100) if total_positions > 0 else 0
                short_pct = (nc['short'] / total_positions * 100) if total_positions > 0 else 0

                assets.append({
                    'name': item['instrument'],
                    'longContracts': nc['long'],
                    'shortContracts': nc['short'],
                    'deltaLong': change['net'] if change['net'] > 0 else 0,
                    'deltaShort': abs(change['net']) if change['net'] < 0 else 0,
                    'longPct': round(long_pct, 2),
                    'shortPct': round(short_pct, 2),
                    'netChange': change['net_percent_change'],
                    'netPosition': nc['net'],
                    'openInterest': int(item.get('open_interest', total_positions) / 1000),
                    'deltaOI': change['net']
                })

            return {
                'status': 'success',
                'source': 'CFTC',
                'last_update': cot_results[0]['report_date'] if cot_results else datetime.now().isoformat(),
                'assets': assets
            }

        # Final fallback: Demo data
        logger.warning("Using demo COT data (APIs unavailable)")
        return {
            'status': 'demo',
            'source': 'demo',
            'last_update': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'message': 'Add NASDAQ_API_KEY environment variable for real-time data (free at data.nasdaq.com)',
            'assets': [
                { 'name': 'EUR', 'longContracts': 125000, 'shortContracts': 95000, 'deltaLong': 5000, 'deltaShort': 0, 'longPct': 56.82, 'shortPct': 43.18, 'netChange': 20.0, 'netPosition': 30000, 'openInterest': 220000, 'deltaOI': 5000 },
                { 'name': 'Gold', 'longContracts': 250000, 'shortContracts': 150000, 'deltaLong': 15000, 'deltaShort': 0, 'longPct': 62.5, 'shortPct': 37.5, 'netChange': 17.6, 'netPosition': 100000, 'openInterest': 400000, 'deltaOI': 15000 },
                { 'name': 'JPY', 'longContracts': 176400, 'shortContracts': 96900, 'deltaLong': 14727, 'deltaShort': 0, 'longPct': 64.54, 'shortPct': 35.46, 'netChange': 2.82, 'netPosition': 79500, 'openInterest': 273300, 'deltaOI': 10273 },
                { 'name': 'SPX', 'longContracts': 229106, 'shortContracts': 401946, 'deltaLong': 0, 'deltaShort': 33685, 'longPct': 36.31, 'shortPct': 63.69, 'netChange': 3.07, 'netPosition': -172840, 'openInterest': 631052, 'deltaOI': -33685 }
            ]
        }

    except Exception as e:
        logger.error(f"Error in COT data endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"COT data fetch failed: {str(e)}")

@app.get("/api/risk-radar")
async def get_risk_radar():
    """Get Risk Radar market stress analysis"""
    try:
        from fredapi import Fred
        import warnings
        warnings.filterwarnings('ignore')

        # FRED API Key - aus Environment Variable oder Standard
        FRED_API_KEY = os.environ.get("FRED_API_KEY", "a650cab7da43489ec04d1073446a338f")
        fred = Fred(api_key=FRED_API_KEY)

        # Daten laden (letzte 3 Jahre für Z-Score Berechnung)
        start_date = (datetime.now() - timedelta(days=3*365)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Loading Risk Radar data from {start_date} to {end_date}")

        # Basis-Indikatoren laden
        series_config = {
            'BAMLH0A0HYM2': 'HY_OAS',      # High Yield Option-Adjusted Spread
            'BAMLC0A0CM': 'IG_OAS',        # Investment Grade Corporate OAS
            'STLFSI4': 'STLFSI',           # St. Louis Fed Financial Stress Index
            'VIXCLS': 'VIX'                # VIX Volatility Index
        }

        data_series = {}
        for fred_code, name in series_config.items():
            try:
                series = fred.get_series(fred_code, observation_start=start_date, observation_end=end_date)
                if series is not None and len(series) > 0:
                    data_series[name] = series
                    logger.info(f"Loaded {name}: {len(series)} data points")
            except Exception as e:
                logger.warning(f"Could not load {name}: {e}")

        if not data_series:
            raise ValueError("Could not load any FRED data series")

        # DataFrame erstellen
        df = pd.concat(data_series.values(), axis=1, keys=data_series.keys()).sort_index()
        df = df.asfreq("B").ffill()

        # Z-Scores berechnen (252 Tage Lookback)
        lookback = 252

        def rolling_z(x, lb=lookback):
            rolling_mean = x.rolling(window=lb, min_periods=int(lb*0.8)).mean()
            rolling_std = x.rolling(window=lb, min_periods=int(lb*0.8)).std()
            z_score = (x - rolling_mean) / rolling_std
            return z_score

        for col in df.columns:
            df[f"{col}_Z"] = rolling_z(df[col])
            df[f"{col}_Z"] = df[f"{col}_Z"].clip(-3, 3)

        # Daten bereinigen
        z_cols = [col for col in df.columns if col.endswith('_Z')]
        df = df.dropna(subset=z_cols, thresh=3)

        if df.empty:
            raise ValueError("Not enough data after Z-score calculation")

        # Composite Score berechnen
        base_weights = {
            "HY_OAS_Z": 0.30,
            "IG_OAS_Z": 0.20,
            "STLFSI_Z": 0.25,
            "VIX_Z": 0.25
        }

        def calculate_composite_flexible(row):
            available_scores = {}
            for col, weight in base_weights.items():
                if col in row.index and pd.notna(row[col]):
                    available_scores[col] = (row[col], weight)

            if not available_scores:
                return np.nan

            total_weight = sum(weight for _, weight in available_scores.values())
            normalized_composite = sum(score * (weight/total_weight)
                                     for score, weight in available_scores.values())
            return normalized_composite

        df["Composite_Z"] = df.apply(calculate_composite_flexible, axis=1)
        df = df.dropna(subset=["Composite_Z"])

        # Regime klassifizieren
        def classify_regime(row):
            cs = row["Composite_Z"]
            flags = 0
            available_indicators = 0

            for col in base_weights.keys():
                if col in row.index and pd.notna(row[col]):
                    available_indicators += 1
                    threshold = 1.0 if 'STLFSI_Z' in col else 1.5
                    if row[col] >= threshold:
                        flags += 1

            flag_ratio = flags / max(available_indicators, 1)

            if cs >= 2.5:
                return "ALERT"
            elif cs >= 2.0 and flag_ratio >= 0.75:
                return "ALERT"
            elif cs >= 1.75:
                return "WARNING"
            elif flag_ratio >= 0.75 and cs >= 1.25:
                return "WARNING"
            elif cs >= 1.0:
                return "WATCH"
            elif flag_ratio >= 0.6 and cs >= 0.5:
                return "WATCH"
            else:
                return "CALM"

        df["Regime"] = df.apply(classify_regime, axis=1)
        df["Regime_shift"] = df["Regime"].ne(df["Regime"].shift(1))

        # Aktueller Zustand
        latest = df.iloc[-1]
        latest_date = latest.name

        # Einzelkomponenten
        components = {}
        for col in base_weights.keys():
            if col in df.columns:
                last_valid_idx = df[col].last_valid_index()
                if last_valid_idx:
                    components[col.replace('_Z', '')] = {
                        'value': float(df[col][last_valid_idx]),
                        'date': last_valid_idx.strftime('%Y-%m-%d')
                    }

        # Letzte Alerts
        alerts = df[df["Regime_shift"] & df["Regime"].isin(["WATCH", "WARNING", "ALERT"])]
        alert_list = []
        for idx in alerts.tail(10).index:
            alert_list.append({
                'date': idx.strftime('%Y-%m-%d'),
                'composite_z': float(df.loc[idx, 'Composite_Z']),
                'regime': df.loc[idx, 'Regime']
            })

        # Historische Daten für Chart (letzte 6 Monate)
        recent_df = df.tail(130)
        historical_data = []
        for idx in recent_df.index:
            historical_data.append({
                'date': idx.strftime('%Y-%m-%d'),
                'composite_z': float(recent_df.loc[idx, 'Composite_Z']) if pd.notna(recent_df.loc[idx, 'Composite_Z']) else None,
                'regime': recent_df.loc[idx, 'Regime']
            })

        # Regime-Statistiken (letzte 12 Monate)
        recent_stats = df.tail(252)
        regime_counts = recent_stats["Regime"].value_counts()
        total_days = len(recent_stats)

        regime_distribution = {
            'CALM': int(regime_counts.get('CALM', 0)),
            'WATCH': int(regime_counts.get('WATCH', 0)),
            'WARNING': int(regime_counts.get('WARNING', 0)),
            'ALERT': int(regime_counts.get('ALERT', 0))
        }

        response = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'current_state': {
                'date': latest_date.strftime('%Y-%m-%d'),
                'composite_z': float(latest['Composite_Z']),
                'regime': latest['Regime'],
                'components': components
            },
            'alerts': alert_list,
            'historical_data': historical_data,
            'statistics': {
                'regime_distribution': regime_distribution,
                'total_days': total_days,
                'composite_stats': {
                    'mean': float(recent_stats['Composite_Z'].mean()),
                    'std': float(recent_stats['Composite_Z'].std()),
                    'max': float(recent_stats['Composite_Z'].max()),
                    'min': float(recent_stats['Composite_Z'].min())
                }
            },
            'thresholds': {
                'CALM': '< 1.0',
                'WATCH': '>= 1.0',
                'WARNING': '>= 1.75',
                'ALERT': '>= 2.5'
            }
        }

        logger.info(f"Risk Radar analysis complete: {latest['Regime']} regime")
        return response

    except ImportError:
        logger.error("fredapi not installed. Run: pip install fredapi")
        raise HTTPException(
            status_code=500,
            detail="Risk Radar requires 'fredapi' package. Contact administrator."
        )
    except Exception as e:
        logger.error(f"Error in Risk Radar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Risk Radar analysis failed: {str(e)}")

# ===== SENTIMENT ENDPOINTS =====

@app.get("/api/sentiment")
async def get_sentiment_data():
    """
    Get Risk On/Risk Off sentiment data for multiple timeframes
    Returns calculated sentiment scores based on various market indicators
    """
    try:
        # Fetch market data for sentiment indicators
        vix_data = None
        spx_data = None
        gold_data = None
        dxy_data = None

        try:
            # Fetch VIX (Volatility Index)
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="1mo")
            if not vix_hist.empty:
                vix_current = vix_hist['Close'].iloc[-1]
                vix_daily_change = ((vix_hist['Close'].iloc[-1] / vix_hist['Close'].iloc[-2]) - 1) * 100 if len(vix_hist) > 1 else 0
                vix_weekly_avg = vix_hist['Close'].tail(5).mean() if len(vix_hist) >= 5 else vix_current
                vix_monthly_avg = vix_hist['Close'].mean()
                vix_data = {
                    'current': vix_current,
                    'daily': vix_current,
                    'weekly': vix_weekly_avg,
                    'monthly': vix_monthly_avg,
                    'change': vix_daily_change
                }
        except Exception as e:
            logger.warning(f"Failed to fetch VIX data: {e}")

        try:
            # Fetch S&P 500
            spx = yf.Ticker("^GSPC")
            spx_hist = spx.history(period="1mo")
            if not spx_hist.empty:
                spx_daily = ((spx_hist['Close'].iloc[-1] / spx_hist['Close'].iloc[-2]) - 1) * 100 if len(spx_hist) > 1 else 0
                spx_weekly = ((spx_hist['Close'].iloc[-1] / spx_hist['Close'].iloc[-5]) - 1) * 100 if len(spx_hist) >= 5 else spx_daily
                spx_monthly = ((spx_hist['Close'].iloc[-1] / spx_hist['Close'].iloc[0]) - 1) * 100 if len(spx_hist) > 0 else spx_daily
                spx_data = {
                    'daily': spx_daily,
                    'weekly': spx_weekly,
                    'monthly': spx_monthly,
                    'current': spx_hist['Close'].iloc[-1]
                }
        except Exception as e:
            logger.warning(f"Failed to fetch SPX data: {e}")

        try:
            # Fetch Gold (GC=F)
            gold = yf.Ticker("GC=F")
            gold_hist = gold.history(period="1mo")

            if not gold_hist.empty and spx_data:
                gold_price = gold_hist['Close'].iloc[-1]
                gold_spx_ratio = gold_price / spx_data['current']
                gold_data = {
                    'price': gold_price,
                    'gold_spx_ratio': gold_spx_ratio
                }
        except Exception as e:
            logger.warning(f"Failed to fetch Gold data: {e}")

        try:
            # Fetch DXY (US Dollar Index) - using UUP ETF as proxy
            dxy = yf.Ticker("UUP")
            dxy_hist = dxy.history(period="1mo")
            if not dxy_hist.empty:
                # Convert UUP price to approximate DXY value
                dxy_current = dxy_hist['Close'].iloc[-1] * 4  # Rough conversion
                dxy_data = {
                    'current': dxy_current
                }
        except Exception as e:
            logger.warning(f"Failed to fetch DXY data: {e}")

        # Calculate sentiment scores
        def calculate_score(vix_val, spx_perf, gold_spx, dxy_val, hy_spreads=3.2, crypto_sent=65):
            score = 0
            count = 0

            # VIX: Lower = Risk On
            if vix_val is not None:
                vix_score = max(-100, min(100, (20 - vix_val) * 5))
                score += vix_score
                count += 1

            # SPX: Positive = Risk On
            if spx_perf is not None:
                score += max(-100, min(100, spx_perf * 10))
                count += 1

            # Gold/SPX: Lower = Risk On
            if gold_spx is not None:
                score += max(-100, min(100, -gold_spx * 50))
                count += 1

            # DXY: Lower = Risk On
            if dxy_val is not None:
                score += max(-100, min(100, (100 - dxy_val) * 2))
                count += 1

            # HY Spreads: Lower = Risk On
            score += max(-100, min(100, (5 - hy_spreads) * 20))
            count += 1

            # Crypto Sentiment
            score += (crypto_sent - 50) * 2
            count += 1

            return score / count if count > 0 else 0

        # Calculate scores for each timeframe
        daily_score = calculate_score(
            vix_data['daily'] if vix_data else None,
            spx_data['daily'] if spx_data else None,
            gold_data['gold_spx_ratio'] if gold_data else None,
            dxy_data['current'] if dxy_data else None,
            3.2,  # Mock HY Spreads
            65    # Mock Crypto Sentiment
        )

        weekly_score = calculate_score(
            vix_data['weekly'] if vix_data else None,
            spx_data['weekly'] if spx_data else None,
            gold_data['gold_spx_ratio'] if gold_data else None,
            dxy_data['current'] if dxy_data else None,
            3.1,
            68
        )

        monthly_score = calculate_score(
            vix_data['monthly'] if vix_data else None,
            spx_data['monthly'] if spx_data else None,
            gold_data['gold_spx_ratio'] if gold_data else None,
            dxy_data['current'] if dxy_data else None,
            2.9,
            72
        )

        return {
            "daily": {
                "vix": round(vix_data['daily'], 2) if vix_data else None,
                "spx": round(spx_data['daily'], 2) if spx_data else None,
                "goldSpx": round(gold_data['gold_spx_ratio'], 3) if gold_data else None,
                "dxy": round(dxy_data['current'], 1) if dxy_data else None,
                "hySpreads": 3.2,
                "cryptoSentiment": 65,
                "score": round(daily_score, 1)
            },
            "weekly": {
                "vix": round(vix_data['weekly'], 2) if vix_data else None,
                "spx": round(spx_data['weekly'], 2) if spx_data else None,
                "goldSpx": round(gold_data['gold_spx_ratio'], 3) if gold_data else None,
                "dxy": round(dxy_data['current'], 1) if dxy_data else None,
                "hySpreads": 3.1,
                "cryptoSentiment": 68,
                "score": round(weekly_score, 1)
            },
            "monthly": {
                "vix": round(vix_data['monthly'], 2) if vix_data else None,
                "spx": round(spx_data['monthly'], 2) if spx_data else None,
                "goldSpx": round(gold_data['gold_spx_ratio'], 3) if gold_data else None,
                "dxy": round(dxy_data['current'], 1) if dxy_data else None,
                "hySpreads": 2.9,
                "cryptoSentiment": 72,
                "score": round(monthly_score, 1)
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching sentiment data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sentiment data: {str(e)}")

# ===== SEASONALITY ENDPOINTS =====

@app.get("/api/seasonality/assets")
async def get_seasonality_assets():
    """
    Get available assets for seasonality analysis grouped by category
    """
    assets = {
        "crypto": [
            {"symbol": "BTC-USD", "name": "Bitcoin"},
            {"symbol": "ETH-USD", "name": "Ethereum"},
            {"symbol": "BNB-USD", "name": "Binance Coin"},
            {"symbol": "XRP-USD", "name": "Ripple"},
            {"symbol": "ADA-USD", "name": "Cardano"},
            {"symbol": "SOL-USD", "name": "Solana"},
            {"symbol": "DOGE-USD", "name": "Dogecoin"},
            {"symbol": "MATIC-USD", "name": "Polygon"},
            {"symbol": "DOT-USD", "name": "Polkadot"}
        ],
        "stocks": [
            {"symbol": "AAPL", "name": "Apple"},
            {"symbol": "MSFT", "name": "Microsoft"},
            {"symbol": "GOOGL", "name": "Google"},
            {"symbol": "AMZN", "name": "Amazon"},
            {"symbol": "TSLA", "name": "Tesla"},
            {"symbol": "NVDA", "name": "NVIDIA"},
            {"symbol": "META", "name": "Meta"},
            {"symbol": "NFLX", "name": "Netflix"},
            {"symbol": "AMD", "name": "AMD"},
            {"symbol": "INTC", "name": "Intel"},
            {"symbol": "JPM", "name": "JP Morgan"},
            {"symbol": "BAC", "name": "Bank of America"},
            {"symbol": "V", "name": "Visa"},
            {"symbol": "MA", "name": "Mastercard"},
            {"symbol": "DIS", "name": "Disney"},
            {"symbol": "PYPL", "name": "PayPal"}
        ],
        "commodities": [
            {"symbol": "GC=F", "name": "Gold Futures"},
            {"symbol": "SI=F", "name": "Silver Futures"},
            {"symbol": "CL=F", "name": "Crude Oil Futures"},
            {"symbol": "NG=F", "name": "Natural Gas Futures"},
            {"symbol": "HG=F", "name": "Copper Futures"},
            {"symbol": "PL=F", "name": "Platinum Futures"},
            {"symbol": "GLD", "name": "Gold ETF (GLD)"},
            {"symbol": "SLV", "name": "Silver ETF (SLV)"},
            {"symbol": "USO", "name": "Oil ETF (USO)"}
        ],
        "indices": [
            {"symbol": "SPY", "name": "S&P 500 ETF (SPY)"},
            {"symbol": "QQQ", "name": "NASDAQ ETF (QQQ)"},
            {"symbol": "DIA", "name": "Dow Jones ETF (DIA)"},
            {"symbol": "IWM", "name": "Russell 2000 ETF (IWM)"},
            {"symbol": "EFA", "name": "MSCI EAFE ETF"},
            {"symbol": "EEM", "name": "Emerging Markets ETF"},
            {"symbol": "VTI", "name": "Total Stock Market ETF"}
        ],
        "forex": [
            {"symbol": "EURUSD=X", "name": "EUR/USD (May have limited data)"},
            {"symbol": "GBPUSD=X", "name": "GBP/USD (May have limited data)"},
            {"symbol": "FXE", "name": "Euro ETF (FXE)"},
            {"symbol": "FXB", "name": "British Pound ETF (FXB)"},
            {"symbol": "FXY", "name": "Japanese Yen ETF (FXY)"},
            {"symbol": "UUP", "name": "US Dollar ETF (UUP)"}
        ]
    }
    return assets

@app.get("/api/seasonality/{symbol}")
async def get_seasonality(symbol: str):
    """
    Calculate seasonality data for a given symbol using local CSV data
    Returns monthly average returns, quarterly performance, and historical heatmap
    """
    try:
        # CSV mapping for available assets
        csv_mapping = {
            'EURUSD': 'EURUSD/EURUSD_D1',
            'GBPUSD': 'GBPUSD/GBPUSD_D1',
            'USDJPY': 'USDJPY/USDJPY_D1',
            'USDCHF': 'USDCHF/USDCHF_D1',
            'USDCAD': 'USDCAD/USDCAD_D1',
            'XAUUSD': 'XAUUSD/XAUUSD_D1',
            'BTCUSD': 'BTCUSD/BTCUSD_D1',
            'US500': 'US500/USA500IDXUSD_D1',
        }

        dataset_id = csv_mapping.get(symbol)
        if not dataset_id:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")

        # Use same path as hosted datasets API
        data_root = os.environ.get("DATA_ROOT_PATH", "data/datasets")
        full_path = os.path.join(data_root, f"{dataset_id}.csv")

        logger.info(f"Loading seasonality data from: {full_path}")

        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"CSV file not found for {symbol}: {full_path}")

        # Load CSV (same logic as analyze/hosted)
        try:
            hist = pd.read_csv(full_path, sep='\t', header=0, index_col=False)
        except:
            hist = pd.read_csv(full_path)

        logger.info(f"CSV columns for {symbol}: {list(hist.columns)}, rows: {len(hist)}")

        # Find time column
        time_col = None
        for col in ['Time', 'time', 'Date', 'date', 'timestamp', 'Timestamp']:
            if col in hist.columns:
                time_col = col
                break

        if time_col is None:
            raise HTTPException(status_code=500, detail=f"No time column found. Columns: {list(hist.columns)}")

        # Parse and set index
        hist[time_col] = pd.to_datetime(hist[time_col])
        hist.set_index(time_col, inplace=True)
        hist.sort_index(inplace=True)

        # Ensure OHLC columns exist (they should already be capitalized)
        required_cols = ['Open', 'High', 'Low', 'Close']
        for col in required_cols:
            if col not in hist.columns:
                raise HTTPException(status_code=500, detail=f"Missing column: {col}. Available: {list(hist.columns)}")

        # Convert to numeric
        for col in required_cols:
            hist[col] = pd.to_numeric(hist[col], errors='coerce')

        # Remove NaN
        hist = hist.dropna(subset=required_cols)

        data_source = "Local CSV Data"

        logger.info(f"Loaded {len(hist)} rows for {symbol}, date range: {hist.index.min()} to {hist.index.max()}")

        if hist is None or hist.empty:
            raise HTTPException(
                status_code=503,
                detail=f"Unable to load data for {symbol}."
            )

        logger.info(f"Using {data_source} for {symbol} seasonality analysis")

        # Calculate monthly returns
        hist['Year'] = hist.index.year
        hist['Month'] = hist.index.month
        hist['MonthName'] = hist.index.strftime('%B')
        hist['Quarter'] = hist.index.quarter

        # Calculate monthly percentage changes
        monthly_data = []
        for year in hist['Year'].unique():
            for month in range(1, 13):
                month_data = hist[(hist['Year'] == year) & (hist['Month'] == month)]
                if len(month_data) > 1:
                    first_price = month_data['Close'].iloc[0]
                    last_price = month_data['Close'].iloc[-1]
                    pct_change = ((last_price - first_price) / first_price) * 100
                    monthly_data.append({
                        'year': int(year),
                        'month': int(month),
                        'return': float(pct_change)
                    })

        # Calculate average returns per month
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_avg = []
        for month in range(1, 13):
            month_returns = [d['return'] for d in monthly_data if d['month'] == month]
            if month_returns:
                avg_return = np.mean(month_returns)
                win_rate = (sum(1 for r in month_returns if r > 0) / len(month_returns)) * 100
                monthly_avg.append({
                    'month': month_names[month - 1],
                    'avg_return': round(float(avg_return), 2),
                    'win_rate': round(float(win_rate), 1),
                    'count': len(month_returns)
                })

        # Calculate quarterly performance
        quarterly_data = []
        for quarter in range(1, 5):
            quarter_returns = []
            for year in hist['Year'].unique():
                quarter_data = hist[(hist['Year'] == year) & (hist['Quarter'] == quarter)]
                if len(quarter_data) > 1:
                    first_price = quarter_data['Close'].iloc[0]
                    last_price = quarter_data['Close'].iloc[-1]
                    pct_change = ((last_price - first_price) / first_price) * 100
                    quarter_returns.append(pct_change)

            if quarter_returns:
                quarterly_data.append({
                    'quarter': f'Q{quarter}',
                    'avg_return': round(float(np.mean(quarter_returns)), 2),
                    'win_rate': round((sum(1 for r in quarter_returns if r > 0) / len(quarter_returns)) * 100, 1)
                })

        # Find best and worst months
        sorted_months = sorted(monthly_avg, key=lambda x: x['avg_return'], reverse=True)
        best_months = ', '.join([m['month'] for m in sorted_months[:3]])
        worst_months = ', '.join([m['month'] for m in sorted_months[-3:]])

        # Get current price
        current_price = float(hist['Close'].iloc[-1])

        # Build heatmap data (Year x Month grid)
        years = sorted(hist['Year'].unique(), reverse=True)[:10]  # Last 10 years
        heatmap = []
        for year in years:
            year_data = {'year': int(year)}
            for month in range(1, 13):
                month_return = next((d['return'] for d in monthly_data if d['year'] == year and d['month'] == month), None)
                year_data[month_names[month - 1]] = round(month_return, 2) if month_return is not None else None
            heatmap.append(year_data)

        # Get asset name (just use symbol since we don't use yfinance anymore)
        asset_name = symbol

        return {
            "symbol": symbol,
            "name": asset_name,
            "current_price": round(current_price, 2),
            "best_months": best_months,
            "worst_months": worst_months,
            "data_range": f"{int(hist['Year'].min())} - {int(hist['Year'].max())}",
            "data_source": data_source,
            "monthly_seasonality": monthly_avg,
            "quarterly_performance": quarterly_data,
            "heatmap": heatmap,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error calculating seasonality for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate seasonality: {str(e)}")

# ============================================
# HOSTED DATASETS API - V1.1.2
# ============================================

# Path to datasets folder (now included in project - D1, H1, M1 only)
DATA_ROOT = os.environ.get("DATA_ROOT_PATH", "data/datasets")

@app.get("/api/datasets")
async def list_datasets():
    """List all available hosted datasets"""
    try:
        # Load metadata
        metadata_path = "data/metadata.json"
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            return metadata
        else:
            # Fallback: scan datasets dynamically
            logger.warning("Metadata file not found, scanning datasets...")
            return {
                "total_datasets": 0,
                "total_size_mb": 0,
                "last_updated": datetime.now().isoformat(),
                "instruments": [],
                "timeframes": [],
                "datasets": [],
                "message": "No datasets available. Run scan_datasets.py to generate metadata."
            }
    except Exception as e:
        logger.error(f"Error listing datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")

@app.get("/api/datasets/{dataset_id:path}")
async def get_dataset(dataset_id: str):
    """Load a specific dataset by ID (e.g., EURUSD/EURUSD_H1)"""
    try:
        # Construct file path
        csv_path = os.path.join(DATA_ROOT, f"{dataset_id}.csv")

        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")

        # Load CSV
        df = pd.read_csv(csv_path)

        # Get basic info
        file_size_mb = round(os.path.getsize(csv_path) / (1024 * 1024), 2)

        return {
            "dataset_id": dataset_id,
            "rows": len(df),
            "columns": list(df.columns),
            "size_mb": file_size_mb,
            "first_date": str(df.iloc[0].get('time', df.iloc[0].get('timestamp', 'N/A'))),
            "last_date": str(df.iloc[-1].get('time', df.iloc[-1].get('timestamp', 'N/A'))),
            "sample": df.head(10).to_dict(orient='records')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading dataset {dataset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load dataset: {str(e)}")

@app.post("/api/analyze/hosted")
async def analyze_hosted_dataset(request: Dict[str, Any]):
    """Analyze a hosted dataset without requiring file upload"""
    global analyzer_instance

    try:
        dataset_id = request.get('dataset_id')
        pattern = request.get('pattern')

        if not dataset_id:
            raise HTTPException(status_code=400, detail="dataset_id is required")
        if not pattern:
            raise HTTPException(status_code=400, detail="pattern is required")

        # Get instrument and timeframe from dataset_id
        parts = dataset_id.split('/')
        instrument = parts[0] if len(parts) > 0 else "Unknown"
        timeframe = parts[-1].split('_')[-1] if len(parts) > 1 else "Unknown"

        logger.info(f"Analyzing hosted dataset: {dataset_id} with pattern {pattern}")

        # Construct file path
        csv_path = os.path.join(DATA_ROOT, f"{dataset_id}.csv")

        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")

        # Load CSV (try tab-separated first, then comma-separated)
        # Your datasets use tab-separated format with extra trailing tabs
        try:
            df = pd.read_csv(csv_path, sep='\t', header=0, index_col=False)
        except:
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                logger.error(f"Failed to load CSV: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")

        # Process data to match yfinance format
        # Detect Time column (could be 'Time', 'time', 'Date', etc.)
        time_col = None
        for col in ['Time', 'time', 'Date', 'date', 'timestamp', 'Timestamp']:
            if col in df.columns:
                time_col = col
                break

        if time_col is None:
            # Log available columns for debugging
            logger.error(f"Available columns: {list(df.columns)}")
            raise HTTPException(status_code=400, detail=f"No time column found in dataset. Available columns: {list(df.columns)}")

        # Rename to standard format
        df = df.rename(columns={time_col: 'Date'})
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)

        # Ensure OHLC columns exist
        required_cols = ['Open', 'High', 'Low', 'Close']
        for col in required_cols:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Missing required column: {col}")

        # Convert to numeric
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Remove NaN rows
        df = df.dropna(subset=required_cols)

        if len(df) < 10:
            raise HTTPException(
                status_code=400,
                detail="Nicht genügend historische Daten verfügbar"
            )

        # Initialize analyzer and set data directly
        analyzer_instance = ProbabilityAnalyzer()
        analyzer_instance.data = df
        analyzer_instance.symbol = instrument
        analyzer_instance.timeframe = timeframe

        # Add candle types (required for analysis)
        analyzer_instance.data['Candle_Type'] = analyzer_instance.data.apply(
            lambda row: 'Bullish' if row['Close'] > row['Open']
            else ('Bearish' if row['Close'] < row['Open'] else 'Doji'),
            axis=1
        )

        # Calculate probabilities using existing logic
        results = analyzer_instance.calculate_probabilities(pattern)

        # Prepare response (same format as /api/analyze)
        response = {
            'dataset_id': dataset_id,
            'total_matches': results['total_matches'],
            'next_bullish': results['next_bullish'],
            'next_bearish': results['next_bearish'],
            'bullish_probability': round(results['bullish_probability'], 2),
            'bearish_probability': round(results['bearish_probability'], 2),
            'symbol': instrument,
            'timeframe': timeframe,
            'pattern': pattern,
            'data_info': {
                'total_candles': len(df),
                'date_range': {
                    'start': df.index[0].strftime('%Y-%m-%d'),
                    'end': df.index[-1].strftime('%Y-%m-%d')
                },
                'candle_types': {
                    'bullish': int(sum(df['Candle_Type'] == 'Bullish')),
                    'bearish': int(sum(df['Candle_Type'] == 'Bearish')),
                    'doji': int(sum(df['Candle_Type'] == 'Doji'))
                }
            }
        }

        logger.info(f"Analysis complete: {results['total_matches']} matches found")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing hosted dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze dataset: {str(e)}")

# ============================================
# INTRADAY SCREENER API - Polygon.io
# ============================================

@app.get("/api/intraday/screener")
async def get_intraday_screener(current_user: User = Depends(get_current_active_user)):
    """
    Get intraday M1 data for US500, VIX, EURUSD, XAUUSD from Polygon.io
    Returns last 24 hours of minute data
    """
    try:
        import requests

        # Polygon.io API key from environment
        polygon_api_key = os.environ.get("POLYGON_API_KEY", "")

        if not polygon_api_key:
            raise HTTPException(status_code=500, detail="Polygon.io API key not configured")

        # Symbol mapping for Polygon.io
        symbols = {
            'US500': 'I:SPX',        # S&P 500 Index
            'VIX': 'I:VIX',          # VIX Index
            'EURUSD': 'C:EURUSD',    # Forex pair
            'XAUUSD': 'C:XAUUSD'     # Gold
        }

        # Time range: last 24 hours
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)

        # Format dates for Polygon API
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        results = {}

        for symbol_key, polygon_symbol in symbols.items():
            try:
                # Polygon.io aggregates endpoint for minute bars
                url = f"https://api.polygon.io/v2/aggs/ticker/{polygon_symbol}/range/1/minute/{start_str}/{end_str}"
                params = {
                    'adjusted': 'true',
                    'sort': 'asc',
                    'limit': 50000,
                    'apiKey': polygon_api_key
                }

                logger.info(f"Fetching {symbol_key} from Polygon.io: {polygon_symbol}")
                response = requests.get(url, params=params, timeout=30)

                if response.status_code != 200:
                    logger.warning(f"Polygon.io returned {response.status_code} for {symbol_key}")
                    continue

                data = response.json()

                if data.get('resultsCount', 0) == 0 or 'results' not in data:
                    logger.warning(f"No data from Polygon.io for {symbol_key}")
                    continue

                # Extract OHLC data
                bars = data['results']
                timestamps = [bar['t'] for bar in bars]  # Unix timestamp in ms
                opens = [bar['o'] for bar in bars]
                highs = [bar['h'] for bar in bars]
                lows = [bar['l'] for bar in bars]
                closes = [bar['c'] for bar in bars]
                volumes = [bar.get('v', 0) for bar in bars]

                results[symbol_key] = {
                    'timestamps': timestamps,
                    'opens': opens,
                    'highs': highs,
                    'lows': lows,
                    'closes': closes,
                    'volumes': volumes,
                    'count': len(bars)
                }

                logger.info(f"✅ {symbol_key}: {len(bars)} bars loaded")

            except Exception as e:
                logger.error(f"Error fetching {symbol_key}: {str(e)}")
                continue

        if not results:
            raise HTTPException(status_code=503, detail="Failed to fetch data from Polygon.io for all symbols")

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in intraday screener: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Intraday screener error: {str(e)}")

@app.get("/api/yield-spread/analyze")
async def analyze_yield_spreads(
    period: str = "1y",
    current_user: User = Depends(get_current_active_user)
):
    """
    Comprehensive yield spread analysis

    Args:
        period: Time period (1mo, 3mo, 6mo, 1y, 2y)

    Returns:
        Complete analysis including:
        - Current yields, spreads, Z-scores
        - Rolling correlations (30/90/180 days)
        - Lead/Lag analysis
        - Historical data for charts
        - Alerts for extreme conditions
    """
    try:
        analyzer = get_analyzer()
        result = analyzer.analyze(period=period)
        return result
    except Exception as e:
        logger.error(f"Error in yield spread analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/yield-spread/summary")
async def get_yield_spread_summary(
    current_user: User = Depends(get_current_active_user)
):
    """
    Quick summary of current yield spreads and FX

    Returns:
        Current values and 1-day changes
    """
    try:
        analyzer = get_analyzer()
        result = analyzer.get_summary()
        return result
    except Exception as e:
        logger.error(f"Error getting yield spread summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Serve static HTML files
@app.get("/")
async def read_root():
    """Serve landing page"""
    return FileResponse("index.html")

@app.get("/login.html")
async def read_login():
    """Serve login page"""
    return FileResponse("login.html")

@app.get("/terminal.html")
async def read_terminal():
    """Serve terminal interface"""
    return FileResponse("terminal.html")

@app.get("/admin.html")
async def read_admin():
    """Serve admin panel"""
    return FileResponse("admin.html")

@app.get("/index.html")
async def read_index():
    """Serve index page"""
    return FileResponse("index.html")

if __name__ == "__main__":
    # Auto-create admin user on Railway deployment
    if os.environ.get("PORT"):
        try:
            import subprocess
            logger.info("Checking for admin user initialization...")
            subprocess.run([sys.executable, "init_admin.py"], check=False)
        except Exception as e:
            logger.warning(f"Admin init script failed: {e}")

    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
