# RallyCal Infrastructure as Code - Main Configuration
# Provisions cloud infrastructure for RallyCal application

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }

  # Backend configuration for state management
  # Uncomment and configure for production use
  # backend "s3" {
  #   bucket         = "rallycal-terraform-state"
  #   key            = "infrastructure/terraform.tfstate"
  #   region         = "us-west-2"
  #   dynamodb_table = "rallycal-terraform-locks"
  #   encrypt        = true
  # }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "RallyCal"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "RallyCal Team"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "RallyCal Team"
  }

  # Database configuration
  db_name     = "rallycal"
  db_username = "rallycal"

  # Application configuration
  app_name = "rallycal"
  app_port = 8000
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  name_prefix = local.name_prefix
  cidr_block  = var.vpc_cidr_block
  
  availability_zones     = data.aws_availability_zones.available.names
  private_subnet_cidrs   = var.private_subnet_cidrs
  public_subnet_cidrs    = var.public_subnet_cidrs
  database_subnet_cidrs  = var.database_subnet_cidrs
  
  enable_nat_gateway = var.enable_nat_gateway
  enable_vpn_gateway = var.enable_vpn_gateway
  
  tags = local.common_tags
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security"

  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  
  app_port = local.app_port
  
  tags = local.common_tags
}

# Database Module (RDS PostgreSQL)
module "database" {
  source = "./modules/database"

  name_prefix = local.name_prefix
  
  # Database configuration
  db_name     = local.db_name
  db_username = local.db_username
  db_password = random_password.db_password.result
  
  # Network configuration
  vpc_id             = module.vpc.vpc_id
  database_subnet_ids = module.vpc.database_subnet_ids
  security_group_ids = [module.security_groups.database_security_group_id]
  
  # Instance configuration
  instance_class      = var.db_instance_class
  allocated_storage   = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  
  # Backup and maintenance
  backup_retention_period = var.db_backup_retention_period
  backup_window          = var.db_backup_window
  maintenance_window     = var.db_maintenance_window
  
  # Monitoring and performance
  monitoring_interval = var.db_monitoring_interval
  performance_insights_enabled = var.db_performance_insights_enabled
  
  # High availability
  multi_az = var.db_multi_az
  
  tags = local.common_tags
}

# Cache Module (ElastiCache Redis)
module "cache" {
  source = "./modules/cache"
  
  name_prefix = local.name_prefix
  
  # Network configuration
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.private_subnet_ids
  security_group_ids = [module.security_groups.cache_security_group_id]
  
  # Instance configuration
  node_type         = var.redis_node_type
  num_cache_nodes   = var.redis_num_cache_nodes
  parameter_group_name = var.redis_parameter_group_name
  
  # High availability
  automatic_failover_enabled = var.redis_automatic_failover_enabled
  
  tags = local.common_tags
}

# Application Load Balancer Module
module "load_balancer" {
  source = "./modules/load_balancer"

  name_prefix = local.name_prefix
  
  # Network configuration
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  security_group_ids = [module.security_groups.alb_security_group_id]
  
  # SSL configuration
  domain_name = var.domain_name
  zone_id     = var.route53_zone_id
  
  # Target group configuration
  app_port = local.app_port
  health_check_path = "/health"
  
  tags = local.common_tags
}

# ECS Cluster Module
module "ecs" {
  source = "./modules/ecs"

  name_prefix = local.name_prefix
  
  # Network configuration
  vpc_id            = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_ids = [module.security_groups.app_security_group_id]
  
  # Load balancer configuration
  target_group_arn = module.load_balancer.target_group_arn
  
  # Application configuration
  app_name  = local.app_name
  app_port  = local.app_port
  app_image = var.app_image
  
  # Service configuration
  desired_count = var.ecs_desired_count
  cpu          = var.ecs_cpu
  memory       = var.ecs_memory
  
  # Environment variables
  environment_variables = {
    RALLYCAL_ENVIRONMENT = var.environment
    RALLYCAL_LOG_LEVEL   = var.log_level
    RALLYCAL_HOST        = "0.0.0.0"
    RALLYCAL_PORT        = tostring(local.app_port)
    DATABASE_URL         = "postgresql+asyncpg://${local.db_username}:${random_password.db_password.result}@${module.database.db_endpoint}:5432/${local.db_name}"
    REDIS_URL            = "redis://${module.cache.redis_endpoint}:6379/0"
  }
  
  # Secrets
  secrets = {
    RALLYCAL_SECRET_KEY = module.secrets.secret_key_arn
  }
  
  # Auto scaling configuration
  autoscaling_enabled = var.ecs_autoscaling_enabled
  autoscaling_min_capacity = var.ecs_autoscaling_min_capacity
  autoscaling_max_capacity = var.ecs_autoscaling_max_capacity
  
  tags = local.common_tags
}

# Secrets Manager Module
module "secrets" {
  source = "./modules/secrets"

  name_prefix = local.name_prefix
  
  # Application secrets
  secret_key = var.secret_key != "" ? var.secret_key : random_password.secret_key.result
  
  tags = local.common_tags
}

resource "random_password" "secret_key" {
  length  = 64
  special = true
}

# Monitoring and Logging Module
module "monitoring" {
  source = "./modules/monitoring"

  name_prefix = local.name_prefix
  
  # ECS configuration
  ecs_cluster_name = module.ecs.cluster_name
  ecs_service_name = module.ecs.service_name
  
  # Database configuration
  db_instance_id = module.database.db_instance_id
  
  # Load balancer configuration
  alb_arn_suffix = module.load_balancer.alb_arn_suffix
  target_group_arn_suffix = module.load_balancer.target_group_arn_suffix
  
  # Notification configuration
  notification_email = var.notification_email
  
  tags = local.common_tags
}