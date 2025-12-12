import pytest
from unittest.mock import MagicMock, patch
from src.tools.forex import tool

# --- Fixtures ---

@pytest.fixture
def mock_service():
    """
    Patches the singleton 'forex_service' inside the tool module.
    """
    with patch("src.tools.forex.tool.forex_service") as mock:
        yield mock

# --- Validation Tests ---

def test_ticker_validation_success():
    """Test that valid tickers (standard and prefixed) are accepted."""
    # Should not raise validation error
    assert "Input Validation Error" not in tool.get_forex_last_quote("EURUSD")
    assert "Input Validation Error" not in tool.get_forex_last_quote("C:EURUSD")
    assert "Input Validation Error" not in tool.get_forex_last_quote("X:BTCUSD")

def test_ticker_validation_failure():
    """Test that invalid tickers are rejected."""
    result = tool.get_forex_last_quote("INVALID_TICKER_TOO_LONG")
    assert "Input Validation Error" in result
    
    result = tool.get_forex_last_quote("EU") # Too short
    assert "Input Validation Error" in result

# --- Functional Tests ---

def test_get_forex_tickers(mock_service):
    # Setup Mock
    mock_service.get_tickers.return_value = {
        "results": [
            {"ticker": "C:EURUSD", "name": "Euro / US Dollar", "locale": "global"},
            {"ticker": "C:GBPUSD", "name": "British Pound / US Dollar", "locale": "global"}
        ]
    }

    # Execute
    result = tool.get_forex_tickers(limit=2)

    # Assert
    assert "Forex Tickers" in result
    assert "C:EURUSD - Euro / US Dollar" in result
    assert "C:GBPUSD" in result
    mock_service.get_tickers.assert_called_once()

def test_get_forex_conversion(mock_service):
    mock_service.get_conversion.return_value = {
        "converted": 110.50,
        "last": {"ask": 1.1050}
    }

    result = tool.get_forex_conversion(from_currency="EUR", to_currency="USD", amount=100)

    assert "100.0 EUR -> USD" in result
    assert "Result: 110.5000 USD" in result
    mock_service.get_conversion.assert_called_with("EUR", "USD", {"amount": 100.0})

def test_get_forex_last_quote_success(mock_service):
    mock_service.get_last_quote.return_value = {
        "ticker": "C:EURUSD",
        "bid": 1.0500,
        "ask": 1.0502,
        "timestamp": 123456789
    }

    result = tool.get_forex_last_quote("EURUSD")

    assert "Last Quote for EURUSD" in result
    assert "Bid: 1.05" in result
    assert "Ask: 1.0502" in result

def test_get_forex_last_quote_restricted(mock_service):
    """Test the fallback message when API returns empty bid/ask (Free Tier)."""
    mock_service.get_last_quote.return_value = {
        "ticker": "C:EURUSD",
        # Missing bid/ask keys
        "status": "OK"
    }

    result = tool.get_forex_last_quote("EURUSD")

    assert "unavailable on the current API plan" in result
    assert "Please use 'get_forex_prev_close'" in result

def test_get_forex_market_status(mock_service):
    mock_service.get_market_status.return_value = {
        "market": "forex",
        "status": "open",
        "exchanges": {"open": True}
    }

    result = tool.get_forex_market_status()

    assert "Forex Market Status" in result
    assert "Status: open" in result

def test_get_forex_movers(mock_service):
    mock_service.get_market_movers.return_value = {
        "tickers": [
            {"ticker": "C:EURUSD", "todaysChangePerc": 0.5, "day": {"c": 1.05}}
        ]
    }

    result = tool.get_forex_movers("gainers")

    assert "Top Forex Gainers" in result
    assert "C:EURUSD | Change: 0.50%" in result

def test_get_forex_prev_close(mock_service):
    mock_service.get_prev_day.return_value = {
        "results": [
            {"o": 1.1, "h": 1.2, "l": 1.0, "c": 1.15, "v": 1000}
        ]
    }

    result = tool.get_forex_prev_close("EURUSD")

    assert "Previous Day Close for EURUSD" in result
    assert "Close: 1.15" in result
    # Check that service prefixed it correctly (logic in service, but we mock call)
    mock_service.get_prev_day.assert_called_with("EURUSD")

def test_get_forex_prev_close_empty(mock_service):
    mock_service.get_prev_day.return_value = {"results": []}
    result = tool.get_forex_prev_close("EURUSD")
    assert "No previous day data found" in result

def test_get_forex_history(mock_service):
    mock_service.get_custom_bars.return_value = {
        "results": [
            {"t": 1700000000, "o": 1.1, "c": 1.2}
        ]
    }

    result = tool.get_forex_history("EURUSD", from_date="2024-01-01", to_date="2024-01-02")

    assert "Historical Data for EURUSD" in result
    assert "TS: 1700000000" in result
    assert "C: 1.2" in result

def test_get_forex_indicator(mock_service):
    mock_service.get_rsi.return_value = {
        "results": {
            "values": [
                {"timestamp": 12345, "value": 55.5}
            ]
        }
    }

    result = tool.get_forex_indicator("rsi", "EURUSD")

    assert "RSI Indicator for EURUSD" in result
    assert "Value: 55.5" in result
    mock_service.get_rsi.assert_called_once()

def test_get_forex_indicator_unsupported(mock_service):
    result = tool.get_forex_indicator("invalid_ind", "EURUSD")
    assert "Error: Unsupported indicator type" in result

def test_get_forex_exchanges(mock_service):
    mock_service.get_exchanges.return_value = {
        "results": [
            {"id": 1, "name": "ForexExchange", "type": "TRADING"}
        ]
    }

    result = tool.get_forex_exchanges()

    assert "Forex Exchanges" in result
    assert "Name: ForexExchange" in result

# --- Error Handling Tests ---

def test_api_error_handling(mock_service):
    """Test that exceptions are passed to handle_api_error."""

    error_msg = "API Key Invalid"
    mock_service.get_tickers.side_effect = Exception(error_msg)
    
    with patch("src.tools.forex.tool.handle_api_error") as mock_handler:
        mock_handler.return_value = f"Mocked Error: {error_msg}"
        result = tool.get_forex_tickers()
        
        assert f"Mocked Error: {error_msg}" in result
        mock_handler.assert_called_once()