"""Unit tests for protocol classes and adapters."""

import pytest
import json
from mcp_framework.core.protocol import (
    MCPRequest, MCPResponse, MCPError, MCPMethod, ProtocolAdapter
)


class TestMCPRequest:
    """Test cases for MCPRequest class."""

    def test_create_request(self):
        """Test creating an MCP request."""
        request = MCPRequest(
            id=1,
            method="tools/list",
            params={"test": "value"}
        )
        
        assert request.jsonrpc == "2.0"
        assert request.id == 1
        assert request.method == "tools/list"
        assert request.params == {"test": "value"}

    def test_create_request_without_params(self):
        """Test creating an MCP request without params."""
        request = MCPRequest(
            id=2,
            method="tools/list"
        )
        
        assert request.jsonrpc == "2.0"
        assert request.id == 2
        assert request.method == "tools/list"
        assert request.params is None

    def test_request_with_string_id(self):
        """Test creating an MCP request with string ID."""
        request = MCPRequest(
            id="abc-123",
            method="tools/call"
        )
        
        assert request.id == "abc-123"


class TestMCPResponse:
    """Test cases for MCPResponse class."""

    def test_create_success_response(self):
        """Test creating a success response."""
        response = MCPResponse(
            id=1,
            result={"data": "test"}
        )
        
        assert response.jsonrpc == "2.0"
        assert response.id == 1
        assert response.result == {"data": "test"}
        assert response.error is None

    def test_create_error_response(self):
        """Test creating an error response."""
        response = MCPResponse(
            id=2,
            error={"code": -32601, "message": "Method not found"}
        )
        
        assert response.jsonrpc == "2.0"
        assert response.id == 2
        assert response.result is None
        assert response.error["code"] == -32601
        assert response.error["message"] == "Method not found"


class TestMCPError:
    """Test cases for MCPError class."""

    def test_create_error(self):
        """Test creating an MCP error."""
        error = MCPError(
            code=-32602,
            message="Invalid params"
        )
        
        assert error.code == -32602
        assert error.message == "Invalid params"
        assert error.data is None

    def test_create_error_with_data(self):
        """Test creating an MCP error with additional data."""
        error = MCPError(
            code=-32603,
            message="Internal error",
            data={"details": "Database connection failed"}
        )
        
        assert error.code == -32603
        assert error.message == "Internal error"
        assert error.data == {"details": "Database connection failed"}


class TestMCPMethod:
    """Test cases for MCPMethod enum."""

    def test_method_values(self):
        """Test MCP method enum values."""
        assert MCPMethod.INITIALIZE == "initialize"
        assert MCPMethod.LIST_TOOLS == "tools/list"
        assert MCPMethod.CALL_TOOL == "tools/call"
        assert MCPMethod.LIST_RESOURCES == "resources/list"
        assert MCPMethod.READ_RESOURCE == "resources/read"
        assert MCPMethod.LIST_PROMPTS == "prompts/list"
        assert MCPMethod.GET_PROMPT == "prompts/get"

    def test_method_as_string(self):
        """Test using MCP method as string."""
        method = MCPMethod.LIST_TOOLS
        assert str(method) == "tools/list"
        assert method.value == "tools/list"


class TestProtocolAdapter:
    """Test cases for ProtocolAdapter class."""

    @pytest.fixture
    def adapter(self):
        """Create a ProtocolAdapter instance."""
        return ProtocolAdapter()

    def test_from_lambda_event(self, adapter):
        """Test converting Lambda event to MCP request."""
        event = {
            "body": json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {"test": "value"},
                "id": 1
            })
        }
        
        request = adapter.from_lambda_event(event)
        
        assert isinstance(request, MCPRequest)
        assert request.jsonrpc == "2.0"
        assert request.method == "tools/list"
        assert request.params == {"test": "value"}
        assert request.id == 1

    def test_from_lambda_event_no_params(self, adapter):
        """Test converting Lambda event without params."""
        event = {
            "body": json.dumps({
                "jsonrpc": "2.0",
                "method": "initialize",
                "id": 2
            })
        }
        
        request = adapter.from_lambda_event(event)
        
        assert isinstance(request, MCPRequest)
        assert request.method == "initialize"
        assert request.params is None

    def test_to_lambda_response_success(self, adapter):
        """Test converting MCP response to Lambda response."""
        mcp_response = MCPResponse(
            id=1,
            result={"tools": []}
        )
        
        response = adapter.to_lambda_response(mcp_response)
        
        assert response["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        
        body = json.loads(response["body"])
        assert body["jsonrpc"] == "2.0"
        assert body["id"] == 1
        assert body["result"] == {"tools": []}

    def test_to_lambda_response_error(self, adapter):
        """Test converting MCP error response to Lambda response."""
        mcp_response = MCPResponse(
            id=2,
            error={"code": -32601, "message": "Method not found"}
        )
        
        response = adapter.to_lambda_response(mcp_response)
        
        # Error responses should still return 200 for JSON-RPC
        assert response["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in response["headers"]
        
        body = json.loads(response["body"])
        assert body["jsonrpc"] == "2.0"
        assert body["id"] == 2
        assert body["error"]["code"] == -32601
        assert body["error"]["message"] == "Method not found"

    def test_to_lambda_response_with_complex_result(self, adapter):
        """Test converting response with complex result."""
        mcp_response = MCPResponse(
            id=3,
            result={
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "A test tool",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "input": {"type": "string"}
                            },
                            "required": ["input"]
                        }
                    }
                ]
            }
        )
        
        response = adapter.to_lambda_response(mcp_response)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body["result"]["tools"]) == 1
        assert body["result"]["tools"][0]["name"] == "test_tool"

    def test_from_lambda_event_invalid_json(self, adapter):
        """Test handling invalid JSON in Lambda event."""
        event = {
            "body": "invalid json"
        }
        
        # Should raise an exception or handle gracefully
        with pytest.raises(Exception):
            adapter.from_lambda_event(event)

    def test_from_lambda_event_missing_body(self, adapter):
        """Test handling missing body in Lambda event."""
        event = {}
        
        # Should raise an exception or handle gracefully
        with pytest.raises(Exception):
            adapter.from_lambda_event(event)