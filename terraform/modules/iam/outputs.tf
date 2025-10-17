output "tool_manager_role_arn" {
  description = "Tool Manager Lambda role ARN"
  value       = aws_iam_role.tool_manager.arn
}

output "monitoring_role_arn" {
  description = "Monitoring Lambda role ARN"
  value       = aws_iam_role.monitoring.arn
}
