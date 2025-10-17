output "tool_manager_arn" {
  description = "Tool Manager Lambda ARN"
  value       = aws_lambda_function.tool_manager.arn
}

output "tool_manager_invoke_arn" {
  description = "Tool Manager Lambda invoke ARN"
  value       = aws_lambda_function.tool_manager.invoke_arn
}

output "authorizer_invoke_arn" {
  description = "Authorizer Lambda invoke ARN"
  value       = aws_lambda_function.authorizer.invoke_arn
}

output "monitoring_arn" {
  description = "Monitoring Lambda ARN"
  value       = aws_lambda_function.monitoring.arn
}
