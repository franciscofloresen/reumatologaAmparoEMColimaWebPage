output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.website.domain_name
}

output "api_gateway_invoke_url" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_api.reservations.api_endpoint
}

output "s3_bucket_name" {
  description = "S3 bucket name for website hosting"
  value       = aws_s3_bucket.website.id
}

output "sns_topic_arn" {
  description = "SNS topic ARN for notifications"
  value       = aws_sns_topic.reservations.arn
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.admin.id
}

output "cognito_client_id" {
  description = "Cognito Client ID"
  value       = aws_cognito_user_pool_client.admin.id
}

