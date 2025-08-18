"""MCP Protocol definitions and adapters"""

from typing import Any, Dict, List, Optional, Union
import json
# Try to use pydantic if available, otherwise use simple classes
try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Simple fallback classes
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def model_dump_json(self):
            import json
            return json.dumps(self.__dict__)
from enum import Enum


class MCPMethod(str, Enum):
    """MCP protocol methods"""
    INITIALIZE = "initialize"
    LIST_TOOLS = "tools/list"
    CALL_TOOL = "tools/call"
    LIST_RESOURCES = "resources/list"
    READ_RESOURCE = "resources/read"
    LIST_PROMPTS = "prompts/list"
    GET_PROMPT = "prompts/get"


class MCPRequest(BaseModel):
    """MCP protocol request"""
    jsonrpc: str = "2.0"
    id: Union[str, int]
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """MCP protocol response"""
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPError(BaseModel):
    """MCP protocol error"""
    code: int
    message: str
    data: Optional[Any] = None


class ProtocolAdapter:
    """Adapts between Lambda request/response and MCP protocol"""
    
    @staticmethod
    def from_lambda_event(event: Dict[str, Any]) -> MCPRequest:
        """Convert Lambda event to MCP request"""
        # Handle API Gateway proxy format
        if "body" in event:
            import json
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event
        
        return MCPRequest(
            jsonrpc=body.get("jsonrpc", "2.0"),
            id=body.get("id", 1),
            method=body.get("method", ""),
            params=body.get("params", {})
        )
    
    @staticmethod
    def to_lambda_response(response: MCPResponse, status_code: int = 200) -> Dict[str, Any]:
        """Convert MCP response to Lambda response"""
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": response.model_dump_json() if hasattr(response, 'model_dump_json') else json.dumps(response.__dict__)
        }
    
    @staticmethod
    def create_error_response(
        request_id: Union[str, int],
        code: int,
        message: str,
        data: Optional[Any] = None
    ) -> MCPResponse:
        """Create an error response"""
        return MCPResponse(
            id=request_id,
            error={
                "code": code,
                "message": message,
                "data": data
            }
        )
    
    @staticmethod
    def create_success_response(
        request_id: Union[str, int],
        result: Any
    ) -> MCPResponse:
        """Create a success response"""
        return MCPResponse(
            id=request_id,
            result=result
        )