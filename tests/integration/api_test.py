from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    """Test public health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_mcp_sse_unauthorized(client: TestClient):
    """Test that missing API key returns 403."""
    # Override settings to ensure auth is enabled for this test
    # (Assuming your test settings enable auth)
    response = client.get("/mcp/sse")
    # Note: Depending on how settings are mocked, this might be 403 or 401
    assert response.status_code in [401, 403]

def test_mcp_auth_success(client, auth_headers):
    """
    Test that valid API key allows access.
    We test against the POST endpoint because it returns immediately,
    whereas the SSE endpoint hangs open (infinite stream), causing tests to get stuck.
    """
    # 1. Send a dummy handshake (Initialize)
    # We don't care if the handshake fails logic-wise, 
    # we only care that we got past the 403 Forbidden check.
    payload = {
        "jsonrpc": "2.0", 
        "id": 0, 
        "method": "initialize", 
        "params": {
            "protocolVersion": "2024-11-05", 
            "capabilities": {}, 
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    
    response = client.post("/mcp/messages/?session_id=test_session", json=payload, headers=auth_headers)