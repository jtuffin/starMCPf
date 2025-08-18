#!/bin/bash
# Test the simplified MCP server

echo "Testing Simplified MCP Server"
echo "=============================="
echo ""
echo "Starting the simple demo server..."
echo "This will connect the interactive client to the simplified demo."
echo ""

cd /home/jtuffin/projects/mcp_framework

# Start the interactive client with the simple demo
python3 interactive_client.py python3 examples/simple_demo.py