#!/bin/bash
# JS Rush Production Deployment Script
# Run this on your production server: bash deploy.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    log_error "Don't run as root! Run as your deploy user."
    exit 1
fi

PROJECT_DIR="/var/www/jsrush"
REPO_URL=""

echo "=========================================="
echo "   JS Rush Production Deployment"
echo "=========================================="
echo ""

# Get repo URL if not set
if [[ -z "$REPO_URL" ]]; then
    read -p "Git repository URL (e.g., https://github.com/user/repo.git): " REPO_URL
    if [[ -z "$REPO_URL" ]]; then
        log_error "Repository URL required"
        exit 1
    fi
fi

# Step 1: Clone or update repo
log_info "Step 1: Setting up repository..."
if [[ -d "$PROJECT_DIR/.git" ]]; then
    log_info "Updating existing repository..."
    cd "$PROJECT_DIR"
    git fetch origin
    git reset --hard origin/main
else
    log_info "Cloning repository..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# Step 2: Python environment
log_info "Step 2: Setting up Python environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Step 3: Create directories
log_info "Step 3: Creating directories..."
mkdir -p logs static/uploads/kyc static/uploads/avatars
chmod 755 logs static/uploads

# Step 4: Configure .env
log_info "Step 4: Configuring production environment..."
if [[ ! -f ".env" ]]; then
    cp .env.production .env
    log_warn "Created .env from .env.production template"
fi

log_warn "Now you need to fill in the REQUIRED values in .env"
log_warn "Press Enter to open .env in nano editor..."
read
nano .env

# Verify required values
log_info "Verifying required environment variables..."
source .env

required_vars=(
    "SECRET_KEY"
    "DATABASE_URL"
    "JWT_SECRET_KEY"
    "WHISH_CHANNEL"
    "WHISH_SECRET"
    "WHISH_WEBSITE_URL"
    "WHISH_BASE_URL"
    "WHISH_WEBHOOK_SECRET"
    "MAIL_PASSWORD"
    "SENTRY_DSN"
)

missing=0
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        log_error "Missing required variable: $var"
        missing=1
    fi
done

if [[ $missing -eq 1 ]]; then
    log_error "Please fill in all required variables in .env and re-run script"
    exit 1
fi

# Step 5: Run migrations on Supabase
log_info "Step 5: Running database migrations on Supabase..."
export DATABASE_URL="${DATABASE_URL/6543/5432}"
flask db upgrade
log_info "Migrations completed!"

# Step 6: Configure systemd service
log_info "Step 6: Configuring systemd service..."
sudo cp jsrush.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable jsrush

# Step 7: Configure Nginx
log_info "Step 7: Configuring Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/jsrush
sudo ln -sf /etc/nginx/sites-available/jsrush /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Step 7: SSL Certificate
log_info "Step 8: SSL Certificate..."
read -p "Enter your domain (e.g., jsrush.com): " DOMAIN
if [[ -n "$DOMAIN" ]]; then
    sudo certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN"
fi

# Step 8: Start services
log_info "Step 9: Starting services..."
sudo systemctl start jsrush
sudo systemctl start redis-server

# Step 9: Health check
log_info "Step 10: Health check..."
sleep 3
if curl -f -s "http://localhost:5000/health" > /dev/null; then
    log_info "✅ Health check passed!"
else
    log_error "❌ Health check failed! Check logs: sudo journalctl -u jsrush -f"
    exit 1
fi

echo ""
echo "=========================================="
echo "   🎉 DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Your JS Rush app is now running at:"
echo "  https://$DOMAIN"
echo ""
echo "Next steps:"
echo "  1. Update Whish Money callbacks in merchant portal:"
echo "     - Success: https://$DOMAIN/whish/success"
echo "     - Failure: https://$DOMAIN/whish/failure"
echo "     - Webhook: https://$DOMAIN/webhook/whish"
echo ""
echo "  2. Monitor logs:"
echo "     sudo journalctl -u jsrush -f"
echo ""
echo "  3. Check health:"
echo "     curl https://$DOMAIN/health"
echo ""
echo "Logs: sudo journalctl -u jsrush -f"
echo "Restart: sudo systemctl restart jsrush"
echo ""
log_info "Deployment successful! 🎉"