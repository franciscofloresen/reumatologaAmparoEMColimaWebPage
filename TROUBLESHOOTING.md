# Troubleshooting Guide

## Issues Fixed (Oct 15, 2025)

### 1. Chatbot Not Responding (Returns Empty Response)

**Problem**: Chatbot returned 200 status but empty response

**Root Cause**: 
- GPT-5 nano API endpoint (`/v1/responses`) was not working correctly
- The Responses API format was different than expected

**Solution**: 
- Reverted to Chat Completions API (`/v1/chat/completions`)
- Using `gpt-3.5-turbo` model (stable and reliable)
- Added proper error logging and traceback

**Code Location**: `terraform/lambda/chatbot_function.py`

### 2. Email Notifications Not Working

**Problem**: No email confirmations sent when reservations are made

**Root Cause**: 
- SNS topic subscription was deleted or never confirmed
- The subscription needs to be confirmed via email

**Solution**:
- Recreated SNS subscription via Terraform
- **ACTION REQUIRED**: Check email `mariamparoem2021@gmail.com` for AWS SNS confirmation email
- Click the "Confirm subscription" link in the email

**How to Check Status**:
```bash
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:107759015501:reservation-notifications \
  --region us-east-1
```

**Expected Output** (after confirmation):
```json
{
  "Subscriptions": [
    {
      "SubscriptionArn": "arn:aws:sns:...",
      "Endpoint": "mariamparoem2021@gmail.com",
      "Protocol": "email",
      "TopicArn": "arn:aws:sns:us-east-1:107759015501:reservation-notifications"
    }
  ]
}
```

## Common Issues

### Chatbot Returns 500 Error

**Check**:
1. OpenAI API key is valid in Parameter Store
2. Lambda has internet access
3. Check CloudWatch logs:
```bash
aws logs tail /aws/lambda/chatbot-handler --since 10m --region us-east-1
```

### Reservations Not Showing in Admin Panel

**Check**:
1. DynamoDB table has data:
```bash
aws dynamodb scan --table-name Reservations --region us-east-1
```
2. API Gateway endpoint is correct in admin.html
3. CORS is enabled on API Gateway

### Email Notifications Not Received

**Check**:
1. SNS subscription is confirmed (see above)
2. Check spam/junk folder
3. Verify Lambda has SNS publish permissions
4. Check Lambda logs for SNS errors:
```bash
aws logs tail /aws/lambda/reservation-handler --since 10m --region us-east-1
```

## Testing Commands

### Test Chatbot
```bash
aws lambda invoke --function-name chatbot-handler \
  --cli-binary-format raw-in-base64-out \
  --payload '{"body":"{\"message\":\"Hola\"}"}' \
  --region us-east-1 /tmp/response.json && cat /tmp/response.json
```

### Test Reservation Creation
```bash
curl -X POST https://mpwzml63ql.execute-api.us-east-1.amazonaws.com/reservations \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","phone":"1234567890","preferredDate":"2025-10-20","preferredTime":"10:00 AM","message":"Test"}'
```

### View CloudWatch Logs
```bash
# Chatbot logs
aws logs tail /aws/lambda/chatbot-handler --follow --region us-east-1

# Reservation logs
aws logs tail /aws/lambda/reservation-handler --follow --region us-east-1

# Admin logs
aws logs tail /aws/lambda/admin-handler --follow --region us-east-1
```

## Contact Information

- **AWS Region**: us-east-1
- **CloudFront Domain**: d1xhxoyow6y15n.cloudfront.net
- **API Gateway**: https://mpwzml63ql.execute-api.us-east-1.amazonaws.com
- **Notification Email**: mariamparoem2021@gmail.com
