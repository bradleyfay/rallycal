# Railway Deployment Guide

## Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/8nKqBv?referralCode=rallycal)

## Manual Setup

### Prerequisites

1. [Railway CLI](https://docs.railway.app/develop/cli) installed
2. Railway account (free tier available)

### Step 1: Create Railway Project

```bash
# Login to Railway
railway login

# Create new project
railway init

# Link to existing project (if already created)
# railway link
```

### Step 2: Add PostgreSQL Database

```bash
# Add PostgreSQL service
railway add postgresql

# This automatically sets DATABASE_URL environment variable
```

### Step 3: Configure Environment Variables

Set the following environment variables in the Railway dashboard:

**Required:**
- `SECURITY_SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

**Optional (customize as needed):**
- `SECURITY_CORS_ORIGINS` - Your domain(s), comma-separated
- `CALENDAR_CONFIG_FILE` - Path to your calendar config (default: config/calendars.yaml)
- `SERVER_WORKERS` - Number of workers (default: 2)

### Step 4: Deploy

```bash
# Deploy from current directory
railway up

# Or deploy from specific directory
railway up --service rallycal-web
```

### Step 5: Set Custom Domain (Optional)

```bash
# Add custom domain
railway domain

# Or configure in Railway dashboard
```

## Configuration

### Calendar Configuration

Create your calendar configuration file at `config/calendars.yaml`:

```yaml
calendars:
  - name: "Soccer Team"
    url: "https://teamsnap.com/api/v2/teams/123/icalendar"
    color: "#FF0000"
    enabled: true
  
  - name: "Baseball League"
    url: "https://leaguelineup.com/calendar.ics"
    color: "#0000FF" 
    enabled: true

settings:
  title: "Family Sports Calendar"
  description: "Consolidated calendar for all family sports activities"
  timezone: "America/New_York"
```

### Environment Variables

All configuration can be done through Railway environment variables:

- `ENVIRONMENT` - Set to "production"
- `DB_URL` - Automatically set by Railway PostgreSQL addon
- `SECURITY_SECRET_KEY` - Generate a secure random string
- `SECURITY_CORS_ORIGINS` - Comma-separated list of allowed origins
- `CALENDAR_*` - Calendar processing settings
- `SERVER_*` - Web server configuration

## Monitoring

Railway provides built-in monitoring:

- **Logs**: View in Railway dashboard or `railway logs`
- **Metrics**: CPU, memory, network usage
- **Health Checks**: Automatic monitoring of `/health` endpoint
- **Alerts**: Configure notifications for downtime

## Scaling

Railway auto-scales based on your plan:

- **Starter**: 1 CPU, 1GB RAM
- **Developer**: 2 CPU, 2GB RAM  
- **Team**: 4 CPU, 4GB RAM

To manually scale:

```bash
# Scale vertically (more resources per instance)
railway variables set SERVER_WORKERS=4

# Railway handles horizontal scaling automatically
```

## Custom Domain

1. Go to Railway project settings
2. Add your domain under "Custom Domains"
3. Configure DNS CNAME record to point to Railway
4. Update `SECURITY_CORS_ORIGINS` to include your domain

## Cost Estimation

Railway pricing (as of 2024):

- **Starter**: $5/month - Perfect for personal use
- **Developer**: $20/month - Small family/team use
- **Team**: $99/month - Multiple families/organizations

PostgreSQL addon: $5/month for managed database

## Troubleshooting

### Common Issues

1. **App won't start**: Check logs with `railway logs`
2. **Database connection failed**: Verify PostgreSQL addon is connected
3. **502 Bad Gateway**: Usually indicates app startup issues, check environment variables
4. **Calendar feeds not loading**: Check calendar URL accessibility and authentication

### Debug Commands

```bash
# View logs
railway logs

# Shell into container
railway shell

# Check environment variables
railway variables

# Restart service
railway restart
```

### Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- RallyCal Issues: Create GitHub issue for app-specific problems