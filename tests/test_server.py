"""Unit tests for the MCPServer class."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from mcp_framework.core.server import MCPServer, Tool, Resource, Prompt


class TestMCPServer:
    """Test cases for MCPServer class."""

    @pytest.fixture
    def server_class(self):
        """Create a test server class with decorated methods."""
        
        class TestServer(MCPServer):
            def __init__(self, config=None):
                super().__init__(config)
                self.test_value = "test"
            
            @Tool(name="test_tool", description="A test tool")
            async def test_tool(self, param: str) -> dict:
                return {"result": f"Processed: {param}"}
            
            @Resource(uri="test://resource")
            async def test_resource(self) -> dict:
                return {"data": "resource_data"}
            
            @Prompt(name="test_prompt", description="A test prompt")
            async def test_prompt(self, context: dict) -> str:
                return f"Prompt with context: {context}"
        
        return TestServer

    @pytest.fixture
    async def server(self, server_class):
        """Create a test server instance."""
        server = server_class()
        await server.initialize()
        return server

    @pytest.mark.asyncio
    async def test_server_initialization(self, server_class):
        """Test server initializes correctly."""
        server = server_class()
        assert server._tools == {}
        assert server._resources == {}
        assert server._prompts == {}
        
        await server.initialize()
        
        assert "test_tool" in server._tools
        assert "test://resource" in server._resources
        assert "test_prompt" in server._prompts

    @pytest.mark.asyncio
    async def test_tool_registration(self, server):
        """Test tool registration and metadata."""
        tool_info = server._tools["test_tool"]
        assert tool_info["name"] == "test_tool"
        assert tool_info["description"] == "A test tool"
        assert callable(tool_info["handler"])

    @pytest.mark.asyncio
    async def test_resource_registration(self, server):
        """Test resource registration and metadata."""
        resource_info = server._resources["test://resource"]
        assert resource_info["uri"] == "test://resource"
        assert callable(resource_info["handler"])

    @pytest.mark.asyncio
    async def test_prompt_registration(self, server):
        """Test prompt registration and metadata."""
        prompt_info = server._prompts["test_prompt"]
        assert prompt_info["name"] == "test_prompt"
        assert prompt_info["description"] == "A test prompt"
        assert callable(prompt_info["handler"])

    @pytest.mark.asyncio
    async def test_handle_initialize(self, server):
        """Test initialize request handling."""
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {}
            },
            "id": 1
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["protocolVersion"] == "0.1.0"
        assert "tools" in response["result"]["capabilities"]

    @pytest.mark.asyncio
    async def test_handle_tools_list(self, server):
        """Test tools/list request handling."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 2
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response
        tools = response["result"]["tools"]
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_handle_tools_call(self, server):
        """Test tools/call request handling."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "test_tool",
                "arguments": {"param": "test_input"}
            },
            "id": 3
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "result" in response
        assert response["result"]["content"][0]["text"] == '{"result": "Processed: test_input"}'

    @pytest.mark.asyncio
    async def test_handle_resources_list(self, server):
        """Test resources/list request handling."""
        request = {
            "jsonrpc": "2.0",
            "method": "resources/list",
            "id": 4
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 4
        assert "result" in response
        resources = response["result"]["resources"]
        assert len(resources) == 1
        assert resources[0]["uri"] == "test://resource"

    @pytest.mark.asyncio
    async def test_handle_resources_read(self, server):
        """Test resources/read request handling."""
        request = {
            "jsonrpc": "2.0",
            "method": "resources/read",
            "params": {
                "uri": "test://resource"
            },
            "id": 5
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 5
        assert "result" in response
        assert response["result"]["contents"][0]["text"] == '{"data": "resource_data"}'

    @pytest.mark.asyncio
    async def test_handle_prompts_list(self, server):
        """Test prompts/list request handling."""
        request = {
            "jsonrpc": "2.0",
            "method": "prompts/list",
            "id": 6
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 6
        assert "result" in response
        prompts = response["result"]["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["name"] == "test_prompt"

    @pytest.mark.asyncio
    async def test_handle_prompts_get(self, server):
        """Test prompts/get request handling."""
        request = {
            "jsonrpc": "2.0",
            "method": "prompts/get",
            "params": {
                "name": "test_prompt",
                "arguments": {"context": {"key": "value"}}
            },
            "id": 7
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 7
        assert "result" in response
        assert "Prompt with context:" in response["result"]["messages"][0]["content"]["text"]

    @pytest.mark.asyncio
    async def test_handle_unknown_method(self, server):
        """Test handling of unknown method."""
        request = {
            "jsonrpc": "2.0",
            "method": "unknown/method",
            "id": 8
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 8
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Method not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_tool_not_found(self, server):
        """Test handling of non-existent tool."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "nonexistent_tool",
                "arguments": {}
            },
            "id": 9
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 9
        assert "error" in response
        assert "Tool not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_tool_execution_error(self, server_class):
        """Test handling of tool execution errors."""
        
        class ErrorServer(MCPServer):
            @Tool(name="error_tool", description="Tool that raises error")
            async def error_tool(self):
                raise ValueError("Test error")
        
        server = ErrorServer()
        await server.initialize()
        
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "error_tool",
                "arguments": {}
            },
            "id": 10
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 10
        assert "error" in response
        assert "Test error" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_multiple_tools_registration(self):
        """Test registering multiple tools."""
        
        class MultiToolServer(MCPServer):
            @Tool(name="tool1", description="First tool")
            async def tool1(self):
                return {"tool": 1}
            
            @Tool(name="tool2", description="Second tool")
            async def tool2(self):
                return {"tool": 2}
        
        server = MultiToolServer()
        await server.initialize()
        
        assert len(server._tools) == 2
        assert "tool1" in server._tools
        assert "tool2" in server._tools

    @pytest.mark.asyncio
    async def test_server_with_config(self):
        """Test server initialization with config."""
        config = {"test_key": "test_value"}
        
        class ConfigServer(MCPServer):
            pass
        
        server = ConfigServer(config=config)
        assert server.config == config

    @pytest.mark.asyncio
    async def test_tool_with_complex_parameters(self):
        """Test tool with complex parameter types."""
        
        class ComplexServer(MCPServer):
            @Tool(name="complex_tool", description="Tool with complex params")
            async def complex_tool(self, items: list, options: dict = None):
                return {
                    "items_count": len(items),
                    "has_options": options is not None
                }
        
        server = ComplexServer()
        await server.initialize()
        
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "complex_tool",
                "arguments": {
                    "items": [1, 2, 3],
                    "options": {"key": "value"}
                }
            },
            "id": 11
        }
        
        response = await server.handle_request(request)
        assert "result" in response
        result = eval(response["result"]["content"][0]["text"])
        assert result["items_count"] == 3
        assert result["has_options"] is True