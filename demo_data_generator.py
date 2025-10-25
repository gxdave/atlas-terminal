"""
Generate realistic demo data for seasonality analysis
This ensures the terminal always works even when APIs fail
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_crypto_seasonality(symbol: str, years: int = 10) -> pd.DataFrame:
    """Generate realistic crypto seasonality data"""

    # Base prices for different cryptos
    base_prices = {
        'BTC-USD': 30000,
        'ETH-USD': 2000,
        'BNB-USD': 300,
        'XRP-USD': 0.5,
        'ADA-USD': 0.4,
        'SOL-USD': 25,
        'DOGE-USD': 0.08,
        'MATIC-USD': 0.9,
        'DOT-USD': 6
    }

    base_price = base_prices.get(symbol, 100)

    # Crypto seasonal patterns (higher volatility)
    monthly_patterns = {
        1: 0.05,   # Jan (January effect)
        2: -0.02,  # Feb
        3: 0.03,   # Mar
        4: 0.08,   # Apr (Spring rally)
        5: -0.05,  # May (Sell in May)
        6: -0.03,  # Jun
        7: 0.02,   # Jul
        8: -0.01,  # Aug
        9: 0.04,   # Sep
        10: 0.06,  # Oct (Uptober)
        11: 0.09,  # Nov (Best month)
        12: 0.03   # Dec
    }

    dates = []
    prices = []

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)

    current_date = start_date
    current_price = base_price * 0.3  # Start lower

    while current_date <= end_date:
        month = current_date.month

        # Apply seasonal pattern
        monthly_change = monthly_patterns[month]

        # Add randomness
        daily_change = monthly_change / 30 + random.uniform(-0.02, 0.02)

        current_price *= (1 + daily_change)
        current_price = max(current_price, base_price * 0.1)  # Floor

        dates.append(current_date)
        prices.append(current_price)

        current_date += timedelta(days=1)

    df = pd.DataFrame({
        'Close': prices,
        'Open': [p * random.uniform(0.98, 1.02) for p in prices],
        'High': [p * random.uniform(1.0, 1.05) for p in prices],
        'Low': [p * random.uniform(0.95, 1.0) for p in prices],
        'Volume': [random.uniform(1e9, 5e9) for _ in prices]
    }, index=dates)

    return df

def generate_stock_seasonality(symbol: str, years: int = 10) -> pd.DataFrame:
    """Generate realistic stock seasonality data"""

    # Base prices for different stocks
    base_prices = {
        'AAPL': 150,
        'MSFT': 300,
        'GOOGL': 120,
        'AMZN': 130,
        'TSLA': 200,
        'NVDA': 400,
        'META': 280,
        'SPY': 400,
        'QQQ': 350,
        'DIA': 340
    }

    base_price = base_prices.get(symbol, 100)

    # Stock seasonal patterns (Santa Rally, September effect, etc.)
    monthly_patterns = {
        1: 0.04,   # Jan (January effect)
        2: 0.01,   # Feb
        3: 0.02,   # Mar
        4: 0.03,   # Apr (Tax day bounce)
        5: -0.01,  # May (Sell in May)
        6: 0.00,   # Jun
        7: 0.02,   # Jul
        8: 0.00,   # Aug
        9: -0.03,  # Sep (Worst month)
        10: 0.02,  # Oct (Recovery)
        11: 0.04,  # Nov (Strong)
        12: 0.05   # Dec (Santa Rally)
    }

    dates = []
    prices = []

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)

    current_date = start_date
    current_price = base_price * 0.6  # Start lower for growth

    # Add overall uptrend for stocks
    daily_trend = 0.0003  # ~11% annual growth

    while current_date <= end_date:
        month = current_date.month

        # Apply seasonal pattern
        monthly_change = monthly_patterns[month]

        # Add trend and randomness
        daily_change = (monthly_change / 30) + daily_trend + random.uniform(-0.01, 0.01)

        current_price *= (1 + daily_change)
        current_price = max(current_price, base_price * 0.3)  # Floor

        dates.append(current_date)
        prices.append(current_price)

        current_date += timedelta(days=1)

    df = pd.DataFrame({
        'Close': prices,
        'Open': [p * random.uniform(0.99, 1.01) for p in prices],
        'High': [p * random.uniform(1.0, 1.02) for p in prices],
        'Low': [p * random.uniform(0.98, 1.0) for p in prices],
        'Volume': [random.uniform(5e7, 2e8) for _ in prices]
    }, index=dates)

    return df

def get_demo_data(symbol: str) -> pd.DataFrame:
    """
    Get demo data for a symbol
    Returns realistic seasonality patterns
    """

    if '-USD' in symbol:
        # Crypto
        return generate_crypto_seasonality(symbol, years=10)
    else:
        # Stock/ETF
        return generate_stock_seasonality(symbol, years=10)


# Pre-generate data for common symbols to save CPU
PREGENERATED_DATA = {}

def init_demo_data():
    """Pre-generate demo data for popular symbols"""
    global PREGENERATED_DATA

    # Popular symbols
    symbols = [
        'BTC-USD', 'ETH-USD', 'BNB-USD',
        'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA',
        'SPY', 'QQQ', 'DIA'
    ]

    for symbol in symbols:
        PREGENERATED_DATA[symbol] = get_demo_data(symbol)

# Initialize on import
init_demo_data()
