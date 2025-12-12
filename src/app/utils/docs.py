from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

def custom_openapi(app: FastAPI):
    """
    Wraps the default OpenAPI generator to inject:
    1. The 'Authorize' button (API Key).
    2. The hidden MCP routes (/mcp/sse, /mcp/messages).
    """
    def _openapi():
        if app.openapi_schema:
            return app.openapi_schema

        # 1. Generate the standard schema (includes /health, etc.)
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # 2. Define the Security Scheme (x-api-key header)
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        
        openapi_schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "x-api-key",
                "description": "Enter your MCP Server API Key"
            }
        }

        # 3. Manually Add the MCP Routes
        mcp_paths = {
            "/mcp/sse": {
                "get": {
                    "tags": ["MCP Protocol"],
                    "summary": "MCP Event Stream (SSE)",
                    "description": "Connects to the Server-Sent Events stream for MCP.",
                    "operationId": "mcp_sse_connect",
                    "security": [{"ApiKeyAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Stream opened successfully",
                            "content": {"text/event-stream": {}}
                        }
                    }
                }
            },
            "/mcp/messages": {
                "post": {
                    "tags": ["MCP Protocol"],
                    "summary": "MCP JSON-RPC Endpoint",
                    "description": "Send JSON-RPC messages to interact with tools/resources.",
                    "operationId": "mcp_send_message",
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "jsonrpc": {"type": "string", "example": "2.0"},
                                        "method": {"type": "string", "example": "tools/list"},
                                        "params": {"type": "object"},
                                        "id": {"type": "integer", "example": 1}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "JSON-RPC Response",
                            "content": {"application/json": {}}
                        }
                    }
                }
            }
        }

        # 4. Merge paths
        # We use .setdefault just in case, though usually 'paths' exists
        openapi_schema.setdefault("paths", {}).update(mcp_paths)

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return _openapi