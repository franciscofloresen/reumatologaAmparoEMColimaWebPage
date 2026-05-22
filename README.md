# Medical Practice Web Platform - Full-Stack Application

A comprehensive web platform for a rheumatology medical practice featuring appointment management, AI-powered chatbot, and serverless AWS infrastructure.

## 🎯 Project Overview

Professional medical website with integrated appointment booking system, patient testimonials management, and intelligent chatbot assistance. Built with modern web technologies and deployed on AWS serverless architecture for scalability and cost-efficiency.

**Live Demo:** [dramariamparoenriquezreumatologiaintegral.com](https://dramariamparoenriquezreumatologiaintegral.com)

## 🏗️ Architecture

### Frontend
- **Technology:** Vanilla JavaScript, HTML5, CSS3
- **Styling:** Tailwind CSS
- **Features:** Responsive design, interactive chatbot UI, admin dashboard
- **Hosting:** AWS S3 + CloudFront CDN

### Backend
- **Runtime:** Node.js + Express.js
- **API:** RESTful endpoints with rate limiting
- **Security:** Helmet.js, CORS, input validation (Joi)
- **Email:** Nodemailer integration

### AWS Infrastructure (Terraform)
- **Compute:** AWS Lambda (Python 3.12, ARM64)
- **Storage:** DynamoDB (appointments), S3 (static hosting)
- **CDN:** CloudFront distribution
- **API:** API Gateway (HTTP API)
- **Notifications:** SNS for email alerts
- **Authentication:** AWS Cognito
- **Monitoring:** CloudWatch Logs
- **IaC:** Terraform for infrastructure provisioning

## 🚀 Key Features

### Patient-Facing Features
- ✅ Responsive medical practice website
- ✅ Online appointment booking system
- ✅ AI-powered chatbot for FAQs (OpenAI integration)
- ✅ WhatsApp integration for direct contact
- ✅ Interactive location map
- ✅ Patient testimonials display
- ✅ Service information and pricing

### Administrative Features
- ✅ Testimonials management dashboard
- ✅ Appointment management system
- ✅ Star rating system (1-5 stars)
- ✅ CRUD operations for patient reviews
- ✅ Secure admin authentication (AWS Cognito)

### Technical Features
- ✅ Serverless architecture (cost-optimized)
- ✅ Infrastructure as Code (Terraform)
- ✅ API rate limiting and security headers
- ✅ Email notifications via SNS
- ✅ CloudWatch monitoring and logging
- ✅ HTTPS with CloudFront
- ✅ CORS configuration for cross-origin requests

## 📁 Project Structure

```
├── frontend/
│   ├── index.html              # Main landing page
│   ├── admin.html              # Testimonials admin panel
│   ├── admin-appointments.html # Appointments management
│   ├── reservations.html       # Booking interface
│   ├── login.html              # Admin authentication
│   └── images/                 # Static assets
├── backend/
│   ├── server.js               # Express server
│   ├── database.js             # Database abstraction
│   ├── package.json            # Dependencies
│   └── routes/
│       ├── contact.js          # Contact form API
│       └── appointments.js     # Appointments API
├── terraform/
│   ├── main.tf                 # Main infrastructure
│   ├── iam.tf                  # IAM roles and policies
│   ├── cognito.tf              # Authentication setup
│   ├── variables.tf            # Configuration variables
│   ├── outputs.tf              # Stack outputs
│   └── lambda/
│       ├── lambda_function.py  # Appointments handler
│       ├── chatbot_function.py # AI chatbot logic
│       └── admin_function.py   # Admin operations
├── start.sh                    # Local development script
└── upload-to-s3.sh            # Deployment script
```

## 🛠️ Technology Stack

### Frontend
- HTML5, CSS3, JavaScript (ES6+)
- Tailwind CSS
- Responsive Design
- LocalStorage API

### Backend
- Node.js 18+
- Express.js 4.x
- Joi (validation)
- Nodemailer
- Express Rate Limit
- Helmet.js
- CORS

### AWS Services
- **Lambda** - Serverless compute (ARM64, Python 3.12)
- **API Gateway** - HTTP API endpoints
- **DynamoDB** - NoSQL database for appointments
- **S3** - Static website hosting
- **CloudFront** - Global CDN
- **SNS** - Email notifications
- **Cognito** - User authentication
- **CloudWatch** - Logging and monitoring
- **Systems Manager** - Parameter Store for secrets

### DevOps
- Terraform (IaC)
- Git version control
- AWS CLI
- Shell scripting

## 📊 AWS Cost Optimization

- **Lambda:** ARM64 architecture (20% cheaper than x86)
- **API Gateway:** HTTP API instead of REST API (70% cheaper)
- **CloudFront:** PriceClass_100 (North America & Europe only)
- **DynamoDB:** On-demand pricing (pay per request)
- **S3:** Standard storage class, no versioning
- **Lambda Memory:** 128 MB minimum allocation

**Estimated Monthly Cost:** ~$5-10 USD for low-medium traffic

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd reumatologaAmparoEMColimaWebPage

# Install dependencies
cd backend
npm install

# Start development server
npm run dev

# Or use the startup script
./start.sh
```

**Access Points:**
- Main Site: http://localhost:3000
- Admin Panel: http://localhost:3000/admin
- Appointments: http://localhost:3000/admin-appointments
- API Health: http://localhost:3000/health

### AWS Deployment

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Review deployment plan
terraform plan

# Deploy infrastructure
terraform apply

# Upload frontend to S3
./upload-to-s3.sh
```

## 🔒 Security Features

- **Rate Limiting:** 100 requests per 15 minutes per IP
- **Input Validation:** Joi schema validation on all inputs
- **Security Headers:** Helmet.js implementation
- **CORS:** Configured for specific origins
- **HTTPS:** Enforced via CloudFront
- **Authentication:** AWS Cognito for admin access
- **IAM:** Least privilege principle for Lambda functions
- **Secrets Management:** AWS Systems Manager Parameter Store

## 📈 Performance Optimizations

- CloudFront CDN for global content delivery
- Lambda ARM64 for faster cold starts
- Minimal Lambda memory allocation (128 MB)
- S3 static hosting for fast page loads
- Lazy loading for images
- Minified CSS/JS assets

## 🧪 API Endpoints

### Public Endpoints
```
POST /api/contact          # Contact form submission
POST /api/appointments     # Create appointment
GET  /api/appointments     # List appointments (admin)
```

### Admin Endpoints (Cognito Auth Required)
```
GET    /api/testimonials   # List all testimonials
POST   /api/testimonials   # Create testimonial
PUT    /api/testimonials/:id  # Update testimonial
DELETE /api/testimonials/:id  # Delete testimonial
```

## 📝 Environment Variables

```bash
# Backend (.env)
PORT=3000
FRONTEND_URL=http://localhost:3000
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# Terraform (terraform.tfvars)
aws_region=us-east-1
project_name=reumatologia-app
environment=production
```

## 🎨 Features Showcase

### AI Chatbot
- OpenAI GPT integration
- Context-aware responses
- Medical practice information
- Appointment scheduling guidance
- Multi-language support (Spanish/English)

### Appointment System
- Real-time availability checking
- Email confirmations via SNS
- Admin dashboard for management
- Patient information collection
- Appointment history tracking

### Admin Dashboard
- Secure authentication
- Testimonials CRUD operations
- Star rating management
- Appointment overview
- Responsive design

## 📚 Documentation

- [Architecture Details](terraform/ARCHITECTURE.md)
- [Deployment Guide](terraform/README.md)
- [Quick Start Guide](terraform/QUICKSTART.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Change Log](CHANGES.md)

## 🔄 CI/CD Pipeline

Currently using manual deployment scripts. Future improvements:
- GitHub Actions for automated testing
- Automated Terraform deployments
- Blue-green deployment strategy
- Automated rollback capabilities

## 🌐 Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## 📱 Responsive Design

- Mobile-first approach
- Breakpoints: 640px, 768px, 1024px, 1280px
- Touch-friendly interface
- Optimized for all screen sizes

## 🤝 Contributing

This is a private client project. For inquiries, please contact the developer.

## 👨‍💻 Developer

**Francisco Flores Enríquez**

Full-Stack Developer specializing in:
- Modern web applications
- AWS serverless architecture
- Infrastructure as Code (Terraform)
- RESTful API design
- Responsive UI/UX implementation

## 📄 License

Private project - All rights reserved

## 🎯 Project Highlights for Recruiters

### Technical Skills Demonstrated
- ✅ Full-stack web development (Frontend + Backend)
- ✅ AWS cloud architecture and deployment
- ✅ Infrastructure as Code with Terraform
- ✅ RESTful API design and implementation
- ✅ Database design (DynamoDB, JSON storage)
- ✅ Security best practices
- ✅ Cost optimization strategies
- ✅ Responsive web design
- ✅ AI/ML integration (OpenAI)
- ✅ DevOps practices

### Business Value Delivered
- 💰 Cost-effective serverless solution (~$5-10/month)
- 🚀 Scalable architecture (handles traffic spikes)
- 🔒 Enterprise-grade security
- 📱 Mobile-responsive design
- 🌍 Global CDN distribution
- ⚡ Fast page load times
- 🤖 AI-powered customer service
- 📊 Admin analytics dashboard

### Project Complexity
- Multi-tier architecture
- Multiple AWS services integration
- Real-time data processing
- Third-party API integrations
- Authentication and authorization
- Email notification system
- Infrastructure automation

---

**Built with ❤️ for modern healthcare delivery**
