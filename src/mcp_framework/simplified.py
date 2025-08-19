"""Simplified MCP Framework - Minimal API for developers"""

import asyncio
import json
import sys
import logging
from typing import Callable, Dict, Any, List
from functools import wraps

# Set up logging
logger = logging.getLogger(__name__)

# Global registry for tools, resources, and prompts
_tools = {}
_resources = {}
_prompts = {}


def tool(name: str, description: str = "", parameters: dict = None):
    """Simple decorator for tools - no class needed"""
    def decorator(func: Callable):
        import inspect
        
        # Auto-generate parameters from function signature if not provided
        if parameters is None:
            sig = inspect.signature(func)
            params = {}
            props = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name not in ['self', 'cls']:
                    # Simple type mapping
                    param_type = "string"  # Default to string
                    if param.annotation != inspect.Parameter.empty:
                        if param.annotation == int:
                            param_type = "integer"
                        elif param.annotation == float:
                            param_type = "number"
                        elif param.annotation == bool:
                            param_type = "boolean"
                    
                    props[param_name] = {"type": param_type}
                    
                    if param.default == inspect.Parameter.empty:
                        required.append(param_name)
            
            if props:
                params = {
                    "type": "object",
                    "properties": props,
                    "required": required
                }
            else:
                params = {}
        else:
            params = parameters
        
        _tools[name] = {
            "name": name,
            "description": description,
            "handler": func,
            "parameters": params
        }
        return func
    return decorator


def resource(uri: str, description: str = ""):
    """Simple decorator for resources"""
    def decorator(func: Callable):
        _resources[uri] = {
            "uri": uri,
            "description": description,
            "handler": func
        }
        return func
    return decorator


def prompt(name: str, description: str = ""):
    """Simple decorator for prompts"""
    def decorator(func: Callable):
        _prompts[name] = {
            "name": name,
            "description": description,
            "handler": func
        }
        return func
    return decorator


async def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming MCP requests"""
    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id", 1)
    
    # Log incoming request
    logger.info(f"Processing MCP method: {method} with params: {json.dumps(params)}")
    
    try:
        # Route to appropriate handler
        if method == "initialize":
            result = {
                "protocolVersion": "1.0",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False}
                },
                "serverInfo": {
                    "name": _server_config.get("name", "mcp-server"),
                    "version": _server_config.get("version", "1.0.0")
                }
            }
        
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["parameters"]
                    }
                    for t in _tools.values()
                ]
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Log tool call
            logger.info(f"Tool call: {tool_name} with arguments: {json.dumps(arguments)}")
            
            if tool_name in _tools:
                handler = _tools[tool_name]["handler"]
                try:
                    if asyncio.iscoroutinefunction(handler):
                        tool_result = await handler(**arguments)
                    else:
                        tool_result = handler(**arguments)
                    
                    # Log tool result
                    logger.info(f"Tool {tool_name} result: {json.dumps(tool_result)}")
                    
                except TypeError as e:
                    # Handle missing arguments more gracefully
                    logger.error(f"Tool '{tool_name}' error: {str(e)}")
                    raise ValueError(f"Tool '{tool_name}' error: {str(e)}")
                result = {"content": [{"type": "text", "text": json.dumps(tool_result)}]}
            else:
                logger.error(f"Unknown tool requested: {tool_name}")
                raise ValueError(f"Unknown tool: {tool_name}")
        
        elif method == "resources/list":
            result = {
                "resources": [
                    {
                        "uri": r["uri"],
                        "description": r["description"]
                    }
                    for r in _resources.values()
                ]
            }
        
        elif method == "resources/read":
            uri = params.get("uri")
            if uri in _resources:
                handler = _resources[uri]["handler"]
                if asyncio.iscoroutinefunction(handler):
                    resource_result = await handler()
                else:
                    resource_result = handler()
                result = {"contents": [{"uri": uri, "text": json.dumps(resource_result)}]}
            else:
                raise ValueError(f"Unknown resource: {uri}")
        
        elif method == "prompts/list":
            result = {
                "prompts": [
                    {
                        "name": p["name"],
                        "description": p["description"]
                    }
                    for p in _prompts.values()
                ]
            }
        
        elif method == "prompts/get":
            prompt_name = params.get("name")
            context = params.get("context", {})
            if prompt_name in _prompts:
                handler = _prompts[prompt_name]["handler"]
                if asyncio.iscoroutinefunction(handler):
                    prompt_result = await handler(context)
                else:
                    prompt_result = handler(context)
                result = {"description": prompt_result}
            else:
                raise ValueError(f"Unknown prompt: {prompt_name}")
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


# Global server configuration
_server_config = {}


def serve(name: str = "mcp-server", version: str = "1.0.0", **kwargs):
    """Start serving the MCP server - this is all you need!"""
    global _server_config
    _server_config = {"name": name, "version": version, **kwargs}
    
    # Print to stderr so it doesn't interfere with JSON protocol on stdout
    sys.stderr.write(f"Starting {name} v{version}...\n")
    sys.stderr.write(f"Tools: {len(_tools)}, Resources: {len(_resources)}, Prompts: {len(_prompts)}\n")
    sys.stderr.flush()
    
    # Run the stdio server
    asyncio.run(_stdio_server())


async def _stdio_server():
    """Handle stdio communication for MCP protocol"""
    while True:
        try:
            # Read from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            # Parse request
            request = json.loads(line)
            
            # Handle request
            response = await handle_request(request)
            
            # Write response
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()


# For Lambda deployment
def lambda_handler(event, context):
    """AWS Lambda handler - automatically created"""
    import json
    
    # Parse the event
    if "body" in event:
        body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
    else:
        body = event
    
    # Handle the request
    response = asyncio.run(handle_request(body))
    
    # Return Lambda response
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(response)
    }