from fastmcp import FastMCP
from src.tools.crypto.tool import (
    get_crypto_prices, get_top_cryptos, get_crypto_metadata, get_historical_prices,
    get_trending_cryptos, get_global_crypto_metrics, get_market_pairs, get_latest_ohlcv,
    get_top_exchanges, get_crypto_map, get_crypto_categories, get_fear_and_greed_index,
    get_historical_top_cryptos, get_latest_crypto_news, get_blockchain_statistics,
    get_cmc20_index, get_price_performance
)

def register_tools(mcp: FastMCP):
    """
    Registers all tool modules to the MCP server.
    This acts as the central registry.
    """
    
    # 1. CoinMarketCap Tools
    tool_functions = [
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
    
    for tool in tool_functions:
        mcp.tool(name=tool.__name__)(tool)
    
    return mcp