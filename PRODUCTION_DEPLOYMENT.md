# Production Deployment Guide - Containerized Setup

This guide covers deploying PandaTales with **PostgreSQL and MinIO running as Docker containers** (not managed services).

## 📦 Architecture Overview

### Services Running as Containers:
- **PostgreSQL 15** - Database (containerized with persistent volume)
- **MinIO** - Object Storage (containerized with persistent volume)
- **FastAPI Backend** - API Server
- **Next.js Frontend** - Web Application
- **Nginx** - Reverse Proxy (production only)

## 🚀 Production Deployment Steps

### 1. Prepare Production Environment File

```bash
# Copy the example file
cp .env.prod.example .env.prod

# Edit with production values
nano .env.prod  # or use your preferred editor
```

**Critical Variables to Change:**
- `POSTGRES_PASSWORD` - Strong database password
- `MINIO_ROOT_USER` - MinIO admin username
- `MINIO_ROOT_PASSWORD` - Strong MinIO password (min 32 chars)
- `SECRET_KEY` - Random secret for app encryption
- `JWT_SECRET_KEY` - Random secret for JWT tokens
- `ALLOWED_ORIGINS` - Your production domain(s)
- `OPENAI_API_KEY` - Your OpenAI API key
- `STRIPE_SECRET_KEY` - Your Stripe secret key
- `STRIPE_PUBLISHABLE_KEY` - Your Stripe publishable key

### 2. Build Production Images

```bash
# Build all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Or build individually
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build frontend
```

### 3. Start Production Services

```bash
# Start all containers in detached mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d

# Check logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Check specific service
docker-compose logs -f backend
```

### 4. Verify Services are Running

```bash
# Check all containers
docker ps

# Expected containers:
# - pandatales_postgres
# - pandatales_minio
# - pandatales_backend
# - pandatales_frontend
# - pandatales_nginx (if using nginx)

# Check health status
docker-compose ps
```

## 🔒 Data Persistence

### Docker Volumes

Both PostgreSQL and MinIO use Docker named volumes for data persistence:

```bash
# List volumes
docker volume ls | grep pandatales

# Expected volumes:
# - pandatales_postgres_data
# - pandatales_minio_data

# Inspect volume
docker volume inspect pandatales_postgres_data
```

### Backup Strategy

#### PostgreSQL Backup

```bash
# Manual backup
docker exec pandatales_postgres pg_dump -U pandatales_prod pandatales_prod > backup_$(date +%Y%m%d).sql

# Restore from backup
docker exec -i pandatales_postgres psql -U pandatales_prod pandatales_prod < backup_20260414.sql

# Automated backup (add to crontab)
0 2 * * * docker exec pandatales_postgres pg_dump -U pandatales_prod pandatales_prod | gzip > /backups/postgres_$(date +\%Y\%m\%d_\%H\%M).sql.gz
```

#### MinIO Backup

```bash
# Backup MinIO data (copy volume contents)
docker run --rm -v pandatales_minio_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/minio_backup_$(date +%Y%m%d).tar.gz /data

# Or use MinIO mc client to mirror buckets
docker exec pandatales_minio mc mirror /data/pandatales /backup/pandatales
```

## 🔧 Maintenance Commands

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Run database migrations
docker-compose exec backend alembic upgrade head
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f minio

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Database Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Check current version
docker-compose exec backend alembic current
```

### Access Services Directly

```bash
# PostgreSQL shell
docker exec -it pandatales_postgres psql -U pandatales_prod -d pandatales_prod

# MinIO console
# Access via browser: http://your-server:9001

# Backend shell
docker exec -it pandatales_backend sh

# Check backend Python environment
docker exec pandatales_backend python --version
```

## 📊 Monitoring

### Check Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Volume usage
docker system df -v
```

### Health Checks

```bash
# PostgreSQL health
docker exec pandatales_postgres pg_isready -U pandatales_prod

# MinIO health
curl http://localhost:9000/minio/health/live

# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000
```

## 🔐 Security Considerations

### Network Isolation

The containers communicate on an isolated bridge network (`pandatales_network`). External access is only through exposed ports.

### Port Exposure

**Development:**
- PostgreSQL: 5432 ✓ (for local tools)
- MinIO API: 9000 ✓
- MinIO Console: 9001 ✓
- Backend: 8000 ✓
- Frontend: 3000 ✓

**Production (Recommended):**
- PostgreSQL: 5432 ⚠️ (only if needed for external tools, otherwise remove)
- MinIO API: 9000 ⚠️ (only if needed for external access, otherwise internal only)
- MinIO Console: 9001 ⚠️ (remove or protect with firewall)
- Backend: 8000 ❌ (behind nginx)
- Frontend: 3000 ❌ (behind nginx)
- Nginx: 80, 443 ✓

### Firewall Rules

If running on a server, lock down ports:

```bash
# Allow only HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Block direct access to services (accessed via nginx)
ufw deny 8000/tcp
ufw deny 3000/tcp

# Only allow PostgreSQL/MinIO from localhost if needed
ufw deny 5432/tcp
ufw deny 9000/tcp
ufw deny 9001/tcp
```

## 🆘 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Check specific service
docker-compose ps

# Restart service
docker-compose restart backend
```

### Database Connection Issues

```bash
# Verify postgres is running
docker ps | grep postgres

# Check postgres logs
docker-compose logs postgres

# Test connection
docker exec pandatales_backend python -c "import asyncpg; print('Connection test')"
```

### MinIO Connection Issues

```bash
# Check MinIO logs
docker-compose logs minio

# Verify bucket exists
docker exec pandatales_minio mc ls myminio

# Recreate bucket
docker exec pandatales_minio mc mb myminio/pandatales
```

### Clean Restart

```bash
# Stop all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Start fresh
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d

# If data is corrupted, remove volumes (⚠️ DESTROYS DATA)
docker-compose down -v
```

## 📈 Scaling Considerations

### Current Setup (Single Server)
- PostgreSQL: 1 container
- MinIO: 1 container
- Backend: 1 container (4 workers)
- Frontend: 1 container

### Future Scaling Options

**Database:**
- PostgreSQL Replication (primary + replicas)
- Connection pooling (PgBouncer)
- Read replicas for queries

**Storage:**
- MinIO distributed mode (4+ nodes)
- Or migrate to cloud storage (S3, Azure Blob)

**Application:**
- Multiple backend containers with load balancer
- CDN for frontend static assets
- Redis for caching

## 📝 Additional Notes

### Why Containerized DB/MinIO?

✅ **Pros:**
- Simple deployment
- No external dependencies
- Full control over configuration
- Cost-effective for small-medium workloads
- Easy local development/production parity

⚠️ **Considerations:**
- Requires backup strategy
- Manual scaling
- Need to monitor disk space
- Ensure volume backups

### When to Consider Managed Services

- Very large scale (>1TB data)
- Compliance requirements (automated backups, encryption)
- Multi-region deployments
- Enterprise SLAs needed

## 🔗 Related Documentation

- [Docker Setup](./DOCKER_SETUP.md)
- [Docker Quickstart](./DOCKER_QUICKSTART.md)
- [Server README](./server/README.md)
- [Database Schema](./server/DATABASE_SCHEMA.md)
