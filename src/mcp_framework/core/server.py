"""Core MCP Server implementation with FastMCP integration"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Type, Union
from functools import wraps
import inspect
# Try to use pydantic if available, otherwise use simple classes
try:
    from pydantic import BaseModel, Field
except ImportError:
    # Simple fallback classes
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    # Fallback for when structlog is not installed
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class ToolDefinition(BaseModel):
    """Tool definition for MCP protocol"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    

class ResourceDefinition(BaseModel):
    """Resource definition for MCP protocol"""
    uri: str
    description: str
    handler: Callable


class PromptDefinition(BaseModel):
    """Prompt definition for MCP protocol"""
    name: str
    description: str
    handler: Callable


def Tool(name: str, description: str, parameters: Optional[Dict[str, Any]] = None):
    """Decorator for defining MCP tools"""
    def decorator(func: Callable) -> Callable:
        func._mcp_tool = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters or {},
            handler=func
        )
        return func
    return decorator


def Resource(uri: str, description: str = ""):
    """Decorator for defining MCP resources"""
    def decorator(func: Callable) -> Callable:
        func._mcp_resource = ResourceDefinition(
            uri=uri,
            description=description,
            handler=func
        )
        return func
    return decorator


def Prompt(name: str, description: str):
    """Decorator for defining MCP prompts"""
    def decorator(func: Callable) -> Callable:
        func._mcp_prompt = PromptDefinition(
            name=name,
            description=description,
            handler=func
        )
        return func
    return decorator


class MCPServer:
    """Base MCP Server implementation using FastMCP"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.tools: Dict[str, ToolDefinition] = {}
        self.resources: Dict[str, ResourceDefinition] = {}
        self.prompts: Dict[str, PromptDefinition] = {}
        
        # Auto-discover decorated methods
        self._discover_handlers()
        
        # Initialize FastMCP when available
        self._init_fastmcp()
        
        if hasattr(logger, 'info'):
            try:
                # Try structlog-style logging
                logger.info(
                    "MCP Server initialized",
                    tools=len(self.tools),
                    resources=len(self.resources),
                    prompts=len(self.prompts)
                )
            except TypeError:
                # Fall back to standard logging
                logger.info(f"MCP Server initialized - tools: {len(self.tools)}, resources: {len(self.resources)}, prompts: {len(self.prompts)}")
    
    def _discover_handlers(self):
        """Discover and register decorated handlers"""
        for name, method in inspect.getmembers(self):
            if hasattr(method, '_mcp_tool'):
                tool_def = method._mcp_tool
                self.tools[tool_def.name] = tool_def
                
            elif hasattr(method, '_mcp_resource'):
                resource_def = method._mcp_resource
                self.resources[resource_def.uri] = resource_def
                
            elif hasattr(method, '_mcp_prompt'):
                prompt_def = method._mcp_prompt
                self.prompts[prompt_def.name] = prompt_def
    
    def _init_fastmcp(self):
        """Initialize FastMCP integration"""
        try:
            from fastmcp import FastMCP
            self.mcp = FastMCP(
                name=self.config.get("name", "mcp-framework-server"),
                version=self.config.get("version", "0.1.0")
            )
            
            # Register tools with FastMCP
            for tool_def in self.tools.values():
                self._register_tool_with_fastmcp(tool_def)
                
            # Register resources with FastMCP
            for resource_def in self.resources.values():
                self._register_resource_with_fastmcp(resource_def)
                
        except ImportError:
            logger.warning("FastMCP not installed, running in compatibility mode")
            self.mcp = None
    
    def _register_tool_with_fastmcp(self, tool_def: ToolDefinition):
        """Register a tool with FastMCP"""
        if not self.mcp:
            return
            
        # FastMCP registration would go here
        # This is a placeholder for actual FastMCP integration
        pass
    
    def _register_resource_with_fastmcp(self, resource_def: ResourceDefinition):
        """Register a resource with FastMCP"""
        if not self.mcp:
            return
            
        # FastMCP registration would go here
        # This is a placeholder for actual FastMCP integration
        pass
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Handle a tool call"""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool_def = self.tools[tool_name]
        
        # Call the handler
        if asyncio.iscoroutinefunction(tool_def.handler):
            result = await tool_def.handler(self, **arguments)
        else:
            result = tool_def.handler(self, **arguments)
        
        try:
            logger.info("Tool executed", tool=tool_name, success=True)
        except TypeError:
            logger.info(f"Tool executed: {tool_name}")
        return result
    
    async def handle_resource_request(self, uri: str) -> Any:
        """Handle a resource request"""
        if uri not in self.resources:
            raise ValueError(f"Unknown resource: {uri}")
        
        resource_def = self.resources[uri]
        
        # Call the handler
        if asyncio.iscoroutinefunction(resource_def.handler):
            result = await resource_def.handler(self)
        else:
            result = resource_def.handler(self)
        
        try:
            logger.info("Resource served", uri=uri, success=True)
        except TypeError:
            logger.info(f"Resource served: {uri}")
        return result
    
    async def handle_prompt_request(self, prompt_name: str, context: Dict[str, Any]) -> str:
        """Handle a prompt request"""
        if prompt_name not in self.prompts:
            raise ValueError(f"Unknown prompt: {prompt_name}")
        
        prompt_def = self.prompts[prompt_name]
        
        # Call the handler
        if asyncio.iscoroutinefunction(prompt_def.handler):
            result = await prompt_def.handler(self, context)
        else:
            result = prompt_def.handler(self, context)
        
        try:
            logger.info("Prompt generated", prompt=prompt_name, success=True)
        except TypeError:
            logger.info(f"Prompt generated: {prompt_name}")
        return result
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources"""
        return [
            {
                "uri": resource.uri,
                "description": resource.description
            }
            for resource in self.resources.values()
        ]
    
    def list_prompts(self) -> List[Dict[str, Any]]:
        """List all available prompts"""
        return [
            {
                "name": prompt.name,
                "description": prompt.description
            }
            for prompt in self.prompts.values()
        ]