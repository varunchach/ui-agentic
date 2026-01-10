"""BFSI KPI schema definitions and validation."""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class GrowthType(str, Enum):
    """Growth metric types."""
    QOQ = "QoQ"  # Quarter over Quarter
    YOY = "YoY"  # Year over Year


class KPIMetrics(BaseModel):
    """BFSI KPI metrics structure."""
    
    # Financial Metrics
    revenue: Optional[float] = Field(
        default=None,
        description="Total revenue in currency units (e.g., INR crores, USD millions)"
    )
    net_profit: Optional[float] = Field(
        default=None,
        description="Net profit in currency units"
    )
    roe: Optional[float] = Field(
        default=None,
        description="Return on Equity (ROE) as percentage"
    )
    roa: Optional[float] = Field(
        default=None,
        description="Return on Assets (ROA) as percentage"
    )
    
    # Asset Quality Metrics
    gnpa: Optional[float] = Field(
        default=None,
        description="Gross Non-Performing Assets (GNPA) as percentage"
    )
    nnpa: Optional[float] = Field(
        default=None,
        description="Net Non-Performing Assets (NNPA) as percentage"
    )
    pcr: Optional[float] = Field(
        default=None,
        description="Provision Coverage Ratio (PCR) as percentage"
    )
    
    # Capital Adequacy
    crar: Optional[float] = Field(
        default=None,
        description="Capital to Risk-Weighted Assets Ratio (CRAR) as percentage"
    )
    car: Optional[float] = Field(
        default=None,
        description="Capital Adequacy Ratio (CAR) as percentage"
    )
    
    # Growth Metrics
    revenue_growth_qoq: Optional[float] = Field(
        default=None,
        description="Revenue growth Quarter over Quarter as percentage"
    )
    revenue_growth_yoy: Optional[float] = Field(
        default=None,
        description="Revenue growth Year over Year as percentage"
    )
    profit_growth_qoq: Optional[float] = Field(
        default=None,
        description="Profit growth Quarter over Quarter as percentage"
    )
    profit_growth_yoy: Optional[float] = Field(
        default=None,
        description="Profit growth Year over Year as percentage"
    )
    
    # Metadata
    currency: Optional[str] = Field(
        default=None,
        description="Currency unit (e.g., INR, USD)"
    )
    period: Optional[str] = Field(
        default=None,
        description="Reporting period (e.g., Q1 FY2024, Annual 2023)"
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary with 'not_found' for None values."""
        result = {}
        for field_name, field_value in self.model_dump().items():
            if field_value is None:
                result[field_name] = "not_found"
            else:
                result[field_name] = field_value
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "KPIMetrics":
        """Create from dictionary, converting 'not_found' to None."""
        processed_data = {}
        for key, value in data.items():
            if value == "not_found" or value is None:
                processed_data[key] = None
            else:
                processed_data[key] = value
        return cls(**processed_data)


# KPI extraction patterns for reference
KPI_PATTERNS = {
    "revenue": [
        r"revenue[:\s]+([\d,]+\.?\d*)",
        r"total\s+revenue[:\s]+([\d,]+\.?\d*)",
        r"income[:\s]+([\d,]+\.?\d*)",
    ],
    "net_profit": [
        r"net\s+profit[:\s]+([\d,]+\.?\d*)",
        r"profit\s+after\s+tax[:\s]+([\d,]+\.?\d*)",
        r"pat[:\s]+([\d,]+\.?\d*)",
    ],
    "roe": [
        r"roe[:\s]+([\d,]+\.?\d*)%?",
        r"return\s+on\s+equity[:\s]+([\d,]+\.?\d*)%?",
    ],
    "roa": [
        r"roa[:\s]+([\d,]+\.?\d*)%?",
        r"return\s+on\s+assets[:\s]+([\d,]+\.?\d*)%?",
    ],
    "gnpa": [
        r"gnpa[:\s]+([\d,]+\.?\d*)%?",
        r"gross\s+npa[:\s]+([\d,]+\.?\d*)%?",
        r"gross\s+non[- ]?performing\s+assets[:\s]+([\d,]+\.?\d*)%?",
    ],
    "nnpa": [
        r"nnpa[:\s]+([\d,]+\.?\d*)%?",
        r"net\s+npa[:\s]+([\d,]+\.?\d*)%?",
        r"net\s+non[- ]?performing\s+assets[:\s]+([\d,]+\.?\d*)%?",
    ],
    "pcr": [
        r"pcr[:\s]+([\d,]+\.?\d*)%?",
        r"provision\s+coverage\s+ratio[:\s]+([\d,]+\.?\d*)%?",
    ],
    "crar": [
        r"crar[:\s]+([\d,]+\.?\d*)%?",
        r"capital\s+to\s+risk[-\s]+weighted\s+assets\s+ratio[:\s]+([\d,]+\.?\d*)%?",
    ],
    "car": [
        r"car[:\s]+([\d,]+\.?\d*)%?",
        r"capital\s+adequacy\s+ratio[:\s]+([\d,]+\.?\d*)%?",
    ],
}


def validate_kpi_data(data: dict) -> tuple[bool, Optional[str]]:
    """Validate KPI data structure.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        KPIMetrics.from_dict(data)
        return True, None
    except Exception as e:
        return False, str(e)
