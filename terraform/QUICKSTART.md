# 🚀 Quick Start Guide - 5 Minutes to Deploy

## Prerequisites Check
```bash
# Check Terraform
terraform version  # Should be 1.0+

# Check AWS CLI
aws sts get-caller-identity  # Should show your AWS account
```

## Deploy in 4 Commands

```bash
# 1. Go to terraform directory
cd terraform

# 2. Configure your email
cp terraform.tfvars.example terraform.tfvars
echo 'notification_email = "your-email@example.com"' > terraform.tfvars

# 3. Deploy everything
./deploy.sh

# 4. Get your URLs
terraform output
```

## What You Get

✅ **Website URL**: `https://d1234567890.cloudfront.net`
✅ **API Endpoint**: `https://abc123.execute-api.us-east-1.amazonaws.com`
✅ **Email Notifications**: Automatic alerts for new reservations
✅ **Database**: DynamoDB table for storing reservations

## Post-Deployment (2 minutes)

### 1. Confirm Email
Check inbox → Click AWS SNS confirmation link

### 2. Upload Website
```bash
aws s3 sync ../frontend/ s3://$(terraform output -raw s3_bucket_name)/
```

### 3. Update Frontend
Edit `frontend/reservations.html`:
```javascript
const API_URL = 'YOUR_API_GATEWAY_URL/reservations';
```

## Test It

```bash
# Get API URL
API=$(terraform output -raw api_gateway_invoke_url)

# Send test reservation
curl -X POST $API/reservations \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Juan",
    "lastName": "Pérez",
    "phone": "3121234567",
    "preferredDate": "2025-10-20",
    "preferredTime": "10:00",
    "consultationType": "primera-vez"
  }'
```

Expected: `{"message": "Reservation created successfully", "reservationId": "..."}`

## Common Commands

```bash
# View logs
aws logs tail /aws/lambda/reservation-handler --follow

# Check reservations
aws dynamodb scan --table-name Reservations

# Update infrastructure
terraform apply

# Destroy everything
terraform destroy
```

## Cost

- **Free Tier**: $0.00/month (first 12 months)
- **After**: ~$0.50-2.00/month for 100-1000 reservations

## Troubleshooting

**Problem**: Email not arriving
**Solution**: Check spam, confirm SNS subscription

**Problem**: CORS error
**Solution**: API Gateway CORS is configured, check API URL

**Problem**: Lambda timeout
**Solution**: Increase timeout in `main.tf` (line ~150)

## Files Overview

| File | Purpose |
|------|---------|
| `main.tf` | All AWS resources |
| `variables.tf` | Configuration inputs |
| `outputs.tf` | URLs and ARNs |
| `iam.tf` | Lambda permissions |
| `lambda/lambda_function.py` | Backend logic |

## Architecture

```
User → CloudFront → S3 → API Gateway → Lambda → DynamoDB
                                         ↓
                                       SNS → Email
```

## Support

- 📖 Full docs: `README.md`
- 🏗️ Architecture: `ARCHITECTURE.md`
- 🐛 Issues: Check CloudWatch Logs

---

**Total Setup Time**: 5-10 minutes
**Monthly Cost**: $0.00 (Free Tier)
**Scalability**: 1,000+ reservations/month
