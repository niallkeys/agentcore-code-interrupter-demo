variable "environment" {
  description = "Environment name"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket name"
  type        = string
}

variable "log_bucket" {
  description = "S3 bucket for access logs"
  type        = string
}
