# Dynamic Tool Runtime - Terraform Infrastructure

This directory contains Terraform configurations for deploying the Dynamic Tool Runtime system on AWS.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- Python 3.12 (for Lambda functions)

## Project Structure

```
terraform/
├── main.tf                 # Root module configuration
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── bootstrap/              # State management setup
├── modules/                # Reusable Terraform modules
│   ├── api_gateway/       # API Gateway configuration
│   ├── cloudwatch/        # Monitoring and logging
│   ├── dynamodb/          # Tool metadata storage
│   ├── iam/               # IAM roles and policies
│   ├── lambda/            # Lambda functions
│   └── s3/                # Code artifact storage
└── environments/          # Environment-specific configs
    ├── dev.tfvars
    ├── staging.tfvars
    └── prod.tfvars
```

## Deployment Steps

### 1. Bootstrap State Management (First Time Only)

Before deploying the main infrastructure, set up Terraform state management:

```bash
cd terraform/bootstrap

# Initialize Terraform
terraform init

# Deploy state bucket and lock table for dev environment
terraform apply \
  -var="environment=dev" \
  -var="state_bucket_name=dynamic-tool-runtime-tfstate-dev" \
  -var="lock_table_name=dynamic-tool-runtime-tflock-dev"
```

Repeat for staging and prod environments as needed.

### 2. Deploy Main Infrastructure

```bash
cd terraform

# Initialize Terraform with backend configuration
terraform init -backend-config=environments/dev-backend.hcl

# Review the deployment plan
terraform plan -var-file=environments/dev.tfvars

# Deploy the infrastructure
terraform apply -var-file=environments/dev.tfvars
```

### 3. Deploy to Other Environments

For staging:
```bash
terraform init -backend-config=environments/staging-backend.hcl -reconfigure
terraform apply -var-file=environments/staging.tfvars
```

For production:
```bash
terraform init -backend-config=environments/prod-backend.hcl -reconfigure
terraform apply -var-file=environments/prod.tfvars
```

## Infrastructure Components

### DynamoDB Table
- Stores tool metadata and definitions
- Global secondary indexes for agent-based and code-hash lookups
- Point-in-time recovery enabled
- Server-side encryption enabled

### S3 Bucket
- Stores validated code artifacts
- Versioning enabled for audit trail
- Server-side encryption (AES256)
- Lifecycle policies for cost optimization

### Lambda Functions
- **Tool Manager**: Orchestrates tool lifecycle operations
- **Authorizer**: Handles API authentication
- **Monitoring**: Processes logs and metrics
- Runtime: Python 3.12
- X-Ray tracing enabled

### API Gateway
- HTTP API with custom Lambda authorizer
- CORS enabled for web clients
- CloudWatch logging for all requests
- Routes: POST/GET/PUT/DELETE /tools, POST /tools/{toolId}/execute

### IAM Roles
- Least privilege access policies
- Separate roles for different Lambda functions
- Bedrock access for Code Interpreter integration

### CloudWatch
- Log groups with retention policies
- Custom metrics and alarms
- Dashboard for system monitoring
- S3 bucket for long-term log storage

## Configuration Variables

Key variables to customize per environment:

- `environment`: Environment name (dev/staging/prod)
- `aws_region`: AWS region for deployment
- `agentcore_gateway_url`: AgentCore Gateway endpoint
- `terraform_state_bucket`: S3 bucket for Terraform state
- `terraform_lock_table`: DynamoDB table for state locking

## Outputs

After deployment, Terraform outputs:

- `api_gateway_url`: API endpoint for tool operations
- `dynamodb_table_name`: Table name for tool metadata
- `s3_bucket_name`: Bucket name for code artifacts
- `tool_manager_lambda_arn`: Lambda function ARN
- `cloudwatch_log_group`: Log group name

## Updating Lambda Code

Lambda functions use placeholder code initially. To deploy actual code:

1. Build your Lambda deployment package
2. Update the `filename` and `source_code_hash` in `modules/lambda/main.tf`
3. Run `terraform apply` to update the functions

## Cleanup

To destroy all infrastructure:

```bash
# Destroy main infrastructure
terraform destroy -var-file=environments/dev.tfvars

# Destroy state management (optional, only if completely removing)
cd bootstrap
terraform destroy \
  -var="environment=dev" \
  -var="state_bucket_name=dynamic-tool-runtime-tfstate-dev" \
  -var="lock_table_name=dynamic-tool-runtime-tflock-dev"
```

## Security Considerations

- All S3 buckets have public access blocked
- Server-side encryption enabled on all storage
- IAM roles follow least privilege principle
- CloudWatch logs retained for audit purposes
- X-Ray tracing enabled for debugging

## Cost Optimization

- DynamoDB uses on-demand billing
- S3 lifecycle policies archive old versions
- Lambda functions sized appropriately
- CloudWatch log retention limits set
- Pay-per-request pricing where possible
