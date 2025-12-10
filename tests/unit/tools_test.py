from src.tools.crypto.tool import get_crypto_prices, get_top_cryptos

def test_get_crypto_prices_success(mock_cmc_service):
    """Test standard price fetching."""
    # 1. Setup Mock Return
    mock_cmc_service.get_quotes.return_value = {
        "data": {
            "BTC": {
                "name": "Bitcoin",
                "symbol": "BTC",
                "quote": {"USD": {"price": 99000.50}}
            }
        }
    }

    # 2. Call Tool
    result = get_crypto_prices(symbols="BTC")

    # 3. Assert Output format
    assert "Bitcoin (BTC): $99,000.50" in result
    mock_cmc_service.get_quotes.assert_called_with(["BTC"])

def test_get_crypto_prices_validation_error():
    """Test that invalid symbols return an error message immediately."""
    result = get_crypto_prices(symbols="INVALID_SYMBOL_TOO_LONG")
    assert "Input Validation Error" in result

def test_get_top_cryptos_success(mock_cmc_service):
    """Test top list fetching."""
    mock_cmc_service.get_listings.return_value = {
        "data": [
            {
                "cmc_rank": 1,
                "name": "Bitcoin",
                "symbol": "BTC",
                "quote": {"USD": {"price": 100.00}}
            }
        ]
    }

    result = get_top_cryptos(limit=5)

    assert "Top 5 Cryptocurrencies" in result
    assert "#1 Bitcoin (BTC): $100.00" in result
    mock_cmc_service.get_listings.assert_called_with(5)