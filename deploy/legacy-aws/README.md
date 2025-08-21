# Legacy AWS Infrastructure (Deprecated)

⚠️ **This infrastructure is deprecated and should not be used for new deployments.**

## Migration Notice

This directory contains the original complex AWS/Terraform infrastructure that has been replaced with simplified deployment options:

- **Railway** - Recommended for beginners ($10/month)
- **Render** - Recommended for teams ($14/month)  
- **Docker Compose** - Self-hosted option

See the main [DEPLOYMENT.md](../../DEPLOYMENT.md) for current deployment options.

## Why We Moved Away

The AWS infrastructure was overly complex for an MVP application:

- **High Cost**: $50-100+ per month
- **Complex Setup**: Required AWS expertise and Terraform knowledge
- **Maintenance Overhead**: Multiple services to monitor and maintain
- **Slow Development**: Infrastructure changes required careful planning

The new platforms provide the same functionality with:

- **Lower Cost**: $10-20 per month
- **Simple Setup**: Deploy in 5-10 minutes
- **Automatic Scaling**: Built-in load balancing and auto-scaling
- **Zero Maintenance**: Managed databases, SSL, monitoring included

## Migration Path (If Needed)

If you're currently running on this AWS infrastructure and need to migrate:

### 1. Export Data
```bash
# Backup RDS database
pg_dump $RDS_CONNECTION_STRING > rallycal-backup.sql

# Export configuration files from S3
aws s3 cp s3://your-config-bucket/calendars.yaml ./config/
```

### 2. Deploy New Platform
Follow one of the modern deployment guides:
- [Railway Setup](../railway-setup.md)
- [Render Setup](../render-setup.md)

### 3. Import Data
```bash
# Restore database to new platform
psql $NEW_DATABASE_URL < rallycal-backup.sql
```

### 4. Update DNS
Point your domain to the new platform and test functionality.

### 5. Decommission AWS (Safely)
```bash
# Destroy AWS resources (CAREFUL!)
cd deploy/legacy-aws/terraform
terraform destroy

# Verify no unexpected charges
aws billing get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-31
```

## Cost Comparison

### Legacy AWS (Monthly)
- EC2 t3.medium: $30
- RDS t3.micro: $15  
- ALB: $16
- Route53: $0.50
- S3: $5
- CloudWatch: $3
- **Total: ~$70/month**

### New Platforms (Monthly)
- Railway: $10 (web + database)
- Render: $14 (web + database)
- **Savings: 80-85%**

## Files Preserved

This directory contains the complete original infrastructure:

- `main.tf` - Root Terraform configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `modules/` - Reusable infrastructure components
- `environments/` - Environment-specific configurations

These are kept for reference but should not be used for new deployments.

---

**For current deployment instructions, see [DEPLOYMENT.md](../../DEPLOYMENT.md)**