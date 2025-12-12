from pydantic import BaseModel, Field, field_validator
import re
from typing import Optional

class ForexTickerInput(BaseModel):
    ticker: str = Field(..., description="Forex Pair Ticker (e.g. C:EURUSD, EURUSD)")

    @field_validator('ticker')
    def validate_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r'^([A-Z]{1,2}:)?[A-Z0-9]{3,10}$', v):
            raise ValueError(f"Error: Invalid forex ticker format: {v}. Try adding 'C:' prefix (e.g. C:EURUSD).")
        return v

class TickersListInput(BaseModel):
    limit: int = Field(100, ge=1, le=1000, description="Number of tickers to retrieve (1-1000)")
    market: str = Field("fx", description="Market type (default: fx)")
    

class ConversionInput(BaseModel):
    from_currency: str = Field(..., description="Source Currency (e.g. USD)")
    to_currency: str = Field(..., description="Target Currency (e.g. EUR)")
    amount: float = Field(1.0, gt=0, description="Amount to convert")

    @field_validator('from_currency', 'to_currency')
    def validate_currency(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r'^[A-Z]{3}$', v):
            raise ValueError(f"Error: Currency code must be 3 letters (e.g. USD): {v}")
        return v

class HistoricalQuotesInput(ForexTickerInput):
    timestamp: Optional[str] = Field(None, description="Query by timestamp (YYYY-MM-DD or Unix MS)")
    limit: int = Field(100, ge=1, le=50000, description="Max results")

class MarketMoversInput(BaseModel):
    direction: str = Field(..., description="Direction: 'gainers' or 'losers'")

    @field_validator('direction')
    def validate_direction(cls, v: str) -> str:
        v = v.lower()
        if v not in ['gainers', 'losers']:
            raise ValueError("Error: Direction must be 'gainers' or 'losers'")
        return v

class CustomBarsInput(ForexTickerInput):
    multiplier: int = Field(1, ge=1, description="Time interval multiplier (e.g. 1 for 1-minute)")
    timespan: str = Field(..., description="Timespan: minute, hour, day, week, month, quarter, year")
    from_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    to_date: str = Field(..., description="End date (YYYY-MM-DD)")

    @field_validator('timespan')
    def validate_timespan(cls, v: str) -> str:
        valid = ['minute', 'hour', 'day', 'week', 'month', 'quarter', 'year']
        if v.lower() not in valid:
            raise ValueError(f"Error: Timespan must be one of {valid}")
        return v.lower()

class IndicatorInput(ForexTickerInput):
    timespan: str = Field("day", description="Timespan for aggregation (minute, hour, day)")
    window: int = Field(14, ge=1, description="Window size for calculation")
    series_type: str = Field("close", description="Price type: open, high, low, close")
    limit: int = Field(10, ge=1, description="Number of data points to return")
    
    
class ExchangesInput(BaseModel):
    asset_class: str = Field("fx", description="Asset class (default: fx)")
    locale: str = Field("global", description="Locale (default: global)")

class MarketSnapshotInput(BaseModel):
    tickers: Optional[str] = Field(None, description="Comma-separated list of tickers to filter")
    limit: int = Field(100, ge=1, le=1000, description="Number of results")

    @field_validator('tickers')
    def validate_tickers(cls, v: str | None) -> str | None:
        if v:
            return ",".join([t.strip().upper() for t in v.split(",") if t.strip()])
        return v
    
