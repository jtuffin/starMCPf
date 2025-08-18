# MCP Framework

An opinionated framework for building Model Context Protocol (MCP) servers optimized for AWS Lambda deployment.

## Features

- **Simple API**: Decorator-based tool, resource, and prompt definitions
- **Lambda-Ready**: Built-in adaptation layer for AWS Lambda and API Gateway
- **FastMCP Integration**: Lightweight async-first MCP implementation
- **Enterprise Features**: Security, observability, and deployment tooling
- **AWS Native**: CloudFormation templates and deployment scripts included

## Quick Start

### Installation

```bash
pip install mcp-framework
```

### Creating an MCP Server

```python
from mcp_framework import MCPServer, Tool, Resource, Prompt

class MyMCPServer(MCPServer):
    
    @Tool(name="get_data", description="Fetch data from database")
    async def get_data(self, query: str) -> dict:
        # Your business logic here
        return {"result": "data"}
    
    @Resource(uri="config://settings")
    async def get_settings(self) -> dict:
        return {"setting": "value"}
    
    @Prompt(name="analyze", description="Generate analysis prompt")
    async def analyze_prompt(self, context: dict) -> str:
        return f"Analyze: {context}"
```

### Lambda Deployment

```python
from mcp_framework import create_lambda_handler

# Lambda handler
def lambda_handler(event, context):
    handler = create_lambda_handler(MyMCPServer, {
        "name": "my-mcp-server",
        "version": "1.0.0"
    })
    return handler(event, context)
```

## Architecture

The framework provides:

1. **Core Framework** - Base MCP server implementation with FastMCP
2. **Lambda Adapter** - Converts between Lambda events and MCP protocol
3. **Security Module** - Authentication, authorization, input validation
4. **Observability** - CloudWatch logging, metrics, and tracing
5. **Deployment Tools** - CloudFormation templates and scripts

## Demo Server

See `examples/demo_server.py` for a complete working example with:
- Multiple tools (weather, calculator, data storage)
- Resources (config, metrics, database)
- Prompts (weather analysis, data insights)

Run the demo locally:
```bash
python examples/demo_server.py
```

## Project Structure

```
mcp-framework/
├── src/mcp_framework/       # Framework source code
│   ├── core/               # Core MCP server implementation
│   ├── security/           # Security features
│   ├── observability/      # Logging and metrics
│   ├── integration/        # External integrations
│   └── dev/               # Development tools
├── templates/              # CloudFormation templates
├── scripts/               # Deployment scripts
├── examples/              # Example implementations
└── tests/                 # Test suite
```

## Development Status

This framework is in active development. Current features:
- ✅ Core MCP server with decorators
- ✅ Lambda adaptation layer
- ✅ Working demo server
- ⏳ Security module (in progress)
- ⏳ CloudFormation templates (in progress)
- ⏳ Full FastMCP integration (in progress)

## License

MIT