# Render Deployment Guide

## Quick Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/rallycal)

## Manual Setup

### Prerequisites

1. [Render account](https://render.com) (free tier available)
2. GitHub repository with your RallyCal code
3. [Render CLI](https://render.com/docs/cli) (optional but recommended)

### Option 1: Infrastructure as Code (Recommended)

1. **Connect Repository**: Link your GitHub repository to Render
2. **Deploy from render.yaml**: Render will automatically detect the `render.yaml` file
3. **Review Configuration**: Check services, environment variables, and database settings
4. **Deploy**: Click deploy - Render will provision database and web service automatically

### Option 2: Manual Setup

#### Step 1: Create PostgreSQL Database

1. Go to Render dashboard
2. Click "New" → "PostgreSQL"
3. Configure:
   - Name: `rallycal-postgres`
   - Database: `rallycal`
   - User: `rallycal`
   - Plan: Starter ($7/month)
   - Region: Choose closest to your users

#### Step 2: Create Web Service

1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - Name: `rallycal-web`
   - Runtime: Docker
   - Build Command: (leave empty)
   - Start Command: `/app/start.sh`
   - Plan: Starter ($7/month)

#### Step 3: Configure Environment Variables

Set the following in the web service environment:

**Required:**
```
ENVIRONMENT=production
DB_URL=[connection string from PostgreSQL service]
SECURITY_SECRET_KEY=[generate secure random string]
```

**Optional:**
```
SERVER_WORKERS=2
SECURITY_CORS_ORIGINS=https://your-app.onrender.com
CALENDAR_CONFIG_FILE=config/calendars.yaml
```

### Step 4: Deploy

Render will automatically deploy when you push to your main branch.

## Configuration

### Calendar Setup

Create `config/calendars.yaml` in your repository:

```yaml
calendars:
  - name: "Soccer Team A"
    url: "https://teamsnap.com/api/v2/teams/123/icalendar"
    color: "#FF6B6B"
    enabled: true
    
  - name: "Baseball League"  
    url: "https://leaguelineup.com/calendar.ics"
    color: "#4ECDC4"
    enabled: true

settings:
  title: "Smith Family Sports"
  description: "All our sports activities in one calendar"
  timezone: "America/Los_Angeles"
```

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Runtime environment | `production` | Yes |
| `DB_URL` | PostgreSQL connection string | Auto-set by Render | Yes |
| `SECURITY_SECRET_KEY` | JWT signing key | Auto-generated | Yes |
| `SECURITY_CORS_ORIGINS` | Allowed origins | `*` | No |
| `SERVER_WORKERS` | Number of workers | `2` | No |
| `CALENDAR_FETCH_TIMEOUT` | Request timeout (seconds) | `30` | No |

## Custom Domain

1. Go to your web service settings
2. Click "Custom Domains"
3. Add your domain (e.g., `calendar.yourdomain.com`)
4. Configure DNS CNAME record to point to your Render URL
5. Render will automatically provision SSL certificate

## Monitoring & Logs

### Built-in Monitoring
- **Logs**: Real-time logs in Render dashboard
- **Metrics**: CPU, memory, response times
- **Health Checks**: Automatic monitoring of `/health` endpoint
- **Alerts**: Email notifications for service issues

### Accessing Logs
```bash
# Install Render CLI
brew install render-cli  # macOS
# or download from: https://render.com/docs/cli

# View logs
render logs -s rallycal-web

# Follow logs in real-time
render logs -s rallycal-web --tail
```

## Scaling

### Vertical Scaling (More Power)
Upgrade your service plan in the Render dashboard:
- **Starter**: 0.5 CPU, 512MB RAM ($7/month)
- **Standard**: 1 CPU, 2GB RAM ($25/month)  
- **Pro**: 2 CPU, 4GB RAM ($85/month)

### Horizontal Scaling (More Instances)
Available on Standard and Pro plans:
- Configure auto-scaling rules
- Set min/max instance counts
- Scale based on CPU or memory thresholds

## Cost Breakdown

### Monthly Costs (USD)
- **Web Service (Starter)**: $7/month
- **PostgreSQL (Starter)**: $7/month
- **Custom Domain**: Free
- **SSL Certificate**: Free
- **Total**: ~$14/month

### Cost Optimization Tips
1. Use Render's free tier for development/testing
2. Start with Starter plans and scale as needed
3. Monitor usage with Render's built-in analytics
4. Consider using SQLite for low-traffic deployments

## Backup & Recovery

### Database Backups
Render automatically backs up PostgreSQL databases:
- **Daily backups** retained for 7 days (Starter plan)
- **Point-in-time recovery** available on higher plans
- **Manual backups** available anytime

### Configuration Backup
Keep your configuration in version control:
- `render.yaml` - Infrastructure configuration
- `config/calendars.yaml` - Calendar sources
- Environment variables documented

## Troubleshooting

### Common Issues

**Service Won't Start**
```bash
# Check logs for startup errors
render logs -s rallycal-web

# Common causes:
# - Missing environment variables
# - Database connection failed
# - Port binding issues
```

**Database Connection Issues**
```bash
# Verify database is running
render services list

# Check connection string
render env get DB_URL -s rallycal-web

# Test connection from web service shell
render shell rallycal-web
python -c "import asyncpg; print('Connection test')"
```

**Calendar Feeds Not Loading**
- Check calendar URLs are accessible
- Verify authentication if required
- Check logs for fetch timeout errors
- Test URLs manually with curl/httpie

### Debug Commands

```bash
# Service status
render services list

# Environment variables
render env list -s rallycal-web

# Shell access
render shell rallycal-web

# Deploy logs
render deploys list -s rallycal-web
```

### Performance Tuning

**Database Performance**
- Monitor query performance in logs
- Add database indexes for common queries
- Consider connection pooling settings
- Upgrade to higher database plan if needed

**Web Service Performance**  
- Adjust `SERVER_WORKERS` based on CPU usage
- Monitor response times in dashboard
- Enable caching for frequently accessed data
- Consider CDN for static assets

## Support

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Status Page**: https://status.render.com
- **RallyCal Issues**: GitHub repository issues