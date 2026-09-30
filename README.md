# JS Rush - Production Deployment Guide

## Quick Start

### Prerequisites
- Ubuntu 22.04/24.04 LTS server
- Domain name with DNS configured
- Gmail account with App Password for SMTP
- Supabase account for PostgreSQL
- Whish Money merchant account

### Quick Deploy

```bash
# 1. Clone repository
git clone https://github.com/yourusername/jsrush.git
cd jsrush

# 2. Run deployment script (as root)
sudo ./deploy/setup_production.sh

# 3. Configure environment variables
nano .env.production

# 4. Deploy
railway up
# OR
./deploy/setup_production.sh
```

## Security Checklist

### Pre-Deployment
- [ ] Generate strong SECRET_KEY and JWT_SECRET_KEY (32+ chars)
- [ ] Enable 2FA on Gmail account and generate App Password
- [ ] Configure Whish Money merchant account
- [ ] Set up Supabase PostgreSQL database
- [ ] Configure DNS records for domain

### Post-Deployment
- [ ] Change default admin password
- [ ] Enable 2FA for admin account
- [ ] Verify SSL certificate (Let's Encrypt)
- [ ] Test email verification flow
- [ ] Test deposit/withdrawal flow
- [ ] Configure firewall (ufw allow 22/80/443)
- [ ] Enable automated backups
- [ ] Configure log rotation
- [ ] Set up monitoring (Sentry, Prometheus)

## Environment Variables

### Required (.env.production)
```bash
# Security
SECRET_KEY=your-32-char-secret-key
JWT_SECRET_KEY=another-32-char-secret
SERVER_NAME=yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (Gmail SMTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER="JS Rush <noreply@yourdomain.com>"

# Whish Money
WHISH_CHANNEL=your_channel_id
WHISH_SECRET=your_secret_key
WHISH_WEBSITE_URL=https://yourdomain.com
WHISH_BASE_URL=https://whish.money/itel-service/api
WHISH_WEBHOOK_SECRET=your_webhook_secret
WHISH_SANDBOX=false

# Security
SECRET_KEY=your-32-char-secret
JWT_SECRET_KEY=another-32-char-secret
EMAIL_VERIFICATION_REQUIRED=true
ADMIN_2FA_REQUIRED=true
```

## Deployment Commands

### Using Railway (Recommended)
```bash
# Install CLI
npm install -g @railway/cli
railway login
railway up
```

### Manual Server Deployment
```bash
# Run setup script as root
sudo ./deploy/setup_production.sh

# Or manual steps:
# 1. Copy files to /var/www/jsrush
# 2. Create venv and install deps
# 3. Copy .env.production to .env
# 4. Run setup script
sudo ./deploy/setup_production.sh
```

## Security Checklist

### Application Security
- [ ] Strong SECRET_KEY and JWT_SECRET_KEY (32+ chars)
- [ ] HTTPS enforced (SESSION_COOKIE_SECURE=True)
- [ ] Secure cookies (HttpOnly, SameSite=Lax)
- [ ] CSRF protection enabled
- [ ] Security headers (HSTS, CSP, X-Frame-Options)
- [ ] Rate limiting enabled
- [ ] CSRF protection on forms
- [ ] Input validation and sanitization

### Authentication & Authorization
- [ ] Email verification required
- [ ] 2FA for admin accounts
- [ ] Password strength requirements
- [ ] Account lockout after failed attempts
- [ ] Session timeout configured
- [ ] Secure password hashing (bcrypt)

### Infrastructure Security
- [ ] HTTPS enforced (SSL/TLS)
- [ ] Firewall configured (22, 80, 443 only)
- [ ] SSH key authentication only
- [ ] Fail2ban configured
- [ ] Automatic security updates
- [ ] Non-root user for app

### Data Protection
- [ ] Encrypted database connections (SSL)
- [ ] Encrypted backups
- [ ] S3 backup encryption
- [ ] PII encryption at rest
- [ ] Regular backup testing

### Monitoring & Logging
- [ ] Sentry error tracking
- [ ] Prometheus metrics
- [ ] Log rotation configured
- [ ] Audit logging for admin actions
- [ ] Login notifications
- [ ] Failed login alerts

### Backup & Recovery
- [ ] Daily automated backups
- [ ] Off-site backup storage (S3)
- [ ] Backup encryption
- [ ] RPO/RTO tested
- [ ] Disaster recovery tested

## Environment Variables Reference

### Required Variables
```bash
# Core
SECRET_KEY=                        # 32+ chars
JWT_SECRET_KEY=                    # 32+ chars
SERVER_NAME=yourdomain.com

# Database
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://...

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=app_password

# Whish Money
WHISH_CHANNEL=your_channel
WHISH_SECRET=your_secret
WHISH_WEBSITE_URL=https://domain.com
WHISH_BASE_URL=https://whish.money/itel-service/api
WHISH_WEBHOOK_SECRET=webhook_secret
WHISH_SANDBOX=false

# Security
SECRET_KEY=32+ chars
JWT_SECRET_KEY=32+ chars
EMAIL_VERIFICATION_REQUIRED=true
ADMIN_2FA_REQUIRED=true
```

## Monitoring Endpoints

- Health: `GET /health`
- Metrics: `GET /metrics` (Prometheus)
- Admin: `/admin` (admin only)

## Backup & Recovery

### Automated Backups
```bash
# Daily at 2 AM
0 2 * * * /var/www/jsrush/venv/bin/python /var/www/jsrush/scripts/backup_database.py

# Test restore
python scripts/test_disaster_recovery.py
```

### Disaster Recovery
- RPO: 1 hour (backup frequency)
- RTO: 4 hours (restore time)
- Tested monthly

## Monitoring

### Sentry (Error Tracking)
```bash
SENTRY_DSN=https://...
```

### Prometheus Metrics
- Endpoint: `/metrics`
- Scrape interval: 15s

### Health Checks
```bash
curl https://yourdomain.com/health
```

## Emergency Procedures

### Rollback Deployment
```bash
git revert HEAD
git push origin main
# Railway auto-deploys
```

### Emergency Maintenance
```bash
# Maintenance mode
systemctl stop jsrush
# ... maintenance ...
systemctl start jsrush
```

### Data Breach Response
1. Rotate all secrets immediately
2. Revoke all sessions
3. Notify affected users
4. Report to authorities (GDPR)

## Support

- Documentation: `/docs`
- Issues: GitHub Issues
- Security: security@yourdomain.com