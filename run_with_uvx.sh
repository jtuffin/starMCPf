#!/bin/bash
# Run the MCP server locally using uvx or standard Python

echo "Starting Demo MCP Server..."
echo "================================"
echo ""
echo "This server implements the MCP protocol over stdio."
echo "It can be connected to Claude Desktop or other MCP clients."
echo ""

# Check if uvx is available
if command -v uvx &> /dev/null; then
    echo "Running with uvx..."
    uvx python local_server.py
else
    echo "uvx not found, using python3 directly..."
    python3 local_server.py
fi