# Smart Campus Intelligence — Production Deployment Guide

## 1. Prerequisites & System Requirements

- **Operating System**: Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9) or macOS
- **Container Engine**: Docker Engine 24.0+ and Docker Compose v2.20+
- **Host Specifications**:
  - Minimum: 2 vCPU, 4GB RAM, 20GB SSD
  - Recommended (Production): 4 vCPU, 8GB RAM, 50GB NVMe SSD
- **Network Requirements**:
  - Ports `80` (HTTP) and `443` (HTTPS) exposed
  - Port `5432` restricted to internal Docker network `campus_backend_net`

---

## 2. Production Docker Deployment

### Step 1: Clone Repository & Create Environment Configuration
```bash
git clone <repository_url> smart-campus-intelligence
cd smart-campus-intelligence

# Copy production environment template
cp .env.production.example .env.production
```

### Step 2: Configure Production Secrets
Edit `.env.production` and generate cryptographically secure secrets:
```bash
# Generate a 64-character hex secret for JWT signing
openssl rand -hex 32

# Configure database credentials, CORS domains, and LLM API keys
nano .env.production
```

### Step 3: Launch Production Container Stack
Execute Docker Compose with the production configuration file:
```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### Step 4: Verify Container Health Status
Inspect container health probes:
```bash
docker compose -f docker-compose.prod.yml ps
```
Expected output:
- `smart_campus_prod_db`: `Up (healthy)`
- `smart_campus_prod_backend`: `Up (healthy)`
- `smart_campus_prod_frontend`: `Up (healthy)`

Test HTTP health endpoints directly:
```bash
curl -i http://localhost/health
curl -i http://localhost/ready
```

---

## 3. Database Initialization & Alembic Migrations

The database container automatically initializes the `pgvector` extension upon first launch via `database/init.sql`.

To apply Alembic schema migrations inside the production container:
```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

To seed initial canonical academic data, career roles, and university policy handbooks:
```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.core.seed_data
```

---

## 4. SSL/TLS Termination & Domain Configuration

For public internet deployment with HTTPS:
1. Place your SSL certificate and private key at `/etc/ssl/certs/campus.crt` and `/etc/ssl/private/campus.key`.
2. Update `docker/nginx.conf` with the SSL server block:
```nginx
server {
    listen 443 ssl http2;
    server_name campus.institution.edu;

    ssl_certificate /etc/ssl/certs/campus.crt;
    ssl_certificate_key /etc/ssl/private/campus.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # ... include proxy configurations from docker/nginx.conf
}
```

---

## 5. Automated Backup & Disaster Recovery

### Automated Daily Backup via Cron
Add the automated backup script to the system crontab:
```bash
# Run database backup every night at 2:00 AM UTC
0 2 * * * /path/to/smart-campus-intelligence/database/backup_db.sh /var/backups/smart_campus >> /var/log/campus_backup.log 2>&1
```

### Restoration Routine
To restore from a compressed archive:
```bash
./database/restore_db.sh /var/backups/smart_campus/smart_campus_pg_20261109_020000.sql.gz
```
