# Docker Compose Command Reference

Detailed guide for using Docker Compose files directly (without helper scripts).

## 📋 Available Compose Files

| File | Type | Purpose |
|------|------|---------|
| `docker-compose.yml` | **Base/Default** | Complete setup for quick development |
| `docker-compose.dev.yml` | **Standalone** | Full dev environment with hot-reload |
| `docker-compose.prod.yml` | **Override** | Production settings (requires base file) |

## 🚀 Running Different Environments

### Development - Standalone (Recommended)

**Best for:** Daily development work with hot-reload

```bash
# With env file
docker-compose -f docker-compose.dev.yml --env-file .env.development up

# Without env file (uses defaults)  
docker-compose -f docker-compose.dev.yml up

# Detached mode (background)
docker-compose -f docker-compose.dev.yml up -d
```

**Includes:** PostgreSQL, MinIO, Backend (hot-reload), Frontend (hot-reload)

**Volumes:** Separate dev volumes (`postgres_data_dev`, `minio_data_dev`)

### Development - Base File

**Best for:** Quick testing without env files

```bash
# Simple command
docker-compose up

# Detached mode
docker-compose up -d
```

**Includes:** All services with default development settings

### Production

**Best for:** Deployment to servers

**IMPORTANT:** Prod file is an OVERRIDE - must be combined with base!

```bash
# Step 1: Create production env
cp .env.prod.example .env.prod
# Edit .env.prod with strong passwords!

# Step 2: Start production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d

# View logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

## 📋 Common Operations

### Viewing Status & Logs

```bash
# Check container status
docker-compose ps
docker-compose -f docker-compose.dev.yml ps

# View all logs (follow mode)
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs backend --tail=50

# Dev file logs
docker-compose -f docker-compose.dev.yml logs -f backend
```

### Stopping Services

```bash
# Stop containers (keeps volumes)
docker-compose down
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (⚠️ DELETES ALL DATA!)
docker-compose down -v
docker-compose -f docker-compose.dev.yml down -v
```

### Building Images

```bash
# Build all services
docker-compose build
docker-compose -f docker-compose.dev.yml build

# Build specific service
docker-compose build backend
docker-compose -f docker-compose.dev.yml build frontend

# Rebuild and restart
docker-compose up -d --build
```

### Restarting Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose -f docker-compose.dev.yml restart backend
```

## 🔧 Database Operations

### Run Migrations

```bash
# Using base file
docker-compose exec backend alembic upgrade head

# Using dev file
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Check migration status
docker-compose exec backend alembic current

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "add new field"
```

### Access Database

```bash
# PostgreSQL shell (base)
docker-compose exec postgres psql -U pandatales -d pandatales

# PostgreSQL shell (dev)
docker-compose -f docker-compose.dev.yml exec postgres psql -U pandatales_dev -d pandatales_dev

# Backup database
docker-compose exec postgres pg_dump -U pandatales pandatales > backup.sql

# Restore database
docker-compose exec -T postgres psql -U pandatales pandatales < backup.sql
```

## 📦 Container Access

### Execute Commands

```bash
# Backend shell
docker-compose exec backend sh
docker-compose -f docker-compose.dev.yml exec backend sh

# Run Python command
docker-compose exec backend python -c "print('Hello')"

# Check Python packages
docker-compose exec backend pip list

# PostgreSQL shell
docker-compose exec postgres psql -U pandatales
```

## 🔍 Troubleshooting

### ❌ Error: "No address associated with hostname"

**Problem:** Backend can't find PostgreSQL

**Cause:** Missing base services (postgres, minio)

**Solutions:**

```bash
# ❌ WRONG - only loads backend/frontend overrides
docker-compose -f docker-compose.dev.yml up

# ✅ FIX 1 - Use standalone dev file (already fixed!)
docker-compose -f docker-compose.dev.yml --env-file .env.development up

# ✅ FIX 2 - Use base file
docker-compose up

# ✅ FIX 3 - Combine base + prod (production)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

### ❌ Error: "Port already in use"

```bash
# Find what's using the port (Windows)
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F

# Or change port in .env.development
BACKEND_PORT=8001
```

### ❌ Containers won't start / Health check failing

```bash
# Clean restart
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d

# Check logs
docker-compose -f docker-compose.dev.yml logs postgres
docker-compose -f docker-compose.dev.yml logs minio

# Nuclear option: Remove everything and start fresh
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

### ❌ Old data persisting after code changes

```bash
# Remove only backend/frontend containers (keeps DB data)
docker-compose -f docker-compose.dev.yml rm -f backend frontend
docker-compose -f docker-compose.dev.yml up -d --build backend frontend

# Full rebuild of specific service
docker-compose -f docker-compose.dev.yml build --no-cache backend
docker-compose -f docker-compose.dev.yml up -d backend
```

## 📊 Container Resource Monitoring

```bash
# View resource usage
docker stats

# View disk usage
docker system df

# View volume usage
docker volume ls
docker volume inspect pandatales_postgres_data_dev
```

## 🧹 Cleanup

```bash
# Remove stopped containers
docker-compose down

# Remove containers and volumes
docker-compose -f docker-compose.dev.yml down -v

# Remove unused images
docker image prune -a

# Remove everything (⚠️ ALL Docker data)
docker system prune -a --volumes
```

## 🌐 Service URLs

### Development (docker-compose.dev.yml)

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | - |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin123 |
| PostgreSQL | localhost:5432 | pandatales_dev / pandatales |

### Production (docker-compose.yml + docker-compose.prod.yml)

| Service | URL | Credentials |
|---------|-----|-------------|
| Application | http://your-domain.com | Via Nginx |
| API | http://your-domain.com/api | Via Nginx |
| MinIO Console | http://your-domain.com:9001 | From .env.prod |
| PostgreSQL | localhost:5432 | From .env.prod |

## 💡 Tips & Best Practices

### Development Workflow

1. **Start services:** `docker-compose -f docker-compose.dev.yml up -d`
2. **View logs:** `docker-compose -f docker-compose.dev.yml logs -f backend`
3. **Make code changes** (auto-reloads!)
4. **Run migrations if needed:** `docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head`
5. **Test at:** http://localhost:3000
6. **Stop when done:** `docker-compose -f docker-compose.dev.yml down`

### Separate Dev/Prod Data

Development uses separate volumes:
- `postgres_data_dev` (dev)
- `postgres_data` (base/prod)
- `minio_data_dev` (dev)
- `minio_data` (base/prod)

This prevents dev work from affecting production data.

### Quick Aliases (Optional)

Add to PowerShell profile (`$PROFILE`):

```powershell
function dcup { docker-compose -f docker-compose.dev.yml up -d }
function dcdown { docker-compose -f docker-compose.dev.yml down }
function dclogs { docker-compose -f docker-compose.dev.yml logs -f $args }
function dcps { docker-compose -f docker-compose.dev.yml ps }
function dcbuild { docker-compose -f docker-compose.dev.yml build $args }
```

Then use:
```powershell
dcup           # Start dev
dclogs backend # View backend logs
dcdown         # Stop dev
```

## 🔗 Related Documentation

- [Docker Quickstart](./DOCKER_QUICKSTART.md) - Using helper scripts
- [Docker Setup](./DOCKER_SETUP.md) - Initial setup guide
- [Production Deployment](./PRODUCTION_DEPLOYMENT.md) - Production guide
- [Server README](./server/README.md) - Backend documentation
