# JS Rush - Production Deployment Guide

## Prerequisites
- Ubuntu 20.04/22.04 server
- Domain name pointing to server IP
- Supabase project created
- Whish Money merchant account
- Gmail account with App Password

## Quick Deploy

```bash
# On your server:
git clone <your-repo> /var/www/jsrush
cd /var/www/jsrush
bash deploy.sh
```

The script will:
1. Clone repo & install dependencies
2. Open `.env` for you to fill in secrets
3. Run migrations on Supabase
4. Configure systemd + nginx + SSL
5. Start services & health check

## Required Values to Fill in `.env`

| Variable | Source |
|----------|--------|
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `WHISH_CHANNEL` | Whish Merchant Dashboard |
| `WHISH_SECRET` | Whish Merchant Dashboard |
| `WHISH_WEBHOOK_SECRET` | Whish Merchant Dashboard |
| `MAIL_PASSWORD` | Gmail App Password |
| `SENTRY_DSN` | Sentry.io (optional) |
| `TWILIO_*` | Twilio Console (optional) |

## Whish Money Production Setup

1. Get live credentials from Whish Merchant Dashboard
2. Set in `.env`:
   ```env
   WHISH_SANDBOX=false
   WHISH_BASE_URL=https://whish.money/itel-service/api
   ```
3. Update callbacks in Whish Merchant Portal:
   - Success: `https://yourdomain.com/whish/success`
   - Failure: `https://yourdomain.com/whish/failure`
   - Webhook: `https://yourdomain.com/webhook/whish`

## Supabase Database

The connection string is already configured:
```
DATABASE_URL=postgresql://postgres:pHRneOHv7uweiB7X@db.kjrcjadawbjxygdkcsaq.supabase.co:6543/postgres
```

Migrations run automatically via `flask db upgrade` using direct connection (port 5432).

## Post-Deploy Verification

```bash
# Health check
curl https://yourdomain.com/health

# Check logs
sudo journalctl -u jsrush -f

# Test registration + email verification
# Test Whish deposit/withdrawal
# Test all 11 games (90% house edge)
```

## Service Management

```bash
sudo systemctl restart jsrush      # Restart app
sudo systemctl status jsrush       # Check status
sudo journalctl -u jsrush -f       # Follow logs
```

## Rollback

```bash
git -C /var/www/jsrush log --oneline -5
git -C /var/www/jsrush reset --hard <commit-hash>
sudo systemctl restart jsrush
flask db upgrade
```