#!/usr/bin/env python3
"""Local MCP server runner for testing and development"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the demo server
from examples.demo_server import DemoMCPServer

async def handle_stdio():
    """Handle JSON-RPC communication over stdio for MCP protocol"""
    server = DemoMCPServer({
        "name": "demo-mcp-server",
        "version": "0.1.0"
    })
    
    # Read from stdin, write to stdout (MCP protocol)
    while True:
        try:
            # Read a line from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            # Parse JSON-RPC request
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            # Handle the request
            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id", 1)
            
            result = None
            error = None
            
            try:
                # Route based on method
                if method == "initialize":
                    result = {
                        "protocolVersion": "1.0",
                        "capabilities": {
                            "tools": {"listChanged": False},
                            "resources": {"subscribe": False, "listChanged": False},
                            "prompts": {"listChanged": False}
                        },
                        "serverInfo": {
                            "name": server.config.get("name"),
                            "version": server.config.get("version")
                        }
                    }
                    
                elif method == "tools/list":
                    result = {"tools": server.list_tools()}
                    
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    tool_result = await server.handle_tool_call(tool_name, arguments)
                    result = {"content": [{"type": "text", "text": json.dumps(tool_result)}]}
                    
                elif method == "resources/list":
                    result = {"resources": server.list_resources()}
                    
                elif method == "resources/read":
                    uri = params.get("uri")
                    resource_result = await server.handle_resource_request(uri)
                    result = {"contents": [{"uri": uri, "text": json.dumps(resource_result)}]}
                    
                elif method == "prompts/list":
                    result = {"prompts": server.list_prompts()}
                    
                elif method == "prompts/get":
                    prompt_name = params.get("name")
                    context = params.get("context", {})
                    prompt_result = await server.handle_prompt_request(prompt_name, context)
                    result = {"description": prompt_result}
                    
                else:
                    error = {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                    
            except Exception as e:
                error = {
                    "code": -32603,
                    "message": str(e)
                }
            
            # Build response
            response = {
                "jsonrpc": "2.0",
                "id": request_id
            }
            
            if error:
                response["error"] = error
            else:
                response["result"] = result
            
            # Write response to stdout
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            
        except Exception as e:
            # Log errors to stderr
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    # Run the server
    asyncio.run(handle_stdio())