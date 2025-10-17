resource "aws_dynamodb_table" "tools" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "toolId"

  attribute {
    name = "toolId"
    type = "S"
  }

  attribute {
    name = "agentId"
    type = "S"
  }

  attribute {
    name = "codeHash"
    type = "S"
  }

  global_secondary_index {
    name            = "AgentIdIndex"
    hash_key        = "agentId"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "CodeHashIndex"
    hash_key        = "codeHash"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  ttl {
    attribute_name = "expiresAt"
    enabled        = true
  }

  tags = {
    Name = var.table_name
  }
}
