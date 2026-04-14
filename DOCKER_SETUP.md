# 🐼 PandaTales - Docker Setup Guide

Complete Docker containerization for the PandaTales application stack.

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Development Mode](#development-mode)
- [Production Mode](#production-mode)
- [Service Details](#service-details)
- [Troubleshooting](#troubleshooting)
- [Useful Commands](#useful-commands)

## 🏗️ Architecture

The PandaTales stack consists of four main services:

```
┌─────────────────────────────────────────────────────┐
│                    PandaTales Stack                  │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────┐      ┌──────────────────────┐    │
│  │   Frontend   │      │      Backend API      │    │
│  │  (Next.js)   │─────▶│     (FastAPI)        │    │
│  │  Port: 3000  │      │     Port: 8000       │    │
│  └──────────────┘      └──────────────────────┘    │
│                               │          │          │
│                               ▼          ▼          │
│                        ┌──────────┐  ┌────────┐    │
│                        │PostgreSQL│  │ MinIO  │    │
│                        │Port: 5432│  │Port:   │    │
│                        └──────────┘  │9000/   │    │
│                                      │9001    │    │
│                                      └────────┘    │
└─────────────────────────────────────────────────────┘
```

## 🔧 Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Disk Space**: At least 5GB free space
- **Memory**: Minimum 4GB RAM recommended

### Verify Installation

```bash
docker --version
docker-compose --version
```

## 🚀 Quick Start

### 1. Clone and Navigate

```bash
cd PandaTales
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env.development

# Edit .env.development and add your API keys (optional for basic testing)
# Required: OPENAI_API_KEY, STRIPE_SECRET_KEY (for full functionality)
```

### 3. Start All Services

```bash
# Start everything (production mode)
docker-compose up -d

# Or for development mode with hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001
- **PostgreSQL**: localhost:5432

### 5. Initial Setup

The services will automatically:
- ✅ Create database tables (via Alembic migrations)
- ✅ Initialize MinIO bucket
- ✅ Start all services with health checks

## ⚙️ Environment Configuration

### Environment Files

| File | Purpose |
|------|---------|
| `.env.example` | Template with all available variables |
| `.env.development` | Development configuration (local) |
| `.env.production` | Production configuration (deploy) |

### Key Variables

```bash
# Database
POSTGRES_USER=pandatales
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=pandatales

# MinIO Object Storage
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_BUCKET=pandatales

# JWT Security
JWT_SECRET_KEY=your_32_character_minimum_secret_key

# API Keys (Optional)
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

## 🔨 Development Mode

Development mode enables:
- ✨ Hot-reload for code changes
- 🔍 Debug logging
- 📂 Source code volumes mounted

### Start Development Environment

```bash
# Using development override
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or use the development env file
docker-compose --env-file .env.development up
```

### Development Features

- **Frontend**: Changes in `client/` reflect immediately
- **Backend**: FastAPI auto-reloads on code changes
- **Database**: Persistent data in Docker volume
- **MinIO**: File storage persists across restarts

## 🚢 Production Mode

Production mode enables:
- 🔒 Enhanced security
- ⚡ Optimized builds
- 🔄 Auto-restart on failure
- 📊 Production-grade web server (Gunicorn)

### Build for Production

```bash
# Build images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start in detached mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Production Checklist

- [ ] Update all secrets in `.env.production`
- [ ] Set strong database password
- [ ] Configure JWT secret (32+ characters)
- [ ] Add real API keys (OpenAI, Stripe, etc.)
- [ ] Set up SSL/TLS certificates
- [ ] Configure domain names
- [ ] Set up reverse proxy (Nginx)
- [ ] Enable monitoring and logging
- [ ] Configure backup strategy

## 📦 Service Details

### PostgreSQL Database

```yaml
Image: postgres:15-alpine
Port: 5432
Volume: postgres_data
Health Check: ✅ Enabled
```

**Access Database:**
```bash
docker-compose exec postgres psql -U pandatales -d pandatales
```

### MinIO Object Storage

```yaml
Image: minio/minio:latest
API Port: 9000
Console Port: 9001
Volume: minio_data
Default Credentials: minioadmin/minioadmin123
```

**Access MinIO Console:**
1. Open http://localhost:9001
2. Login with MINIO_ROOT_USER and MINIO_ROOT_PASSWORD
3. View/manage buckets and files

### Backend API (FastAPI)

```yaml
Build: ./server/Dockerfile
Port: 8000
Framework: FastAPI + Uvicorn
Auto-reload: Yes (dev mode)
```

**View API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend (Next.js)

```yaml
Build: ./client/Dockerfile
Port: 3000
Framework: Next.js 14
Build Mode: Standalone
```

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check service logs
docker-compose logs

# Check specific service
docker-compose logs backend
docker-compose logs frontend
```

### Database Connection Failed

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres pg_isready -U pandatales
```

### MinIO Bucket Not Created

```bash
# Check MinIO initialization logs
docker-compose logs minio_init

# Manually create bucket
docker-compose exec minio mc mb myminio/pandatales
```

### Port Already in Use

```bash
# Change ports in .env file
FRONTEND_PORT=3001
BACKEND_PORT=8001
POSTGRES_PORT=5433
```

### Reset Everything

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove all images
docker-compose down -v --rmi all

# Start fresh
docker-compose up --build
```

## 🎯 Useful Commands

### Container Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart a specific service
docker-compose restart backend

# View logs (follow mode)
docker-compose logs -f

# View logs for specific service
docker-compose logs -f frontend
```

### Development Commands

```bash
# Rebuild a specific service
docker-compose build backend

# Rebuild without cache
docker-compose build --no-cache

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Access backend shell
docker-compose exec backend bash

# Access database shell
docker-compose exec postgres psql -U pandatales
```

### Cleanup Commands

```bash
# Remove stopped containers
docker-compose rm

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Full cleanup (CAUTION: Removes all data)
docker-compose down -v --rmi all --remove-orphans
```

### Monitoring

```bash
# View resource usage
docker stats

# View running containers
docker-compose ps

# Check service health
docker-compose ps --format json | jq '.[] | {name: .Name, health: .Health}'
```

## 📊 Health Checks

All services include health checks:

- **PostgreSQL**: `pg_isready` command
- **MinIO**: HTTP health endpoint
- **Backend**: HTTP endpoint `/health`
- **Frontend**: Node.js HTTP check

View health status:
```bash
docker-compose ps
```

## 🔐 Security Notes

### Development

- Default credentials are used for convenience
- Debug mode is enabled
- CORS allows localhost origins

### Production

- ⚠️ **MUST** change all default passwords
- ⚠️ **MUST** use strong JWT secret
- ⚠️ Disable debug mode
- ⚠️ Configure proper CORS origins
- ⚠️ Use HTTPS/TLS
- ⚠️ Set up proper firewall rules
- ⚠️ Regular security updates

## 📝 Next Steps

1. ✅ Services are running
2. 🧪 Test the application at http://localhost:3000
3. 📖 Check API documentation at http://localhost:8000/docs
4. 🎨 Start developing features
5. 🚀 Deploy to production when ready

## 🆘 Getting Help

- Check logs: `docker-compose logs -f`
- Verify health: `docker-compose ps`
- Inspect container: `docker-compose exec <service> sh`
- Review documentation: `./server/README.md`

---

**Happy Coding! 🐼📚**
