# AI-Enhanced Video Meeting PoC - Deployment Guide

**Complete guide for deploying the system on your Ubuntu server.**

---

## Prerequisites

Before starting, ensure you have:

- **Ubuntu 22.04+** server with SSH access
- **Docker 24+** installed
- **Docker Compose 2.23+** installed
- **Minimum Hardware:**
  - 4 CPU cores
  - 16GB RAM (32GB recommended for GPU)
  - 50GB storage
- **KIMI K2 API Key** from [platform.moonshot.ai](https://platform.moonshot.ai)

---

## Step-by-Step Deployment

### 1. Install Docker and Docker Compose

If not already installed:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify installations
docker --version
docker compose version
```

**Log out and log back in** for group changes to take effect.

---

### 2. Clone Repository

```bash
cd ~
git clone <your-repo-url> Live-meeting-assistant
cd Live-meeting-assistant
```

---

### 3. Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Generate secrets
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env.secrets
echo "LIVEKIT_API_KEY=LK$(openssl rand -hex 16)" >> .env.secrets
echo "LIVEKIT_API_SECRET=$(openssl rand -base64 48)" >> .env.secrets
echo "POSTGRES_PASSWORD=$(openssl rand -base64 24)" >> .env.secrets

# View generated secrets
cat .env.secrets
```

Now edit `.env` with your favorite editor:

```bash
nano .env
```

**Required Changes:**

1. Copy secrets from `.env.secrets` into `.env`:
   - `JWT_SECRET`
   - `LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET`
   - `POSTGRES_PASSWORD`

2. Set your **KIMI K2 API Key**:
   ```
   LLM_API_KEY=sk-your-actual-kimi-k2-api-key-here
   ```

3. Change default admin password:
   ```
   ADMIN_DEFAULT_PASSWORD=your-strong-password-here
   ```

4. **(Production only)** Update URLs for your domain:
   ```
   DOMAIN=your-domain.com
   VITE_API_BASE_URL=https://your-domain.com/api
   VITE_WS_URL=wss://your-domain.com
   VITE_LIVEKIT_URL=wss://your-domain.com:7880
   ```

Save and exit (`Ctrl+X`, then `Y`, then `Enter` in nano).

---

### 4. Start Database First

```bash
# Start PostgreSQL
docker compose up -d postgres

# Wait for database to be ready (~10 seconds)
sleep 10

# Check PostgreSQL logs
docker compose logs postgres
```

---

### 5. Run Database Migrations

```bash
# Run Alembic migrations
docker compose run --rm backend alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial, Initial schema with all tables
```

---

### 6. Seed Database with Users

```bash
# Create admin and test users
docker compose run --rm backend python infra/scripts/seed_db.py
```

Expected output:
```
🌱 Seeding database...
✅ Created admin user: admin
✅ Created test user: john
✅ Created test user: jane
✨ Database seeding complete!
```

---

### 7. Start All Services

```bash
# Build and start all containers
docker compose up -d

# Check status
docker compose ps
```

All services should show "Up" status:
- `ai-meeting-backend`
- `ai-meeting-frontend`
- `ai-meeting-livekit`
- `ai-meeting-postgres`
- `ai-meeting-redis`
- `ai-meeting-stt`

---

### 8. Verify Services

```bash
# Check backend health
curl http://localhost:8000/health
# Expected: {"status":"healthy","environment":"development","debug":true}

# Check frontend
curl http://localhost:3000
# Expected: HTML content

# Check all service logs
docker compose logs -f
```

---

### 9. Access the Application

**Open your browser:**

```
http://your-server-ip:3000
```

Or if local:
```
http://localhost:3000
```

**Login with default credentials:**

- **Admin:** `admin` / `<your ADMIN_DEFAULT_PASSWORD>`
- **User 1:** `john` / `user123`
- **User 2:** `jane` / `user123`

---

### 10. Test the System

**Create a test meeting:**

1. **Window 1 (Admin):**
   - Login as `admin`
   - Click "Create Room"
   - Enter room name: "Test Meeting"
   - Click "Join Room"
   - Allow camera/microphone permissions

2. **Window 2 (Participant):**
   - Open incognito/private browser
   - Go to `http://localhost:3000`
   - Login as `john`
   - Click on "Test Meeting" room
   - Click "Join Room"
   - Allow camera/microphone permissions

3. **Verify:**
   - Both users should see each other's video
   - Audio should work in both directions
   - (Note: Transcript and AI thought board require LiveKit Agent implementation - Phase 3)

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs for specific service
docker compose logs backend
docker compose logs livekit
docker compose logs stt

# Restart specific service
docker compose restart backend

# Rebuild and restart
docker compose up -d --build backend
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Restart database
docker compose restart postgres

# Verify migrations
docker compose run --rm backend alembic current
```

### No Video/Audio in LiveKit

**Common causes:**

1. **Browser permissions:** Check microphone/camera permissions
2. **HTTPS required:** LiveKit requires HTTPS in production (use ngrok for testing)
3. **Firewall:** Ensure ports 7880, 7881, 7882/udp are open
4. **WebSocket connection:** Check `VITE_LIVEKIT_URL` in `.env`

**Debug:**

```bash
# Check LiveKit logs
docker compose logs livekit

# Verify LiveKit is running
curl http://localhost:7881/
# Should return 404 but confirm service is up
```

### Frontend Build Errors

```bash
# Rebuild frontend
docker compose build frontend

# Check frontend logs
docker compose logs frontend

# Access frontend container
docker compose exec frontend sh
```

### Backend API Errors

```bash
# Check backend logs
docker compose logs backend | tail -50

# Restart backend
docker compose restart backend

# Access backend container
docker compose exec backend bash

# Run migrations manually
docker compose exec backend alembic upgrade head
```

---

## Production Deployment

For production deployment, additional steps are required:

### 1. SSL/TLS Certificates

Use Let's Encrypt with Certbot:

```bash
# Install Certbot
sudo apt install certbot

# Obtain certificate
sudo certbot certonly --standalone -d your-domain.com

# Certificates will be at:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

Update `.env`:
```
SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 2. Enable Nginx Reverse Proxy

```bash
# Start with nginx profile
docker compose --profile production up -d
```

### 3. Production Environment Settings

Update `.env`:
```
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING

# Update all URLs to HTTPS
VITE_API_BASE_URL=https://your-domain.com/api
VITE_WS_URL=wss://your-domain.com
VITE_LIVEKIT_URL=wss://your-domain.com:7880
```

### 4. Security Hardening

```bash
# Change all default passwords in .env
# Enable firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 7880/tcp
sudo ufw allow 7882/udp
sudo ufw enable

# Set restrictive file permissions
chmod 600 .env
```

### 5. Monitoring & Logs

```bash
# View all logs
docker compose logs -f

# Export logs to file
docker compose logs > deployment.log

# Monitor resource usage
docker stats
```

---

## Maintenance

### Backup Database

```bash
# Create backup
docker compose exec postgres pg_dump -U postgres meeting_ai > backup_$(date +%Y%m%d).sql

# Restore from backup
docker compose exec -T postgres psql -U postgres meeting_ai < backup_20250116.sql
```

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose down
docker compose up -d --build

# Run new migrations
docker compose exec backend alembic upgrade head
```

### Clean Up

```bash
# Stop all services
docker compose down

# Remove volumes (WARNING: deletes all data)
docker compose down -v

# Remove unused images
docker image prune -a
```

---

## Next Steps

Once the system is deployed and working:

1. **Implement LiveKit Agent** for audio extraction (Phase 3)
2. **Connect STT Service** (WhisperLive integration)
3. **Add LLM Integration** for thought board
4. **Implement WebSocket** for real-time transcript updates
5. **Build Admin Panel** UI components

See [ARCHITECTURE.md](./ARCHITECTURE.md) for complete implementation roadmap.

---

## Support

- **Documentation:** [README.md](./README.md) | [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Issues:** Check service logs with `docker compose logs <service-name>`
- **Reset:** `docker compose down -v && docker compose up -d` (WARNING: deletes data)

---

**Your system is now deployed and ready for development!** 🚀
