# MCP Framework Demo Guide

This guide covers everything you need to know about running and testing the MCP Framework demos.

## Overview

The MCP Framework provides two approaches for building MCP servers:

1. **Class-based API** - Full control and flexibility for complex servers
2. **Simplified API** - Minimal code with decorator-only approach

Both approaches implement the same MCP protocol and can be tested with the same tools.

## Quick Start

### Testing with the Interactive Client

The interactive client provides a menu-driven interface to test any MCP server:

```bash
# Run with the default demo server
python3 interactive_client.py

# Or specify a different server
python3 interactive_client.py python3 examples/simple_demo.py
```

### Using the Test Script

For the simplified demo specifically:

```bash
./test_simple.sh
```

This launches the interactive client connected to the simplified demo server.

## The Two Approaches

### 1. Class-Based Approach (`examples/demo_server.py`)

The full-featured approach using classes:

```python
from mcp_framework import MCPServer, Tool, Resource, Prompt

class DemoMCPServer(MCPServer):
    
    @Tool(name="get_weather", description="Get weather", parameters={...})
    async def get_weather(self, location: str) -> dict:
        # Implementation
        return {"temperature": "72°F", ...}
```

**Features:**
- Full control over server behavior
- Access to server state and configuration
- Suitable for complex business logic
- Can maintain state between calls

**Running:**
```bash
python3 examples/demo_server.py  # Runs built-in tests
```

### 2. Simplified Approach (`examples/simple_demo.py`)

The minimal code approach using just decorators:

```python
from mcp_framework.simplified import tool, resource, prompt, serve

@tool("get_weather", "Get weather for a location")
async def get_weather(location: str) -> dict:
    return {"location": location, "temperature": "72°F"}

# That's it! Just call serve:
serve(name="simple-mcp", version="1.0.0")
```

**Features:**
- Minimal boilerplate code
- Auto-generates parameter schemas from function signatures
- Perfect for quick prototypes
- No class needed - just functions

**Running:**
```bash
python3 examples/simple_demo.py  # Starts the server
```

## Interactive Client Usage

The interactive client (`interactive_client.py`) provides a menu-driven interface:

```
============================================
Commands:
  1. Call Tool
  2. Read Resource
  3. Generate Prompt
  4. List Capabilities
  5. Refresh
  6. Raw Request (Advanced)
  0. Exit
============================================
```

### Features:
- **Call Tool**: Interactive tool execution with parameter input
- **Read Resource**: Fetch and display resources
- **Generate Prompt**: Create prompts with context
- **List Capabilities**: See all available tools, resources, and prompts
- **Raw Request**: Send custom JSON-RPC requests for testing

### Example Session:

1. Start the client:
```bash
python3 interactive_client.py
```

2. Select "1" to call a tool
3. Choose "get_weather" from the list
4. Enter location: "San Francisco" or "94102"
5. See the weather results

## Available Demo Features

### Tools
Both demos include these tools:

- **get_weather**: Get weather for a location
  - Accepts city names or US zip codes
  - Returns temperature, conditions, humidity, wind
  - Zip codes are mapped to city names (e.g., 94102 → San Francisco, CA)

- **calculate**: Perform mathematical calculations
  - Accepts expressions like "100 * 2 + 50"
  - Returns the calculated result

The full demo also includes:
- **store_data**: Store key-value pairs
- **retrieve_data**: Retrieve stored data

### Resources
- **config://settings**: Server configuration
- **metrics://stats**: Server metrics (full demo only)
- **data://database**: Database contents (full demo only)

### Prompts
- **analyze_weather**: Generate weather analysis prompts
- **data_insights**: Generate data insights prompts (full demo only)

## Testing Methods

### 1. Interactive Client for Local Servers (Recommended)
Best for interactive testing of local MCP servers:
```bash
# Test default demo server
python3 interactive_client.py

# Test specific server
python3 interactive_client.py python3 examples/simple_demo.py
```

### 2. Interactive Client for Lambda Deployments
Test your deployed MCP servers on AWS Lambda:
```bash
# Test Lambda-deployed server
python3 interactive_client_lambda.py https://your-api.execute-api.region.amazonaws.com/prod/mcp
```

Features of the Lambda client:
- Works over HTTP/HTTPS with API Gateway endpoints
- Same interactive menu interface as local client
- Connection testing with response time measurement
- Handles Lambda proxy response format
- Full support for tools, resources, and prompts

### 3. Test Client
Automated test that verifies all protocol methods:
```bash
python3 test_mcp_client.py
```

### 4. Direct Protocol Testing
Send JSON-RPC messages directly:
```bash
# For local servers (stdio)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python3 local_server.py

# For Lambda servers (HTTP)
curl -X POST https://your-api.execute-api.region.amazonaws.com/prod/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### 5. Integration with Claude Desktop
Add to your `claude_desktop_config.json`:

For local servers:
```json
{
  "mcpServers": {
    "demo-mcp": {
      "command": "python3",
      "args": ["/absolute/path/to/local_server.py"]
    }
  }
}
```

For Lambda servers (if Claude Desktop supports HTTP):
```json
{
  "mcpServers": {
    "demo-mcp-lambda": {
      "url": "https://your-api.execute-api.region.amazonaws.com/prod/mcp"
    }
  }
}
```

### 6. Using with UVX
If you have `uv` installed:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run with uvx
uvx python local_server.py
```

## Troubleshooting

### Common Issues

1. **"No module named pydantic"**
   - The framework works without pydantic - we added fallbacks
   - Just ignore the warning about FastMCP not being installed

2. **"int object has no attribute isdigit"**
   - Fixed by converting all inputs to strings
   - Update to latest version of the demos

3. **Interactive client fails to connect**
   - Make sure no startup messages go to stdout
   - All debug output should go to stderr
   - Check that the server returns valid JSON

4. **Missing location details for zip codes**
   - Only common US zip codes are mapped
   - Unknown zips show as "Area [zipcode]"
   - This is expected behavior for the demo

## Development Tips

### Creating Your Own MCP Server

Using the simplified approach:

```python
from mcp_framework.simplified import tool, resource, serve

@tool("my_tool", "Description of my tool")
async def my_tool(param1: str, param2: int = 10) -> dict:
    # Your logic here
    return {"result": f"Processed {param1} with {param2}"}

@resource("data://mydata")
async def get_data() -> dict:
    return {"data": "value"}

serve(name="my-mcp", version="1.0.0")
```

### Parameter Types
The simplified API automatically detects parameter types from type hints:
- `str` → string parameter
- `int` → integer parameter
- `float` → number parameter
- `bool` → boolean parameter
- Parameters without defaults are required
- Parameters with defaults are optional

### Lambda Deployment
Both approaches support Lambda deployment. The framework includes:
- Lambda handler creation
- Request/response adaptation
- API Gateway integration

## Summary

The MCP Framework provides flexible options for building MCP servers:

- **Use the class-based approach** when you need full control, state management, or complex business logic
- **Use the simplified approach** for quick prototypes, simple tools, or when minimal code is preferred
- **Test with the interactive client** for the best development experience
- **Deploy to Lambda** when ready for production

All demos use the same MCP protocol and can be tested with the same tools, making it easy to start simple and grow as needed.