resource "aws_apigatewayv2_api" "main" {
  name          = "dynamic-tool-runtime-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
    max_age       = 300
  }

  tags = {
    Name = "dynamic-tool-runtime-${var.environment}"
  }
}

resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  tags = {
    Name = "dynamic-tool-runtime-${var.environment}"
  }
}

resource "aws_apigatewayv2_authorizer" "lambda" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "REQUEST"
  authorizer_uri   = var.authorizer_invoke_arn
  identity_sources = ["$request.header.Authorization"]
  name             = "lambda-authorizer"

  authorizer_payload_format_version = "2.0"
  enable_simple_responses           = true
}

resource "aws_apigatewayv2_integration" "tool_manager" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  integration_uri        = var.tool_manager_invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# POST /tools - Create tool
resource "aws_apigatewayv2_route" "create_tool" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /tools"
  target    = "integrations/${aws_apigatewayv2_integration.tool_manager.id}"

  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.lambda.id
}

# GET /tools/{toolId} - Get tool
resource "aws_apigatewayv2_route" "get_tool" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /tools/{toolId}"
  target    = "integrations/${aws_apigatewayv2_integration.tool_manager.id}"

  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.lambda.id
}

# PUT /tools/{toolId} - Update tool
resource "aws_apigatewayv2_route" "update_tool" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "PUT /tools/{toolId}"
  target    = "integrations/${aws_apigatewayv2_integration.tool_manager.id}"

  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.lambda.id
}

# DELETE /tools/{toolId} - Delete tool
resource "aws_apigatewayv2_route" "delete_tool" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "DELETE /tools/{toolId}"
  target    = "integrations/${aws_apigatewayv2_integration.tool_manager.id}"

  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.lambda.id
}

# POST /tools/{toolId}/execute - Execute tool
resource "aws_apigatewayv2_route" "execute_tool" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /tools/{toolId}/execute"
  target    = "integrations/${aws_apigatewayv2_integration.tool_manager.id}"

  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.lambda.id
}

resource "aws_lambda_permission" "api_gateway_tool_manager" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = split(":", var.tool_manager_invoke_arn)[6]
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_authorizer" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = split(":", var.authorizer_invoke_arn)[6]
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/dynamic-tool-runtime-${var.environment}"
  retention_in_days = 30
}
