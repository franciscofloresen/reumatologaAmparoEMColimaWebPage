#!/bin/bash

set -e

echo "🚀 AWS Serverless Reservation System Deployment"
echo "================================================"
echo ""

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo "❌ Error: terraform.tfvars not found"
    echo "📝 Please create it from terraform.tfvars.example:"
    echo "   cp terraform.tfvars.example terraform.tfvars"
    echo "   # Then edit with your email address"
    exit 1
fi

# Check AWS credentials
echo "🔍 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS credentials not configured"
    echo "📝 Run: aws configure"
    exit 1
fi
echo "✅ AWS credentials found"
echo ""

# Initialize Terraform
echo "📦 Initializing Terraform..."
terraform init
echo ""

# Plan
echo "📋 Creating deployment plan..."
terraform plan -out=tfplan
echo ""

# Confirm
read -p "🤔 Do you want to deploy this infrastructure? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

# Apply
echo "🚀 Deploying infrastructure..."
terraform apply tfplan
rm tfplan
echo ""

# Get outputs
echo "📊 Deployment Complete! Here are your endpoints:"
echo "================================================"
terraform output
echo ""

echo "📧 IMPORTANT: Check your email and confirm the SNS subscription!"
echo ""
echo "📤 Next steps:"
echo "   1. Confirm SNS email subscription"
echo "   2. Upload website files to S3:"
echo "      aws s3 sync ../frontend/ s3://\$(terraform output -raw s3_bucket_name)/"
echo "   3. Update frontend with API endpoint"
echo "   4. Visit CloudFront URL to test"
echo ""
echo "✅ Deployment successful!"
