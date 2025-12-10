import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from starlette.routing import Mount

from src.app.main import app

# 1. Mock CMC Service for ALL tests
@pytest.fixture(autouse=True)
def mock_cmc_service():
    """
    Automatically mock the CMC service for ALL tests.
    This ensures we never accidentally hit the real API and waste credits.
    """
    with patch("src.tools.crypto.tool.cmc_service") as mock:
        mock.get_quotes.return_value = {"data": {}}
        mock.get_listings.return_value = {"data": []}
        yield mock

@pytest.fixture
def client():
    """
    Creates a TestClient where the API Key is FORCED to be 'secret123'.
    This guarantees tests pass regardless of what is in your .env file.
    """
    found_mount = False
    for route in app.routes:
        if isinstance(route, Mount) and route.path == "/mcp":
            route.app.api_key = "secret123"
            found_mount = True
            break
    
    if not found_mount:
        print("⚠️ Warning: Could not find /mcp route to inject test key.")

    return TestClient(app)

# 3. Auth Headers Helper
@pytest.fixture
def auth_headers():
    return {"X-API-Key": "secret123"}