from typing import Annotated
from pydantic import Field, ValidationError
from src.tools.crypto.service import CoinMarketCapService
from src.tools.crypto.schemas import (
    CryptoPriceInput, TopCryptoInput, CryptoInfoInput, HistoricalQuotesInput, TrendingInput,
    GlobalMetricsInput, MarketPairsInput, OhlcvLatestInput, ExchangeListingsInput,
    CryptoMapInput, CategoriesInput, FearAndGreedInput, HistoricalListingsInput,
    LatestContentInput, BlockchainStatsInput, Cmc20IndexInput, PricePerformanceStatsInput
)
from src.common.exceptions import handle_api_error
from src.common.settings import get_settings

# Instantiate service once
cmc_service = CoinMarketCapService()
settings = get_settings()

def get_crypto_prices(
    symbols: Annotated[str, Field(description="Comma-separated symbols (e.g. BTC,ETH)")]
) -> str:
    """[Crypto] Get current price for one or more cryptocurrencies."""
    
    # Validation
    try:
        validated_input = CryptoPriceInput(symbols=symbols)
    except ValidationError as e:
        # Return a readable error message to the LLM
        return f"Input Validation Error: {str(e)}"

    # Logic
    # The validator in schemas.py cleans the string, so we use that
    symbol_list = validated_input.symbols.split(',')
    
    try:
        response = cmc_service.get_quotes(symbol_list)
        data = response.get("data", {})
        if not data: 
            return "Error: No data returned from API."
            
        result_lines = ["Cryptocurrency Prices:", "-" * 50]
        for symbol in symbol_list:
            if symbol in data:
                crypto = data[symbol]
                quote = crypto.get("quote", {}).get("USD", {})
                result_lines.append(f"{crypto.get('name')} ({symbol}): ${quote.get('price', 0):,.2f}")
        return "\n".join(result_lines)
        
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)


def get_top_cryptos(
    limit: Annotated[int, Field(10, description="Number of cryptocurrencies (1-100)")] = 10
) -> str:
    """[Crypto] Get top cryptocurrencies by market cap."""
    
    # Validation
    try:
        validated_input = TopCryptoInput(limit=limit)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    # Logic
    try:
        response = cmc_service.get_listings(validated_input.limit)
        data = response.get("data", [])
        
        lines = [f"Top {validated_input.limit} Cryptocurrencies by Market Cap:", "=" * 70]
        for c in data:
            q = c.get("quote", {}).get("USD", {})
            lines.append(f"#{c.get('cmc_rank')} {c.get('name')} ({c.get('symbol')}): ${q.get('price', 0):,.2f}")
        return "\n".join(lines)
        
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)


def get_crypto_metadata(
    symbols: Annotated[str, Field(description="Comma-separated symbols (e.g. BTC,ETH)")]
) -> str:
    """[Crypto] Get static metadata (logo, description, website, etc.) for cryptocurrencies."""
    
    try:
        validated_input = CryptoInfoInput(symbols=symbols)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    symbol_list = validated_input.symbols.split(',')
    params = {"symbol": validated_input.symbols}
    
    try:
        response = cmc_service.get_crypto_info(params)
        data = response.get("data", {})
        if not data:
            return "Error: No data returned from API."
        
        result_lines = ["Cryptocurrency Metadata:", "-" * 50]
        for symbol in symbol_list:
            if symbol in data:
                info = data[symbol][0] if isinstance(data[symbol], list) else data[symbol]  # Handles list response
                result_lines.append(f"{info.get('name')} ({symbol}):")
                result_lines.append(f"  Description: {info.get('description', 'N/A')[:200]}...")  # Truncate long desc
                result_lines.append(f"  Website: {info.get('urls', {}).get('website', ['N/A'])[0]}")
                result_lines.append(f"  Logo: {info.get('logo', 'N/A')}")
                result_lines.append(f"  Technical Doc: {info.get('urls', {}).get('technical_doc', ['N/A'])[0]}")
                result_lines.append("")
        return "\n".join(result_lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_historical_prices(
    symbols: Annotated[str, Field(description="Comma-separated symbols (e.g. BTC,ETH)")],
    time_start: Annotated[str | None, Field(None, description="Start time (ISO 8601 or Unix timestamp)")] = None,
    time_end: Annotated[str | None, Field(None, description="End time (ISO 8601 or Unix timestamp)")] = None,
    interval: Annotated[str, Field("daily", description="Data interval (e.g., 5m, hourly, daily)")] = "daily"
) -> str:
    """[Crypto] Get historical market quotes for cryptocurrencies."""
    
    try:
        validated_input = HistoricalQuotesInput(symbols=symbols, time_start=time_start, time_end=time_end, interval=interval)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    symbol_list = validated_input.symbols.split(',')
    params = {
        "symbol": validated_input.symbols,
        "interval": validated_input.interval
    }
    if validated_input.time_start:
        params["time_start"] = validated_input.time_start
    if validated_input.time_end:
        params["time_end"] = validated_input.time_end
    
    try:
        response = cmc_service.get_historical_quotes(params)
        data = response.get("data", {})
        if not data:
            return "Error: No data returned from API."
        
        result_lines = ["Historical Cryptocurrency Prices:", "-" * 50]
        for symbol in symbol_list:
            if symbol in data:
                quotes = data[symbol][0]["quotes"] if isinstance(data[symbol], list) else data[symbol].get("quotes", [])
                result_lines.append(f"{symbol} Historical Data:")
                for quote in quotes[:10]:  # Limit to first 10 for brevity
                    ts = quote.get("timestamp", "N/A")
                    price = quote.get("quote", {}).get("USD", {}).get("price", 0)
                    result_lines.append(f"  {ts}: ${price:,.2f}")
                result_lines.append("")
        return "\n".join(result_lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_trending_cryptos(
    limit: Annotated[int, Field(10, description="Number of trending cryptos (1-100)")] = 10,
    time_period: Annotated[str, Field("24h", description="Time period (1h, 24h, 7d, 30d)")] = "24h"
) -> str:
    """[Crypto] Get trending cryptocurrencies based on search volume."""
    
    try:
        validated_input = TrendingInput(limit=limit, time_period=time_period)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    params = {
        "limit": validated_input.limit,
        "time_period": validated_input.time_period
    }
    
    try:
        response = cmc_service.get_trending_latest(params)
        data = response.get("data", [])
        if not data:
            return "Error: No data returned from API."
        
        lines = [f"Top {validated_input.limit} Trending Cryptos ({time_period}):", "=" * 70]
        for c in data:
            q = c.get("quote", {}).get("USD", {})
            lines.append(f"#{c.get('rank')} {c.get('name')} ({c.get('symbol')}): ${q.get('price', 0):,.2f}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_global_crypto_metrics() -> str:
    """[Crypto] Get latest global cryptocurrency market metrics."""
    
    try:
        validated_input = GlobalMetricsInput()
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    try:
        response = cmc_service.get_global_metrics()
        data = response.get("data", {})
        if not data:
            return "Error: No data returned from API."
        
        quote = data.get("quote", {}).get("USD", {})
        lines = ["Global Crypto Metrics:", "-" * 50]
        lines.append(f"Total Market Cap: ${quote.get('total_market_cap', 0):,.2f}")
        lines.append(f"24h Volume: ${quote.get('total_volume_24h', 0):,.2f}")
        lines.append(f"BTC Dominance: {data.get('btc_dominance', 0):.2f}%")
        lines.append(f"Active Cryptocurrencies: {data.get('active_cryptocurrencies', 0)}")
        lines.append(f"Active Exchanges: {data.get('active_exchanges', 0)}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_market_pairs(
    symbol: Annotated[str, Field(description="Single symbol (e.g. BTC)")],
    limit: Annotated[int, Field(10, description="Number of market pairs (1-100)")] = 10
) -> str:
    """[Crypto] Get active market pairs for a cryptocurrency."""
    
    try:
        validated_input = MarketPairsInput(symbol=symbol, limit=limit)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    params = {
        "symbol": validated_input.symbol,
        "limit": validated_input.limit
    }
    
    try:
        response = cmc_service.get_market_pairs(params)
        data = response.get("data", {})
        pairs = data.get("market_pairs", [])
        if not pairs:
            return "Error: No data returned from API."
        
        lines = [f"Market Pairs for {data.get('name')} ({symbol}):", "-" * 50]
        for p in pairs[:limit]:
            lines.append(f"{p.get('exchange', {}).get('name', 'N/A')} - {p.get('base_symbol')}/{p.get('quote_symbol')}: ${p.get('quote', {}).get('USD', {}).get('price', 0):,.2f} (Vol: ${p.get('quote', {}).get('USD', {}).get('volume_24h', 0):,.2f})")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_latest_ohlcv(
    symbols: Annotated[str, Field(description="Comma-separated symbols (e.g. BTC,ETH)")]
) -> str:
    """[Crypto] Get latest OHLCV data for cryptocurrencies."""
    
    try:
        validated_input = OhlcvLatestInput(symbols=symbols)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    symbol_list = validated_input.symbols.split(',')
    params = {"symbol": validated_input.symbols}
    
    try:
        response = cmc_service.get_ohlcv_latest(params)
        data = response.get("data", {})
        if not data:
            return "Error: No data returned from API."
        
        result_lines = ["Latest OHLCV Data:", "-" * 50]
        for symbol in symbol_list:
            if symbol in data:
                ohlcv = data[symbol][0].get("quote", {}).get("USD", {}) if isinstance(data[symbol], list) else {}
                result_lines.append(f"{symbol}:")
                result_lines.append(f"  Open: ${ohlcv.get('open', 0):,.2f}")
                result_lines.append(f"  High: ${ohlcv.get('high', 0):,.2f}")
                result_lines.append(f"  Low: ${ohlcv.get('low', 0):,.2f}")
                result_lines.append(f"  Close: ${ohlcv.get('close', 0):,.2f}")
                result_lines.append(f"  Volume: ${ohlcv.get('volume', 0):,.2f}")
                result_lines.append("")
        return "\n".join(result_lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_top_exchanges(
    limit: Annotated[int, Field(10, description="Number of exchanges (1-100)")] = 10
) -> str:
    """[Crypto] Get top exchanges by trading volume."""
    
    try:
        validated_input = ExchangeListingsInput(limit=limit)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    params = {"limit": validated_input.limit}
    
    try:
        response = cmc_service.get_exchange_listings(params)
        data = response.get("data", [])
        if not data:
            return "Error: No data returned from API."
        
        lines = [f"Top {limit} Exchanges by Volume:", "=" * 70]
        for e in data:
            q = e.get("quote", {}).get("USD", {})
            lines.append(f"#{e.get('rank')} {e.get('name')}: 24h Volume ${q.get('volume_24h', 0):,.2f} | Liquidity Score: {e.get('liquidity_score', 0)}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_crypto_map(
    limit: Annotated[int, Field(100, description="Number of cryptos (1-5000)")] = 100,
    listing_status: Annotated[str, Field("active", description="Listing status (active, inactive, untracked)")] = "active"
) -> str:
    """[Crypto] Get mapping of all supported cryptocurrencies."""
    
    try:
        validated_input = CryptoMapInput(limit=limit, listing_status=listing_status)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    params = {
        "limit": validated_input.limit,
        "listing_status": validated_input.listing_status
    }
    
    try:
        response = cmc_service.get_crypto_map(params)
        data = response.get("data", [])
        if not data:
            return "Error: No data returned from API."
        
        lines = [f"Cryptocurrency Map ({listing_status}, top {limit}):", "-" * 50]
        for c in data:
            lines.append(f"ID: {c.get('id')} | {c.get('name')} ({c.get('symbol')}) | Rank: {c.get('rank', 'N/A')} | First Historical Data: {c.get('first_historical_data', 'N/A')}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_crypto_categories(
    limit: Annotated[int, Field(100, description="Number of categories (1-500)")] = 100
) -> str:
    """[Crypto] Get list of cryptocurrency categories."""
    
    try:
        validated_input = CategoriesInput(limit=limit)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    params = {"limit": validated_input.limit}
    
    try:
        response = cmc_service.get_categories(params)
        data = response.get("data", [])
        if not data:
            return "Error: No data returned from API."
        
        lines = ["Cryptocurrency Categories:", "-" * 50]
        for cat in data:
            lines.append(f"{cat.get('name')} (ID: {cat.get('id')}) | Num Coins: {cat.get('num_tokens', 0)} | Avg Price Change 24h: {cat.get('avg_price_change', 0):.2f}%")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_fear_and_greed_index() -> str:
    """[Crypto] Get the latest Crypto Fear and Greed Index."""
    
    try:
        validated_input = FearAndGreedInput()
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    try:
        response = cmc_service.get_fear_and_greed()
        data = response.get("data", {})
        if not data:
            return "Error: No data returned from API."
        
        value = data.get("value", 0)
        classification = data.get("value_classification", "N/A")
        lines = ["Crypto Fear & Greed Index:", "-" * 50]
        lines.append(f"Value: {value} ({classification})")
        lines.append(f"Timestamp: {data.get('timestamp', 'N/A')}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)
    
def get_historical_top_cryptos(
    date: Annotated[str, Field(description="Historical date (YYYY-MM-DD)")],
    limit: Annotated[int, Field(10, description="Number of cryptocurrencies (1-100)")] = 10
) -> str:
    """[Crypto] Get historical top cryptocurrencies by market cap on a specific date."""
    
    try:
        validated_input = HistoricalListingsInput(date=date, limit=limit)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    params = {
        "date": validated_input.date,
        "limit": validated_input.limit
    }
    
    try:
        response = cmc_service.get_historical_listings(params)
        data = response.get("data", [])
        if not data:
            return "Error: No data returned from API."
        
        lines = [f"Top {limit} Cryptocurrencies by Market Cap on {date}:", "=" * 70]
        for c in data:
            q = c.get("quote", {}).get("USD", {})
            lines.append(f"#{c.get('cmc_rank')} {c.get('name')} ({c.get('symbol')}): ${q.get('price', 0):,.2f}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_latest_crypto_news(
    symbol: Annotated[str | None, Field(None, description="Comma-separated symbols (e.g. BTC,ETH)")] = None,
    limit: Annotated[int, Field(10, description="Number of news items (1-100)")] = 10
) -> str:
    """[Crypto] Get latest cryptocurrency news and articles."""
    
    try:
        validated_input = LatestContentInput(symbol=symbol, limit=limit)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    params = {"limit": validated_input.limit}
    if validated_input.symbol:
        params["symbol"] = validated_input.symbol
    
    try:
        response = cmc_service.get_latest_content(params)
        data = response.get("data", [])
        if not data:
            return "Error: No data returned from API."
        
        lines = ["Latest Crypto News:", "-" * 50]
        for item in data:
            lines.append(f"{item.get('title', 'N/A')} ({item.get('published_at', 'N/A')})")
            lines.append(f"  Source: {item.get('source', {}).get('name', 'N/A')}")
            lines.append(f"  Summary: {item.get('description', 'N/A')[:200]}...")
            lines.append(f"  URL: {item.get('url', 'N/A')}")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_blockchain_statistics(
    slug: Annotated[str, Field(description="Blockchain slug (e.g. bitcoin, ethereum)")]
) -> str:
    """[Crypto] Get latest blockchain network statistics."""
    
    try:
        validated_input = BlockchainStatsInput(slug=slug)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    params = {"slug": validated_input.slug}
    
    try:
        response = cmc_service.get_blockchain_stats(params)
        data = response.get("data", {})
        if not data:
            return "Error: No data returned from API."
        
        stats = list(data.values())[0] if data else {}  # Assumes single blockchain response
        lines = [f"Blockchain Stats for {slug.capitalize()}:", "-" * 50]
        lines.append(f"Hashrate: {stats.get('hashrate', 'N/A')}")
        lines.append(f"Transaction Count 24h: {stats.get('transaction_count_24h', 'N/A')}")
        lines.append(f"Average Transaction Fee USD: ${stats.get('average_transaction_fee_usd', 0):,.2f}")
        lines.append(f"Difficulty: {stats.get('difficulty', 'N/A')}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_cmc20_index() -> str:
    """[Crypto] Get the latest CMC 20 Index value and constituents."""
    
    try:
        validated_input = Cmc20IndexInput()
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    try:
        response = cmc_service.get_cmc20_index()
        data = response.get("data", {})
        if not data:
            return "Error: No data returned from API."
        
        lines = ["CMC 20 Index:", "-" * 50]
        lines.append(f"Value: {data.get('value', 0):,.2f}")
        lines.append(f"Timestamp: {data.get('timestamp', 'N/A')}")
        lines.append("Constituents:")
        for c in data.get('constituents', [])[:20]:  # Top 20
            lines.append(f"  {c.get('name')} ({c.get('symbol')}): Weight {c.get('weight', 0):.2f}%")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)

def get_price_performance(
    symbols: Annotated[str, Field(description="Comma-separated symbols (e.g. BTC,ETH)")]
) -> str:
    """[Crypto] Get price performance stats for cryptocurrencies."""
    
    try:
        validated_input = PricePerformanceStatsInput(symbols=symbols)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"
    
    symbol_list = validated_input.symbols.split(',')
    params = {"symbol": validated_input.symbols}
    
    try:
        response = cmc_service.get_price_performance_stats(params)
        data = response.get("data", {})
        if not data:
            return "Error: No data returned from API."
        
        result_lines = ["Price Performance Stats:", "-" * 50]
        for symbol in symbol_list:
            if symbol in data:
                stats = data[symbol][0] if isinstance(data[symbol], list) else data[symbol]
                usd = stats.get("quote", {}).get("USD", {})
                result_lines.append(f"{stats.get('name')} ({symbol}):")
                result_lines.append(f"  All-Time High: ${usd.get('all_time_high', {}).get('price', 0):,.2f} ({usd.get('all_time_high', {}).get('percent_down', 0):.2f}% down)")
                result_lines.append(f"  All-Time Low: ${usd.get('all_time_low', {}).get('price', 0):,.2f}")
                result_lines.append(f"  24h Change: {usd.get('percent_change_24h', 0):.2f}%")
                result_lines.append(f"  7d Change: {usd.get('percent_change_7d', 0):.2f}%")
                result_lines.append(f"  30d Change: {usd.get('percent_change_30d', 0):.2f}%")
                result_lines.append("")
        return "\n".join(result_lines)
    except Exception as e:
        return handle_api_error(e, settings.COINMARKETCAP_API_KEY)