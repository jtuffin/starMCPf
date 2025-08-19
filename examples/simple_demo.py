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
    """Simple calculator - safely evaluates basic math expressions"""
    import re
    
    try:
        # Remove whitespace
        expr = expression.replace(" ", "")
        
        # Only allow numbers, operators, parentheses, and decimal points
        if not re.match(r'^[0-9+\-*/().\s]+$', expr):
            return {"error": "Invalid characters in expression"}
        
        # Parse for basic operations
        # Support: +, -, *, /, parentheses, and decimals
        # Use a simple recursive descent parser or safer evaluation
        
        # For simplicity, use a basic operator parser
        def safe_eval(s):
            # Check for balanced parentheses
            if s.count('(') != s.count(')'):
                raise ValueError("Unbalanced parentheses")
            
            # Parse the expression step by step
            # This is a simple implementation - could be enhanced
            import operator
            ops = {'+': operator.add, '-': operator.sub, 
                   '*': operator.mul, '/': operator.truediv}
            
            # Handle parentheses first
            while '(' in s:
                # Find innermost parentheses
                start = s.rfind('(')
                end = s.find(')', start)
                if end == -1:
                    raise ValueError("Unbalanced parentheses")
                inner = s[start+1:end]
                inner_result = safe_eval(inner)
                s = s[:start] + str(inner_result) + s[end+1:]
            
            # Handle leading negative number BEFORE other operations
            if s.startswith('-'):
                s = '0' + s  # Convert -x to 0-x for easier parsing
            
            # Handle multiplication and division
            for op in ['*', '/']:
                while op in s:
                    match = re.search(r'([\d.]+)\s*[' + re.escape(op) + r']\s*([\d.]+)', s)
                    if match:
                        left = float(match.group(1))
                        right = float(match.group(2))
                        if op == '/' and right == 0:
                            raise ValueError("Division by zero")
                        result = ops[op](left, right)
                        s = s[:match.start()] + str(result) + s[match.end():]
                    else:
                        break
            
            # Handle addition and subtraction
            # Need to handle negative numbers properly
            s = re.sub(r'--', '+', s)  # Double negative becomes positive
            
            # Process addition first, then subtraction
            # This ensures proper left-to-right evaluation
            while '+' in s:
                match = re.search(r'(-?[\d.]+)\s*\+\s*(-?[\d.]+)', s)
                if match:
                    left = float(match.group(1))
                    right = float(match.group(2))
                    result = left + right
                    s = s[:match.start()] + str(result) + s[match.end():]
                else:
                    break
            
            while '-' in s[1:]:  # Skip first char if negative
                match = re.search(r'(-?[\d.]+)\s*-\s*(-?[\d.]+)', s)
                if match:
                    left = float(match.group(1))
                    right = float(match.group(2))
                    result = left - right
                    s = s[:match.start()] + str(result) + s[match.end():]
                else:
                    break
            
            # Return final number
            return float(s)
        
        result = safe_eval(expr)
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": f"Invalid expression: {str(e)}"}

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