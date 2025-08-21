# RallyCal Terraform Variables
# Defines all configurable parameters for infrastructure deployment

# ==============================================================================
# General Configuration
# ==============================================================================

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "rallycal"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

# ==============================================================================
# Networking Configuration
# ==============================================================================

variable "vpc_cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.100.0/24", "10.0.200.0/24"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_vpn_gateway" {
  description = "Enable VPN Gateway"
  type        = bool
  default     = false
}

# ==============================================================================
# Database Configuration (RDS)
# ==============================================================================

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage for RDS instance (GB)"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS instance (GB)"
  type        = number
  default     = 100
}

variable "db_backup_retention_period" {
  description = "Number of days to retain database backups"
  type        = number
  default     = 7
}

variable "db_backup_window" {
  description = "Preferred backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "db_maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "Sun:04:00-Sun:05:00"
}

variable "db_monitoring_interval" {
  description = "Enhanced monitoring interval (seconds)"
  type        = number
  default     = 60
}

variable "db_performance_insights_enabled" {
  description = "Enable Performance Insights"
  type        = bool
  default     = true
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

# ==============================================================================
# Cache Configuration (ElastiCache Redis)
# ==============================================================================

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

variable "redis_parameter_group_name" {
  description = "Parameter group for Redis"
  type        = string
  default     = "default.redis7"
}

variable "redis_automatic_failover_enabled" {
  description = "Enable automatic failover for Redis"
  type        = bool
  default     = false
}

# ==============================================================================
# Application Configuration (ECS)
# ==============================================================================

variable "app_image" {
  description = "Docker image for the application"
  type        = string
  default     = "ghcr.io/rallycal/rallycal:latest"
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "ecs_cpu" {
  description = "CPU units for ECS task"
  type        = number
  default     = 256
}

variable "ecs_memory" {
  description = "Memory (MB) for ECS task"
  type        = number
  default     = 512
}

variable "ecs_autoscaling_enabled" {
  description = "Enable ECS service auto scaling"
  type        = bool
  default     = true
}

variable "ecs_autoscaling_min_capacity" {
  description = "Minimum number of ECS tasks"
  type        = number
  default     = 1
}

variable "ecs_autoscaling_max_capacity" {
  description = "Maximum number of ECS tasks"
  type        = number
  default     = 10
}

# ==============================================================================
# Domain and SSL Configuration
# ==============================================================================

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
  default     = ""
}

# ==============================================================================
# Application Security
# ==============================================================================

variable "secret_key" {
  description = "Secret key for application (leave empty to auto-generate)"
  type        = string
  default     = ""
  sensitive   = true
}

# ==============================================================================
# Monitoring and Logging
# ==============================================================================

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
  
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be DEBUG, INFO, WARNING, ERROR, or CRITICAL."
  }
}

variable "notification_email" {
  description = "Email address for monitoring notifications"
  type        = string
  default     = ""
}

# ==============================================================================
# Environment-Specific Overrides
# ==============================================================================

variable "environment_config" {
  description = "Environment-specific configuration overrides"
  type = map(object({
    db_instance_class               = optional(string)
    db_multi_az                    = optional(bool)
    ecs_desired_count              = optional(number)
    ecs_cpu                        = optional(number)
    ecs_memory                     = optional(number)
    redis_node_type               = optional(string)
    redis_automatic_failover_enabled = optional(bool)
  }))
  
  default = {
    development = {
      db_instance_class = "db.t3.micro"
      db_multi_az      = false
      ecs_desired_count = 1
      ecs_cpu          = 256
      ecs_memory       = 512
      redis_node_type  = "cache.t3.micro"
      redis_automatic_failover_enabled = false
    }
    
    staging = {
      db_instance_class = "db.t3.small"
      db_multi_az      = false
      ecs_desired_count = 2
      ecs_cpu          = 512
      ecs_memory       = 1024
      redis_node_type  = "cache.t3.small"
      redis_automatic_failover_enabled = false
    }
    
    production = {
      db_instance_class = "db.t3.medium"
      db_multi_az      = true
      ecs_desired_count = 3
      ecs_cpu          = 1024
      ecs_memory       = 2048
      redis_node_type  = "cache.t3.medium"
      redis_automatic_failover_enabled = true
    }
  }
}

# ==============================================================================
# Feature Flags
# ==============================================================================

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring and alerting"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable CloudWatch Logs"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "enable_ssl" {
  description = "Enable SSL/TLS termination at load balancer"
  type        = bool
  default     = true
}

# ==============================================================================
# Cost Optimization
# ==============================================================================

variable "enable_spot_instances" {
  description = "Use Spot instances for ECS tasks (cost optimization)"
  type        = bool
  default     = false
}

variable "enable_scheduled_scaling" {
  description = "Enable scheduled auto scaling for cost optimization"
  type        = bool
  default     = false
}

variable "scheduled_scaling_config" {
  description = "Configuration for scheduled scaling"
  type = object({
    scale_down_cron     = optional(string, "0 22 * * *")  # 10 PM UTC
    scale_down_capacity = optional(number, 1)
    scale_up_cron       = optional(string, "0 6 * * *")   # 6 AM UTC
    scale_up_capacity   = optional(number, 3)
  })
  default = {}
}