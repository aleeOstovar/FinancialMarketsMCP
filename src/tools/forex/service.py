import asyncio
import json
from typing import Dict, Any, List, Callable, TypeVar

from massive import RESTClient
from urllib3.exceptions import HTTPError as UrllibHTTPError, MaxRetryError

from src.common.settings import get_settings
from src.common.logger import setup_logger
from src.common.custom_exceptions import (
    ProviderConnectionError, 
    ProviderTimeoutError, 
    DataNotFound, 
    RateLimitExceeded, 
    InvalidInputError
)

logger = setup_logger(__name__)
settings = get_settings()

T = TypeVar("T")

class MassiveForexService:
    def __init__(self):
        # Concurrency Cap
        self._semaphore = asyncio.Semaphore(getattr(settings, "FOREX_MAX_CONCURRENCY", 10))
        
        #Initialize Client 
        self.client = RESTClient(api_key=settings.MASSIVE_API_KEY)
        
        # Manual Base URL Configuration 
        if hasattr(settings, "MASSIVE_BASE_URL") and settings.MASSIVE_BASE_URL:
            self.client.base_url = settings.MASSIVE_BASE_URL
            
    async def _execute_bounded(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Executes a blocking SDK call in a thread with a strict timeout.
        """
        async with self._semaphore:
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(func, *args, **kwargs),
                    timeout=getattr(settings, "FOREX_TIMEOUT_SECONDS", 30)
                )
                
            except (asyncio.TimeoutError, TimeoutError):
                logger.error("Massive API Request Timed Out")
                raise ProviderTimeoutError("External data provider timed out.")
                
            except (MaxRetryError, UrllibHTTPError) as e:
                logger.error(f"Massive API Network Error: {e}", exc_info=True)
                raise ProviderConnectionError("Failed to connect to Forex Data Provider.")
                
            except Exception as e:
                error_str = str(e)
                if "401" in error_str:
                    logger.critical("Massive API Key invalid!")
                    raise ProviderConnectionError("Internal Configuration Error (API Key).")
                if "429" in error_str:
                    raise RateLimitExceeded("Forex data rate limit reached.")
                if "404" in error_str:
                    raise DataNotFound(f"Resource not found.")
                
                logger.error(f"Unexpected API Error: {e}", exc_info=True)
                raise RuntimeError(f"Provider Error: {error_str}")

    def _ensure_prefix(self, ticker: str) -> str:
        """Helper: Ensure 'C:' prefix."""
        ticker = ticker.strip().upper().replace("X:", "").replace("C:", "")
        return f"C:{ticker}"
    def _split_pair(self, ticker: str):
            """
            Helper: Splits ticker into (Base, Quote).
            Handles standard 'EURUSD' and hyphenated 'EUR-USD'.
            """
            # Remove common prefixes
            clean = ticker.replace("C:", "").replace("X:", "").strip().upper()
            
            # Handle Hyphenated (e.g. "EUR-USD") - Seen in Massive Docs
            if "-" in clean:
                parts = clean.split("-")
                if len(parts) == 2:
                    return parts[0], parts[1]

            # Handle Standard (e.g. "EURUSD")
            if len(clean) == 6:
                return clean[:3], clean[3:]

            # Fail explicitly if format is unknown
            raise InvalidInputError(f"Invalid ticker format: '{ticker}'. Expected 6 chars (EURUSD) or hyphenated (EUR-USD).")


    async def get_tickers(self, params: Dict[str, Any]) -> List[Any]:
        limit = params.get("limit", 100)
        return await self._execute_bounded(
            lambda: list(self.client.list_tickers(market="fx", limit=limit))
        )

    async def get_exchanges(self, params: Dict[str, Any]) -> List[Any]:
        return await self._execute_bounded(
            lambda: list(self.client.get_exchanges(asset_class="fx", locale="global"))
        )

    async def get_market_status(self) -> Any:
        return await self._execute_bounded(self.client.get_market_status)

    async def get_conversion(self, from_ccy: str, to_ccy: str, params: Dict[str, Any]) -> Any:
        amount = params.get("amount", 1.0)
        return await self._execute_bounded(
            self.client.get_real_time_currency_conversion,
            from_ccy, to_ccy, amount=amount, precision=2
        )

    async def get_last_quote(self, ticker: str) -> Any:
        # Split the single ticker string into (from, to)
        base, quote = self._split_pair(ticker)
        return await self._execute_bounded(
            self.client.get_last_forex_quote, 
            base, 
            quote
        )

    async def get_historical_quotes(self, ticker: str, params: Dict[str, Any]) -> List[Any]:
        """
        Retrieves quotes using Raw Mode to prevent SDK iterator timeouts.
        Returns a list of Dictionaries (not SDK Objects).
        """
        # Inject defaults
        params.setdefault("order", "asc")
        params.setdefault("sort", "timestamp")
        
        
        params["limit"] = min(params.get("limit", 100), 1000)

        def safe_fetch():
            response = self.client.list_quotes(self._ensure_prefix(ticker), raw=True, **params)
            if hasattr(response, 'data'):
                json_data = json.loads(response.data.decode("utf-8"))
            else:
                json_data = json.loads(response)

            return json_data.get("results", [])

        return await self._execute_bounded(safe_fetch)

    async def get_snapshot_ticker(self, ticker: str) -> Any:
        return await self._execute_bounded(
            self.client.get_snapshot_ticker, 
            market_type="forex",
            ticker=self._ensure_prefix(ticker)
        )

    async def get_snapshot_all(self, params: Dict[str, Any]) -> List[Any]:
        tickers = params.get("tickers")
        return await self._execute_bounded(
            lambda: list(self.client.get_snapshot_all(market_type="forex", tickers=tickers))
        )

    async def get_market_movers(self, direction: str) -> List[Any]:
        return await self._execute_bounded(
            lambda: list(self.client.get_snapshot_direction(market_type="forex", direction=direction))
        )

    async def get_prev_day(self, ticker: str) -> Any:
        return await self._execute_bounded(
            self.client.get_previous_close_agg, 
            self._ensure_prefix(ticker)
        )

    async def get_custom_bars(self, ticker: str, multiplier: int, timespan: str, from_date: str, to_date: str, params: Dict[str, Any]) -> List[Any]:
        sort = params.get("sort", "asc")
        return await self._execute_bounded(
            lambda: list(self.client.list_aggs(
                ticker=self._ensure_prefix(ticker),
                multiplier=multiplier,
                timespan=timespan,
                from_=from_date,
                to=to_date,
                limit=50000,
                adjusted=True,
                sort=sort
            ))
        )

    # --- Technical Indicators ---
    
    def _inject_defaults(self, params: Dict[str, Any]) -> Dict[str, Any]:
        defaults = {"adjusted": True, "order": "desc", "limit": 10}
        return {**defaults, **params}

    async def get_sma(self, ticker: str, params: Dict[str, Any]) -> Any:
        return await self._execute_bounded(
            self.client.get_sma, self._ensure_prefix(ticker), **self._inject_defaults(params)
        )

    async def get_ema(self, ticker: str, params: Dict[str, Any]) -> Any:
        return await self._execute_bounded(
            self.client.get_ema, self._ensure_prefix(ticker), **self._inject_defaults(params)
        )

    async def get_macd(self, ticker: str, params: Dict[str, Any]) -> Any:
        return await self._execute_bounded(
            self.client.get_macd, self._ensure_prefix(ticker), **self._inject_defaults(params)
        )

    async def get_rsi(self, ticker: str, params: Dict[str, Any]) -> Any:
        return await self._execute_bounded(
            self.client.get_rsi, self._ensure_prefix(ticker), **self._inject_defaults(params)
        )

    async def get_bollinger(self, ticker: str, params: Dict[str, Any]) -> Any:
        return await self._execute_bounded(
            self.client.get_bollinger_bands, self._ensure_prefix(ticker), **self._inject_defaults(params)
        )

    async def get_market_holidays(self) -> List[Any]:
        return await self._execute_bounded(self.client.get_market_holidays)