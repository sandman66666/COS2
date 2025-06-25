# Heroku Deployment Guide

This guide explains how to deploy the Strategic Intelligence System to Heroku while maintaining local development capabilities.

## Prerequisites

1. **Heroku CLI installed** (✅ Already installed)
2. **Heroku account** 
3. **Google Cloud Console project** with OAuth configured
4. **Anthropic API key**

## Quick Deployment Steps

### 1. Login to Heroku
```bash
heroku login
```

### 2. Add Heroku Remote
```bash
heroku git:remote -a cos2
```

### 3. Set Environment Variables

Set the required environment variables in Heroku:

```bash
# Required: Anthropic API key
heroku config:set ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key

# Required: Google OAuth credentials
heroku config:set GOOGLE_CLIENT_ID=your-google-client-id
heroku config:set GOOGLE_CLIENT_SECRET=your-google-client-secret

# Optional: Set app name for auto-redirect URL generation
heroku config:set HEROKU_APP_NAME=cos2

# Optional: Override default settings
heroku config:set ENVIRONMENT=production
heroku config:set LOG_LEVEL=INFO
```

### 4. Update Google OAuth Settings

In your [Google Cloud Console](https://console.cloud.google.com/):

1. Go to **APIs & Services > Credentials**
2. Edit your OAuth 2.0 Client ID
3. Add to **Authorized redirect URIs**:
   ```
   https://cos2.herokuapp.com/auth/callback
   ```
   (Replace `cos2` with your actual Heroku app name)

### 5. Deploy
```bash
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main
```

### 6. Initialize Database (if needed)
```bash
heroku run python -c "from storage.storage_manager_sync import initialize_storage_manager_sync; initialize_storage_manager_sync()"
```

### 7. Open Your App
```bash
heroku open
```

## Environment Variables Reference

### Required Variables
- `ANTHROPIC_API_KEY`: Your Anthropic Claude API key
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret

### Auto-Configured by Heroku
- `DATABASE_URL`: PostgreSQL connection string (via addon)
- `PORT`: Application port
- `DYNO`: Heroku dyno identifier

### Optional Variables
- `HEROKU_APP_NAME`: Your app name (for auto-redirect URL)
- `ENVIRONMENT`: Set to "production"
- `LOG_LEVEL`: "INFO" or "DEBUG"
- `API_SECRET_KEY`: Auto-generated for sessions

## Database Setup

The app automatically uses Heroku PostgreSQL when `DATABASE_URL` is available:

```bash
# Add PostgreSQL addon (if not already added)
heroku addons:create heroku-postgresql:essential-0

# Check database info
heroku pg:info

# Connect to database (optional)
heroku pg:psql
```

## Monitoring and Logs

```bash
# View logs
heroku logs --tail

# Monitor app performance
heroku ps

# Check config
heroku config
```

## Scaling

```bash
# Scale web dynos
heroku ps:scale web=1

# Upgrade to professional dyno for better performance
heroku ps:type web=standard-1x
```

## Local vs Heroku Differences

| Feature | Local Development | Heroku Production |
|---------|------------------|-------------------|
| **Database** | Local PostgreSQL | Heroku PostgreSQL addon |
| **Redis** | Local Redis | Heroku Redis addon (optional) |
| **Environment** | `.env` file | Heroku config vars |
| **OAuth Redirect** | `localhost:8080` | `your-app.herokuapp.com` |
| **Logging** | Console output | Heroku logs |
| **Port** | 8080 (configurable) | Dynamic (Heroku sets) |

## Troubleshooting

### Common Issues

**1. Application Error**
```bash
heroku logs --tail
# Check for missing environment variables or startup errors
```

**2. OAuth Redirect Mismatch**
- Ensure Google OAuth redirect URI matches your Heroku app URL
- Set `HEROKU_APP_NAME` config var correctly

**3. Database Connection Issues**
```bash
heroku pg:info
# Verify PostgreSQL addon is provisioned
```

**4. Build Failures**
- Check `requirements.txt` for problematic dependencies
- Use `requirements-heroku.txt` if needed:
```bash
# Use alternative requirements file
echo "python-3.12.0" > runtime.txt
cp requirements-heroku.txt requirements.txt
git add . && git commit -m "Use Heroku-optimized requirements"
git push heroku main
```

### Performance Optimization

**1. Use Heroku-optimized requirements**
```bash
cp requirements-heroku.txt requirements.txt
```

**2. Add Redis for session storage** (optional)
```bash
heroku addons:create heroku-redis:mini
```

**3. Enable log drains** for monitoring
```bash
heroku drains:add https://your-logging-service.com/endpoint
```

## Security Considerations

### Environment Variables
- Never commit `.env` files
- Use Heroku config vars for all secrets
- Rotate API keys regularly

### Database Security
- Heroku PostgreSQL includes SSL by default
- Connection credentials are auto-managed
- Enable connection pooling for high traffic

### OAuth Security
- Use HTTPS redirect URIs only
- Validate all redirect URIs in Google Console
- Use secure session cookies (auto-configured)

## Cost Optimization

### Free Tier Usage
- **Dynos**: 550-1000 free hours/month
- **PostgreSQL**: 10k rows, 20 connections
- **Build time**: No limits

### Upgrade Recommendations
- **Standard-1X dyno**: Better performance ($25/month)
- **Essential PostgreSQL**: More storage ($5/month)
- **Redis addon**: Session management ($3/month)

## Maintenance

### Regular Updates
```bash
# Update dependencies
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push heroku main
```

### Database Maintenance
```bash
# Backup database
heroku pg:backups:capture

# Download backup
heroku pg:backups:download

# Restore from backup
heroku pg:backups:restore [backup-id]
```

### Monitor Resource Usage
```bash
# Check dyno metrics
heroku metrics

# Database metrics  
heroku pg:info
```

## Development Workflow

### Recommended Flow
1. **Develop locally** with `.env` file
2. **Test locally** with local PostgreSQL
3. **Commit changes** to git
4. **Deploy to Heroku** with `git push heroku main`
5. **Test on Heroku** with real OAuth flow
6. **Monitor logs** for any issues

### Environment Parity
The app automatically detects Heroku environment and adjusts:
- Database connections (local vs Heroku PostgreSQL)
- OAuth redirect URIs (localhost vs herokuapp.com)
- Port binding (8080 vs Heroku dynamic)
- Session security (development vs production)

---

Your Strategic Intelligence System is now ready for production deployment on Heroku! 🚀 