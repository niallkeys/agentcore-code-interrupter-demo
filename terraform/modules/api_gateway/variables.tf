variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tool_manager_invoke_arn" {
  description = "Tool Manager Lambda invoke ARN"
  type        = string
}

variable "authorizer_invoke_arn" {
  description = "Authorizer Lambda invoke ARN"
  type        = string
}
