# RallyCal Production Environment Configuration
# Terraform variables for production deployment

# ==============================================================================
# Environment Configuration
# ==============================================================================
project_name = "rallycal"
environment  = "production"
aws_region   = "us-west-2"

# ==============================================================================
# Network Configuration
# ==============================================================================
vpc_cidr_block          = "10.0.0.0/16"
public_subnet_cidrs     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_subnet_cidrs    = ["10.0.10.0/24", "10.0.20.0/24", "10.0.30.0/24"]
database_subnet_cidrs   = ["10.0.100.0/24", "10.0.200.0/24", "10.0.300.0/24"]

enable_nat_gateway = true
enable_vpn_gateway = false

# ==============================================================================
# Database Configuration - Production
# ==============================================================================
db_instance_class           = "db.t3.medium"
db_allocated_storage        = 50
db_max_allocated_storage    = 200
db_backup_retention_period  = 14
db_backup_window           = "03:00-04:00"
db_maintenance_window      = "Sun:04:00-Sun:06:00"
db_monitoring_interval     = 60
db_performance_insights_enabled = true
db_multi_az                = true  # High availability for production

# ==============================================================================
# Cache Configuration - Production
# ==============================================================================
redis_node_type                    = "cache.t3.medium"
redis_num_cache_nodes              = 2
redis_parameter_group_name         = "default.redis7"
redis_automatic_failover_enabled   = true  # High availability for production

# ==============================================================================
# Application Configuration - Production
# ==============================================================================
app_image = "ghcr.io/rallycal/rallycal:latest"

ecs_desired_count = 3
ecs_cpu          = 1024
ecs_memory       = 2048

# Auto scaling configuration
ecs_autoscaling_enabled     = true
ecs_autoscaling_min_capacity = 2
ecs_autoscaling_max_capacity = 20

# ==============================================================================
# Domain Configuration - Production
# ==============================================================================
domain_name      = "rallycal.com"
route53_zone_id  = ""  # Set this with your actual Route53 hosted zone ID

# ==============================================================================
# Security Configuration
# ==============================================================================
# secret_key should be provided via environment variable or secure method
# Do not set it directly in this file for production

# ==============================================================================
# Monitoring Configuration
# ==============================================================================
log_level         = "INFO"
notification_email = "alerts@rallycal.com"

# ==============================================================================
# Feature Flags - Production
# ==============================================================================
enable_monitoring = true
enable_logging   = true
enable_backup    = true
enable_ssl       = true

# Production optimization
enable_spot_instances     = false  # Use on-demand instances for production stability
enable_scheduled_scaling  = false  # No scheduled scaling in production

# ==============================================================================
# Production-Specific Overrides
# ==============================================================================

# Note: The following configuration provides:
# - High availability with Multi-AZ RDS and Redis failover
# - Adequate resources for production workloads
# - Proper backup and retention policies
# - Enhanced monitoring and alerting
# - Security best practices

# Estimated monthly cost for this configuration:
# - ECS Fargate: ~$45-60 (3 tasks with 1 vCPU, 2GB RAM each)
# - RDS Multi-AZ db.t3.medium: ~$60-80
# - ElastiCache Redis: ~$50-70 (2 nodes)
# - Application Load Balancer: ~$20-25
# - NAT Gateway: ~$45
# - Data transfer and other services: ~$20-30
# Total estimated: $240-290 per month
# 
# This can be optimized based on actual usage patterns