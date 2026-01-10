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
            response.raise_for_status()  # Raise exception for bad status codes
            data = response.json()
            
            # World Bank API returns [metadata, data_array]
            if not isinstance(data, list) or len(data) < 2:
                logger.warning(f"Unexpected API response structure: {type(data)}")
                return {"error": "Invalid API response format"}
            
            data_array = data[1]
            
            # If no data for requested year, try to get latest available
            if not data_array or len(data_array) == 0:
                if year:
                    # Year not available, try without year filter
                    logger.info(f"No data for {year}, fetching latest available")
                    params_no_year = {"format": "json", "per_page": 10}
                    response = requests.get(url, params=params_no_year, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    data_array = data[1] if len(data) > 1 else []
            
            if data_array and len(data_array) > 0:
                # Get the most recent entry (first in array is usually latest)
                latest = data_array[0]
                
                # Check if value exists and is not None
                gdp_value = latest.get("value")
                if gdp_value is None:
                    # Try to find entry with value
                    for entry in data_array:
                        if entry.get("value") is not None:
                            latest = entry
                            gdp_value = latest.get("value")
                            break
                
                if gdp_value is not None:
                    return {
                        "country": country,
                        "year": latest.get("date"),
                        "gdp_usd": float(gdp_value),
                        "indicator": latest.get("indicator", {}).get("value", "GDP") if isinstance(latest.get("indicator"), dict) else "GDP"
                    }
                else:
                    logger.warning(f"GDP data found but value is None for {country}")
                    return {"error": f"GDP data exists but value is not available for {country}"}
            
            return {"error": f"No GDP data found for {country}" + (f" in year {year}" if year else "")}
            
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
            year = kwargs.get("year")
            data = self.get_gdp_data(country, year)
            if "error" in data:
                error_msg = data['error']
                # If year was requested but not found, provide helpful message
                if year and "No GDP data found" in error_msg:
                    return f"GDP data for {year} is not available yet. The latest available data will be shown instead. {error_msg}"
                return f"Error: {error_msg}"
            
            formatted = f"GDP Data for {data['country']}:\n\n"
            formatted += f"Year: {data['year']}\n"
            if data.get('gdp_usd'):
                gdp_billions = data['gdp_usd'] / 1e9
                formatted += f"GDP: ${gdp_billions:.2f} billion USD\n"
                if year and str(data['year']) != str(year):
                    formatted += f"\nNote: Data for {year} is not available yet. Showing latest available year ({data['year']}).\n"
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
