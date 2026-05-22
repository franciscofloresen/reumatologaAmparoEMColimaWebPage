# Common IAM Policy Document for CloudWatch Logs
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# --- Reservation Role ---
resource "aws_iam_role" "reservation" {
  name               = "reservation-api-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "reservation_policy" {
  name = "reservation-api-policy"
  role = aws_iam_role.reservation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:Scan", "dynamodb:Query", "dynamodb:UpdateItem"]
        Resource = [aws_dynamodb_table.reservations.arn, "${aws_dynamodb_table.reservations.arn}/index/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter"]
        Resource = "arn:aws:ssm:*:*:parameter/reumatologia-app/google-*"
      }
    ]
  })
}

# --- Admin Role ---
resource "aws_iam_role" "admin" {
  name               = "admin-api-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "admin_policy" {
  name = "admin-api-policy"
  role = aws_iam_role.admin.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:Scan", "dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem", "dynamodb:PutItem"]
        Resource = [
          aws_dynamodb_table.reservations.arn, 
          "${aws_dynamodb_table.reservations.arn}/index/*",
          aws_dynamodb_table.testimonies.arn
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter"]
        Resource = "arn:aws:ssm:*:*:parameter/reumatologia-app/google-*"
      }
    ]
  })
}

# --- Sync Role ---
resource "aws_iam_role" "sync" {
  name               = "calendar-sync-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "sync_policy" {
  name = "calendar-sync-policy"
  role = aws_iam_role.sync.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:Query"]
        Resource = [aws_dynamodb_table.reservations.arn, "${aws_dynamodb_table.reservations.arn}/index/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter", "ssm:PutParameter"]
        Resource = "arn:aws:ssm:*:*:parameter/reumatologia-app/google-*"
      }
    ]
  })
}

# --- Chatbot Role ---
resource "aws_iam_role" "chatbot" {
  name               = "chatbot-api-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "chatbot_policy" {
  name = "chatbot-api-policy"
  role = aws_iam_role.chatbot.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}
