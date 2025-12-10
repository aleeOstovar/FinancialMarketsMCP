from pydantic import BaseModel, Field, field_validator
import re

class CryptoPriceInput(BaseModel):
    symbols: str = Field(..., description="Comma-separated symbols (e.g. BTC,ETH)")

    @field_validator('symbols')
    def validate_symbols(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Error: Cryptocurrency symbols cannot be empty.")
        parsed = [s.strip().upper() for s in v.split(",") if s.strip()]
        if not parsed:
            raise ValueError("Error: No valid cryptocurrency symbols provided.")
            
        for symbol in parsed:
            if not re.match(r'^[A-Z0-9]{1,10}$', symbol):
                raise ValueError(f"Error: Invalid cryptocurrency symbol format: {symbol}")
        
        return ",".join(parsed)

class TopCryptoInput(BaseModel):
    limit: int = Field(10, ge=1, le=100, description="Number of cryptocurrencies (1-100)")


class CryptoInfoInput(CryptoPriceInput):  
    pass

class HistoricalQuotesInput(BaseModel):
    symbols: str = Field(..., description="Comma-separated symbols (e.g. BTC,ETH)")
    time_start: str | None = Field(None, description="Start time (ISO 8601 or Unix timestamp)")
    time_end: str | None = Field(None, description="End time (ISO 8601 or Unix timestamp)")
    interval: str = Field("daily", description="Data interval (e.g., 5m, hourly, daily)")

    @field_validator('symbols')
    def validate_symbols(cls, v: str) -> str:
        return CryptoPriceInput.validate_symbols(v)  

class TrendingInput(BaseModel):
    limit: int = Field(10, ge=1, le=100, description="Number of trending cryptos (1-100)")
    time_period: str = Field("24h", description="Time period (1h, 24h, 7d, 30d)", pattern=r"^(1h|24h|7d|30d)$")

class GlobalMetricsInput(BaseModel):
    pass  

class MarketPairsInput(BaseModel):
    symbol: str = Field(..., description="Single symbol (e.g. BTC)")
    limit: int = Field(10, ge=1, le=100, description="Number of market pairs (1-100)")

    @field_validator('symbol')
    def validate_symbol(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r'^[A-Z0-9]{1,10}$', v):
            raise ValueError(f"Error: Invalid cryptocurrency symbol format: {v}")
        return v

class OhlcvLatestInput(CryptoPriceInput):
    pass

class ExchangeListingsInput(BaseModel):
    limit: int = Field(10, ge=1, le=100, description="Number of exchanges (1-100)")

class CryptoMapInput(BaseModel):
    limit: int = Field(100, ge=1, le=5000, description="Number of cryptos (1-5000)")
    listing_status: str = Field("active", description="Listing status (active, inactive, untracked)")

class CategoriesInput(BaseModel):
    limit: int = Field(100, ge=1, le=500, description="Number of categories (1-500)")

class FearAndGreedInput(BaseModel):
    pass  

class HistoricalListingsInput(BaseModel):
    date: str = Field(..., description="Historical date (YYYY-MM-DD)")
    limit: int = Field(10, ge=1, le=100, description="Number of cryptocurrencies (1-100)")

class LatestContentInput(BaseModel):
    symbol: str | None = Field(None, description="Comma-separated symbols (e.g. BTC,ETH)")
    limit: int = Field(10, ge=1, le=100, description="Number of news items (1-100)")

    @field_validator('symbol')
    def validate_symbol(cls, v: str | None) -> str | None:
        if v:
            return CryptoPriceInput.validate_symbols(v)  # Reuse if provided
        return v

class BlockchainStatsInput(BaseModel):
    slug: str = Field(..., description="Blockchain slug (e.g. bitcoin, ethereum)")

    @field_validator('slug')
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r'^[a-z0-9-]{1,50}$', v):
            raise ValueError(f"Error: Invalid blockchain slug format: {v}")
        return v

class Cmc20IndexInput(BaseModel):
    pass  

class PricePerformanceStatsInput(CryptoPriceInput):  
    pass