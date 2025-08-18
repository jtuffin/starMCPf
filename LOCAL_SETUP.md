# Local MCP Server Setup Guide

## Quick Start

### 1. Test the Server Locally

Run the test client to verify everything works:

```bash
python3 test_mcp_client.py
```

This will test all the MCP protocol methods and show you the server is working.

### 2. Run as Standalone Server

For manual testing or debugging:

```bash
python3 local_server.py
```

Or with the helper script:

```bash
./run_with_uvx.sh
```

The server communicates via stdin/stdout using the MCP protocol.

## Integration with Claude Desktop

### Step 1: Find your Claude Desktop config file

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Step 2: Add the MCP server configuration

Edit the config file and add:

```json
{
  "mcpServers": {
    "demo-mcp": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp_framework/local_server.py"]
    }
  }
}
```

Replace `/absolute/path/to/mcp_framework` with the actual path to this project.

### Step 3: Restart Claude Desktop

After saving the config, restart Claude Desktop. The MCP server will be available.

## Using with UVX

If you have `uvx` installed (from the `uv` package manager):

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the server with uvx
uvx python local_server.py
```

## Available Features

### Tools
- **get_weather**: Get weather for any location (mock data)
- **calculate**: Perform mathematical calculations
- **store_data**: Store key-value pairs in memory
- **retrieve_data**: Retrieve stored data by key

### Resources
- **config://settings**: Server configuration
- **metrics://stats**: Server metrics and statistics
- **data://database**: View all stored data

### Prompts
- **analyze_weather**: Generate weather analysis prompts
- **data_insights**: Generate data insights prompts

## Testing the Protocol

You can test individual MCP protocol messages manually:

```bash
# Start the server
python3 local_server.py

# In another terminal, send requests via echo and pipe:
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 local_server.py

# Or interactively:
python3 local_server.py
# Then type: {"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
# Press Enter to see the response
```

## Troubleshooting

### Server doesn't start
- Ensure Python 3.9+ is installed: `python3 --version`
- Check the path in your Claude config is absolute, not relative

### Claude doesn't see the server
- Restart Claude Desktop after config changes
- Check the config file is valid JSON (use a JSON validator)
- Look for errors in Claude's developer console

### Tools not working
- Run `test_mcp_client.py` to verify the server works locally
- Check stderr output when running `local_server.py` manually

## Next Steps

1. **Customize the server**: Edit `examples/demo_server.py` to add your own tools
2. **Deploy to Lambda**: Use the framework to deploy to AWS
3. **Add real integrations**: Replace mock data with real business logic

## Protocol Details

The MCP server implements the Model Context Protocol over JSON-RPC 2.0:

- **Transport**: stdio (stdin for requests, stdout for responses)
- **Format**: Line-delimited JSON
- **Methods**: initialize, tools/list, tools/call, resources/list, resources/read, prompts/list, prompts/get

Each request follows this format:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "method_name",
  "params": {}
}
```

Responses are:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {}
}
```