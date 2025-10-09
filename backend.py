"""
Atlas Terminal Backend - FastAPI Integration
Integriert den Probability Analyzer für das Atlas Terminal
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
import yfinance as yf
import logging
from datetime import datetime, timedelta
import sys
import os

# Add Prob_Analyzer path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../Prob_Analyzer'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Atlas Terminal API",
    description="Backend API für Atlas Terminal mit Probability Analyzer",
    version="1.1.1"
)

# CORS Middleware - Allow all origins for public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for public deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    def load_data(self, symbol: str, timeframe: str, period: str = "5y") -> pd.DataFrame:
        """Load historical OHLC data from yfinance"""
        try:
            logger.info(f"Loading data for {symbol} with timeframe {timeframe}")
            ticker = yf.Ticker(symbol)

            data = ticker.history(period=period, interval=timeframe)

            if data.empty:
                raise ValueError(f"No data available for symbol {symbol}")

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

# API Endpoints

@app.get("/")
async def root():
    return {
        "message": "Atlas Terminal API v1.1.1",
        "status": "running",
        "endpoints": [
            "/api/assets",
            "/api/timeframes",
            "/api/analyze"
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

@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get current market data for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")

        if len(hist) >= 2:
            current_price = float(hist['Close'].iloc[-1])
            prev_price = float(hist['Close'].iloc[-2])
            change = current_price - prev_price
            change_percent = (change / prev_price) * 100

            return {
                'symbol': symbol,
                'price': round(current_price, 5),
                'change': round(change, 5),
                'changePercent': round(change_percent, 2),
                'volume': int(hist['Volume'].iloc[-1])
            }
        else:
            raise HTTPException(status_code=404, detail="Keine Daten verfügbar")

    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}")
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
