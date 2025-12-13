from fastmcp import FastMCP

# Crypto Imports
from src.tools.crypto.tool import (
    get_crypto_prices, get_top_cryptos, get_crypto_metadata, get_historical_prices,
    get_trending_cryptos, get_global_crypto_metrics, get_market_pairs, get_latest_ohlcv,
    get_top_exchanges, get_crypto_map, get_crypto_categories, get_fear_and_greed_index,
    get_historical_top_cryptos, get_latest_crypto_news, get_blockchain_statistics,
    get_cmc20_index, get_price_performance
)
# Forex Imports
from src.tools.forex.tool import (
    get_forex_tickers,
    get_forex_exchanges,
    get_forex_conversion,
    get_forex_last_quote,
    get_forex_market_status,
    get_forex_movers,
    get_forex_prev_close,
    get_forex_history,
    get_forex_historical_quotes,
    get_forex_indicator,
    get_forex_market_snapshot,
    get_forex_snapshot,
    get_forex_market_holidays
)

def register_tools(mcp: FastMCP):
    """
    Registers all tool modules to the MCP server.
    This acts as the central registry.
    """
    
    # --- Crypto Domain ---
    crypto_tools = [
        get_crypto_prices,
        get_top_cryptos,
        get_crypto_metadata,
        get_historical_prices,
        get_trending_cryptos,
        get_global_crypto_metrics,
        get_market_pairs,
        get_latest_ohlcv,
        get_top_exchanges,
        get_crypto_map,
        get_crypto_categories,
        get_fear_and_greed_index,
        get_historical_top_cryptos,
        get_latest_crypto_news,
        get_blockchain_statistics,
        get_cmc20_index,
        get_price_performance
    ]
    
    # --- Forex Domain ---
    forex_tools = [
        get_forex_tickers,
        get_forex_exchanges,
        get_forex_conversion,
        get_forex_last_quote,
        get_forex_market_status,
        get_forex_movers,
        get_forex_prev_close,
        get_forex_history,
        get_forex_historical_quotes,
        get_forex_indicator,
        get_forex_market_snapshot,
        get_forex_snapshot,
        get_forex_market_holidays
    ]
    # 
    all_tools =  crypto_tools + forex_tools
    
    for tool in all_tools:
        mcp.tool(name=tool.__name__)(tool)
    
    return mcp