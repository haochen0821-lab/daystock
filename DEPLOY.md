# Daystock Deployment Guide

## Architecture

- **App**: Flask + Gunicorn (Python 3.11)
- **DB**: SQLite (`/data/daystock.db`)
- **Container**: Docker + docker-compose
- **Port**: 5201
- **Web Server**: Nginx reverse proxy
- **CDN/DNS**: Cloudflare (Proxied A record)
- **Domain**: https://dayprompt.dayspringmatsu.com

## VPS Setup (DigitalOcean)

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone repo
cd /opt
git clone git@github.com:haochen0821-lab/dayprompt.git
cd dayprompt

# Create data directory
mkdir -p data

# Build and run
docker compose up -d --build
```

## Nginx Setup

```bash
# Copy nginx config
sudo cp nginx-dayprompt.conf /etc/nginx/sites-available/dayprompt
sudo ln -s /etc/nginx/sites-available/dayprompt /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Cloudflare DNS

- Type: A
- Name: dayprompt
- Content: 152.42.205.215
- Proxy status: Proxied

## CI/CD (GitHub Actions)

Push to `main` branch triggers automatic deployment:

1. SSH into VPS
2. `git pull origin main`
3. Generate `version.json`
4. `docker compose up -d --build`

### Required GitHub Secrets

| Secret | Value |
|--------|-------|
| VPS_HOST | 152.42.205.215 |
| VPS_USER | root |
| VPS_SSH_KEY | SSH private key |

## Default Admin Account

- Username: `admin`
- Password: `admin1234`
- Role: superadmin

## Data Persistence

SQLite database is stored in `./data/daystock.db` and mounted as a Docker volume.
**Never delete the data directory.**

## Check Version

Visit `/version` to see the current deployment info.
