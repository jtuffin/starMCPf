#!/usr/bin/env python3
"""Interactive MCP Client - Command-line interface for testing MCP servers"""

import json
import subprocess
import sys
import os
from typing import Dict, Any, Optional

class InteractiveMCPClient:
    def __init__(self, server_command: list):
        """Initialize the MCP client with a server command"""
        self.server_command = server_command
        self.process = None
        self.request_id = 0
        self.tools = []
        self.resources = []
        self.prompts = []
        
    def start(self):
        """Start the MCP server process"""
        print("Starting MCP server...")
        self.process = subprocess.Popen(
            self.server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # Capture stderr
            text=False  # Use bytes
        )
        
        # Initialize the connection
        response = self.send_request({
            "method": "initialize",
            "params": {}
        })
        
        if response and "result" in response:
            server_info = response["result"].get("serverInfo", {})
            print(f"✓ Connected to: {server_info.get('name', 'Unknown')} v{server_info.get('version', '?')}")
            print()
            self.refresh_capabilities()
        else:
            print("Failed to initialize server")
            return False
        
        return True
    
    def send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a request to the server and get response"""
        if not self.process:
            return None
        
        self.request_id += 1
        request["jsonrpc"] = "2.0"
        request["id"] = self.request_id
        
        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            self.process.stdin.flush()
            
            # Read response
            response_line = self.process.stdout.readline()
            if response_line:
                return json.loads(response_line.decode())
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def refresh_capabilities(self):
        """Refresh the list of tools, resources, and prompts"""
        # Get tools
        response = self.send_request({"method": "tools/list", "params": {}})
        if response and "result" in response:
            self.tools = response["result"].get("tools", [])
        
        # Get resources
        response = self.send_request({"method": "resources/list", "params": {}})
        if response and "result" in response:
            self.resources = response["result"].get("resources", [])
        
        # Get prompts  
        response = self.send_request({"method": "prompts/list", "params": {}})
        if response and "result" in response:
            self.prompts = response["result"].get("prompts", [])
    
    def list_capabilities(self):
        """Display available tools, resources, and prompts"""
        print("\n📦 Available Tools:")
        if self.tools:
            for i, tool in enumerate(self.tools, 1):
                print(f"  {i}. {tool['name']}: {tool['description']}")
        else:
            print("  No tools available")
        
        print("\n📁 Available Resources:")
        if self.resources:
            for i, resource in enumerate(self.resources, 1):
                print(f"  {i}. {resource['uri']}: {resource.get('description', 'No description')}")
        else:
            print("  No resources available")
        
        print("\n💭 Available Prompts:")
        if self.prompts:
            for i, prompt in enumerate(self.prompts, 1):
                print(f"  {i}. {prompt['name']}: {prompt['description']}")
        else:
            print("  No prompts available")
        print()
    
    def call_tool(self):
        """Interactive tool calling"""
        if not self.tools:
            print("No tools available")
            return
        
        print("\nAvailable tools:")
        for i, tool in enumerate(self.tools, 1):
            print(f"  {i}. {tool['name']}: {tool['description']}")
        
        try:
            choice = int(input("\nSelect tool number (or 0 to cancel): "))
            if choice == 0:
                return
            if choice < 1 or choice > len(self.tools):
                print("Invalid choice")
                return
            
            tool = self.tools[choice - 1]
            print(f"\nCalling tool: {tool['name']}")
            
            # Get parameters if needed
            params = tool.get('parameters', {})
            if params and params.get('properties'):
                print("Enter parameters:")
                arguments = {}
                for param_name, param_info in params['properties'].items():
                    value = input(f"  {param_name} ({param_info.get('description', 'no description')}): ")
                    # Try to parse as JSON, otherwise use as string
                    try:
                        arguments[param_name] = json.loads(value)
                    except:
                        arguments[param_name] = value
            else:
                arguments = {}
            
            # Call the tool
            response = self.send_request({
                "method": "tools/call",
                "params": {
                    "name": tool['name'],
                    "arguments": arguments
                }
            })
            
            if response and "result" in response:
                content = response["result"].get("content", [])
                if content and isinstance(content, list) and len(content) > 0:
                    result_text = content[0].get("text", "No result")
                    try:
                        result_data = json.loads(result_text)
                        print(f"\n✅ Result:\n{json.dumps(result_data, indent=2)}")
                    except:
                        print(f"\n✅ Result: {result_text}")
            elif response and "error" in response:
                print(f"\n❌ Error: {response['error'].get('message', 'Unknown error')}")
            
        except ValueError:
            print("Invalid input")
        except Exception as e:
            print(f"Error: {e}")
    
    def read_resource(self):
        """Interactive resource reading"""
        if not self.resources:
            print("No resources available")
            return
        
        print("\nAvailable resources:")
        for i, resource in enumerate(self.resources, 1):
            print(f"  {i}. {resource['uri']}: {resource.get('description', '')}")
        
        try:
            choice = int(input("\nSelect resource number (or 0 to cancel): "))
            if choice == 0:
                return
            if choice < 1 or choice > len(self.resources):
                print("Invalid choice")
                return
            
            resource = self.resources[choice - 1]
            print(f"\nReading resource: {resource['uri']}")
            
            response = self.send_request({
                "method": "resources/read",
                "params": {"uri": resource['uri']}
            })
            
            if response and "result" in response:
                contents = response["result"].get("contents", [])
                if contents and isinstance(contents, list) and len(contents) > 0:
                    result_text = contents[0].get("text", "No content")
                    try:
                        result_data = json.loads(result_text)
                        print(f"\n📄 Content:\n{json.dumps(result_data, indent=2)}")
                    except:
                        print(f"\n📄 Content: {result_text}")
            elif response and "error" in response:
                print(f"\n❌ Error: {response['error'].get('message', 'Unknown error')}")
                
        except ValueError:
            print("Invalid input")
        except Exception as e:
            print(f"Error: {e}")
    
    def get_prompt(self):
        """Interactive prompt generation"""
        if not self.prompts:
            print("No prompts available")
            return
        
        print("\nAvailable prompts:")
        for i, prompt in enumerate(self.prompts, 1):
            print(f"  {i}. {prompt['name']}: {prompt['description']}")
        
        try:
            choice = int(input("\nSelect prompt number (or 0 to cancel): "))
            if choice == 0:
                return
            if choice < 1 or choice > len(self.prompts):
                print("Invalid choice")
                return
            
            prompt = self.prompts[choice - 1]
            print(f"\nGenerating prompt: {prompt['name']}")
            
            # Get context
            context_str = input("Enter context (JSON format, or press Enter for empty): ")
            if context_str:
                try:
                    context = json.loads(context_str)
                except:
                    context = {"text": context_str}
            else:
                context = {}
            
            response = self.send_request({
                "method": "prompts/get",
                "params": {
                    "name": prompt['name'],
                    "context": context
                }
            })
            
            if response and "result" in response:
                description = response["result"].get("description", "No prompt generated")
                print(f"\n💭 Generated Prompt:\n{description}")
            elif response and "error" in response:
                print(f"\n❌ Error: {response['error'].get('message', 'Unknown error')}")
                
        except ValueError:
            print("Invalid input")
        except Exception as e:
            print(f"Error: {e}")
    
    def run_interactive_session(self):
        """Run the interactive command-line interface"""
        print("=" * 60)
        print("MCP Interactive Client")
        print("=" * 60)
        
        if not self.start():
            print("Failed to start server")
            return
        
        self.list_capabilities()
        
        while True:
            print("\n" + "=" * 40)
            print("Commands:")
            print("  1. Call Tool")
            print("  2. Read Resource")
            print("  3. Generate Prompt")
            print("  4. List Capabilities")
            print("  5. Refresh")
            print("  6. Raw Request (Advanced)")
            print("  0. Exit")
            print("=" * 40)
            
            try:
                choice = input("\nSelect option: ").strip()
                
                if choice == "0":
                    print("\nGoodbye!")
                    break
                elif choice == "1":
                    self.call_tool()
                elif choice == "2":
                    self.read_resource()
                elif choice == "3":
                    self.get_prompt()
                elif choice == "4":
                    self.list_capabilities()
                elif choice == "5":
                    print("Refreshing capabilities...")
                    self.refresh_capabilities()
                    print("✓ Refreshed")
                elif choice == "6":
                    self.raw_request()
                else:
                    print("Invalid choice")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        # Cleanup
        if self.process:
            self.process.terminate()
    
    def raw_request(self):
        """Send a raw JSON-RPC request"""
        print("\nEnter raw JSON-RPC request (without jsonrpc and id fields):")
        print("Example: {\"method\": \"tools/list\", \"params\": {}}")
        
        try:
            request_str = input("Request: ")
            request = json.loads(request_str)
            
            response = self.send_request(request)
            
            if response:
                print(f"\nResponse:\n{json.dumps(response, indent=2)}")
            else:
                print("No response received")
                
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
        except Exception as e:
            print(f"Error: {e}")


def main():
    # Default to using the local server
    server_script = os.path.join(os.path.dirname(__file__), "local_server.py")
    
    if len(sys.argv) > 1:
        # Allow custom server command
        server_command = sys.argv[1:]
    else:
        # Use default
        server_command = ["python3", server_script]
    
    print(f"Using server command: {' '.join(server_command)}")
    
    client = InteractiveMCPClient(server_command)
    client.run_interactive_session()


if __name__ == "__main__":
    main()