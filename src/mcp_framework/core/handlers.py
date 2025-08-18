"""Lambda handler for MCP servers"""

import asyncio
import json
from typing import Any, Dict, Optional
from .protocol import MCPRequest, MCPResponse, MCPMethod, ProtocolAdapter
from .server import MCPServer

try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    # Fallback for when structlog is not installed
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class LambdaHandler:
    """AWS Lambda handler for MCP servers"""
    
    def __init__(self, server: MCPServer):
        self.server = server
        self.adapter = ProtocolAdapter()
    
    def handle(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Main Lambda handler entry point"""
        # Handle OPTIONS request for CORS
        if event.get("httpMethod") == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type"
                },
                "body": ""
            }
        
        try:
            # Parse MCP request
            mcp_request = self.adapter.from_lambda_event(event)
            
            # Log the request
            logger.info(
                "Processing MCP request",
                method=mcp_request.method,
                request_id=mcp_request.id
            )
            
            # Route to appropriate handler
            if asyncio.iscoroutinefunction(self._route_request):
                result = asyncio.run(self._route_request(mcp_request))
            else:
                result = self._route_request(mcp_request)
            
            # Create success response
            mcp_response = self.adapter.create_success_response(
                mcp_request.id,
                result
            )
            
        except Exception as e:
            logger.error(
                "Error processing request",
                error=str(e),
                request_id=event.get("requestContext", {}).get("requestId")
            )
            
            # Create error response
            mcp_response = self.adapter.create_error_response(
                request_id=event.get("id", 1),
                code=-32603,
                message=str(e)
            )
        
        # Convert to Lambda response
        return self.adapter.to_lambda_response(mcp_response)
    
    async def _route_request(self, request: MCPRequest) -> Any:
        """Route MCP request to appropriate handler"""
        
        method = request.method
        params = request.params or {}
        
        # Handle different MCP methods
        if method == MCPMethod.INITIALIZE:
            return await self._handle_initialize(params)
        
        elif method == MCPMethod.LIST_TOOLS:
            return self.server.list_tools()
        
        elif method == MCPMethod.CALL_TOOL:
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            return await self.server.handle_tool_call(tool_name, arguments)
        
        elif method == MCPMethod.LIST_RESOURCES:
            return self.server.list_resources()
        
        elif method == MCPMethod.READ_RESOURCE:
            uri = params.get("uri")
            return await self.server.handle_resource_request(uri)
        
        elif method == MCPMethod.LIST_PROMPTS:
            return self.server.list_prompts()
        
        elif method == MCPMethod.GET_PROMPT:
            prompt_name = params.get("name")
            context = params.get("context", {})
            return await self.server.handle_prompt_request(prompt_name, context)
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request"""
        return {
            "protocolVersion": "1.0",
            "capabilities": {
                "tools": {
                    "listChanged": False
                },
                "resources": {
                    "subscribe": False,
                    "listChanged": False
                },
                "prompts": {
                    "listChanged": False
                }
            },
            "serverInfo": {
                "name": self.server.config.get("name", "mcp-framework-server"),
                "version": self.server.config.get("version", "0.1.0")
            }
        }


def create_lambda_handler(server_class: type[MCPServer], config: Optional[Dict[str, Any]] = None):
    """Factory function to create a Lambda handler"""
    server = server_class(config=config)
    handler = LambdaHandler(server)
    return handler.handle