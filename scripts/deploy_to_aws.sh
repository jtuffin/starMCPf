#!/bin/bash
# Deploy MCP server to AWS Lambda and API Gateway

set -e

# Configuration
STACK_NAME="${1:-mcp-server-stack}"
SERVER_FILE="${2:-examples/simple_demo.py}"
S3_BUCKET="${3:-}"
REGION="${AWS_REGION:-us-east-1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}MCP Server AWS Deployment${NC}"
echo "================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Install it with: pip install awscli"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

# Get or create S3 bucket
if [ -z "$S3_BUCKET" ]; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    S3_BUCKET="mcp-lambda-deployments-${ACCOUNT_ID}-${REGION}"
    
    echo "Creating S3 bucket: $S3_BUCKET"
    
    if [ "$REGION" = "us-east-1" ]; then
        aws s3api create-bucket --bucket "$S3_BUCKET" --region "$REGION" 2>/dev/null || true
    else
        aws s3api create-bucket \
            --bucket "$S3_BUCKET" \
            --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION" 2>/dev/null || true
    fi
fi

echo -e "${GREEN}✓${NC} Using S3 bucket: $S3_BUCKET"

# Package the Lambda function
echo ""
echo "Packaging Lambda function..."
PACKAGE_FILE="mcp_lambda_${STACK_NAME}.zip"

python3 scripts/package_lambda.py "$SERVER_FILE" -o "$PACKAGE_FILE"

if [ ! -f "$PACKAGE_FILE" ]; then
    echo -e "${RED}Error: Failed to create Lambda package${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Lambda package created: $PACKAGE_FILE"

# Upload to S3
echo ""
echo "Uploading to S3..."
TIMESTAMP=$(date +%Y%m%d%H%M%S)
S3_KEY="mcp-deployments/${STACK_NAME}/${TIMESTAMP}/mcp_lambda.zip"

aws s3 cp "$PACKAGE_FILE" "s3://${S3_BUCKET}/${S3_KEY}"

echo -e "${GREEN}✓${NC} Uploaded to: s3://${S3_BUCKET}/${S3_KEY}"

# Deploy CloudFormation stack
echo ""
echo "Deploying CloudFormation stack..."

aws cloudformation deploy \
    --template-file templates/mcp_lambda_stack.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        MCPServerName="${STACK_NAME%-stack}" \
        LambdaCodeBucket="$S3_BUCKET" \
        LambdaCodeKey="$S3_KEY" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$REGION"

echo -e "${GREEN}✓${NC} CloudFormation stack deployed"

# Get the outputs
echo ""
echo "Getting deployment information..."

API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
    --output text \
    --region "$REGION")

echo ""
echo -e "${GREEN}Deployment Complete!${NC}"
echo "==================="
echo ""
echo "API Endpoint: ${API_ENDPOINT}"
echo ""
echo "Test your MCP server with:"
echo -e "${YELLOW}curl -X POST ${API_ENDPOINT} \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\",\"params\":{}}'${NC}"
echo ""
echo "To use with Claude Desktop, add to your config:"
echo -e "${YELLOW}{
  \"mcpServers\": {
    \"${STACK_NAME%-stack}\": {
      \"url\": \"${API_ENDPOINT}\"
    }
  }
}${NC}"
echo ""
echo "To delete the stack later:"
echo -e "${YELLOW}aws cloudformation delete-stack --stack-name $STACK_NAME${NC}"