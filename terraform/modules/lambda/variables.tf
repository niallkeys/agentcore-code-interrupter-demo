variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tool_manager_role_arn" {
  description = "IAM role ARN for Tool Manager Lambda"
  type        = string
}

variable "monitoring_role_arn" {
  description = "IAM role ARN for Monitoring Lambda"
  type        = string
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket name"
  type        = string
}

variable "agentcore_gateway_url" {
  description = "AgentCore Gateway URL"
  type        = string
}
