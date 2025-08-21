# RallyCal Validation Guide

This guide provides step-by-step instructions to validate that the RallyCal implementation works correctly.

## Phase 1: Local Development Validation (Start Here)

### 1.1 Quick Health Check

```bash
# 1. Start the development environment
docker-compose up -d

# 2. Wait for services to start (30-60 seconds)
sleep 30

# 3. Check if all services are running
docker-compose ps

# 4. Test basic health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"..."}
```

### 1.2 Comprehensive API Testing

```bash
# Test all health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health/comprehensive  
curl http://localhost:8000/api/v1/health/ready
curl http://localhost:8000/api/v1/health/live

# Test calendar endpoint (may return minimal calendar if no config)
curl http://localhost:8000/api/v1/calendar.ics

# Test metrics endpoint
curl http://localhost:8000/api/v1/metrics

# Test API documentation (if in development mode)
open http://localhost:8000/docs
```

### 1.3 Database Connectivity Test

```bash
# Connect to the running PostgreSQL container
docker-compose exec db psql -U rallycal -d rallycal

# Run inside PostgreSQL:
\dt  -- List tables (should show SQLAlchemy tables)
SELECT health_check();  -- Run our health check function
\q   -- Quit

# Test Redis connectivity
docker-compose exec redis redis-cli ping
# Expected response: PONG
```

### 1.4 Application Logs Review

```bash
# Check application logs for errors
docker-compose logs app

# Check database logs
docker-compose logs db

# Check for any error patterns
docker-compose logs app | grep -i error
docker-compose logs app | grep -i exception
```

## Phase 2: Configuration and Integration Testing

### 2.1 Create Test Calendar Configuration

```bash
# Create config directory
mkdir -p config

# Create a test calendar configuration
cat > config/calendars.yaml << 'EOF'
calendars:
  - name: "Test Soccer Team"
    url: "https://calendar.google.com/calendar/ical/en.usa%23holiday%40group.v.calendar.google.com/public/basic.ics"
    color: "#FF0000"
    enabled: true
    auth:
      type: "none"

manual_events:
  - title: "Test Family Meeting"
    start: "2024-12-25T19:00:00Z"
    end: "2024-12-25T20:00:00Z"
    location: "Home"
    description: "Test manual event"
EOF

# Restart the application to pick up configuration
docker-compose restart app

# Wait for restart
sleep 15

# Test calendar endpoint with real data
curl http://localhost:8000/api/v1/calendar.ics

# You should now see a calendar with holidays and your manual event
```

### 2.2 Test Calendar Webhook (Configuration Updates)

```bash
# Test the webhook endpoint (simulates GitHub webhook)
curl -X POST http://localhost:8000/api/v1/webhooks/config \
  -H "Content-Type: application/json" \
  -d '{
    "ref": "refs/heads/main",
    "commits": [{"modified": ["config/calendars.yaml"]}]
  }'

# Should return: {"message": "Configuration reload triggered"}
```

## Phase 3: Code Quality and Testing Validation

### 3.1 Run the Test Suite

```bash
# Install development dependencies
uv sync --dev

# Run linting checks
uv run ruff check .
uv run ruff format --check .

# Run type checking
uv run mypy src tests

# Run the full test suite
uv run hatch run test

# Run tests with coverage
uv run hatch run test-cov
```

### 3.2 Security and Quality Checks

```bash
# Run security scan
uv run bandit -r src/

# Check for dependency vulnerabilities
uv run safety check

# Validate Docker image security (requires Docker)
docker build -t rallycal:test .
docker run --rm rallycal:test python -c "import src.rallycal; print('✅ Application imports successfully')"
```

## Phase 4: CI/CD Pipeline Validation

### 4.1 GitHub Actions Workflow Test

```bash
# Push changes to trigger CI/CD
git add .
git commit -m "test: trigger CI/CD validation"
git push origin main

# Monitor the GitHub Actions workflow:
# 1. Go to https://github.com/your-username/rallycal/actions
# 2. Watch the "CI Pipeline" workflow
# 3. Ensure all jobs pass (test, build-image, security-scan, etc.)
```

### 4.2 Manual Docker Build Test

```bash
# Test the Docker build process
docker build -t rallycal:local .

# Run the container
docker run -d --name rallycal-test \
  -p 8001:8000 \
  -e RALLYCAL_ENVIRONMENT=development \
  -e DATABASE_URL=sqlite:///./test.db \
  rallycal:local

# Wait for container to start
sleep 10

# Test the containerized application
curl http://localhost:8001/health

# Clean up
docker stop rallycal-test
docker rm rallycal-test
```

## Phase 5: Load and Performance Testing

### 5.1 Basic Load Testing

```bash
# Install hey load testing tool (macOS)
brew install hey

# Run basic load test
hey -n 100 -c 10 http://localhost:8000/health

# Test calendar endpoint under load
hey -n 50 -c 5 http://localhost:8000/api/v1/calendar.ics

# Monitor response times and error rates
```

### 5.2 Memory and Resource Usage

```bash
# Monitor Docker container resource usage
docker stats

# Check for memory leaks by monitoring over time
watch -n 5 'docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"'
```

## Phase 6: Infrastructure Validation (Optional - AWS Deployment)

### 6.1 Terraform Infrastructure Test

```bash
# Navigate to staging environment
cd terraform/environments/staging

# Initialize Terraform
terraform init

# Validate Terraform configuration
terraform validate

# Plan the infrastructure (don't apply yet)
terraform plan -var-file=terraform.tfvars

# If validation looks good, apply (this will cost money!)
# terraform apply -var-file=terraform.tfvars
```

### 6.2 Cloud Deployment Health Check

```bash
# After deployment, test the cloud endpoints
# Replace with your actual domain/load balancer URL
STAGING_URL="https://your-staging-domain.com"

curl $STAGING_URL/health
curl $STAGING_URL/api/v1/health/comprehensive
curl $STAGING_URL/api/v1/calendar.ics
```

## Common Issues and Troubleshooting

### Issue 1: Services Won't Start

```bash
# Check port conflicts
lsof -i :8000
lsof -i :5432

# Check Docker daemon
docker version
docker-compose version

# Reset everything
docker-compose down -v
docker-compose up -d --force-recreate
```

### Issue 2: Database Connection Errors

```bash
# Check database logs
docker-compose logs db

# Test database connectivity
docker-compose exec db pg_isready -U rallycal

# Reset database
docker-compose down -v db
docker-compose up -d db
sleep 10
docker-compose up -d app
```

### Issue 3: Import/Module Errors

```bash
# Verify Python environment
uv run python -c "import src.rallycal; print('✅ Imports work')"

# Check for missing dependencies
uv sync --dev
uv run python -c "import fastapi, sqlalchemy, httpx; print('✅ Dependencies installed')"
```

### Issue 4: Test Failures

```bash
# Run specific test files
uv run pytest tests/unit/test_models.py -v
uv run pytest tests/integration/ -v

# Run with more verbose output
uv run pytest -vvv --tb=long

# Skip slow tests
uv run pytest -m "not slow"
```

## Validation Checklist

Use this checklist to verify all components:

### ✅ Basic Functionality

- [ ] Docker Compose starts all services
- [ ] Application responds to health checks
- [ ] Database connectivity works
- [ ] Redis connectivity works
- [ ] API endpoints return expected responses

### ✅ Configuration Management

- [ ] Calendar configuration loads properly
- [ ] Webhook triggers configuration reload
- [ ] Manual events appear in calendar output
- [ ] External calendar feeds are processed

### ✅ Code Quality

- [ ] All tests pass
- [ ] Linting checks pass
- [ ] Type checking passes
- [ ] Security scans show no critical issues
- [ ] Code coverage meets requirements

### ✅ Performance

- [ ] Health checks respond under 100ms
- [ ] Calendar generation completes under 2s
- [ ] Application handles 100+ concurrent requests
- [ ] Memory usage remains stable over time

### ✅ Production Readiness

- [ ] Docker image builds successfully
- [ ] Container runs in production mode
- [ ] Logs are structured and informative
- [ ] Monitoring endpoints work
- [ ] Security headers are present

### ✅ CI/CD Pipeline

- [ ] GitHub Actions workflow passes
- [ ] Docker image builds and pushes
- [ ] Security scanning completes
- [ ] Deployment process works

### ✅ Infrastructure (If Deployed)

- [ ] Terraform configuration validates
- [ ] AWS resources provision correctly
- [ ] Load balancer routes traffic properly
- [ ] Database and cache are accessible
- [ ] SSL/TLS certificates work

## Success Criteria

The RallyCal implementation is considered validated when:

1. **All health checks pass** in local development
2. **Configuration management works** with real calendar feeds
3. **Test suite passes** with >80% code coverage
4. **Docker containerization works** in production mode
5. **CI/CD pipeline executes** without errors
6. **Performance benchmarks met** (response times, throughput)
7. **Security scans pass** with no critical vulnerabilities

## Quick Start Validation Commands

```bash
# Complete validation in ~5 minutes
docker-compose up -d && sleep 30
curl http://localhost:8000/health | jq .
curl http://localhost:8000/api/v1/calendar.ics | head -10
uv run hatch run test --maxfail=5
docker-compose logs app | tail -20
echo "✅ Basic validation complete!"
```

If all these steps pass, your RallyCal implementation is working correctly! 🎉
