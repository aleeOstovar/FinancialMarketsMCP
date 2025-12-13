from datetime import datetime
from typing import Annotated, Any, List
from pydantic import Field, ValidationError

# Internal Imports
from src.tools.forex.service import MassiveForexService
from src.tools.forex.schemas import (
    ForexTickerInput, TickersListInput, ConversionInput, HistoricalQuotesInput,
    MarketMoversInput, CustomBarsInput, IndicatorInput, ExchangesInput, MarketSnapshotInput
)
from src.common.exceptions import handle_api_error
from src.common.settings import get_settings
from src.common.decorators import monitor_tool

forex_service = MassiveForexService()
settings = get_settings()


def _get_val(obj, key, default=None):
    """Safely get value from Dict or Object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

@monitor_tool
async def get_forex_tickers(
    limit: Annotated[int, Field(100, description="Number of tickers (1-1000)")] = 100
) -> str:
    """[Forex] Retrieve a comprehensive list of supported forex currency pairs."""
    try:
        validated = TickersListInput(limit=limit)
        results = await forex_service.get_tickers({"limit": validated.limit})
        
        lines = [f"Forex Tickers (Top {limit}):", "-" * 50]
        for item in results:
            ticker = getattr(item, 'ticker', 'N/A')
            name = getattr(item, 'name', 'N/A')
            locale = getattr(item, 'locale', 'N/A')
            lines.append(f"{ticker} - {name} ({locale})")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

@monitor_tool
async def get_forex_conversion(
    from_currency: Annotated[str, Field(description="Source Currency (e.g. USD)")],
    to_currency: Annotated[str, Field(description="Target Currency (e.g. EUR)")],
    amount: Annotated[float, Field(1.0, description="Amount to convert")] = 1.0
) -> str:
    """[Forex] Real-time conversion between two currencies."""
    try:
        validated = ConversionInput(from_currency=from_currency, to_currency=to_currency, amount=amount)
        res = await forex_service.get_conversion(validated.from_currency, validated.to_currency, {"amount": validated.amount})
        
        converted = getattr(res, 'converted', 0)
        last_obj = getattr(res, 'last', None)
        rate = getattr(last_obj, 'ask', 0) if last_obj else 0
        
        lines = ["Currency Conversion:", "-" * 50]
        lines.append(f"{validated.amount} {validated.from_currency} -> {validated.to_currency}")
        lines.append(f"Result: {converted:,.4f} {validated.to_currency}")
        lines.append(f"Rate: {rate:,.4f}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

@monitor_tool
async def get_forex_last_quote(
    ticker: Annotated[str, Field(description="Forex Pair (e.g. EURUSD)")]
) -> str:
    """[Forex] Get the most recent bid/ask quote for a currency pair."""
    try:
        validated = ForexTickerInput(ticker=ticker)
        response_obj = await forex_service.get_last_quote(validated.ticker)
        last_data = getattr(response_obj, 'last', None)

        if not last_data:
            return (f"Note: Real-time Bid/Ask quotes for {validated.ticker} are unavailable or returned no data. "
                    "Please use 'get_forex_prev_close' for daily data.")

        # Access attributes on the nested 'last' object
        bid = getattr(last_data, 'bid', None)
        ask = getattr(last_data, 'ask', None)
        timestamp = getattr(last_data, 'timestamp', 'N/A')

        # Safety check for empty values 
        if not bid and not ask:
            return f"No active quote data found for {validated.ticker}."

        lines = [f"Last Quote for {validated.ticker}:", "-" * 50]
        lines.append(f"Bid: {bid}")
        lines.append(f"Ask: {ask}")
        lines.append(f"Timestamp: {timestamp}")
        
        return "\n".join(lines)

    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

@monitor_tool
async def get_forex_market_status() -> str:
    """[Forex] Get current trading status for forex markets."""
    try:
        res = await forex_service.get_market_status()
        
        market = getattr(res, 'market', 'N/A')
        status = getattr(res, 'status', 'N/A') 
        exchanges_open = getattr(getattr(res, 'exchanges', None), 'open', 'N/A')
        
        lines = ["Forex Market Status:", "-" * 50]
        lines.append(f"Market: {market}")
        lines.append(f"Status: {status}")
        lines.append(f"Exchanges Open: {exchanges_open}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

@monitor_tool
async def get_forex_snapshot(
    ticker: Annotated[str, Field(description="Forex Pair (e.g. EURUSD)")]
) -> str:
    """[Forex] Get a comprehensive market data snapshot for a single ticker."""
    try:
        validated = ForexTickerInput(ticker=ticker)
        snap = await forex_service.get_snapshot_ticker(validated.ticker)
        
        ticker_name = getattr(snap, 'ticker', validated.ticker)

        # JSON 'lastQuote' -> Object 'last_quote'
        last_quote = getattr(snap, 'last_quote', None)
        day = getattr(snap, 'day', None)
        prev_day = getattr(snap, 'prev_day', None)
        min_bar = getattr(snap, 'min', None)

        price = "N/A"
        if last_quote:
            ask = getattr(last_quote, 'ask', 0) or getattr(last_quote, 'a', 0)
            bid = getattr(last_quote, 'bid', 0) or getattr(last_quote, 'b', 0)
            if ask and bid:
                price = f"{(ask + bid) / 2:.5f} (Mid)"

        if price == "N/A" and min_bar:
            c = getattr(min_bar, 'close', 0) or getattr(min_bar, 'c', 0)
            if c: price = f"{c} (Last Min)"

        if price == "N/A" and day:
            c = getattr(day, 'close', 0) or getattr(day, 'c', 0)
            if c: price = f"{c} (Day Close)"

        if price == "N/A" and prev_day:
            c = getattr(prev_day, 'close', 0) or getattr(prev_day, 'c', 0)
            if c: price = f"{c} (Prev Close)"

        change = getattr(snap, 'todays_change_perc', 0)

        if change is None: 
            change = getattr(snap, 'todays_change_percent', 0)
            

        vol = getattr(day, 'v', 0) or getattr(day, 'volume', 0)
        if not vol and prev_day:
            vol = getattr(prev_day, 'v', 0) or getattr(prev_day, 'volume', 0)

        lines = [f"Snapshot for {ticker_name}:", "-" * 50]
        lines.append(f"Price: {price}")
        lines.append(f"Change: {change:.2f}%")
        lines.append(f"Volume: {vol:,.0f}")
        return "\n".join(lines)

    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)


@monitor_tool
async def get_forex_movers(
    direction: Annotated[str, Field(description="Direction: 'gainers' or 'losers'")]
) -> str:
    """[Forex] Get top market movers (gainers/losers)."""
    try:
        validated = MarketMoversInput(direction=direction)
        results = await forex_service.get_market_movers(validated.direction)
        
        lines = [f"Top Forex {validated.direction.capitalize()}:", "=" * 50]
        
        for t in results[:10]:
            ticker = getattr(t, 'ticker', 'N/A')
            
            # Try Native API Change
            change = getattr(t, 'todays_change_percent', getattr(t, 'todays_change_perc', 0))
            
            # 2. Extract Price Data
            day = getattr(t, 'day', None)
            price = getattr(day, 'c', getattr(day, 'close', 0)) if day else 0
            
            # Fallback Logic: If API says 0% change
            # We calculate change based on Previous Day's Open vs Close
            if change == 0:
                prev_day = getattr(t, 'prev_day', None)
                if prev_day:
                    o = getattr(prev_day, 'o', getattr(prev_day, 'open', 0))
                    c = getattr(prev_day, 'c', getattr(prev_day, 'close', 0))
                    
                    if o and c and o != 0:
                        change = ((c - o) / o) * 100
                        if price == 0:
                            price = c

            lines.append(f"{ticker} | Change: {change:.2f}% | Price: {price}")
            
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

@monitor_tool
async def get_forex_history(
    ticker: Annotated[str, Field(description="Forex Pair (e.g. EURUSD)")],
    multiplier: Annotated[int, Field(1, description="Time interval")] = 1,
    timespan: Annotated[str, Field("day", description="minute, hour, day")] = "day",
    from_date: Annotated[str, Field(description="YYYY-MM-DD")] = "2024-01-01",
    to_date: Annotated[str, Field(description="YYYY-MM-DD")] = "2024-01-07"
) -> str:
    """[Forex] Get historical OHLC bars for a custom range."""
    try:
        validated = CustomBarsInput(ticker=ticker, multiplier=multiplier, timespan=timespan, from_date=from_date, to_date=to_date)
        results = await forex_service.get_custom_bars(
            validated.ticker, validated.multiplier, validated.timespan, validated.from_date, validated.to_date, {}
        )
        
        lines = [f"Historical Data for {validated.ticker} ({validated.multiplier} {validated.timespan}):", "-" * 50]
        if not results:
            return "No data found for this range."
            
        for bar in results[:20]:
            ts = getattr(bar, 'timestamp', 0)
            o = getattr(bar, 'open', 0)
            c = getattr(bar, 'close', 0)
            h = getattr(bar, 'high', 0)
            l = getattr(bar, 'low', 0)
            lines.append(f"TS: {ts} | O: {o} | H: {h} | L: {l} | C: {c}")
        
        if len(results) > 20:
            lines.append(f"... (+{len(results)-20} more records)")
            
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

@monitor_tool
async def get_forex_historical_quotes(
    ticker: Annotated[str, Field(description="Forex Pair (e.g. EURUSD)")],
    timestamp: Annotated[str | None, Field(None, description="YYYY-MM-DD")] = None,
    limit: Annotated[int, Field(100, description="Max results")] = 100
) -> str:
    """[Forex] Retrieve historical Bid/Ask (BBO) quotes."""
    try:
        if not timestamp or str(timestamp).lower() == "none":
            timestamp = datetime.now().strftime("%Y-%m-%d")
            
        validated = HistoricalQuotesInput(ticker=ticker, timestamp=timestamp, limit=limit)

        params = {
            "limit": validated.limit,
            "timestamp": validated.timestamp
        }

        # Call Service
        results = await forex_service.get_historical_quotes(validated.ticker, params)

        if not results:
            return f"No historical quotes found for {validated.ticker} on {validated.timestamp}."

        lines = [f"Historical Quotes (BBO) for {validated.ticker} on {validated.timestamp}:", "-" * 50]
        
        for q in results[:20]:
            # Use Hybrid Accessor
            # Keys match the JSON output you showed from Playground
            ts = _get_val(q, 'participant_timestamp') or _get_val(q, 'timestamp', 'N/A')
            bid = _get_val(q, 'bid_price') or _get_val(q, 'bid', 'N/A')
            ask = _get_val(q, 'ask_price') or _get_val(q, 'ask', 'N/A')
            
            lines.append(f"Time: {ts} | Bid: {bid} | Ask: {ask}")
        
        if len(results) > 20:
            lines.append(f"... (+{len(results)-20} more records)")

        return "\n".join(lines)
        
    except Exception as e:
        if "timed out" in str(e).lower():
            return "Error: Request timed out. Try specifying a narrower date range."
        return handle_api_error(e, settings.MASSIVE_API_KEY)

@monitor_tool
async def get_forex_indicator(
    indicator: Annotated[str, Field(description="Type: sma, ema, macd, rsi, bollinger")],
    ticker: Annotated[str, Field(description="Forex Pair")],
    timespan: Annotated[str, Field("day")] = "day",
    window: Annotated[int, Field(14)] = 14
) -> str:
    """[Forex] Calculate technical indicators (SMA, EMA, RSI, MACD, Bollinger)."""
    try:
        validated = IndicatorInput(ticker=ticker, timespan=timespan, window=window)
        params = {"timespan": validated.timespan, "window": validated.window, "series_type": validated.series_type, "limit": validated.limit}

        if indicator.lower() == "sma": res = await forex_service.get_sma(validated.ticker, params)
        elif indicator.lower() == "ema": res = await forex_service.get_ema(validated.ticker, params)
        elif indicator.lower() == "macd": res = await forex_service.get_macd(validated.ticker, params)
        elif indicator.lower() == "rsi": res = await forex_service.get_rsi(validated.ticker, params)
        elif indicator.lower() == "bollinger": res = await forex_service.get_bollinger(validated.ticker, params)
        else: return "Error: Unsupported indicator type."

        values = getattr(res, 'values', [])
        lines = [f"{indicator.upper()} Indicator for {validated.ticker}:", "-" * 50]
        
        for val in values[:10]:
            ts = getattr(val, 'timestamp', 'N/A')
            v = getattr(val, 'value', 'N/A')
            lines.append(f"Date: {ts} | Value: {v}")
            
        return "\n".join(lines)

    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)
    
@monitor_tool
async def get_forex_exchanges(
    asset_class: Annotated[str, Field("fx")] = "fx",
    locale: Annotated[str, Field("global")] = "global"
) -> str:
    """[Forex] Retrieve a list of known forex exchanges."""
    try:
        validated = ExchangesInput(asset_class=asset_class, locale=locale)
        results = await forex_service.get_exchanges({"asset_class": validated.asset_class, "locale": validated.locale})

        if not results: return "No exchanges found."

        lines = ["Forex Exchanges:", "-" * 50]
        for ex in results:
            name = getattr(ex, 'name', 'N/A')
            type_ = getattr(ex, 'type', 'N/A')
            id_ = getattr(ex, 'id', 'N/A')
            lines.append(f"ID: {id_} | Name: {name} | Type: {type_}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)
    
@monitor_tool
async def get_forex_market_snapshot(
    tickers: Annotated[str | None, Field(None)] = None,
    limit: Annotated[int, Field(100)] = 100
) -> str:
    """[Forex] Retrieve a comprehensive snapshot of the entire forex market."""
    try:
        validated = MarketSnapshotInput(tickers=tickers, limit=limit)
        params = {"tickers": validated.tickers}
        results = await forex_service.get_snapshot_all(params)

        if not results: return "No snapshot data available."

        lines = [f"Market Snapshot:", "-" * 50]
        
        for t in results[:validated.limit]:
            tick = getattr(t, 'ticker', 'N/A')
            price = getattr(getattr(t, 'last_trade', None), 'p', 'N/A')
            change = getattr(t, 'todays_change_percent', getattr(t, 'todays_change_perc', 0))
            
            lines.append(f"{tick}: {price} ({change:.2f}%)")
        
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)
    
@monitor_tool
async def get_forex_prev_close(
    ticker: Annotated[str, Field(description="Forex Pair (e.g. EURUSD)")]
) -> str:
    """[Forex] Retrieve the previous trading day's OHLC data for a currency pair."""
    try:
        validated = ForexTickerInput(ticker=ticker)
        res = await forex_service.get_prev_day(validated.ticker)
        if isinstance(res, list):
            if not res: return "No previous day data found."
            bar = res[0]
        else:
            bar = res

        o = getattr(bar, 'open', 'N/A')
        h = getattr(bar, 'high', 'N/A')
        l = getattr(bar, 'low', 'N/A')
        c = getattr(bar, 'close', 'N/A')
        v = getattr(bar, 'volume', 'N/A')
        
        lines = [f"Previous Day Close for {validated.ticker}:", "-" * 50]
        lines.append(f"Open: {o} | High: {h} | Low: {l} | Close: {c}")
        lines.append(f"Volume: {v}")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)

@monitor_tool
async def get_forex_market_holidays() -> str:
    """
    [Forex] Retrieve upcoming market holidays and trading hour adjustments.
    Use this to plan for market closures or early closes.
    """
    try:
        holidays = await forex_service.get_market_holidays()

        if not holidays:
            return "No upcoming market holidays found."

        lines = ["Upcoming Market Holidays & Adjustments:", "-" * 50]
        
        for h in holidays:
            name = getattr(h, 'name', 'Holiday')
            h_date = getattr(h, 'date', 'N/A')
            status = getattr(h, 'status', 'N/A')
            exch = getattr(h, 'exchange', 'N/A')
            
            msg = f"{h_date}: {name} ({exch}) - Status: {status.upper()}"
            
            if hasattr(h, 'open') and h.open:
                msg += f" | Hours: {h.open} to {getattr(h, 'close', '?')}"
                
            lines.append(msg)

        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, settings.MASSIVE_API_KEY)