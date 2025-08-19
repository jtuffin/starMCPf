#!/usr/bin/env python3
"""Simplified MCP Server - Minimal code approach"""

import sys
import os
import re
import socket
import platform
import operator

# Add parent directory to path for local development
if __name__ == "__main__":
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
    
    # Get hostname and environment info
    hostname = socket.gethostname()
    is_lambda = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
    
    return {
        "version": "1.0.0",
        "environment": "AWS Lambda" if is_lambda else "local",
        "hostname": hostname,
        "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "local"),
        "region": os.environ.get("AWS_REGION", "local")
    }

@tool("get_system_info", "Get system and environment information")
async def get_system_info() -> dict:
    """Get detailed system information"""
    
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "is_lambda": bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME")),
        "lambda_function": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "not-in-lambda"),
        "lambda_version": os.environ.get("AWS_LAMBDA_FUNCTION_VERSION", "n/a"),
        "aws_region": os.environ.get("AWS_REGION", "not-in-aws"),
        "aws_execution_env": os.environ.get("AWS_EXECUTION_ENV", "not-in-aws"),
        "memory_limit": os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", "n/a"),
        "log_group": os.environ.get("AWS_LAMBDA_LOG_GROUP_NAME", "n/a"),
        "request_id": os.environ.get("AWS_REQUEST_ID", "n/a")
    }

@prompt("analyze")
async def analyze_prompt(context: dict) -> str:
    """Generate an analysis prompt"""
    return f"Please analyze: {context}"

# That's it! Just one line to serve:
if __name__ == "__main__":
    serve(name="simple-mcp", version="1.0.0")