terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration is provided via backend config file
  # Run: terraform init -backend-config=environments/dev-backend.hcl
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "DynamicToolRuntime"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# DynamoDB for tool metadata
module "dynamodb" {
  source = "./modules/dynamodb"

  environment = var.environment
  table_name  = "${var.project_name}-tools-${var.environment}"
}

# S3 for code artifacts
module "s3" {
  source = "./modules/s3"

  environment = var.environment
  bucket_name = "${var.project_name}-artifacts-${var.environment}"
  log_bucket  = module.cloudwatch.log_bucket_id
}

# Lambda functions
module "lambda" {
  source = "./modules/lambda"

  environment           = var.environment
  tool_manager_role_arn = module.iam.tool_manager_role_arn
  monitoring_role_arn   = module.iam.monitoring_role_arn
  dynamodb_table_name   = module.dynamodb.table_name
  s3_bucket_name        = module.s3.bucket_name
  agentcore_gateway_url = var.agentcore_gateway_url
}

# API Gateway
module "api_gateway" {
  source = "./modules/api_gateway"

  environment             = var.environment
  tool_manager_invoke_arn = module.lambda.tool_manager_invoke_arn
  authorizer_invoke_arn   = module.lambda.authorizer_invoke_arn
}

# IAM roles and policies
module "iam" {
  source = "./modules/iam"

  environment        = var.environment
  dynamodb_table_arn = module.dynamodb.table_arn
  s3_bucket_arn      = module.s3.bucket_arn
  log_group_arns     = module.cloudwatch.log_group_arns
}

# CloudWatch logging and monitoring
module "cloudwatch" {
  source = "./modules/cloudwatch"

  environment  = var.environment
  project_name = var.project_name
}
