variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "notification_email" {
  description = "Email address for reservation notifications"
  type        = string
}
