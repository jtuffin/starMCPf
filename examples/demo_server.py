"""Demo MCP Server implementation using the MCP Framework"""

import asyncio
import json
import random
from typing import Dict, Any
from datetime import datetime

# This would normally be: from mcp_framework import MCPServer, Tool, Resource, Prompt
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_framework import MCPServer, Tool, Resource, Prompt, create_lambda_handler


class DemoMCPServer(MCPServer):
    """Example MCP Server with various tools, resources, and prompts"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        # Initialize any business logic connections here
        self.database = {}  # Mock database
        self.metrics = {"requests": 0, "errors": 0}
    
    # ========== TOOLS ==========
    
    @Tool(
        name="get_weather",
        description="Get current weather for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or zip code"}
            },
            "required": ["location"]
        }
    )
    async def get_weather(self, location: str) -> Dict[str, Any]:
        """Fetch weather data (mock implementation)"""
        self.metrics["requests"] += 1
        
        # Ensure location is a string
        location = str(location)
        
        # Mock location data - map zip codes to cities
        zip_to_city = {
            "10001": {"city": "New York", "state": "NY", "country": "USA"},
            "94102": {"city": "San Francisco", "state": "CA", "country": "USA"},
            "90210": {"city": "Beverly Hills", "state": "CA", "country": "USA"},
            "60601": {"city": "Chicago", "state": "IL", "country": "USA"},
            "02134": {"city": "Boston", "state": "MA", "country": "USA"},
            "98101": {"city": "Seattle", "state": "WA", "country": "USA"},
            "33101": {"city": "Miami", "state": "FL", "country": "USA"},
            "30301": {"city": "Atlanta", "state": "GA", "country": "USA"},
            "75201": {"city": "Dallas", "state": "TX", "country": "USA"},
            "80202": {"city": "Denver", "state": "CO", "country": "USA"},
        }
        
        # Determine location details
        location_info = {}
        if location.isdigit() and len(location) == 5:
            # It's a zip code
            if location in zip_to_city:
                location_info = zip_to_city[location]
                display_location = f"{location_info['city']}, {location_info['state']}"
            else:
                # Unknown zip code - make up a generic response
                location_info = {"city": "Unknown City", "state": "XX", "country": "USA"}
                display_location = f"Area {location}"
        else:
            # It's a city name
            display_location = location
            # Try to parse state if provided
            if "," in location:
                parts = location.split(",")
                location_info = {
                    "city": parts[0].strip(),
                    "state": parts[1].strip() if len(parts) > 1 else "",
                    "country": parts[2].strip() if len(parts) > 2 else "USA"
                }
            else:
                location_info = {"city": location, "state": "", "country": "USA"}
        
        # Mock weather data
        weather_conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Stormy"]
        temperature = random.randint(50, 95)
        
        return {
            "location": display_location,
            "location_details": location_info,
            "temperature": f"{temperature}°F",
            "condition": random.choice(weather_conditions),
            "humidity": f"{random.randint(30, 80)}%",
            "wind": f"{random.randint(5, 25)} mph",
            "timestamp": datetime.now().isoformat()
        }
    
    @Tool(
        name="calculate",
        description="Perform mathematical calculations",
        parameters={
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
            },
            "required": ["expression"]
        }
    )
    async def calculate(self, expression: str) -> Dict[str, Any]:
        """Evaluate mathematical expressions safely"""
        self.metrics["requests"] += 1
        
        try:
            # In production, use a proper math parser for safety
            # This is just for demo purposes
            allowed_chars = "0123456789+-*/()., "
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                return {
                    "expression": expression,
                    "result": result,
                    "type": type(result).__name__
                }
            else:
                raise ValueError("Invalid characters in expression")
        except Exception as e:
            self.metrics["errors"] += 1
            return {
                "expression": expression,
                "error": str(e)
            }
    
    @Tool(
        name="store_data",
        description="Store data in the database",
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Storage key"},
                "value": {"description": "Value to store (any JSON type)"}
            },
            "required": ["key", "value"]
        }
    )
    async def store_data(self, key: str, value: Any) -> Dict[str, Any]:
        """Store data in mock database"""
        self.metrics["requests"] += 1
        self.database[key] = value
        
        return {
            "success": True,
            "key": key,
            "stored_at": datetime.now().isoformat()
        }
    
    @Tool(
        name="retrieve_data",
        description="Retrieve data from the database",
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Storage key"}
            },
            "required": ["key"]
        }
    )
    async def retrieve_data(self, key: str) -> Dict[str, Any]:
        """Retrieve data from mock database"""
        self.metrics["requests"] += 1
        
        if key in self.database:
            return {
                "success": True,
                "key": key,
                "value": self.database[key]
            }
        else:
            return {
                "success": False,
                "key": key,
                "error": "Key not found"
            }
    
    # ========== RESOURCES ==========
    
    @Resource(uri="config://settings", description="Server configuration settings")
    async def get_settings(self) -> Dict[str, Any]:
        """Return server configuration"""
        return {
            "server_name": self.config.get("name", "demo-mcp-server"),
            "version": self.config.get("version", "0.1.0"),
            "environment": self.config.get("environment", "development"),
            "features": {
                "weather": True,
                "calculator": True,
                "database": True
            }
        }
    
    @Resource(uri="metrics://stats", description="Server metrics and statistics")
    async def get_metrics(self) -> Dict[str, Any]:
        """Return server metrics"""
        return {
            "total_requests": self.metrics["requests"],
            "total_errors": self.metrics["errors"],
            "error_rate": self.metrics["errors"] / max(self.metrics["requests"], 1),
            "database_size": len(self.database),
            "uptime": "simulated",
            "timestamp": datetime.now().isoformat()
        }
    
    @Resource(uri="data://database", description="Current database contents")
    async def get_database(self) -> Dict[str, Any]:
        """Return all database contents"""
        return {
            "size": len(self.database),
            "keys": list(self.database.keys()),
            "data": self.database
        }
    
    # ========== PROMPTS ==========
    
    @Prompt(name="analyze_weather", description="Generate weather analysis prompt")
    async def analyze_weather_prompt(self, context: Dict[str, Any]) -> str:
        """Generate a weather analysis prompt"""
        location = context.get("location", "unknown location")
        return f"""Analyze the weather conditions for {location}. Consider the following aspects:
1. Current temperature and how it compares to seasonal averages
2. Precipitation likelihood and type
3. Wind conditions and their impact on outdoor activities
4. Air quality and visibility
5. Recommendations for appropriate clothing and activities

Provide a comprehensive analysis that would be helpful for someone planning their day."""
    
    @Prompt(name="data_insights", description="Generate data insights prompt")
    async def data_insights_prompt(self, context: Dict[str, Any]) -> str:
        """Generate a data insights prompt"""
        data_keys = context.get("keys", [])
        return f"""Analyze the stored data with keys: {', '.join(data_keys)}. Provide insights on:
1. Data patterns and trends
2. Potential relationships between different data points
3. Anomalies or outliers
4. Recommendations for data organization
5. Suggestions for additional data that might be valuable

Focus on actionable insights that could improve data utilization."""


# Lambda handler creation
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda entry point"""
    config = {
        "name": "demo-mcp-server",
        "version": "0.1.0",
        "environment": os.environ.get("ENVIRONMENT", "development")
    }
    
    handler = create_lambda_handler(DemoMCPServer, config)
    return handler(event, context)


# Local testing
if __name__ == "__main__":
    try:
        import structlog
        # Configure logging for local testing
        structlog.configure(
            processors=[
                structlog.dev.ConsoleRenderer()
            ]
        )
    except ImportError:
        # Use standard logging if structlog not available
        import logging
        logging.basicConfig(level=logging.INFO)
    
    # Create server instance
    server = DemoMCPServer({
        "name": "demo-mcp-server",
        "version": "0.1.0"
    })
    
    # Test the server
    async def test_server():
        print("\n=== Demo MCP Server Test ===\n")
        
        # List tools
        print("Available Tools:")
        for tool in server.list_tools():
            print(f"  - {tool['name']}: {tool['description']}")
        
        # List resources
        print("\nAvailable Resources:")
        for resource in server.list_resources():
            print(f"  - {resource['uri']}: {resource['description']}")
        
        # List prompts
        print("\nAvailable Prompts:")
        for prompt in server.list_prompts():
            print(f"  - {prompt['name']}: {prompt['description']}")
        
        # Test tool execution
        print("\n--- Testing Tools ---")
        
        # Test weather tool
        weather = await server.handle_tool_call("get_weather", {"location": "New York"})
        print(f"\nWeather in New York: {json.dumps(weather, indent=2)}")
        
        # Test calculator tool
        calc = await server.handle_tool_call("calculate", {"expression": "42 * 10 + 7"})
        print(f"\nCalculation result: {json.dumps(calc, indent=2)}")
        
        # Test data storage
        store = await server.handle_tool_call("store_data", {"key": "test_key", "value": {"data": "test_value"}})
        print(f"\nStore result: {json.dumps(store, indent=2)}")
        
        retrieve = await server.handle_tool_call("retrieve_data", {"key": "test_key"})
        print(f"\nRetrieve result: {json.dumps(retrieve, indent=2)}")
        
        # Test resources
        print("\n--- Testing Resources ---")
        
        settings = await server.handle_resource_request("config://settings")
        print(f"\nSettings: {json.dumps(settings, indent=2)}")
        
        metrics = await server.handle_resource_request("metrics://stats")
        print(f"\nMetrics: {json.dumps(metrics, indent=2)}")
        
        # Test prompts
        print("\n--- Testing Prompts ---")
        
        weather_prompt = await server.handle_prompt_request("analyze_weather", {"location": "San Francisco"})
        print(f"\nWeather Analysis Prompt:\n{weather_prompt}")
        
        print("\n=== Test Complete ===\n")
    
    # Run the test
    asyncio.run(test_server())