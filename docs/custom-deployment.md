# EdgeStore - Custom Private Deployment Guide

This guide explains how to deploy, configure, and maintain **EdgeStore** as your own standalone, hardened storage appliance with personalized credentials, custom storage mounts, and dedicated database volumes.

---

## 1. Quick One-Click Deployment

On Windows, run the automated deployment script:

```powershell
.\deploy-own.ps1
```
Or double-click `deploy-own.bat`.

The script will:
1. Generate a **256-bit cryptographic JWT secret** (`openssl rand -hex 32` equivalent).
2. Prompt you for your chosen **Application Port** (default: `8000`).
3. Prompt you for your **Custom Administrator Username & Password**.
4. Generate a clean `.env` file with these values.
5. Build and start the hardened Docker containers (`edgestore-appliance` and `edgestore-mongo`).
6. Perform an automated health check and output your access endpoints.

---

## 2. Manual Custom Deployment via `.env`

If you prefer to configure EdgeStore manually without the script:

### Step 1: Create your `.env` from the template
```bash
cp .env.example .env
```

### Step 2: Edit your `.env`
Set your custom values:

```ini
# Application Network Port
PORT=8000

# Your Custom Administrator Account
INITIAL_ADMIN_USERNAME=myadmin
INITIAL_ADMIN_PASSWORD=MyStrongPassword2026!
INITIAL_ADMIN_EMAIL=admin@my-domain.com

# Cryptographic Token Signing Secret (Minimum 32 bytes)
JWT_SECRET=b7e19f2a893450c19b384d09214ab68c17e3f810283746591029384756102938

# Custom Named Volumes
PRIMARY_VOLUME_NAME=my_edgestore_primary
REPLICA_VOLUME_NAME=my_edgestore_replica
DB_VOLUME_NAME=my_edgestore_db
MONGO_VOLUME_NAME=my_edgestore_mongo
```

### Step 3: Launch Containers
```bash
docker compose up -d --build
```

---

## 3. Mounting Custom Host Folders or External Drives

If you want EdgeStore to store files directly on your host machine or an external USB hard drive (instead of Docker managed volumes):

In `docker-compose.yml`, change the volume mappings under `edgestore-backend`:

```yaml
    volumes:
      # Example: Bind mount your external drive or local folders
      - D:/MyStorage/Primary:/data/primary
      - E:/MyStorage/Replica:/data/replica
      - C:/MyStorage/DB:/data/db
```

---

## 4. Backups and Disaster Recovery

### Backup Stored Files (Primary & Replica)
To archive your storage volumes directly from Docker:

```bash
# Backup Primary Storage
docker run --rm -v edgestore_custom_primary:/data -v ${PWD}:/backup alpine tar -czf /backup/primary_backup.tar.gz -C /data .

# Backup Replica Storage
docker run --rm -v edgestore_custom_replica:/data -v ${PWD}:/backup alpine tar -czf /backup/replica_backup.tar.gz -C /data .

# Backup MongoDB Client Records
docker exec edgestore-mongo mongodump --out /data/db/mongodump_backup
```

### Restore Stored Files
```bash
docker run --rm -v edgestore_custom_primary:/data -v ${PWD}:/backup alpine tar -xzf /backup/primary_backup.tar.gz -C /data
```

---

## 5. Security Checklist for Production

- [x] **Strong Admin Password**: Ensure `INITIAL_ADMIN_PASSWORD` is at least 16 characters with mixed case, numbers, and symbols.
- [x] **Unique JWT Secret**: Ensure `JWT_SECRET` is freshly generated and not the default value.
- [x] **TLS / HTTPS Reverse Proxy**: Place Nginx, Caddy, or Cloudflare Tunnel in front of port 8000 for encrypted HTTPS traffic.
- [x] **Unprivileged Container User**: The backend runs as UID `10001` (`edgestore`), with `no-new-privileges:true` and all Linux capabilities dropped (`cap_drop: ALL`).
