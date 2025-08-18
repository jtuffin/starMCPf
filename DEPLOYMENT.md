# AWS Lambda Deployment Guide

This guide explains how to deploy your MCP server to AWS Lambda with API Gateway.

## Prerequisites

1. **AWS Account**: You need an AWS account
2. **AWS CLI**: Install and configure the AWS CLI
   ```bash
   pip install awscli
   aws configure
   ```
3. **Python 3.9+**: Required for packaging

## Quick Deploy

Deploy your MCP server with one command:

```bash
./scripts/deploy_to_aws.sh my-mcp-stack examples/simple_demo.py
```

This will:
1. Package your MCP server into a Lambda-compatible zip
2. Create an S3 bucket for deployment artifacts
3. Upload the package to S3
4. Deploy a CloudFormation stack with Lambda and API Gateway
5. Return the API endpoint URL

## Deployment Process

### Step 1: Package Your Server

The packaging script creates a Lambda-ready zip file:

```bash
python3 scripts/package_lambda.py examples/simple_demo.py -o mcp_lambda.zip
```

This creates a zip containing:
- Your MCP server code
- The MCP framework
- A Lambda handler wrapper
- All necessary dependencies

### Step 2: Deploy to AWS

The deployment script handles everything:

```bash
./scripts/deploy_to_aws.sh [stack-name] [server-file] [s3-bucket]
```

Parameters:
- `stack-name`: CloudFormation stack name (default: mcp-server-stack)
- `server-file`: Path to your MCP server (default: examples/simple_demo.py)
- `s3-bucket`: S3 bucket for artifacts (auto-created if not specified)

### Step 3: Test Your Deployment

Once deployed, test with curl:

```bash
# List available tools
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# Call a tool
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/mcp \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc":"2.0",
    "id":2,
    "method":"tools/call",
    "params":{
      "name":"get_weather",
      "arguments":{"location":"San Francisco"}
    }
  }'
```

## CloudFormation Template

The template (`templates/mcp_lambda_stack.yaml`) creates:

### Resources
- **Lambda Function**: Runs your MCP server
- **API Gateway**: HTTP endpoint for the MCP protocol
- **IAM Role**: Permissions for Lambda execution
- **CloudWatch Logs**: For debugging and monitoring
- **CloudWatch Alarms**: For error and throttle monitoring

### Parameters
- `MCPServerName`: Name for your MCP server
- `LambdaCodeBucket`: S3 bucket containing the code
- `LambdaCodeKey`: S3 key for the zip file
- `LambdaMemorySize`: Memory allocation (128-10240 MB)
- `LambdaTimeout`: Function timeout (1-900 seconds)

### Outputs
- `ApiEndpoint`: The URL to access your MCP server
- `LambdaFunctionArn`: ARN of the Lambda function
- `ApiGatewayId`: API Gateway identifier

## Customization

### Adding Permissions

Edit the IAM role in the CloudFormation template to add permissions:

```yaml
Policies:
  - PolicyName: MCPLambdaPolicy
    PolicyDocument:
      Statement:
        # Add S3 access
        - Effect: Allow
          Action:
            - s3:GetObject
            - s3:PutObject
          Resource: !Sub 'arn:aws:s3:::my-bucket/*'
        
        # Add DynamoDB access
        - Effect: Allow
          Action:
            - dynamodb:GetItem
            - dynamodb:PutItem
          Resource: !Sub 'arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/my-table'
```

### Environment Variables

Add environment variables in the template:

```yaml
MCPLambdaFunction:
  Properties:
    Environment:
      Variables:
        MY_API_KEY: !Ref MyApiKeyParameter
        DATABASE_URL: !Ref DatabaseUrlParameter
```

### Using Lambda Layers

For large dependencies, use Lambda layers:

1. Create a layer with dependencies
2. Reference in the template:
   ```yaml
   MCPLambdaFunction:
     Properties:
       Layers:
         - !Ref MyDependenciesLayer
   ```

## Monitoring

### CloudWatch Logs

View logs in the AWS Console or CLI:

```bash
aws logs tail /aws/lambda/your-mcp-function --follow
```

### Metrics

Monitor in CloudWatch:
- Invocation count
- Duration
- Error rate
- Throttles
- Concurrent executions

### Alarms

The template includes alarms for:
- Lambda errors
- Lambda throttles

Add more as needed in the template.

## Cost Optimization

### Lambda Pricing
- First 1M requests/month: Free
- Next requests: $0.20 per 1M requests
- Duration: $0.0000166667 per GB-second

### Tips
1. **Right-size memory**: Start with 512MB, adjust based on metrics
2. **Optimize code**: Minimize cold starts and execution time
3. **Use caching**: Cache responses when appropriate
4. **Set appropriate timeout**: Don't set unnecessarily high timeouts

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure all dependencies are in the package
   - Check Python version compatibility (Lambda uses 3.9)

2. **Timeout errors**
   - Increase Lambda timeout in template
   - Optimize code for faster execution

3. **CORS errors**
   - The template includes CORS headers
   - Check API Gateway OPTIONS method

4. **Permission denied**
   - Check IAM role permissions
   - Ensure Lambda can access required resources

5. **Package too large**
   - Lambda limit is 250MB unzipped
   - Use layers for large dependencies
   - Minimize included files

### Debug Mode

Add debug logging:

```python
import os
import logging

if os.environ.get('DEBUG') == 'true':
    logging.basicConfig(level=logging.DEBUG)
```

Set in CloudFormation:
```yaml
Environment:
  Variables:
    DEBUG: 'true'
```

## Cleanup

To remove all resources:

```bash
# Delete the CloudFormation stack
aws cloudformation delete-stack --stack-name my-mcp-stack

# Optionally, clean up S3 bucket
aws s3 rm s3://your-bucket/mcp-deployments/ --recursive
```

## Advanced Deployment

### Multi-Region

Deploy to multiple regions:

```bash
for region in us-east-1 eu-west-1 ap-southeast-1; do
  AWS_REGION=$region ./scripts/deploy_to_aws.sh mcp-$region
done
```

### CI/CD Pipeline

Example GitHub Actions workflow:

```yaml
name: Deploy MCP Server
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      - run: ./scripts/deploy_to_aws.sh production-mcp
```

## Summary

The deployment process is straightforward:

1. **Write your MCP server** using the simplified or class-based approach
2. **Package it** with `package_lambda.py`
3. **Deploy it** with `deploy_to_aws.sh`
4. **Use the API endpoint** in your applications

The framework handles all the complexity of Lambda adaptation, API Gateway integration, and MCP protocol compliance.