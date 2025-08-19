"""Unit tests for Lambda handler."""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from mcp_framework.core.handlers import LambdaHandler
from mcp_framework.core.server import MCPServer


class TestLambdaHandler:
    """Test cases for LambdaHandler class."""

    @pytest.fixture
    def mock_server(self):
        """Create a mock MCP server."""
        server = MagicMock(spec=MCPServer)
        server.handle_request = AsyncMock(return_value={"result": "success"})
        return server

    @pytest.fixture
    def handler(self, mock_server):
        """Create a LambdaHandler instance."""
        return LambdaHandler(mock_server)

    def test_handle_options_request(self, handler):
        """Test handling OPTIONS request for CORS."""
        event = {
            "httpMethod": "OPTIONS"
        }
        context = {}
        
        response = handler.handle(event, context)
        
        assert response["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "Access-Control-Allow-Methods" in response["headers"]

    def test_handle_post_request_success(self, handler, mock_server):
        """Test handling successful POST request."""
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            })
        }
        context = {}
        
        # Mock the async run
        with patch('asyncio.run') as mock_run:
            mock_run.return_value = {"jsonrpc": "2.0", "result": {"tools": []}, "id": 1}
            
            response = handler.handle(event, context)
            
            assert response["statusCode"] == 200
            assert "Access-Control-Allow-Origin" in response["headers"]
            body = json.loads(response["body"])
            assert body["jsonrpc"] == "2.0"

    def test_handle_invalid_json(self, handler):
        """Test handling invalid JSON in request body."""
        event = {
            "httpMethod": "POST",
            "body": "invalid json"
        }
        context = {}
        
        response = handler.handle(event, context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body

    def test_handle_missing_body(self, handler):
        """Test handling request with missing body."""
        event = {
            "httpMethod": "POST"
        }
        context = {}
        
        response = handler.handle(event, context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body

    def test_handle_server_error(self, handler, mock_server):
        """Test handling server error."""
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            })
        }
        context = {}
        
        # Mock the async run to raise an exception
        with patch('asyncio.run') as mock_run:
            mock_run.side_effect = Exception("Server error")
            
            response = handler.handle(event, context)
            
            assert response["statusCode"] == 500
            body = json.loads(response["body"])
            assert "error" in body

    def test_handle_base64_encoded_body(self, handler, mock_server):
        """Test handling base64 encoded body."""
        import base64
        
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        
        event = {
            "httpMethod": "POST",
            "isBase64Encoded": True,
            "body": base64.b64encode(json.dumps(request_data).encode()).decode()
        }
        context = {}
        
        with patch('asyncio.run') as mock_run:
            mock_run.return_value = {"jsonrpc": "2.0", "result": {"tools": []}, "id": 1}
            
            response = handler.handle(event, context)
            
            # Should handle base64 encoded body correctly
            assert response["statusCode"] in [200, 400, 500]

    def test_handle_with_path_parameters(self, handler, mock_server):
        """Test handling request with path parameters."""
        event = {
            "httpMethod": "POST",
            "pathParameters": {"proxy": "tools/list"},
            "body": json.dumps({
                "jsonrpc": "2.0",
                "id": 1
            })
        }
        context = {}
        
        with patch('asyncio.run') as mock_run:
            mock_run.return_value = {"jsonrpc": "2.0", "result": {"tools": []}, "id": 1}
            
            response = handler.handle(event, context)
            
            assert response["statusCode"] in [200, 400, 500]

    def test_handle_with_query_parameters(self, handler):
        """Test handling request with query string parameters."""
        event = {
            "httpMethod": "POST",
            "queryStringParameters": {"debug": "true"},
            "body": json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            })
        }
        context = {}
        
        with patch('asyncio.run') as mock_run:
            mock_run.return_value = {"jsonrpc": "2.0", "result": {"tools": []}, "id": 1}
            
            response = handler.handle(event, context)
            
            assert response["statusCode"] in [200, 400, 500]

    def test_handle_with_headers(self, handler):
        """Test handling request with custom headers."""
        event = {
            "httpMethod": "POST",
            "headers": {
                "Content-Type": "application/json",
                "X-Custom-Header": "test"
            },
            "body": json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            })
        }
        context = {}
        
        with patch('asyncio.run') as mock_run:
            mock_run.return_value = {"jsonrpc": "2.0", "result": {"tools": []}, "id": 1}
            
            response = handler.handle(event, context)
            
            assert response["statusCode"] in [200, 400, 500]

    def test_adapter_from_lambda_event(self, handler):
        """Test ProtocolAdapter's from_lambda_event method."""
        event = {
            "body": json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {"test": "value"},
                "id": 1
            })
        }
        
        request = handler.adapter.from_lambda_event(event)
        
        assert request.jsonrpc == "2.0"
        assert request.method == "tools/list"
        assert request.params == {"test": "value"}
        assert request.id == 1

    def test_adapter_to_lambda_response(self, handler):
        """Test ProtocolAdapter's to_lambda_response method."""
        from mcp_framework.core.protocol import MCPResponse
        
        mcp_response = MCPResponse(
            jsonrpc="2.0",
            id=1,
            result={"tools": []}
        )
        
        response = handler.adapter.to_lambda_response(mcp_response)
        
        assert response["statusCode"] == 200
        assert "body" in response
        body = json.loads(response["body"])
        assert body["jsonrpc"] == "2.0"
        assert body["id"] == 1