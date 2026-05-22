# Cognito User Pool
resource "aws_cognito_user_pool" "admin" {
  name = "dra-enriquez-admin-pool"

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  mfa_configuration = "OPTIONAL"

  software_token_mfa_configuration {
    enabled = true
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  auto_verified_attributes = ["email"]

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = false
  }
}

# Cognito User Pool Client
resource "aws_cognito_user_pool_client" "admin" {
  name         = "admin-client"
  user_pool_id = aws_cognito_user_pool.admin.id

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  prevent_user_existence_errors = "ENABLED"

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  access_token_validity  = 1
  id_token_validity      = 1
  refresh_token_validity = 30
}

# Create admin user
resource "aws_cognito_user" "admin" {
  user_pool_id = aws_cognito_user_pool.admin.id
  username     = "admin"

  attributes = {
    email          = var.notification_email
    email_verified = true
  }

  temporary_password = "TempPass123!"
}
