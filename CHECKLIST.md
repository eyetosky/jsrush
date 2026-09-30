# Production Deployment Checklist

## Pre-Deploy
- [ ] Supabase project created: `kjrcjadawbjxygdkcsaq`
- [ ] Whish Money merchant account approved
- [ ] Gmail account with App Password: `poshhstyasngjjyr`
- [ ] Domain DNS pointing to server IP
- [ ] Server: Ubuntu 20.04/22.04 with 2GB+ RAM

## Server Setup
- [ ] SSH into server
- [ ] Run: `bash deploy.sh`
- [ ] Script clones repo, installs deps, opens `.env` in nano

## Fill in `.env` (REQUIRED)
- [ ] `SECRET_KEY` - 32 char random string
- [ ] `JWT_SECRET_KEY` - 32 char random string  
- [ ] `WHISH_CHANNEL` - from Whish dashboard
- [ ] `WHISH_SECRET` - from Whish dashboard
- [ ] `WHISH_WEBHOOK_SECRET` - from Whish dashboard
- [ ] `MAIL_PASSWORD` - Gmail App Password: `poshhstyasngjjyr`
- [ ] `SENTRY_DSN` - (optional)
- [ ] `TWILIO_*` - (optional)

## Database Migration
- [ ] Script runs `flask db upgrade` on Supabase (port 5432)
- [ ] Tables created: user, transaction, game_session, etc.

## SSL & Nginx
- [ ] Certbot gets SSL cert for domain
- [ ] Nginx config deployed
- [ ] HTTPS works: `https://yourdomain.com/health`

## Whish Money Production
- [ ] Set `WHISH_SANDBOX=false` in `.env`
- [ ] Update callbacks in Whish Merchant Portal:
  - [ ] Success: `https://domain.com/whish/success`
  - [ ] Failure: `https://domain.com/whish/failure`
  - [ ] Webhook: `https://domain.com/webhook/whish`

## Post-Deploy Tests
- [ ] Visit `https://domain.com` - loads homepage
- [ ] Register account → check email → click verify link → login
- [ ] Deposit via Whish Money → funds appear
- [ ] Play all 11 games → verify 90% house edge
- [ ] Withdraw to Whish wallet → funds sent
- [ ] Admin panel: `/admin` → stats, users, transactions

## Go Live!
- [ ] Update DNS if needed
- [ ] Monitor logs: `sudo journalctl -u jsrush -f`
- [ ] Set up uptime monitoring (UptimeRobot, etc.)

## Rollback Plan
```bash
git -C /var/www/jsrush log --oneline -5
git -C /var/www/jsrush reset --hard <commit>
sudo systemctl restart jsrush
flask db upgrade
```