#!/usr/bin/env python3
"""Test client for the MCP server - simulates MCP protocol interactions"""

import json
import subprocess
import os

def send_request(process, request):
    """Send a request and get response"""
    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json.encode())
    process.stdin.flush()
    
    response_line = process.stdout.readline().decode()
    return json.loads(response_line)

def main():
    print("=== MCP Server Test Client ===\n")
    
    # Start the server as a subprocess
    server_path = os.path.join(os.path.dirname(__file__), "local_server.py")
    process = subprocess.Popen(
        ["python3", server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Test 1: Initialize
        print("1. Testing initialize...")
        response = send_request(process, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        })
        print(f"   Server: {response['result']['serverInfo']['name']} v{response['result']['serverInfo']['version']}")
        print("   ✓ Initialize successful\n")
        
        # Test 2: List tools
        print("2. Testing tools/list...")
        response = send_request(process, {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        })
        tools = response['result']['tools']
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
        print("   ✓ Tools listed\n")
        
        # Test 3: Call a tool (weather)
        print("3. Testing tools/call (get_weather)...")
        response = send_request(process, {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_weather",
                "arguments": {"location": "San Francisco"}
            }
        })
        weather_data = json.loads(response['result']['content'][0]['text'])
        print(f"   Weather in San Francisco:")
        print(f"   - Temperature: {weather_data['temperature']}")
        print(f"   - Condition: {weather_data['condition']}")
        print(f"   - Wind: {weather_data['wind']}")
        print("   ✓ Tool call successful\n")
        
        # Test 4: Call calculator tool
        print("4. Testing tools/call (calculate)...")
        response = send_request(process, {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "calculate",
                "arguments": {"expression": "100 * 2 + 50"}
            }
        })
        calc_data = json.loads(response['result']['content'][0]['text'])
        print(f"   Expression: {calc_data['expression']}")
        print(f"   Result: {calc_data['result']}")
        print("   ✓ Calculation successful\n")
        
        # Test 5: List resources
        print("5. Testing resources/list...")
        response = send_request(process, {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "resources/list",
            "params": {}
        })
        resources = response['result']['resources']
        print(f"   Found {len(resources)} resources:")
        for resource in resources:
            print(f"   - {resource['uri']}: {resource['description']}")
        print("   ✓ Resources listed\n")
        
        # Test 6: Read a resource
        print("6. Testing resources/read (config)...")
        response = send_request(process, {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "resources/read",
            "params": {"uri": "config://settings"}
        })
        config_data = json.loads(response['result']['contents'][0]['text'])
        print(f"   Server config:")
        print(f"   - Name: {config_data['server_name']}")
        print(f"   - Version: {config_data['version']}")
        print(f"   - Environment: {config_data['environment']}")
        print("   ✓ Resource read successful\n")
        
        print("=== All Tests Passed! ===\n")
        print("The MCP server is working correctly and can be integrated with:")
        print("- Claude Desktop (add to claude_desktop_config.json)")
        print("- Any MCP-compatible client")
        print("\nTo add to Claude Desktop, add this to your config:")
        print(json.dumps({
            "mcpServers": {
                "demo-mcp": {
                    "command": "python3",
                    "args": [os.path.abspath(server_path)]
                }
            }
        }, indent=2))
        
    finally:
        # Cleanup
        process.terminate()

if __name__ == "__main__":
    main()