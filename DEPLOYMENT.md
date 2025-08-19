# RallyCal Deployment Guide

This guide provides step-by-step instructions for deploying RallyCal to various environments using the provided Infrastructure-as-Code and CI/CD pipeline.

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform >= 1.5 installed
- Docker and Docker Compose installed
- GitHub repository with necessary secrets configured

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/your-org/rallycal.git
cd rallycal

# 2. Start the development environment
docker-compose up -d

# 3. Access the application
open http://localhost:8000
```

## Environment Setup

### 1. GitHub Repository Configuration

Configure the following secrets in your GitHub repository settings:

```
CODECOV_TOKEN          # Optional: For code coverage reporting
SLACK_WEBHOOK_URL      # Optional: For deployment notifications
AWS_ACCESS_KEY_ID      # For AWS deployment
AWS_SECRET_ACCESS_KEY  # For AWS deployment
```

### 2. AWS Prerequisites

```bash
# Create S3 bucket for Terraform state (optional but recommended)
aws s3 mb s3://rallycal-terraform-state-your-suffix

# Create DynamoDB table for Terraform state locking
aws dynamodb create-table \
  --table-name rallycal-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

## Deployment Methods

### Method 1: CI/CD Pipeline (Recommended)

The GitHub Actions pipeline automatically handles:
- Testing and quality checks
- Docker image building and security scanning  
- Infrastructure provisioning
- Application deployment
- Health checks and rollback capabilities

**Trigger Deployment:**
```bash
# For staging
git push origin main

# For production
gh release create v1.0.0 --title "Release v1.0.0" --notes "Production release"
```

### Method 2: Manual Infrastructure Deployment

```bash
# 1. Navigate to environment directory
cd terraform/environments/staging  # or production

# 2. Initialize Terraform
terraform init

# 3. Plan the deployment
terraform plan -var-file=terraform.tfvars

# 4. Apply the infrastructure
terraform apply -var-file=terraform.tfvars

# 5. Note the outputs
terraform output
```

### Method 3: Local Docker Deployment

```bash
# 1. Build the application image
docker build -t rallycal:local .

# 2. Start with Docker Compose
docker-compose up -d

# 3. Check application health
curl http://localhost:8000/health
```

## Environment-Specific Configuration

### Staging Environment

**Infrastructure Specs:**
- 2 ECS Fargate tasks (512 CPU, 1024 MB RAM)
- RDS PostgreSQL db.t3.small (Single-AZ)
- ElastiCache Redis cache.t3.small
- Application Load Balancer with SSL
- Estimated cost: ~$100-130/month

**Access:**
- URL: https://staging.rallycal.com (configure DNS)
- Health: https://staging.rallycal.com/health
- API: https://staging.rallycal.com/api/v1/
- Calendar: https://staging.rallycal.com/api/v1/calendar.ics

### Production Environment

**Infrastructure Specs:**
- 3 ECS Fargate tasks (1024 CPU, 2048 MB RAM)
- RDS PostgreSQL db.t3.medium (Multi-AZ)
- ElastiCache Redis cache.t3.medium with failover
- Application Load Balancer with SSL
- Estimated cost: ~$240-290/month

**Access:**
- URL: https://rallycal.com (configure DNS)
- Health: https://rallycal.com/health
- API: https://rallycal.com/api/v1/
- Calendar: https://rallycal.com/api/v1/calendar.ics

## Configuration Management

### Environment Variables

The application uses the following environment variables:

```bash
# Core Application
RALLYCAL_ENVIRONMENT=production
RALLYCAL_LOG_LEVEL=INFO
RALLYCAL_HOST=0.0.0.0
RALLYCAL_PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0

# Security
RALLYCAL_SECRET_KEY=your-secret-key-here

# Calendar Configuration
RALLYCAL_CONFIG_FILE=/app/config/calendars.yaml
RALLYCAL_CACHE_TTL=3600
RALLYCAL_FETCH_TIMEOUT=30
```

### Calendar Configuration

Create a `config/calendars.yaml` file:

```yaml
calendars:
  - name: "Soccer Team A"
    url: "https://example.com/soccer-team-a.ics"
    color: "#FF0000"
    enabled: true
    auth:
      type: "none"
  
  - name: "Basketball Team B"
    url: "https://example.com/basketball-team-b.ics"
    color: "#00FF00"
    enabled: true
    auth:
      type: "bearer"
      token: "your-api-token"

manual_events:
  - title: "Family Meeting"
    start: "2024-01-25T19:00:00Z"
    end: "2024-01-25T20:00:00Z"
    location: "Home"
    description: "Monthly planning meeting"
```

## Monitoring and Operations

### Health Check Endpoints

```bash
# Basic health check
curl https://your-domain.com/health

# Comprehensive health check (includes dependencies)
curl https://your-domain.com/api/v1/health/comprehensive

# Readiness check (for load balancer)
curl https://your-domain.com/api/v1/health/ready

# Liveness check (for container orchestration)
curl https://your-domain.com/api/v1/health/live
```

### Monitoring Dashboards

After deployment, access monitoring through:

1. **CloudWatch Dashboard**: 
   - https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=rallycal-production-dashboard

2. **Application Logs**:
   ```bash
   # View application logs
   aws logs tail /ecs/rallycal-production --follow
   
   # View specific time range
   aws logs tail /ecs/rallycal-production --since 1h
   ```

3. **Metrics Endpoint**:
   ```bash
   curl https://your-domain.com/api/v1/metrics
   ```

### Database Operations

```bash
# Connect to production database (use carefully!)
aws rds describe-db-instances --db-instance-identifier rallycal-production

# Create database backup
aws rds create-db-snapshot \
  --db-instance-identifier rallycal-production \
  --db-snapshot-identifier rallycal-manual-backup-$(date +%Y%m%d)

# View recent backups
aws rds describe-db-snapshots --db-instance-identifier rallycal-production
```

## Troubleshooting

### Common Issues

1. **Application won't start**
   ```bash
   # Check logs
   aws logs tail /ecs/rallycal-production --follow
   
   # Check ECS service status
   aws ecs describe-services --cluster rallycal-production --services rallycal
   ```

2. **Database connection issues**
   ```bash
   # Test database connectivity from ECS task
   aws ecs execute-command \
     --cluster rallycal-production \
     --task <task-arn> \
     --command "python -c 'from src.rallycal.database.engine import db_manager; import asyncio; print(asyncio.run(db_manager.check_connection()))'"
   ```

3. **SSL/DNS issues**
   ```bash
   # Check Route53 records
   aws route53 list-resource-record-sets --hosted-zone-id Z123456789
   
   # Check ALB status
   aws elbv2 describe-target-health --target-group-arn <target-group-arn>
   ```

### Rollback Procedures

1. **Application Rollback**
   ```bash
   # Rollback to previous task definition
   aws ecs update-service \
     --cluster rallycal-production \
     --service rallycal \
     --task-definition rallycal-production:123  # previous revision
   ```

2. **Infrastructure Rollback**
   ```bash
   # Rollback Terraform changes
   cd terraform/environments/production
   terraform plan -var-file=terraform.tfvars
   terraform apply -var-file=terraform.tfvars
   ```

## Security Considerations

1. **Secrets Management**
   - Use AWS Secrets Manager for sensitive data
   - Rotate secrets regularly
   - Never commit secrets to version control

2. **Network Security**
   - Application runs in private subnets
   - Database and cache in isolated subnets
   - Security groups restrict access

3. **SSL/TLS**
   - SSL termination at load balancer
   - Force HTTPS redirects
   - Regular certificate renewal

## Cost Optimization

1. **Development Environment**
   - Use scheduled scaling to shut down during off-hours
   - Enable spot instances for cost savings
   - Estimated savings: 40-60%

2. **Production Environment**
   - Monitor CloudWatch billing alerts
   - Use Reserved Instances for predictable workloads
   - Implement auto-scaling based on demand

3. **Storage Optimization**
   - Enable RDS storage auto-scaling
   - Implement log retention policies
   - Use S3 lifecycle policies for backups

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**
   - Review application logs for errors
   - Check monitoring dashboards
   - Verify backup completion

2. **Monthly**
   - Update dependencies
   - Review and rotate secrets
   - Analyze performance metrics
   - Review and optimize costs

3. **Quarterly**
   - Security review and penetration testing
   - Disaster recovery testing
   - Performance optimization review
   - Infrastructure cost review

### Getting Help

- **Documentation**: Check this deployment guide and README
- **Logs**: Application and infrastructure logs via CloudWatch
- **Monitoring**: CloudWatch dashboards and alerts
- **Issues**: GitHub Issues for bug reports and feature requests

---

## Quick Reference Commands

```bash
# Health checks
curl https://your-domain.com/health
curl https://your-domain.com/api/v1/health/comprehensive

# View logs
aws logs tail /ecs/rallycal-production --follow

# Deploy infrastructure
cd terraform/environments/production
terraform apply -var-file=terraform.tfvars

# Build and test locally
docker-compose up -d
curl http://localhost:8000/health

# Run tests
uv run hatch run test

# Deploy via CI/CD
git tag v1.0.0
git push origin v1.0.0
```

This deployment guide provides comprehensive instructions for getting RallyCal running in any environment. For additional support, please refer to the project documentation or create an issue in the GitHub repository.