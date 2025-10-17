output "table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.tools.name
}

output "table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.tools.arn
}

output "table_stream_arn" {
  description = "DynamoDB table stream ARN"
  value       = aws_dynamodb_table.tools.stream_arn
}
