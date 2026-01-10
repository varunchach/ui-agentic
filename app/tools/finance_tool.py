"""Financial data tool using yfinance."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FinanceTool:
    """Financial data tool for stock prices, market data, etc."""
    
    def __init__(self):
        """Initialize finance tool."""
        self._yfinance = None
    
    def _get_yfinance(self):
        """Lazy load yfinance."""
        if self._yfinance is None:
            try:
                import yfinance as yf
                self._yfinance = yf
                logger.info("yfinance loaded for financial data")
            except ImportError:
                raise ImportError(
                    "yfinance not installed. "
                    "Install with: pip install yfinance"
                )
        return self._yfinance
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get stock information.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT', 'HDFCBANK.NS')
            
        Returns:
            Dictionary with stock information
        """
        try:
            yf = self._get_yfinance()
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName", "N/A")),
                "current_price": info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
                "market_cap": info.get("marketCap", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            }
        except Exception as e:
            logger.error(f"Error getting stock info for {symbol}: {str(e)}")
            return {"error": str(e)}
    
    def get_historical_data(self, symbol: str, period: str = "1mo") -> Dict[str, Any]:
        """Get historical stock data.
        
        Args:
            symbol: Stock symbol
            period: Period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            
        Returns:
            Dictionary with historical data summary
        """
        try:
            yf = self._get_yfinance()
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return {"error": "No historical data available"}
            
            return {
                "symbol": symbol,
                "period": period,
                "start_date": str(hist.index[0].date()),
                "end_date": str(hist.index[-1].date()),
                "open": float(hist['Open'].iloc[-1]),
                "high": float(hist['High'].max()),
                "low": float(hist['Low'].min()),
                "close": float(hist['Close'].iloc[-1]),
                "volume": int(hist['Volume'].sum()),
            }
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return {"error": str(e)}
    
    def __call__(self, action: str, symbol: Optional[str] = None, **kwargs) -> str:
        """Make tool callable.
        
        Args:
            action: Action to perform ('stock_info' or 'historical_data')
            symbol: Stock symbol
            **kwargs: Additional parameters
            
        Returns:
            Formatted financial data as string
        """
        if action == "stock_info" and symbol:
            info = self.get_stock_info(symbol)
            if "error" in info:
                return f"Error: {info['error']}"
            
            formatted = f"Stock Information for {info['symbol']}:\n\n"
            formatted += f"Company: {info['name']}\n"
            formatted += f"Current Price: ${info['current_price']}\n"
            formatted += f"Market Cap: ${info['market_cap']:,}\n" if isinstance(info['market_cap'], (int, float)) else f"Market Cap: {info['market_cap']}\n"
            formatted += f"P/E Ratio: {info['pe_ratio']}\n"
            formatted += f"Dividend Yield: {info['dividend_yield']}\n"
            formatted += f"52 Week High: ${info['52_week_high']}\n"
            formatted += f"52 Week Low: ${info['52_week_low']}\n"
            return formatted
        
        elif action == "historical_data" and symbol:
            period = kwargs.get("period", "1mo")
            data = self.get_historical_data(symbol, period)
            if "error" in data:
                return f"Error: {data['error']}"
            
            formatted = f"Historical Data for {data['symbol']} ({data['period']}):\n\n"
            formatted += f"Period: {data['start_date']} to {data['end_date']}\n"
            formatted += f"Current Close: ${data['close']:.2f}\n"
            formatted += f"High: ${data['high']:.2f}\n"
            formatted += f"Low: ${data['low']:.2f}\n"
            formatted += f"Total Volume: {data['volume']:,}\n"
            return formatted
        
        return "Invalid action. Use 'stock_info' or 'historical_data' with a symbol."
