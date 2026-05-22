# AWS Serverless Architecture - Detailed Documentation

## System Architecture

```
┌─────────────┐
│   Patient   │
│   Browser   │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────────────────────────────┐
│              Amazon CloudFront (CDN)                    │
│  • Global edge locations                               │
│  • HTTPS with default certificate (FREE)               │
│  • PriceClass_100 (cheapest)                          │
│  • Cache: 1 hour default                              │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│         Amazon S3 (Static Website Hosting)              │
│  • index.html, CSS, JS                                 │
│  • Standard storage class                             │
│  • Public read access                                 │
│  • No versioning (cost optimization)                  │
└─────────────────────────────────────────────────────────┘

       │ User submits form
       │ POST /reservations
       ▼
┌─────────────────────────────────────────────────────────┐
│        Amazon API Gateway (HTTP API)                    │
│  • HTTP API (cheaper than REST)                        │
│  • CORS enabled                                        │
│  • POST /reservations endpoint                         │
│  • Lambda proxy integration                            │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│              AWS Lambda Function                        │
│  • Runtime: Python 3.12                                │
│  • Architecture: ARM64 (cheaper)                       │
│  • Memory: 128 MB (minimum)                            │
│  • Timeout: 10 seconds                                 │
│  • Environment variables:                              │
│    - DYNAMODB_TABLE                                    │
│    - SNS_TOPIC_ARN                                     │
└──────┬──────────────────────────────────────────────────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────────────────────────────┐
│   DynamoDB   │  │         Amazon SNS                   │
│              │  │  • Topic: reservation-notifications  │
│  Table:      │  │  • Protocol: Email                   │
│  Reservations│  │  • Endpoint: doctor@example.com      │
│              │  │                                      │
│  Billing:    │  └──────┬───────────────────────────────┘
│  PAY_PER_    │         │
│  REQUEST     │         ▼
│              │  ┌──────────────────────────────────────┐
│  Key:        │  │      Email Notification              │
│  reservationId│  │  Subject: Nueva Reserva de Cita     │
└──────────────┘  │  Body: Patient details               │
                  └──────────────────────────────────────┘
```

## Data Flow

### 1. User Accesses Website
```
User → CloudFront → S3 → HTML/CSS/JS delivered to browser
```

### 2. User Submits Reservation Form
```javascript
// Frontend JavaScript
const formData = {
  firstName: "Juan",
  lastName: "Pérez",
  phone: "3121234567",
  email: "juan@example.com",
  preferredDate: "2025-10-20",
  preferredTime: "10:00",
  consultationType: "primera-vez",
  reason: "Dolor articular"
};

fetch('https://api-id.execute-api.us-east-1.amazonaws.com/reservations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formData)
});
```

### 3. API Gateway Receives Request
- Validates HTTP method (POST)
- Checks CORS headers
- Forwards to Lambda with event payload

### 4. Lambda Processes Request
```python
# Lambda function flow:
1. Parse JSON body
2. Validate required fields
3. Generate unique reservationId (UUID)
4. Add metadata (status, createdAt)
5. Save to DynamoDB
6. Format email message
7. Publish to SNS
8. Return success response
```

### 5. DynamoDB Stores Data
```json
{
  "reservationId": "uuid-v4",
  "firstName": "Juan",
  "lastName": "Pérez",
  "phone": "3121234567",
  "email": "juan@example.com",
  "preferredDate": "2025-10-20",
  "preferredTime": "10:00",
  "consultationType": "primera-vez",
  "reason": "Dolor articular",
  "status": "pending",
  "createdAt": "2025-10-12T20:00:00.000Z"
}
```

### 6. SNS Sends Email
```
To: doctor@example.com
Subject: Nueva Reserva de Cita

Nueva Reserva de Cita

ID: uuid-v4
Paciente: Juan Pérez
Teléfono: 3121234567
Email: juan@example.com
Fecha: 2025-10-20
Hora: 10:00
Tipo: primera-vez
Motivo: Dolor articular

Estado: Pendiente de confirmación
```

## AWS Services Breakdown

### 1. Amazon S3
**Purpose**: Host static website files
**Configuration**:
- Bucket policy: Public read access
- Website hosting enabled
- Index document: index.html
- No versioning (cost optimization)

**Free Tier**:
- 5 GB storage
- 20,000 GET requests
- 2,000 PUT requests

### 2. Amazon CloudFront
**Purpose**: Global CDN with HTTPS
**Configuration**:
- Origin: S3 website endpoint
- Price class: 100 (North America, Europe)
- Certificate: Default CloudFront (free)
- Cache TTL: 1 hour default

**Free Tier**:
- 1 TB data transfer out
- 10,000,000 HTTP/HTTPS requests

### 3. Amazon API Gateway (HTTP API)
**Purpose**: RESTful API endpoint
**Configuration**:
- Type: HTTP API (not REST API)
- CORS: Enabled for all origins
- Integration: Lambda proxy
- Stage: $default (auto-deploy)

**Free Tier**:
- 1 million API calls per month (12 months)

**Pricing after Free Tier**:
- $1.00 per million requests

### 4. AWS Lambda
**Purpose**: Backend business logic
**Configuration**:
- Runtime: Python 3.12
- Architecture: ARM64 (20% cheaper)
- Memory: 128 MB (minimum)
- Timeout: 10 seconds
- Ephemeral storage: 512 MB (default)

**Free Tier** (Always Free):
- 1 million requests per month
- 400,000 GB-seconds compute time

**Cost Calculation**:
- 100 requests/month × 1 second × 128 MB = 12.5 GB-seconds
- **Cost: $0.00** (well within Free Tier)

### 5. Amazon DynamoDB
**Purpose**: NoSQL database for reservations
**Configuration**:
- Billing mode: PAY_PER_REQUEST (on-demand)
- Partition key: reservationId (String)
- No sort key
- No GSI/LSI (cost optimization)

**Free Tier** (Always Free):
- 25 GB storage
- 25 WCU (Write Capacity Units)
- 25 RCU (Read Capacity Units)

**Cost Calculation**:
- 100 writes/month = 100 WCU
- Average item size: 1 KB
- Storage: ~0.1 GB
- **Cost: $0.00** (well within Free Tier)

### 6. Amazon SNS
**Purpose**: Email notifications
**Configuration**:
- Topic: reservation-notifications
- Protocol: Email
- Subscription: Requires confirmation

**Free Tier** (Always Free):
- 1,000 email notifications per month

**Pricing after Free Tier**:
- $2.00 per 100,000 emails

**Cost Calculation**:
- 100 emails/month
- **Cost: $0.00** (within Free Tier)

### 7. Amazon CloudWatch
**Purpose**: Logging and monitoring
**Configuration**:
- Log group: /aws/lambda/reservation-handler
- Retention: 7 days
- Metrics: Lambda invocations, errors, duration

**Free Tier** (Always Free):
- 5 GB log ingestion
- 5 GB log storage
- 1 million API requests

## IAM Permissions

### Lambda Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:PutItem"],
      "Resource": "arn:aws:dynamodb:region:account:table/Reservations"
    },
    {
      "Effect": "Allow",
      "Action": ["sns:Publish"],
      "Resource": "arn:aws:sns:region:account:reservation-notifications"
    }
  ]
}
```

**Principle of Least Privilege**: Lambda only has permissions for:
1. Writing logs
2. Writing to specific DynamoDB table
3. Publishing to specific SNS topic

## Security Considerations

### 1. S3 Bucket
- ✅ Public read access (required for website)
- ✅ No public write access
- ⚠️ Consider: Enable encryption at rest (S3-SSE)
- ⚠️ Consider: Enable access logging

### 2. CloudFront
- ✅ HTTPS enforced (redirect-to-https)
- ✅ Default certificate (free)
- ⚠️ Consider: Custom domain with ACM certificate
- ⚠️ Consider: WAF for DDoS protection

### 3. API Gateway
- ✅ CORS configured
- ⚠️ Consider: API key authentication
- ⚠️ Consider: Rate limiting per IP
- ⚠️ Consider: Request validation

### 4. Lambda
- ✅ Minimal IAM permissions
- ✅ Input validation in code
- ✅ Error handling
- ⚠️ Consider: VPC for database access
- ⚠️ Consider: Secrets Manager for sensitive data

### 5. DynamoDB
- ✅ Encryption at rest (default)
- ✅ Encryption in transit (HTTPS)
- ⚠️ Consider: Point-in-time recovery
- ⚠️ Consider: Backup plan

## Scalability

### Current Limits (Free Tier)
- **Requests**: 1 million/month (Lambda)
- **Storage**: 25 GB (DynamoDB)
- **Bandwidth**: 1 TB/month (CloudFront)

### Scaling Considerations
For 1,000 reservations/month:
- Lambda: 1,000 invocations (0.1% of Free Tier)
- DynamoDB: 1,000 writes (4% of Free Tier)
- S3: ~100 MB storage (2% of Free Tier)
- **Conclusion**: Can handle 100x current traffic within Free Tier

### Auto-Scaling
- **Lambda**: Automatic (up to 1,000 concurrent executions)
- **DynamoDB**: PAY_PER_REQUEST scales automatically
- **API Gateway**: Automatic (10,000 RPS default)
- **CloudFront**: Global edge network

## Monitoring and Alerts

### CloudWatch Metrics to Monitor
1. **Lambda**:
   - Invocations
   - Errors
   - Duration
   - Throttles

2. **API Gateway**:
   - Count (requests)
   - 4XXError
   - 5XXError
   - Latency

3. **DynamoDB**:
   - ConsumedWriteCapacityUnits
   - UserErrors
   - SystemErrors

### Recommended Alarms
```bash
# Lambda errors > 5 in 5 minutes
aws cloudwatch put-metric-alarm \
  --alarm-name lambda-errors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold

# API Gateway 5XX errors > 10 in 5 minutes
aws cloudwatch put-metric-alarm \
  --alarm-name api-5xx-errors \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

## Disaster Recovery

### Backup Strategy
1. **DynamoDB**: Enable point-in-time recovery
2. **S3**: Enable versioning for website files
3. **Lambda**: Code stored in Terraform (IaC)
4. **Configuration**: All in Terraform state

### Recovery Procedures
1. **Data Loss**: Restore from DynamoDB backup
2. **Infrastructure Loss**: `terraform apply` recreates everything
3. **Region Failure**: Deploy to different region (multi-region)

## Cost Optimization Tips

1. **Use ARM64 Lambda**: 20% cheaper than x86
2. **Minimize Lambda memory**: 128 MB sufficient for this workload
3. **Use HTTP API**: 70% cheaper than REST API
4. **PAY_PER_REQUEST DynamoDB**: Best for unpredictable traffic
5. **CloudFront PriceClass_100**: Cheapest option
6. **Short log retention**: 7 days vs 30 days
7. **No NAT Gateway**: Lambda doesn't need VPC for this use case

## Future Enhancements

### Phase 2: Admin Dashboard
- Add Cognito for authentication
- Create Lambda functions for CRUD operations
- Add API Gateway routes for GET/PUT/DELETE

### Phase 3: Advanced Features
- SMS notifications via SNS
- Calendar integration (Google Calendar API)
- Automated reminders (EventBridge + Lambda)
- Analytics dashboard (QuickSight)

### Phase 4: Production Hardening
- Custom domain with Route 53
- ACM certificate for HTTPS
- WAF for security
- Multi-region deployment
- CI/CD pipeline (GitHub Actions)

---

**Total Monthly Cost (Free Tier)**: $0.00
**Total Monthly Cost (After Free Tier, 100 reservations)**: ~$0.50
**Total Monthly Cost (After Free Tier, 1,000 reservations)**: ~$2.00
