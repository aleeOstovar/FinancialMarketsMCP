from typing import Annotated
from pydantic import Field, ValidationError
from src.tools.forex.service import MassiveForexService
from src.tools.forex.schemas import (
    ForexTickerInput, TickersListInput, ConversionInput, HistoricalQuotesInput,
    MarketMoversInput, CustomBarsInput, IndicatorInput,ExchangesInput,MarketSnapshotInput
)
from src.common.exceptions import handle_api_error
from src.common.settings import get_settings

# Instantiate service singleton
forex_service = MassiveForexService()
settings = get_settings()

def get_forex_tickers(
    limit: Annotated[int, Field(100, description="Number of tickers (1-1000)")] = 100
) -> str:
    """[Forex] Retrieve a comprehensive list of supported forex currency pairs."""
    try:
        validated = TickersListInput(limit=limit)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"

    try:
        response = forex_service.get_tickers({"limit": validated.limit})
        results = response.get("results", [])
        
        lines = [f"Forex Tickers (Top {limit}):", "-" * 50]
        for item in results:
            lines.append(f"{item.get('ticker')} - {item.get('name')} ({item.get('locale', 'N/A')})")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

def get_forex_conversion(
    from_currency: Annotated[str, Field(description="Source Currency (e.g. USD)")],
    to_currency: Annotated[str, Field(description="Target Currency (e.g. EUR)")],
    amount: Annotated[float, Field(1.0, description="Amount to convert")] = 1.0
) -> str:
    """[Forex] Real-time conversion between two currencies."""
    try:
        validated = ConversionInput(from_currency=from_currency, to_currency=to_currency, amount=amount)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"

    try:
        res = forex_service.get_conversion(validated.from_currency, validated.to_currency, {"amount": validated.amount})
        converted = res.get("converted", 0)
        last_price = res.get("last", {}).get("ask", 0) if isinstance(res.get("last"), dict) else res.get("last", 0)
        
        lines = ["Currency Conversion:", "-" * 50]
        lines.append(f"{validated.amount} {validated.from_currency} -> {validated.to_currency}")
        lines.append(f"Result: {converted:,.4f} {validated.to_currency}")
        lines.append(f"Rate: {last_price:,.4f}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

def get_forex_last_quote(
    ticker: Annotated[str, Field(description="Forex Pair (e.g. EURUSD)")]
) -> str:
    """[Forex] Get the most recent bid/ask quote for a currency pair."""
    try:
        validated = ForexTickerInput(ticker=ticker)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"

    try:
        res = forex_service.get_last_quote(validated.ticker)
        # Assuming 'results' or direct object
        data = res.get("results", res)
        
        lines = [f"Last Quote for {validated.ticker}:", "-" * 50]
        lines.append(f"Bid: {data.get('bid', 'N/A')}") 
        lines.append(f"Ask: {data.get('ask', 'N/A')}")
        lines.append(f"Timestamp: {data.get('timestamp', 'N/A')}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

def get_forex_market_status() -> str:
    """[Forex] Get current trading status for forex markets."""
    try:
        res = forex_service.get_market_status()
        
        lines = ["Forex Market Status:", "-" * 50]
        lines.append(f"Market: {res.get('market', 'N/A')}")
        lines.append(f"Status: {res.get('status', 'N/A')}")
        if "exchanges" in res:
             lines.append(f"Exchanges Open: {res.get('exchanges', {}).get('open', 'N/A')}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

def get_forex_snapshot(
    ticker: Annotated[str, Field(description="Forex Pair (e.g. EURUSD)")]
) -> str:
    """[Forex] Get a comprehensive market data snapshot for a single ticker."""
    try:
        validated = ForexTickerInput(ticker=ticker)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"

    try:
        res = forex_service.get_snapshot_ticker(validated.ticker)
        data = res.get("ticker", {})
        day = data.get("day", {})
        
        lines = [f"Snapshot for {validated.ticker}:", "-" * 50]
        lines.append(f"Price: {data.get('lastTrade', {}).get('p', 'N/A')}")
        lines.append(f"Today's Change: {data.get('todaysChangePerc', 0):.2f}%")
        lines.append(f"Day Open: {day.get('o', 'N/A')} | High: {day.get('h', 'N/A')} | Low: {day.get('l', 'N/A')} | Close: {day.get('c', 'N/A')}")
        lines.append(f"Volume: {day.get('v', 0):,.0f}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

def get_forex_movers(
    direction: Annotated[str, Field(description="Direction: 'gainers' or 'losers'")]
) -> str:
    """[Forex] Get top market movers (gainers/losers)."""
    try:
        validated = MarketMoversInput(direction=direction)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"

    try:
        res = forex_service.get_market_movers(validated.direction)
        tickers = res.get("tickers", [])
        
        lines = [f"Top Forex {validated.direction.capitalize()}:", "=" * 50]
        for t in tickers[:10]:
            lines.append(f"{t.get('ticker')} | Change: {t.get('todaysChangePerc'):.2f}% | Price: {t.get('day', {}).get('c')}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

def get_forex_history(
    ticker: Annotated[str, Field(description="Forex Pair (e.g. EURUSD)")],
    multiplier: Annotated[int, Field(1, description="Time interval multiplier")] = 1,
    timespan: Annotated[str, Field("day", description="minute, hour, day")] = "day",
    from_date: Annotated[str, Field(description="Start YYYY-MM-DD")] = "2024-01-01",
    to_date: Annotated[str, Field(description="End YYYY-MM-DD")] = "2024-01-07"
) -> str:
    """[Forex] Get historical OHLC bars for a custom range."""
    try:
        validated = CustomBarsInput(ticker=ticker, multiplier=multiplier, timespan=timespan, from_date=from_date, to_date=to_date)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"

    try:
        res = forex_service.get_custom_bars(
            validated.ticker, validated.multiplier, validated.timespan, validated.from_date, validated.to_date, {}
        )
        results = res.get("results", [])
        
        lines = [f"Historical Data for {validated.ticker} ({validated.multiplier} {validated.timespan}):", "-" * 50]
        if not results:
            return "No data found for this range."
            
        for bar in results[:20]: # Limit for LLM context window
            lines.append(f"TS: {bar.get('t')} | O: {bar.get('o')} | H: {bar.get('h')} | L: {bar.get('l')} | C: {bar.get('c')}")
        
        if len(results) > 20:
            lines.append(f"... (+{len(results)-20} more records)")
            
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

def get_forex_historical_quotes(
    ticker: Annotated[str, Field(description="Forex Pair (e.g. EURUSD)")],
    timestamp: Annotated[str | None, Field(None, description="Query by timestamp (YYYY-MM-DD or Unix MS)")] = None,
    limit: Annotated[int, Field(100, description="Max results (1-50000)")] = 100
) -> str:
    """[Forex] Retrieve historical Bid/Ask (BBO) quotes for a currency pair."""
    
    try:
        validated = HistoricalQuotesInput(ticker=ticker, timestamp=timestamp, limit=limit)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"

    params = {"limit": validated.limit}
    if validated.timestamp:
        params["timestamp"] = validated.timestamp

    try:
        # Calls GET /v3/quotes/{fxTicker}
        res = forex_service.get_historical_quotes(validated.ticker, params)
        results = res.get("results", [])

        if not results:
            return "No historical quotes found for this criteria."

        lines = [f"Historical Quotes (BBO) for {validated.ticker}:", "-" * 50]
        # Massive API Quotes  return: { "t": timestamp, "y": timestamp_ns, "a": ask_price, "b": bid_price, "as": ask_size, "bs": bid_size }
        for q in results[:20]: # Limit display to avoid context overflow
            ts = q.get('t', 'N/A') 
            ask = q.get('a', 'N/A')
            bid = q.get('b', 'N/A')
            lines.append(f"Time: {ts} | Bid: {bid} | Ask: {ask}")
        
        if len(results) > 20:
            lines.append(f"... (+{len(results)-20} more records)")

        return "\n".join(lines)

    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

def get_forex_indicator(
    indicator: Annotated[str, Field(description="Type: sma, ema, macd, rsi, bollinger")],
    ticker: Annotated[str, Field(description="Forex Pair (e.g. EURUSD)")],
    timespan: Annotated[str, Field("day", description="minute, hour, day")] = "day",
    window: Annotated[int, Field(14, description="Window size")] = 14
) -> str:
    """[Forex] Calculate technical indicators (SMA, EMA, RSI, MACD, Bollinger)."""
    
    try:
        validated = IndicatorInput(ticker=ticker, timespan=timespan, window=window)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"

    params = {
        "timespan": validated.timespan,
        "window": validated.window,
        "series_type": validated.series_type,
        "limit": validated.limit
    }

    try:
        if indicator.lower() == "sma":
            res = forex_service.get_sma(validated.ticker, params)
        elif indicator.lower() == "ema":
            res = forex_service.get_ema(validated.ticker, params)
        elif indicator.lower() == "macd":
            res = forex_service.get_macd(validated.ticker, params)
        elif indicator.lower() == "rsi":
            res = forex_service.get_rsi(validated.ticker, params)
        elif indicator.lower() == "bollinger":
            res = forex_service.get_bollinger(validated.ticker, params)
        else:
            return "Error: Unsupported indicator type."

        results = res.get("results", {}).get("values", [])
        
        lines = [f"{indicator.upper()} Indicator for {validated.ticker}:", "-" * 50]
        for val in results[:10]:
            lines.append(f"Date: {val.get('timestamp')} | Value: {val.get('value')}")
            
        return "\n".join(lines)

    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)
    
def get_forex_exchanges(
    asset_class: Annotated[str, Field("fx", description="Asset class (default: fx)")] = "fx",
    locale: Annotated[str, Field("global", description="Locale (default: global)")] = "global"
) -> str:
    """[Forex] Retrieve a list of known forex exchanges."""
    
    try:
        validated = ExchangesInput(asset_class=asset_class, locale=locale)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"

    params = {
        "asset_class": validated.asset_class,
        "locale": validated.locale
    }

    try:
        res = forex_service.get_exchanges(params)
        results = res.get("results", [])

        if not results:
            return "No exchanges found."

        lines = ["Forex Exchanges:", "-" * 50]
        for ex in results:
            lines.append(f"ID: {ex.get('id')} | Name: {ex.get('name')} | Type: {ex.get('type')} | Locale: {ex.get('locale')}")
            if ex.get('url'):
                lines.append(f"  URL: {ex.get('url')}")
        
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)
    
def get_forex_market_snapshot(
    tickers: Annotated[str | None, Field(None, description="Comma-separated list of tickers to filter")] = None,
    limit: Annotated[int, Field(100, description="Number of results")] = 100
) -> str:
    """[Forex] Retrieve a comprehensive snapshot of the entire forex market (or filtered list)."""

    try:
        validated = MarketSnapshotInput(tickers=tickers, limit=limit)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"

    params = {"limit": validated.limit}
    if validated.tickers:
        params["tickers"] = validated.tickers

    try:
        # Calls GET /v2/snapshot/locale/global/markets/forex/tickers
        res = forex_service.get_snapshot_all(params)
        
        # Depending on API, response might be a list under 'tickers' key or direct list
        data = res.get("tickers", []) if isinstance(res, dict) else res

        if not data:
            return "No snapshot data available."

        lines = [f"Market Snapshot ({len(data)} tickers):", "-" * 50]
        sorted_data = sorted(data, key=lambda x: abs(x.get('todaysChangePerc', 0)), reverse=True)

        for t in sorted_data[:validated.limit]:
            ticker = t.get('ticker')
            price = t.get('lastTrade', {}).get('p', t.get('min', {}).get('c', 0)) # Fallback if structure varies
            change = t.get('todaysChangePerc', 0)
            vol = t.get('day', {}).get('v', 0)
            
            lines.append(f"{ticker}: {price} ({change:+.2f}%) | Vol: {vol:,.0f}")
        
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)
    
def get_forex_prev_close(
    ticker: Annotated[str, Field(description="Forex Pair (e.g. EURUSD)")]
) -> str:
    """[Forex] Retrieve the previous trading day's OHLC data for a currency pair."""
    
    try:
        validated = ForexTickerInput(ticker=ticker)
    except ValidationError as e:
        return f"Input Validation Error: {str(e)}"

    try:
        # Calls GET /v2/aggs/ticker/{fxTicker}/prev
        res = forex_service.get_prev_day(validated.ticker)

        results = res.get("results", [])
        if not results:
            return "No previous day data found."

        bar = results[0]
        lines = [f"Previous Day Close for {validated.ticker}:", "-" * 50]
        lines.append(f"Date: {res.get('status') if 'status' not in ['OK'] else 'Recent'}") # API varies on date field location
        lines.append(f"Open: {bar.get('o')}")
        lines.append(f"High: {bar.get('h')}")
        lines.append(f"Low: {bar.get('l')}")
        lines.append(f"Close: {bar.get('c')}")
        lines.append(f"Volume: {bar.get('v')}")
        lines.append(f"VWAP: {bar.get('vw')}")
        
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)