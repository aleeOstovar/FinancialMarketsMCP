import pytest
from unittest.mock import patch, Mock
from requests.exceptions import HTTPError
from src.tools.crypto.service import CoinMarketCapService

# Sample API Response
SAMPLE_QUOTE_RESPONSE = {
    "data": {
        "BTC": {
            "name": "Bitcoin",
            "quote": {"USD": {"price": 50000.00}}
        }
    }
}

class TestCoinMarketCapService:

    @pytest.fixture
    def service(self):
        # We patch get_settings to avoid needing a real .env file during tests
        with patch("src.tools.crypto.service.get_settings") as mock_settings:
            mock_settings.return_value.COINMARKETCAP_API_KEY = "test_key"
            mock_settings.return_value.COINMARKETCAP_BASE_URL = "http://test-api"
            return CoinMarketCapService()

    def test_get_quotes_success(self, service):
        """Test that get_quotes returns data correctly."""
        with patch("requests.get") as mock_get:
            # Setup Mock
            mock_response = Mock()
            mock_response.json.return_value = SAMPLE_QUOTE_RESPONSE
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            # Run Method
            result = service.get_quotes(["BTC"])

            # Verify
            assert result == SAMPLE_QUOTE_RESPONSE
            mock_get.assert_called_once()
            # Check if headers contain the key
            assert mock_get.call_args[1]['headers']['X-CMC_PRO_API_KEY'] == "test_key"

    def test_api_failure(self, service):
        """Test that HTTP errors are raised."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = HTTPError("401 Unauthorized")
            mock_get.return_value = mock_response

            with pytest.raises(HTTPError):
                service.get_quotes(["BTC"])