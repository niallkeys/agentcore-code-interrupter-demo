output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_url
}

output "dynamodb_table_name" {
  description = "DynamoDB table name for tool metadata"
  value       = module.dynamodb.table_name
}

output "s3_bucket_name" {
  description = "S3 bucket name for code artifacts"
  value       = module.s3.bucket_name
}

output "tool_manager_lambda_arn" {
  description = "Tool Manager Lambda function ARN"
  value       = module.lambda.tool_manager_arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = module.cloudwatch.log_group_name
}
