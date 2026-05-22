# AWS Serverless Reservation System - Terraform Infrastructure

## Architecture Overview

This infrastructure implements a fully serverless, cost-optimized appointment reservation system using AWS Free Tier services:

```
User → CloudFront (HTTPS) → S3 (Static Website) → API Gateway (HTTP API) → Lambda → DynamoDB
                                                                              ↓
                                                                            SNS → Email
```

## Cost Optimization Features

- **S3**: Standard storage class, no versioning
- **CloudFront**: PriceClass_100 (cheapest), default certificate
- **DynamoDB**: PAY_PER_REQUEST billing (Free Tier: 25 GB storage, 25 WCU, 25 RCU)
- **Lambda**: ARM64 architecture, 128MB memory (cheapest options)
- **API Gateway**: HTTP API (cheaper than REST API)
- **SNS**: Extremely cheap, large Free Tier (1,000 email notifications/month free)

## Prerequisites

1. **AWS Account** with Free Tier eligibility
2. **AWS CLI** configured with credentials:
   ```bash
   aws configure
   ```
3. **Terraform** installed (v1.0+):
   ```bash
   brew install terraform  # macOS
   ```

## Project Structure

```
terraform/
├── main.tf                    # All AWS resources
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── iam.tf                     # IAM roles and policies
├── terraform.tfvars.example   # Example variables file
├── lambda/
│   └── lambda_function.py     # Lambda handler code
└── README.md                  # This file
```

## Deployment Instructions

### Step 1: Configure Variables

Create a `terraform.tfvars` file:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
aws_region         = "us-east-1"
notification_email = "doctor@example.com"
```

### Step 2: Initialize Terraform

```bash
terraform init
```

This downloads the AWS provider and initializes the backend.

### Step 3: Review the Plan

```bash
terraform plan
```

Review the resources that will be created:
- S3 bucket for website hosting
- CloudFront distribution
- DynamoDB table
- Lambda function
- API Gateway HTTP API
- SNS topic and email subscription
- IAM role and policies

### Step 4: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted to confirm.

**Deployment time**: ~5-10 minutes (CloudFront takes the longest)

### Step 5: Confirm SNS Email Subscription

After deployment, check your email inbox for an SNS subscription confirmation from AWS. Click the confirmation link to activate email notifications.

### Step 6: Get Output Values

```bash
terraform output
```

You'll receive:
- `cloudfront_domain_name`: Your website URL (e.g., `d1234567890.cloudfront.net`)
- `api_gateway_invoke_url`: API endpoint for reservations
- `s3_bucket_name`: Bucket name for uploading website files

### Step 7: Upload Website Files

Upload your static website to S3:

```bash
# Get bucket name
BUCKET_NAME=$(terraform output -raw s3_bucket_name)

# Upload files from frontend directory
aws s3 sync ../frontend/ s3://$BUCKET_NAME/ \
  --exclude "*.md" \
  --exclude "node_modules/*"
```

### Step 8: Update Frontend API Endpoint

Edit your `reservations.html` to use the API Gateway endpoint:

```javascript
const API_ENDPOINT = 'YOUR_API_GATEWAY_URL/reservations';

// In your form submission:
fetch(API_ENDPOINT, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(reservationData)
})
```

### Step 9: Access Your Website

Visit the CloudFront domain name (from outputs) in your browser:

```
https://d1234567890.cloudfront.net
```

## Testing the System

### Test API Endpoint

```bash
API_URL=$(terraform output -raw api_gateway_invoke_url)

curl -X POST $API_URL/reservations \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Juan",
    "lastName": "Pérez",
    "phone": "3121234567",
    "email": "juan@example.com",
    "preferredDate": "2025-10-20",
    "preferredTime": "10:00",
    "consultationType": "primera-vez",
    "reason": "Consulta general"
  }'
```

Expected response:
```json
{
  "message": "Reservation created successfully",
  "reservationId": "uuid-here"
}
```

### Verify Data in DynamoDB

```bash
aws dynamodb scan --table-name Reservations
```

### Check Email Notification

You should receive an email with the reservation details.

## Monitoring and Logs

### View Lambda Logs

```bash
aws logs tail /aws/lambda/reservation-handler --follow
```

### Check CloudWatch Metrics

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=reservation-handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

## Cost Estimation (Free Tier)

Assuming 100 reservations/month:

| Service | Usage | Cost |
|---------|-------|------|
| S3 | 5 GB storage, 1000 requests | **$0.00** (Free Tier) |
| CloudFront | 50 GB data transfer | **$0.00** (Free Tier) |
| Lambda | 100 invocations, 128MB, 1s avg | **$0.00** (Free Tier) |
| API Gateway | 100 requests | **$0.00** (Free Tier) |
| DynamoDB | 100 writes, 1 GB storage | **$0.00** (Free Tier) |
| SNS | 100 email notifications | **$0.00** (Free Tier) |
| **Total** | | **$0.00/month** |

**Note**: After Free Tier expires (12 months), estimated cost: ~$1-2/month for this traffic level.

## Updating the Infrastructure

### Modify Resources

1. Edit Terraform files
2. Run `terraform plan` to preview changes
3. Run `terraform apply` to apply changes

### Update Lambda Function

```bash
# Edit lambda/lambda_function.py
# Then apply changes
terraform apply
```

## Cleanup (Destroy Infrastructure)

To avoid any charges, destroy all resources:

```bash
terraform destroy
```

Type `yes` to confirm.

**Warning**: This will permanently delete:
- All reservation data in DynamoDB
- Website files in S3
- All logs in CloudWatch

## Troubleshooting

### Issue: SNS emails not arriving

**Solution**: Check spam folder and confirm the subscription via the email link.

### Issue: CORS errors in browser

**Solution**: API Gateway CORS is configured for `*`. Ensure your frontend uses the correct API endpoint.

### Issue: Lambda timeout

**Solution**: Increase timeout in `main.tf`:
```hcl
timeout = 30  # seconds
```

### Issue: CloudFront not serving updated files

**Solution**: Invalidate CloudFront cache:
```bash
DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[0].Id" --output text)
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"
```

## Security Best Practices

1. **Enable S3 bucket encryption** (optional, adds minimal cost)
2. **Restrict API Gateway** to specific origins in production
3. **Add authentication** to API Gateway for production use
4. **Enable CloudTrail** for audit logging
5. **Use AWS Secrets Manager** for sensitive configuration

## Next Steps

1. **Custom Domain**: Add Route 53 and ACM certificate
2. **Authentication**: Add Cognito for user management
3. **Admin Panel**: Create Lambda functions for CRUD operations
4. **Monitoring**: Set up CloudWatch alarms
5. **Backup**: Enable DynamoDB point-in-time recovery

## Support

For issues or questions:
- AWS Documentation: https://docs.aws.amazon.com/
- Terraform AWS Provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs

---

**Infrastructure as Code by Terraform**
**Optimized for AWS Free Tier**
