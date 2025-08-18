#!/usr/bin/env python3
"""Simplified MCP Server - Minimal code approach"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_framework.simplified import tool, resource, prompt, serve

# Just write functions with decorators - no class needed!

@tool("get_weather", "Get weather for a location")
async def get_weather(location: str) -> dict:
    """Just a simple function that returns weather data"""
    return {
        "location": location,
        "temperature": "72°F",
        "condition": "Sunny"
    }

@tool("calculate", "Perform a calculation")
async def calculate(expression: str) -> dict:
    """Simple calculator"""
    try:
        result = eval(expression)  # Just for demo
        return {"expression": expression, "result": result}
    except:
        return {"error": "Invalid expression"}

@resource("config://settings")
async def settings() -> dict:
    """Server configuration"""
    return {
        "version": "1.0.0",
        "environment": "demo"
    }

@prompt("analyze")
async def analyze_prompt(context: dict) -> str:
    """Generate an analysis prompt"""
    return f"Please analyze: {context}"

# That's it! Just one line to serve:
if __name__ == "__main__":
    serve(name="simple-mcp", version="1.0.0")