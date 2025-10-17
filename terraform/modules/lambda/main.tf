resource "aws_lambda_function" "tool_manager" {
  function_name = "tool-manager-${var.environment}"
  role          = var.tool_manager_role_arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 300
  memory_size   = 1024

  filename         = "${path.module}/placeholder.zip"
  source_code_hash = filebase64sha256("${path.module}/placeholder.zip")

  environment {
    variables = {
      ENVIRONMENT           = var.environment
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
      S3_BUCKET_NAME        = var.s3_bucket_name
      AGENTCORE_GATEWAY_URL = var.agentcore_gateway_url
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = {
    Name = "tool-manager-${var.environment}"
  }
}

resource "aws_lambda_function" "authorizer" {
  function_name = "api-authorizer-${var.environment}"
  role          = var.tool_manager_role_arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 256

  filename         = "${path.module}/placeholder.zip"
  source_code_hash = filebase64sha256("${path.module}/placeholder.zip")

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Name = "api-authorizer-${var.environment}"
  }
}

resource "aws_lambda_function" "monitoring" {
  function_name = "monitoring-${var.environment}"
  role          = var.monitoring_role_arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 60
  memory_size   = 512

  filename         = "${path.module}/placeholder.zip"
  source_code_hash = filebase64sha256("${path.module}/placeholder.zip")

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = {
    Name = "monitoring-${var.environment}"
  }
}

resource "aws_cloudwatch_log_group" "tool_manager" {
  name              = "/aws/lambda/tool-manager-${var.environment}"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "authorizer" {
  name              = "/aws/lambda/api-authorizer-${var.environment}"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "monitoring" {
  name              = "/aws/lambda/monitoring-${var.environment}"
  retention_in_days = 30
}
