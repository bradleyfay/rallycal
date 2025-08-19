# RallyCal Staging Environment Configuration
# Terraform variables for staging deployment

# ==============================================================================
# Environment Configuration
# ==============================================================================
project_name = "rallycal"
environment  = "staging"
aws_region   = "us-west-2"

# ==============================================================================
# Network Configuration
# ==============================================================================
vpc_cidr_block          = "10.1.0.0/16"
public_subnet_cidrs     = ["10.1.1.0/24", "10.1.2.0/24"]
private_subnet_cidrs    = ["10.1.10.0/24", "10.1.20.0/24"]
database_subnet_cidrs   = ["10.1.100.0/24", "10.1.200.0/24"]

enable_nat_gateway = true
enable_vpn_gateway = false

# ==============================================================================
# Database Configuration - Staging
# ==============================================================================
db_instance_class           = "db.t3.small"
db_allocated_storage        = 20
db_max_allocated_storage    = 50
db_backup_retention_period  = 3
db_backup_window           = "03:00-04:00"
db_maintenance_window      = "Sun:04:00-Sun:05:00"
db_monitoring_interval     = 60
db_performance_insights_enabled = true
db_multi_az                = false

# ==============================================================================
# Cache Configuration - Staging
# ==============================================================================
redis_node_type                    = "cache.t3.small"
redis_num_cache_nodes              = 1
redis_parameter_group_name         = "default.redis7"
redis_automatic_failover_enabled   = false

# ==============================================================================
# Application Configuration - Staging
# ==============================================================================
app_image = "ghcr.io/rallycal/rallycal:staging"

ecs_desired_count = 2
ecs_cpu          = 512
ecs_memory       = 1024

# Auto scaling configuration
ecs_autoscaling_enabled     = true
ecs_autoscaling_min_capacity = 1
ecs_autoscaling_max_capacity = 5

# ==============================================================================
# Domain Configuration - Staging
# ==============================================================================
domain_name      = "staging.rallycal.com"
route53_zone_id  = ""  # Set this if you have a Route53 hosted zone

# ==============================================================================
# Security Configuration
# ==============================================================================
# secret_key is auto-generated if not specified

# ==============================================================================
# Monitoring Configuration
# ==============================================================================
log_level         = "DEBUG"
notification_email = "devops@rallycal.com"

# ==============================================================================
# Feature Flags - Staging
# ==============================================================================
enable_monitoring = true
enable_logging   = true
enable_backup    = true
enable_ssl       = true

# Cost optimization features
enable_spot_instances     = true   # Use spot instances for cost savings in staging
enable_scheduled_scaling  = true   # Scale down during off hours

scheduled_scaling_config = {
  scale_down_cron     = "0 22 * * *"  # 10 PM UTC - scale down to 1 instance
  scale_down_capacity = 1
  scale_up_cron       = "0 6 * * *"   # 6 AM UTC - scale up to 2 instances
  scale_up_capacity   = 2
}