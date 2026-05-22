terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Fetch OpenAI API Key from Parameter Store
data "aws_ssm_parameter" "openai_api_key" {
  name = "/reumatologia-app/openai-api-key"
}

# S3 Bucket for static website hosting
resource "aws_s3_bucket" "website" {
  bucket = "dra-enriquez-reservations-${random_id.bucket_suffix.hex}"
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket_public_access_block" "website" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "default" {
  name                              = "s3-oac-${random_id.bucket_suffix.hex}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontServicePrincipalReadOnly"
        Effect    = "Allow"
        Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.website.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.website.arn
          }
        }
      }
    ]
  })
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "website" {
  enabled             = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"

  origin {
    domain_name              = aws_s3_bucket.website.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.default.id
    origin_id                = "S3-Website"
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-Website"
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# DynamoDB Table
resource "aws_dynamodb_table" "reservations" {
  name         = "Reservations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "reservationId"

  attribute {
    name = "reservationId"
    type = "S"
  }

  attribute {
    name = "preferredDate"
    type = "S"
  }

  attribute {
    name = "calendarEventId"
    type = "S"
  }

  global_secondary_index {
    name            = "DateIndex"
    hash_key        = "preferredDate"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "CalendarEventIndex"
    hash_key        = "calendarEventId"
    projection_type = "ALL"
  }
}

resource "aws_dynamodb_table" "testimonies" {
  name         = "Testimonies"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

# SNS Topic
resource "aws_sns_topic" "reservations" {
  name = "reservation-notifications"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.reservations.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# Lambda Package (shared for all functions)
data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda_functions.zip"
}

resource "aws_lambda_function" "reservations" {
  filename         = data.archive_file.lambda.output_path
  function_name    = "reservation-handler"
  role             = aws_iam_role.reservation.arn
  handler          = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda.output_base64sha256
  runtime          = "python3.12"
  architectures    = ["arm64"]
  memory_size      = 128
  timeout          = 10

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.reservations.name
      SNS_TOPIC_ARN  = aws_sns_topic.reservations.arn
    }
  }

  layers = [aws_lambda_layer_version.google_api.arn]

}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.reservations.function_name}"
  retention_in_days = 7
}

# Admin Lambda Function

resource "aws_lambda_function" "admin" {
  filename         = data.archive_file.lambda.output_path
  function_name    = "admin-handler"
  role             = aws_iam_role.admin.arn
  handler          = "admin_function.lambda_handler"
  source_code_hash = data.archive_file.lambda.output_base64sha256
  runtime          = "python3.12"
  architectures    = ["arm64"]
  memory_size      = 128
  timeout          = 10

  environment {
    variables = {
      DYNAMODB_TABLE    = aws_dynamodb_table.reservations.name
      TESTIMONIES_TABLE = aws_dynamodb_table.testimonies.name
    }
  }

  layers = [aws_lambda_layer_version.google_api.arn]
}

resource "aws_cloudwatch_log_group" "admin_lambda" {
  name              = "/aws/lambda/${aws_lambda_function.admin.function_name}"
  retention_in_days = 7
}

# Chatbot Lambda Function

resource "aws_lambda_function" "chatbot" {
  filename         = data.archive_file.lambda.output_path
  function_name    = "chatbot-handler"
  role             = aws_iam_role.chatbot.arn
  handler          = "chatbot_function.lambda_handler"
  source_code_hash = data.archive_file.lambda.output_base64sha256
  runtime          = "python3.12"
  architectures    = ["arm64"]
  memory_size      = 128
  timeout          = 30

  environment {
    variables = {
      OPENAI_API_KEY = data.aws_ssm_parameter.openai_api_key.value
    }
  }
}

resource "aws_cloudwatch_log_group" "chatbot_lambda" {
  name              = "/aws/lambda/${aws_lambda_function.chatbot.function_name}"
  retention_in_days = 7
}

# API Gateway HTTP API
resource "aws_apigatewayv2_api" "reservations" {
  name          = "reservations-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["content-type", "authorization"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.reservations.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.reservations.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "admin_lambda" {
  api_id                 = aws_apigatewayv2_api.reservations.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.admin.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "chatbot_lambda" {
  api_id                 = aws_apigatewayv2_api.reservations.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.chatbot.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "post" {
  api_id    = aws_apigatewayv2_api.reservations.id
  route_key = "POST /reservations"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "get_availability" {
  api_id    = aws_apigatewayv2_api.reservations.id
  route_key = "GET /availability"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.reservations.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "cognito-authorizer"

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.admin.id]
    issuer   = "https://${aws_cognito_user_pool.admin.endpoint}"
  }
}

resource "aws_apigatewayv2_route" "get_appointments" {
  api_id             = aws_apigatewayv2_api.reservations.id
  route_key          = "GET /appointments"
  target             = "integrations/${aws_apigatewayv2_integration.admin_lambda.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "put_appointment" {
  api_id             = aws_apigatewayv2_api.reservations.id
  route_key          = "PUT /appointments/{id}"
  target             = "integrations/${aws_apigatewayv2_integration.admin_lambda.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "delete_appointment" {
  api_id             = aws_apigatewayv2_api.reservations.id
  route_key          = "DELETE /appointments/{id}"
  target             = "integrations/${aws_apigatewayv2_integration.admin_lambda.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "get_testimonies" {
  api_id             = aws_apigatewayv2_api.reservations.id
  route_key          = "GET /testimonies"
  target             = "integrations/${aws_apigatewayv2_integration.admin_lambda.id}"
  # Public endpoint (so website visitors can see testimonies)
}

resource "aws_apigatewayv2_route" "post_testimonies" {
  api_id             = aws_apigatewayv2_api.reservations.id
  route_key          = "POST /testimonies"
  target             = "integrations/${aws_apigatewayv2_integration.admin_lambda.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "put_testimonies" {
  api_id             = aws_apigatewayv2_api.reservations.id
  route_key          = "PUT /testimonies/{id}"
  target             = "integrations/${aws_apigatewayv2_integration.admin_lambda.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "delete_testimonies" {
  api_id             = aws_apigatewayv2_api.reservations.id
  route_key          = "DELETE /testimonies/{id}"
  target             = "integrations/${aws_apigatewayv2_integration.admin_lambda.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "chatbot" {
  api_id    = aws_apigatewayv2_api.reservations.id
  route_key = "POST /chat"
  target    = "integrations/${aws_apigatewayv2_integration.chatbot_lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.reservations.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.reservations.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.reservations.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_admin" {
  statement_id  = "AllowAPIGatewayInvokeAdmin"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.admin.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.reservations.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_chatbot" {
  statement_id  = "AllowAPIGatewayInvokeChatbot"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.chatbot.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.reservations.execution_arn}/*/*"
}

# --- Google Calendar Integration ---

# Lambda Layer for Google API dependencies
resource "aws_lambda_layer_version" "google_api" {
  filename   = "${path.module}/layers/google-api/google-api.zip"
  layer_name = "google-api-python"

  compatible_runtimes      = ["python3.12"]
  compatible_architectures = ["arm64"]
}

# Calendar Sync Lambda
resource "aws_lambda_function" "calendar_sync" {
  filename         = data.archive_file.lambda.output_path
  function_name    = "calendar-sync-handler"
  role             = aws_iam_role.sync.arn
  handler          = "calendar_sync_function.lambda_handler"
  source_code_hash = data.archive_file.lambda.output_base64sha256
  runtime          = "python3.12"
  architectures    = ["arm64"]
  memory_size      = 128
  timeout          = 30

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.reservations.name
    }
  }

  layers = [aws_lambda_layer_version.google_api.arn]
}

resource "aws_cloudwatch_log_group" "calendar_sync" {
  name              = "/aws/lambda/${aws_lambda_function.calendar_sync.function_name}"
  retention_in_days = 7
}

# EventBridge Rule (trigger every 5 minutes)
resource "aws_cloudwatch_event_rule" "calendar_sync_rule" {
  name                = "calendar-sync-rule"
  description         = "Triggers calendar sync every 5 minutes"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "calendar_sync_target" {
  rule      = aws_cloudwatch_event_rule.calendar_sync_rule.name
  target_id = "CalendarSyncLambda"
  arn       = aws_lambda_function.calendar_sync.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.calendar_sync.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.calendar_sync_rule.arn
}
