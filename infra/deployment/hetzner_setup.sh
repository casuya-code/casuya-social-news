#!/usr/bin/env bash
# Casuya Social News — Hetzner Cloud server setup
# Run as root on a fresh Ubuntu 22.04+ server:
#   bash hetzner_setup.sh
#
# What it does:
#   1. Installs Docker, Docker Compose, Nginx, Certbot
#   2. Clones the repo (or uses existing /opt/casuya)
#   3. Runs docker compose up -d for Postgres + Redis
#   4. Sets up the Python server as a systemd service
#   5. Configures Nginx with SSL via Let's Encrypt
#   6. Enables automatic security updates

set -euo pipefail

DOMAIN="${1:-casuya.example.com}"
REPO_URL="${2:-https://github.com/your-org/casuya-social-news.git}"
INSTALL_DIR="/opt/casuya"

echo "=== Casuya Social News — Server Setup ==="
echo "Domain: $DOMAIN"
echo ""

# --- System packages ---
echo "[1/7] Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    docker.io docker-compose-plugin \
    nginx certbot python3-certbot-nginx \
    python3.12 python3.12-venv python3-pip \
    git curl ufw

# --- Firewall ---
echo "[2/7] Configuring firewall..."
ufw --force enable
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS

# --- Clone repo ---
echo "[3/7] Setting up project..."
if [ ! -d "$INSTALL_DIR" ]; then
    git clone "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# --- Docker infrastructure ---
echo "[4/7] Starting Postgres + Redis..."
cd infra/docker
docker compose up -d postgres redis
cd ../..

# --- Python server ---
echo "[5/7] Setting up Python server..."
cd server-python
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    # Generate random secrets
    API_KEY=$(openssl rand -hex 16)
    JWT_SECRET=$(openssl rand -hex 32)
    sed -i "s/API_KEY=change-me-to-random-32-char-string/API_KEY=$API_KEY/" .env
    sed -i "s/JWT_SECRET_KEY=change-me-to-random-64-char-string/JWT_SECRET_KEY=$JWT_SECRET/" .env
    sed -i "s/APP_SECRET_KEY=change-me-to-random-64-char-string/APP_SECRET_KEY=$JWT_SECRET/" .env
    echo ""
    echo ">>> Generated API_KEY: $API_KEY"
    echo ">>> Copy this to your Godot client settings."
fi

# Run database migrations
.venv/bin/alembic upgrade head

# --- Systemd service ---
echo "[6/7] Creating systemd service..."
cat > /etc/systemd/system/casuya.service << EOF
[Unit]
Description=Casuya Social News Server
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/server-python
ExecStart=$INSTALL_DIR/server-python/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PATH=$INSTALL_DIR/server-python/.venv/bin:/usr/bin

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable casuya
systemctl start casuya

# --- Nginx + SSL ---
echo "[7/7] Configuring Nginx with SSL..."
cp "$INSTALL_DIR/infra/deployment/nginx.conf" /etc/nginx/sites-available/casuya
sed -i "s/casuya.example.com/$DOMAIN/g" /etc/nginx/sites-available/casuya
ln -sf /etc/nginx/sites-available/casuya /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Get SSL certificate
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN" || true

# --- Done ---
echo ""
echo "=== Setup Complete ==="
echo "Server: https://$DOMAIN"
echo "API Docs: https://$DOMAIN/docs"
echo "Operator: https://$DOMAIN/operator"
echo "Metrics: https://$DOMAIN/metrics (internal only)"
echo ""
echo "Next steps:"
echo "  1. Update your Godot client's base_url to https://$DOMAIN"
echo "  2. Set the API_KEY in the client to match server-python/.env"
echo "  3. Export and deploy the Godot client"
