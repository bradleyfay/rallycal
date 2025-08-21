# RallyCal Deployment Guide

RallyCal supports multiple simplified deployment options, moving away from complex AWS/Terraform infrastructure to developer-friendly platforms.

## Quick Deploy Options

### 🚂 Railway (Recommended for Beginners)
**Cost**: ~$10/month | **Setup**: 5 minutes | **Complexity**: ⭐

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/8nKqBv)

**Best for**: Personal use, quick prototypes, simple scaling
- One-click PostgreSQL addon
- Built-in monitoring and logs
- Automatic HTTPS and custom domains
- Git-based deployments

[📖 Railway Setup Guide →](./deploy/railway-setup.md)

### 🎨 Render (Recommended for Teams)
**Cost**: ~$14/month | **Setup**: 10 minutes | **Complexity**: ⭐⭐

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

**Best for**: Teams, staging/production environments, advanced monitoring
- Infrastructure as Code with `render.yaml`
- Built-in SSL, CDN, and DDoS protection
- Advanced monitoring and alerting
- Blue-green deployments

[📖 Render Setup Guide →](./deploy/render-setup.md)

### 🐳 Docker Compose (Self-Hosted)
**Cost**: VPS cost | **Setup**: 15 minutes | **Complexity**: ⭐⭐⭐

**Best for**: Self-hosting, full control, custom infrastructure
- Complete control over resources
- Works on any VPS/cloud provider
- Includes PostgreSQL and Redis
- Ideal for organizations with existing infrastructure

## Platform Comparison

| Feature | Railway | Render | Docker Compose |
|---------|---------|---------|----------------|
| **Setup Time** | 5 min | 10 min | 15 min |
| **Monthly Cost** | $10 | $14 | $5-20 (VPS) |
| **Auto Scaling** | ✅ | ✅ | ❌ |
| **Built-in Database** | ✅ | ✅ | ✅ |
| **Custom Domain** | ✅ | ✅ | Manual Setup |
| **SSL Certificate** | ✅ | ✅ | Manual Setup |
| **Monitoring** | Built-in | Advanced | Manual Setup |
| **Backup** | Automatic | Automatic | Manual |

## Environment Variables

### Required
```bash
ENVIRONMENT=production
DB_URL=postgresql://user:pass@host:5432/db
SECURITY_SECRET_KEY=your-secret-key-32-chars-min
```

### Optional (with defaults)
```bash
# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_WORKERS=2

# Calendar Processing  
CALENDAR_FETCH_TIMEOUT=30
CALENDAR_RETRY_ATTEMPTS=3
CALENDAR_CACHE_TTL=3600

# Security
SECURITY_CORS_ORIGINS=https://yourdomain.com
SECURITY_RATE_LIMIT_REQUESTS=1000
```

## Docker Compose Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  rallycal:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DB_URL=postgresql://rallycal:password@postgres:5432/rallycal
      - SECURITY_SECRET_KEY=your-secret-key-here
    depends_on:
      - postgres
    restart: unless-stopped
    volumes:
      - ./config:/app/config:ro

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=rallycal
      - POSTGRES_USER=rallycal
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

Deploy with:
```bash
docker-compose up -d
```

## Configuration

Create `config/calendars.yaml`:

```yaml
calendars:
  - name: "Soccer Team"
    url: "https://teamsnap.com/calendar.ics"
    color: "#FF6B6B"
    enabled: true

settings:
  title: "Family Sports Calendar"
  timezone: "America/New_York"
```

## Migration from AWS/Terraform

The old complex AWS infrastructure can be replaced with these simple platforms:

1. **Export data** from existing RDS database
2. **Deploy** to Railway/Render using guides above  
3. **Import data** to new database
4. **Update DNS** to point to new platform
5. **Decommission** AWS resources

The simplified approach reduces monthly costs from $50-100+ to $10-20 while maintaining all functionality.

For detailed setup instructions, see the platform-specific guides in the `deploy/` directory.