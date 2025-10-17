output "log_bucket_id" {
  description = "S3 log bucket ID"
  value       = aws_s3_bucket.logs.id
}

output "log_group_name" {
  description = "Primary CloudWatch log group name"
  value       = aws_cloudwatch_log_group.system.name
}

output "log_group_arns" {
  description = "CloudWatch log group ARNs"
  value = [
    aws_cloudwatch_log_group.system.arn,
    aws_cloudwatch_log_group.security.arn,
    aws_cloudwatch_log_group.audit.arn,
    "${aws_cloudwatch_log_group.system.arn}:*",
    "${aws_cloudwatch_log_group.security.arn}:*",
    "${aws_cloudwatch_log_group.audit.arn}:*"
  ]
}

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}
