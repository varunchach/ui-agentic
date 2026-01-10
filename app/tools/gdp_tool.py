"""GDP and economic data tool."""

import logging
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)


class GDPTool:
    """GDP and economic indicators tool."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize GDP tool.
        
        Args:
            api_key: Optional API key for economic data APIs (e.g., FRED, World Bank)
        """
        self.api_key = api_key
        self.fred_api_key = api_key  # Federal Reserve Economic Data
    
    def get_gdp_data(self, country: str = "US", year: Optional[int] = None) -> Dict[str, Any]:
        """Get GDP data for a country.
        
        Args:
            country: Country code (e.g., 'US', 'IN', 'CN')
            year: Optional specific year
            
        Returns:
            Dictionary with GDP data
        """
        try:
            # Using World Bank API (free, no key required)
            if country.upper() == "US":
                country_code = "USA"
            elif country.upper() == "IN":
                country_code = "IND"
            elif country.upper() == "CN":
                country_code = "CHN"
            else:
                country_code = country.upper()
            
            url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD"
            params = {"format": "json", "per_page": 10}
            if year:
                params["date"] = f"{year}:{year}"
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if len(data) > 1 and data[1]:
                latest = data[1][0] if data[1] else None
                if latest:
                    return {
                        "country": country,
                        "year": latest.get("date"),
                        "gdp_usd": latest.get("value"),
                        "indicator": latest.get("indicator", {}).get("value", "GDP")
                    }
            
            return {"error": "No GDP data found"}
            
        except Exception as e:
            logger.error(f"Error getting GDP data: {str(e)}")
            return {"error": str(e)}
    
    def get_economic_indicators(self, country: str = "US") -> Dict[str, Any]:
        """Get various economic indicators.
        
        Args:
            country: Country code
            
        Returns:
            Dictionary with economic indicators
        """
        # This is a simplified version - can be extended with FRED API if key provided
        gdp_data = self.get_gdp_data(country)
        
        return {
            "country": country,
            "gdp": gdp_data,
            "note": "Additional indicators available with FRED API key"
        }
    
    def __call__(self, action: str, country: Optional[str] = None, **kwargs) -> str:
        """Make tool callable.
        
        Args:
            action: Action ('gdp' or 'indicators')
            country: Country code
            **kwargs: Additional parameters
            
        Returns:
            Formatted economic data as string
        """
        country = country or kwargs.get("country", "US")
        
        if action == "gdp":
            data = self.get_gdp_data(country, kwargs.get("year"))
            if "error" in data:
                return f"Error: {data['error']}"
            
            formatted = f"GDP Data for {data['country']}:\n\n"
            formatted += f"Year: {data['year']}\n"
            if data.get('gdp_usd'):
                gdp_billions = data['gdp_usd'] / 1e9
                formatted += f"GDP: ${gdp_billions:.2f} billion USD\n"
            return formatted
        
        elif action == "indicators":
            data = self.get_economic_indicators(country)
            formatted = f"Economic Indicators for {data['country']}:\n\n"
            if data.get('gdp'):
                gdp = data['gdp']
                if 'gdp_usd' in gdp and gdp['gdp_usd']:
                    gdp_billions = gdp['gdp_usd'] / 1e9
                    formatted += f"GDP ({gdp.get('year', 'N/A')}): ${gdp_billions:.2f} billion USD\n"
            return formatted
        
        return "Invalid action. Use 'gdp' or 'indicators' with a country code."
