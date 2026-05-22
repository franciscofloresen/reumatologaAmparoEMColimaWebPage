#!/bin/bash

set -e

echo "📤 Uploading Website to S3"
echo "=========================="
echo ""

# Check if in correct directory
if [ ! -d "terraform" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Get bucket name from Terraform
cd terraform
BUCKET_NAME=$(terraform output -raw s3_bucket_name 2>/dev/null)

if [ -z "$BUCKET_NAME" ]; then
    echo "❌ Error: Could not get S3 bucket name"
    echo "   Make sure Terraform has been deployed: cd terraform && terraform apply"
    exit 1
fi

echo "✅ S3 Bucket: $BUCKET_NAME"
echo ""

# Get API Gateway URL
API_URL=$(terraform output -raw api_gateway_invoke_url 2>/dev/null)
echo "✅ API Gateway: $API_URL"
echo ""

cd ..

# Upload files
echo "📤 Uploading files..."
aws s3 sync frontend/ s3://$BUCKET_NAME/ \
    --exclude ".DS_Store" \
    --exclude "*.md" \
    --exclude "node_modules/*" \
    --delete

echo ""
echo "✅ Upload complete!"
echo ""
echo "📋 Uploaded files:"
aws s3 ls s3://$BUCKET_NAME/ --recursive --human-readable
echo ""

# Get CloudFront URL
cd terraform
CLOUDFRONT_URL=$(terraform output -raw cloudfront_domain_name 2>/dev/null)
echo "🌐 Your website is available at:"
echo "   https://$CLOUDFRONT_URL"
echo ""
echo "⚠️  IMPORTANT: Update reservations.html with API endpoint:"
echo "   Edit frontend/reservations.html"
echo "   Replace: YOUR_API_GATEWAY_URL_HERE"
echo "   With: $API_URL"
echo ""
echo "   Then re-upload:"
echo "   aws s3 cp frontend/reservations.html s3://$BUCKET_NAME/"
echo ""
