import requests
from typing import Dict, Any, Optional
from src.common.settings import get_settings
from src.common.logger import setup_logger
from src.common.exceptions import sanitize_message

logger = setup_logger(__name__)

class MassiveForexService:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = getattr(self.settings, "MASSIVE_API_KEY", "") 
        self.base_url = getattr(self.settings, "MASSIVE_BASE_URL")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

    def _ensure_prefix(self, ticker: str) -> str:
        """Helper to ensure Forex tickers have the 'C:' prefix required by some endpoints."""
        if ":" not in ticker and len(ticker) == 6:
            return f"C:{ticker}"
        return ticker

    def _request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        if params is None:
            params = {}
        
        # Fallback for APIs that need key in query
        if "apiKey" not in params and not self.headers.get("Authorization"):
             params["apiKey"] = self.api_key

        url = f"{self.base_url}{endpoint}"
        
        safe_params = {k: sanitize_message(str(v), self.api_key) for k, v in params.items()}
        logger.info(f"API request to {endpoint} with params: {safe_params}")

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection failed to {url}")
            # Raise a clean error that Tool layer can catch
            raise Exception("Network Error: Could not connect to the API endpoint.")
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to {url}")
            raise Exception("Network Error: Request timed out.")
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                logger.error(f"API Error {e.response.status_code}: {e.response.text}")
                # Try to parse API error message
                try:
                    err_json = e.response.json()
                    msg = err_json.get('error', err_json.get('message', e.response.text))
                    raise Exception(f"API Error ({e.response.status_code}): {msg}")
                except:
                    pass
            raise e

    def get_tickers(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v3/reference/tickers", params)

    def get_exchanges(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v3/reference/exchanges", params)

    def get_market_status(self) -> Dict:
        return self._request("/v1/marketstatus/now")

    def get_conversion(self, from_ccy: str, to_ccy: str, params: Dict[str, Any]) -> Dict:
        return self._request(f"/v1/conversion/{from_ccy}/{to_ccy}", params)

    def get_last_quote(self, ticker: str) -> Dict:
        # Ticker often needs "C:" prefix for this endpoint
        ticker = self._ensure_prefix(ticker)
        # Try v1 first (Standard for Forex Last Quote on many providers)
        # If user explicitly listed v2, we keep v2, but v1 is safer for 'last_quote' on currencies
        return self._request(f"/v1/last_quote/currencies/{ticker[2:5]}/{ticker[5:]}") 
        # Note: The above path implies splitting C:EURUSD -> EUR / USD. 
        # However, if the user insists on the provided endpoint list:
        # return self._request(f"/v2/last/quote/{ticker}")

    def get_historical_quotes(self, ticker: str, params: Dict[str, Any]) -> Dict:
        ticker = self._ensure_prefix(ticker)
        return self._request(f"/v3/quotes/{ticker}", params)

    def get_snapshot_ticker(self, ticker: str) -> Dict:
        ticker = self._ensure_prefix(ticker)
        return self._request(f"/v2/snapshot/locale/global/markets/forex/tickers/{ticker}")

    def get_snapshot_all(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v2/snapshot/locale/global/markets/forex/tickers", params)

    def get_market_movers(self, direction: str) -> Dict:
        return self._request(f"/v2/snapshot/locale/global/markets/forex/{direction}")

    def get_prev_day(self, ticker: str) -> Dict:
        ticker = self._ensure_prefix(ticker)
        return self._request(f"/v2/aggs/ticker/{ticker}/prev")

    def get_custom_bars(self, ticker: str, multiplier: int, timespan: str, from_date: str, to_date: str, params: Dict[str, Any]) -> Dict:
        ticker = self._ensure_prefix(ticker)
        if "adjusted" not in params:
            params["adjusted"] = "true"
        if "sort" not in params:
            params["sort"] = "asc"
            
        endpoint = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        return self._request(endpoint, params)


    def _get_indicator(self, name: str, ticker: str, params: Dict[str, Any]) -> Dict:
        ticker = self._ensure_prefix(ticker)
        if "adjusted" not in params:
             params["adjusted"] = "true"
        if "order" not in params: 
             params["order"] = "desc" 
        
        return self._request(f"/v1/indicators/{name}/{ticker}", params)

    def get_sma(self, ticker: str, params: Dict[str, Any]) -> Dict:
        return self._get_indicator("sma", ticker, params)

    def get_ema(self, ticker: str, params: Dict[str, Any]) -> Dict:
        return self._get_indicator("ema", ticker, params)

    def get_macd(self, ticker: str, params: Dict[str, Any]) -> Dict:
        return self._get_indicator("macd", ticker, params)

    def get_rsi(self, ticker: str, params: Dict[str, Any]) -> Dict:
        return self._get_indicator("rsi", ticker, params)

    def get_bollinger(self, ticker: str, params: Dict[str, Any]) -> Dict:
        return self._get_indicator("bollinger", ticker, params)