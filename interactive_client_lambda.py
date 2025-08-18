#!/usr/bin/env python3
"""Interactive MCP Client for Lambda/HTTP endpoints - Test your deployed MCP servers"""

import json
import sys
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse

class InteractiveMCPLambdaClient:
    def __init__(self, endpoint_url: str):
        """Initialize the MCP client with an HTTP endpoint"""
        self.endpoint_url = endpoint_url
        self.request_id = 0
        self.tools = []
        self.resources = []
        self.prompts = []
        self.session = requests.Session()
        
        # Validate URL
        parsed = urlparse(endpoint_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {endpoint_url}")
    
    def send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a request to the Lambda endpoint and get response"""
        self.request_id += 1
        request["jsonrpc"] = "2.0"
        request["id"] = self.request_id
        
        try:
            # Send HTTP POST request
            response = self.session.post(
                self.endpoint_url,
                json=request,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            # Check HTTP status
            if response.status_code != 200:
                print(f"HTTP Error {response.status_code}: {response.text}")
                return None
            
            # Parse JSON response
            data = response.json()
            
            # Handle Lambda proxy response format
            if 'body' in data and isinstance(data['body'], str):
                # It's a Lambda proxy response
                return json.loads(data['body'])
            else:
                # Direct JSON-RPC response
                return data
                
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Response text: {response.text[:500]}")
            return None
    
    def start(self):
        """Initialize connection to the MCP server"""
        print(f"Connecting to: {self.endpoint_url}")
        
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
            return True
        else:
            print("Failed to initialize server")
            if response and "error" in response:
                print(f"Error: {response['error'].get('message', 'Unknown error')}")
            return False
    
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
                    required = param_name in params.get('required', [])
                    prompt = f"  {param_name}"
                    if param_info.get('description'):
                        prompt += f" ({param_info.get('description')})"
                    if not required:
                        prompt += " [optional]"
                    prompt += ": "
                    
                    value = input(prompt)
                    if value or required:  # Only add if provided or required
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
    
    def test_connection(self):
        """Test the connection and show response time"""
        import time
        
        print("\nTesting connection...")
        start_time = time.time()
        
        response = self.send_request({
            "method": "tools/list",
            "params": {}
        })
        
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        if response and "result" in response:
            print(f"✅ Connection successful! Response time: {elapsed:.2f}ms")
        else:
            print(f"❌ Connection failed")
    
    def run_interactive_session(self):
        """Run the interactive command-line interface"""
        print("=" * 60)
        print("MCP Lambda Interactive Client")
        print("=" * 60)
        
        if not self.start():
            print("Failed to connect to server")
            print("\nTroubleshooting tips:")
            print("1. Check the URL is correct")
            print("2. Ensure the Lambda function is deployed")
            print("3. Verify API Gateway is configured correctly")
            print("4. Check CloudWatch logs for errors")
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
            print("  6. Test Connection")
            print("  7. Raw Request (Advanced)")
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
                    self.test_connection()
                elif choice == "7":
                    self.raw_request()
                else:
                    print("Invalid choice")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                print(f"Error: {e}")
    
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
    if len(sys.argv) < 2:
        print("Usage: python3 interactive_client_lambda.py <api-endpoint-url>")
        print("\nExample:")
        print("  python3 interactive_client_lambda.py https://abc123.execute-api.us-east-1.amazonaws.com/prod/mcp")
        print("\nTo get your endpoint URL, run:")
        print("  aws cloudformation describe-stacks --stack-name your-stack-name \\")
        print("    --query \"Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue\" --output text")
        sys.exit(1)
    
    endpoint_url = sys.argv[1]
    
    print(f"Connecting to: {endpoint_url}")
    print()
    
    try:
        client = InteractiveMCPLambdaClient(endpoint_url)
        client.run_interactive_session()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()