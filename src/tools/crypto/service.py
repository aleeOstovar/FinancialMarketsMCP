import requests
from typing import Dict, List, Any
from src.common.settings import get_settings
from src.common.logger import setup_logger
from src.common.exceptions import sanitize_message 

logger = setup_logger(__name__)

class CoinMarketCapService:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.COINMARKETCAP_API_KEY
        self.headers = {
            "X-CMC_PRO_API_KEY": self.api_key,
            "Accept": "application/json"
        }
        self.base_url = self.settings.COINMARKETCAP_BASE_URL

    def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict:
        url = f"{self.base_url}{endpoint}"
        
        safe_params = {k: sanitize_message(str(v), self.api_key) for k, v in params.items()}
        logger.info(f"API request to {endpoint} with params: {safe_params}")

        # Note: We let requests raise exceptions here so the Tool layer can catch them 
        # and pass them to handle_api_error, preserving the separation of concerns.
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_quotes(self, symbols: List[str]) -> Dict:
        return self._request("/v1/cryptocurrency/quotes/latest", {"symbol": ",".join(symbols)})

    def get_listings(self, limit: int = 10) -> Dict:
        return self._request("/v1/cryptocurrency/listings/latest", {
            "limit": limit, 
            "sort": "market_cap"
        })

    def get_crypto_info(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v2/cryptocurrency/info", params)

    def get_historical_quotes(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v2/cryptocurrency/quotes/historical", params)

    def get_trending_latest(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v1/cryptocurrency/trending/latest", params)

    def get_global_metrics(self, params: Dict[str, Any] = {}) -> Dict:
        return self._request("/v1/global-metrics/quotes/latest", params)

    def get_market_pairs(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v2/cryptocurrency/market-pairs/latest", params)

    def get_ohlcv_latest(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v2/cryptocurrency/ohlcv/latest", params)

    def get_exchange_listings(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v1/exchange/listings/latest", params)

    def get_crypto_map(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v1/cryptocurrency/map", params)

    def get_categories(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v1/cryptocurrency/categories", params)

    def get_fear_and_greed(self, params: Dict[str, Any] = {}) -> Dict:
        return self._request("/v3/fear-and-greed/latest", params)
    
    def get_historical_listings(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v1/cryptocurrency/listings/historical", params)

    def get_latest_content(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v1/content/latest", params)

    def get_blockchain_stats(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v1/blockchain/statistics/latest", params)

    def get_cmc20_index(self, params: Dict[str, Any] = {}) -> Dict:
        return self._request("/v3/index/cmc20-latest", params)

    def get_price_performance_stats(self, params: Dict[str, Any]) -> Dict:
        return self._request("/v2/cryptocurrency/price-performance-stats/latest", params)