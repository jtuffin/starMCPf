#!/usr/bin/env python3
"""Package MCP server for AWS Lambda deployment"""

import os
import sys
import shutil
import zipfile
import argparse
import tempfile
from pathlib import Path

def create_lambda_package(server_file: str, output_file: str = "mcp_lambda.zip"):
    """Create a Lambda deployment package for an MCP server"""
    
    print(f"Packaging MCP server: {server_file}")
    print(f"Output: {output_file}")
    
    # Create temp directory for packaging
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy the MCP framework
        framework_src = Path(__file__).parent.parent / "src" / "mcp_framework"
        if framework_src.exists():
            print(f"Copying MCP framework from {framework_src}")
            shutil.copytree(framework_src, temp_path / "mcp_framework")
        else:
            print("Warning: MCP framework not found, assuming it will be in Lambda layer")
        
        # Copy the server file
        server_path = Path(server_file)
        if not server_path.exists():
            print(f"Error: Server file {server_file} not found")
            return False
        
        # Copy server to temp directory
        shutil.copy2(server_path, temp_path / "server.py")
        
        # Create Lambda handler wrapper
        handler_code = '''"""Lambda handler for MCP server"""
import json
import sys
import asyncio
import logging
from pathlib import Path

# Set up CloudWatch logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import the user's server
sys.path.insert(0, str(Path(__file__).parent))
import server

# Import framework components
from mcp_framework.simplified import handle_request, _tools, _resources, _prompts, _server_config

# Initialize the server by importing it (decorators will register everything)
# The server module should already have registered all tools/resources/prompts

async def process_request(event):
    """Process an MCP request"""
    # Parse the request
    if "body" in event:
        body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
    else:
        body = event
    
    # Log the incoming request
    logger.info(f"MCP Request: {json.dumps(body)}")
    
    # Handle the MCP request
    response = await handle_request(body)
    
    # Log the response
    logger.info(f"MCP Response: {json.dumps(response)}")
    
    # Return Lambda response format
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(response)
    }

def lambda_handler(event, context):
    """AWS Lambda entry point"""
    
    # Log Lambda invocation details
    logger.info(f"Lambda invoked with request ID: {context.request_id}")
    logger.info(f"Event: {json.dumps(event)}")
    
    # Handle OPTIONS request for CORS
    if event.get("httpMethod") == "OPTIONS":
        logger.info("Handling OPTIONS request for CORS")
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": ""
        }
    
    try:
        # Process the MCP request
        result = asyncio.run(process_request(event))
        logger.info(f"Request processed successfully")
        return result
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e)})
        }
'''
        
        # Write Lambda handler
        handler_file = temp_path / "lambda_handler.py"
        handler_file.write_text(handler_code)
        
        # Create requirements.txt if needed
        requirements = temp_path / "requirements.txt"
        requirements.write_text("""# Minimal requirements for Lambda
# Add any additional dependencies your server needs
""")
        
        # Create the zip file
        print(f"Creating zip package: {output_file}")
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    if not file.endswith('.pyc') and '__pycache__' not in root:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(temp_path)
                        zipf.write(file_path, arcname)
                        print(f"  Added: {arcname}")
        
        # Get file size
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"\nPackage created successfully!")
        print(f"Size: {size_mb:.2f} MB")
        
        if size_mb > 50:
            print("Warning: Package is larger than 50MB, consider using Lambda layers")
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Package MCP server for Lambda")
    parser.add_argument("server", help="Path to MCP server Python file")
    parser.add_argument("-o", "--output", default="mcp_lambda.zip", 
                       help="Output zip file name")
    
    args = parser.parse_args()
    
    success = create_lambda_package(args.server, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()