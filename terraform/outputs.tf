# RallyCal Terraform Outputs
# Defines outputs that will be displayed after deployment

# ==============================================================================
# Network Outputs
# ==============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = module.vpc.database_subnet_ids
}

# ==============================================================================
# Database Outputs
# ==============================================================================

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = module.database.db_endpoint
  sensitive   = true
}

output "database_port" {
  description = "RDS instance port"
  value       = module.database.db_port
}

output "database_name" {
  description = "Database name"
  value       = local.db_name
}

output "database_username" {
  description = "Database username"
  value       = local.db_username
}

# ==============================================================================
# Cache Outputs
# ==============================================================================

output "redis_endpoint" {
  description = "Redis cache endpoint"
  value       = module.cache.redis_endpoint
}

output "redis_port" {
  description = "Redis cache port"
  value       = module.cache.redis_port
}

# ==============================================================================
# Load Balancer Outputs
# ==============================================================================

output "load_balancer_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.load_balancer.dns_name
}

output "load_balancer_zone_id" {
  description = "Zone ID of the load balancer"
  value       = module.load_balancer.zone_id
}

output "load_balancer_arn" {
  description = "ARN of the load balancer"
  value       = module.load_balancer.load_balancer_arn
}

# ==============================================================================
# Application Outputs
# ==============================================================================

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.ecs.service_name
}

output "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = module.ecs.task_definition_arn
}

# ==============================================================================
# Security Outputs
# ==============================================================================

output "app_security_group_id" {
  description = "ID of the application security group"
  value       = module.security_groups.app_security_group_id
}

output "database_security_group_id" {
  description = "ID of the database security group"
  value       = module.security_groups.database_security_group_id
}

output "cache_security_group_id" {
  description = "ID of the cache security group"
  value       = module.security_groups.cache_security_group_id
}

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = module.security_groups.alb_security_group_id
}

# ==============================================================================
# URL and Access Information
# ==============================================================================

output "application_url" {
  description = "URL to access the application"
  value = var.domain_name != "" ? (
    var.enable_ssl ? "https://${var.domain_name}" : "http://${var.domain_name}"
  ) : (
    var.enable_ssl ? "https://${module.load_balancer.dns_name}" : "http://${module.load_balancer.dns_name}"
  )
}

output "health_check_url" {
  description = "Health check endpoint URL"
  value = "${var.domain_name != "" ? (
    var.enable_ssl ? "https://${var.domain_name}" : "http://${var.domain_name}"
  ) : (
    var.enable_ssl ? "https://${module.load_balancer.dns_name}" : "http://${module.load_balancer.dns_name}"
  )}/health"
}

output "api_base_url" {
  description = "Base URL for API endpoints"
  value = "${var.domain_name != "" ? (
    var.enable_ssl ? "https://${var.domain_name}" : "http://${var.domain_name}"
  ) : (
    var.enable_ssl ? "https://${module.load_balancer.dns_name}" : "http://${module.load_balancer.dns_name}"
  )}/api/v1"
}

output "calendar_feed_url" {
  description = "URL for the calendar feed"
  value = "${var.domain_name != "" ? (
    var.enable_ssl ? "https://${var.domain_name}" : "http://${var.domain_name}"
  ) : (
    var.enable_ssl ? "https://${module.load_balancer.dns_name}" : "http://${module.load_balancer.dns_name}"
  )}/api/v1/calendar.ics"
}

# ==============================================================================
# Environment Information
# ==============================================================================

output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

# ==============================================================================
# Connection Strings
# ==============================================================================

output "database_connection_string" {
  description = "Database connection string (without password)"
  value       = "postgresql+asyncpg://${local.db_username}:****@${module.database.db_endpoint}:5432/${local.db_name}"
  sensitive   = true
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "redis://${module.cache.redis_endpoint}:6379/0"
}

# ==============================================================================
# Monitoring and Logging
# ==============================================================================

output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name"
  value       = "/ecs/${local.name_prefix}"
}

output "monitoring_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${local.name_prefix}-dashboard"
}

# ==============================================================================
# Deployment Information
# ==============================================================================

output "deployment_info" {
  description = "Summary of deployment information"
  value = {
    project_name        = var.project_name
    environment        = var.environment
    aws_region         = var.aws_region
    application_url    = var.domain_name != "" ? (
      var.enable_ssl ? "https://${var.domain_name}" : "http://${var.domain_name}"
    ) : (
      var.enable_ssl ? "https://${module.load_balancer.dns_name}" : "http://${module.load_balancer.dns_name}"
    )
    ecs_cluster_name   = module.ecs.cluster_name
    ecs_service_name   = module.ecs.service_name
    database_endpoint  = "****"  # Masked for security
    redis_endpoint     = module.cache.redis_endpoint
    load_balancer_dns  = module.load_balancer.dns_name
  }
}

# ==============================================================================
# Cost Information
# ==============================================================================

output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (approximate)"
  value = {
    disclaimer = "These are rough estimates and actual costs may vary significantly based on usage"
    ecs_fargate = "${var.ecs_desired_count} tasks × $${format("%.2f", var.ecs_cpu * 0.00001235 + var.ecs_memory * 0.00000135 * 24 * 30)} per month"
    rds = "db.${var.db_instance_class} × ~$${var.db_instance_class == "db.t3.micro" ? "15" : var.db_instance_class == "db.t3.small" ? "30" : "60"} per month"
    elasticache = "cache.${var.redis_node_type} × ~$${var.redis_node_type == "cache.t3.micro" ? "12" : var.redis_node_type == "cache.t3.small" ? "25" : "50"} per month"
    alb = "Application Load Balancer × ~$20 per month"
    nat_gateway = var.enable_nat_gateway ? "NAT Gateway × ~$45 per month" : "NAT Gateway: Not enabled"
    data_transfer = "Data transfer costs vary by usage"
    total_estimate = "Total estimated range: $${var.enable_nat_gateway ? "100" : "60"}-200 per month"
  }
}

# ==============================================================================
# Next Steps
# ==============================================================================

output "next_steps" {
  description = "Recommended next steps after deployment"
  value = [
    "1. Configure DNS records if using a custom domain",
    "2. Set up monitoring alerts using the CloudWatch dashboard",
    "3. Configure application secrets in AWS Secrets Manager",
    "4. Set up backup and recovery procedures",
    "5. Configure CI/CD pipeline to deploy to this infrastructure",
    "6. Review and adjust auto-scaling policies based on usage patterns",
    "7. Set up log aggregation and analysis",
    "8. Perform security review and penetration testing"
  ]
}