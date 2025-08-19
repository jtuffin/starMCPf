"""Unit tests for the simplified API."""

import pytest
import asyncio
import json
from mcp_framework.simplified import tool, resource, prompt, handle_request


class TestSimplifiedDecorators:
    """Test cases for the simplified MCP decorators."""

    def test_tool_decorator(self):
        """Test tool decorator registration."""
        from mcp_framework.simplified import _tools
        
        # Clear any existing tools
        _tools.clear()
        
        @tool("test_tool", "A test tool")
        async def test_tool_func(text: str) -> dict:
            return {"result": text.upper()}
        
        assert "test_tool" in _tools
        assert _tools["test_tool"]["name"] == "test_tool"
        assert _tools["test_tool"]["description"] == "A test tool"
        assert callable(_tools["test_tool"]["handler"])

    def test_tool_decorator_with_parameters(self):
        """Test tool decorator with explicit parameters."""
        from mcp_framework.simplified import _tools
        
        _tools.clear()
        
        params = {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        }
        
        @tool("param_tool", "Tool with params", parameters=params)
        async def param_tool_func(input: str) -> dict:
            return {"output": input}
        
        assert "param_tool" in _tools
        assert _tools["param_tool"]["parameters"] == params

    def test_tool_auto_parameters(self):
        """Test tool decorator auto-generating parameters."""
        from mcp_framework.simplified import _tools
        
        _tools.clear()
        
        @tool("auto_param_tool", "Tool with auto params")
        async def auto_param_tool(text: str, count: int = 5) -> dict:
            return {"text": text, "count": count}
        
        tool_info = _tools["auto_param_tool"]
        assert "parameters" in tool_info
        params = tool_info["parameters"]
        assert params["type"] == "object"
        assert "text" in params["properties"]
        assert "count" in params["properties"]
        assert "text" in params["required"]
        assert "count" not in params["required"]  # Has default value

    def test_resource_decorator(self):
        """Test resource decorator registration."""
        from mcp_framework.simplified import _resources
        
        _resources.clear()
        
        @resource("test://data", "Test resource")
        async def test_resource_func() -> dict:
            return {"data": "test data"}
        
        assert "test://data" in _resources
        assert _resources["test://data"]["uri"] == "test://data"
        assert _resources["test://data"]["name"] == "Test resource"
        assert callable(_resources["test://data"]["handler"])

    def test_prompt_decorator(self):
        """Test prompt decorator registration."""
        from mcp_framework.simplified import _prompts
        
        _prompts.clear()
        
        @prompt("test_prompt", "A test prompt")
        async def test_prompt_func(topic: str) -> str:
            return f"Tell me about {topic}"
        
        assert "test_prompt" in _prompts
        assert _prompts["test_prompt"]["name"] == "test_prompt"
        assert _prompts["test_prompt"]["description"] == "A test prompt"
        assert callable(_prompts["test_prompt"]["handler"])


class TestHandleRequest:
    """Test cases for the handle_request function."""

    @pytest.fixture
    def setup_handlers(self):
        """Set up test handlers."""
        from mcp_framework.simplified import _tools, _resources, _prompts
        
        # Clear existing handlers
        _tools.clear()
        _resources.clear()
        _prompts.clear()
        
        # Add test tool
        @tool("test_tool", "A test tool")
        async def test_tool_func(text: str) -> dict:
            return {"result": text.upper()}
        
        # Add test resource
        @resource("test://data", "Test resource")
        async def test_resource_func() -> dict:
            return {"data": "test data"}
        
        # Add test prompt
        @prompt("test_prompt", "A test prompt")
        async def test_prompt_func(topic: str) -> str:
            return f"Tell me about {topic}"

    @pytest.mark.asyncio
    async def test_handle_initialize(self, setup_handlers):
        """Test handling initialize request."""
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {}
            },
            "id": 1
        }
        
        response = await handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["protocolVersion"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_handle_tools_list(self, setup_handlers):
        """Test handling tools/list request."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 2
        }
        
        response = await handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response
        assert "tools" in response["result"]
        tools = response["result"]["tools"]
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_handle_tools_call(self, setup_handlers):
        """Test handling tools/call request."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "test_tool",
                "arguments": {"text": "hello"}
            },
            "id": 3
        }
        
        response = await handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "result" in response
        assert "content" in response["result"]
        content = response["result"]["content"]
        assert len(content) == 1
        assert content[0]["type"] == "text"
        assert '"result": "HELLO"' in content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_resources_list(self, setup_handlers):
        """Test handling resources/list request."""
        request = {
            "jsonrpc": "2.0",
            "method": "resources/list",
            "id": 4
        }
        
        response = await handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 4
        assert "result" in response
        assert "resources" in response["result"]
        resources = response["result"]["resources"]
        assert len(resources) == 1
        assert resources[0]["uri"] == "test://data"

    @pytest.mark.asyncio
    async def test_handle_resources_read(self, setup_handlers):
        """Test handling resources/read request."""
        request = {
            "jsonrpc": "2.0",
            "method": "resources/read",
            "params": {
                "uri": "test://data"
            },
            "id": 5
        }
        
        response = await handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 5
        assert "result" in response
        assert "contents" in response["result"]
        contents = response["result"]["contents"]
        assert len(contents) == 1
        assert contents[0]["uri"] == "test://data"
        assert '"data": "test data"' in contents[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_prompts_list(self, setup_handlers):
        """Test handling prompts/list request."""
        request = {
            "jsonrpc": "2.0",
            "method": "prompts/list",
            "id": 6
        }
        
        response = await handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 6
        assert "result" in response
        assert "prompts" in response["result"]
        prompts = response["result"]["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["name"] == "test_prompt"

    @pytest.mark.asyncio
    async def test_handle_prompts_get(self, setup_handlers):
        """Test handling prompts/get request."""
        request = {
            "jsonrpc": "2.0",
            "method": "prompts/get",
            "params": {
                "name": "test_prompt",
                "arguments": {"topic": "Python"}
            },
            "id": 7
        }
        
        response = await handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 7
        assert "result" in response
        assert "messages" in response["result"]
        messages = response["result"]["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"]["text"] == "Tell me about Python"

    @pytest.mark.asyncio
    async def test_handle_unknown_method(self, setup_handlers):
        """Test handling unknown method."""
        request = {
            "jsonrpc": "2.0",
            "method": "unknown/method",
            "id": 8
        }
        
        response = await handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 8
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Method not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_tool_not_found(self, setup_handlers):
        """Test handling non-existent tool."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "nonexistent",
                "arguments": {}
            },
            "id": 9
        }
        
        response = await handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 9
        assert "error" in response
        assert "Tool not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_notification(self, setup_handlers):
        """Test handling notification (no id)."""
        request = {
            "jsonrpc": "2.0",
            "method": "notification"
        }
        
        response = await handle_request(request)
        
        # Notifications should not return a response
        assert response is None

    @pytest.mark.asyncio
    async def test_handle_tool_error(self, setup_handlers):
        """Test handling tool execution error."""
        from mcp_framework.simplified import _tools
        
        @tool("error_tool", "Tool that raises error")
        async def error_tool():
            raise ValueError("Test error")
        
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "error_tool",
                "arguments": {}
            },
            "id": 10
        }
        
        response = await handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 10
        assert "error" in response
        assert "Test error" in response["error"]["message"]