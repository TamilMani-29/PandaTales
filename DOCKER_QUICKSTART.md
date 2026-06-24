# 🎯 Docker Quick Start

Get PandaTales running in under 5 minutes with Docker!

## ⚡ Prerequisites

- Docker Desktop installed and running
- At least 4GB RAM available

## 🚀 Quick Start (3 Steps)

### 1. Setup Environment

```bash
# Windows PowerShell
copy .env.example .env.development

# Linux/Mac
cp .env.example .env.development
```

### 2. Start Everything

```bash
# Windows PowerShell
.\docker-manager.ps1 start

# Linux/Mac
chmod +x docker-manager.sh
./docker-manager.sh start
```

### 3. Access the App

Open your browser and visit:
- **App**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **MinIO**: http://localhost:9001

## 🎮 Common Commands

### Windows (PowerShell)

```powershell
# Start services
.\docker-manager.ps1 start

# View logs
.\docker-manager.ps1 logs

# Stop everything
.\docker-manager.ps1 stop

# Check status
.\docker-manager.ps1 status

# See all commands
.\docker-manager.ps1 help
```

### Linux/Mac (Bash)

```bash
# Start services
./docker-manager.sh start

# View logs
./docker-manager.sh logs

# Stop everything
./docker-manager.sh stop

# Check status
./docker-manager.sh status

# See all commands
./docker-manager.sh help
```

## 📚 Full Documentation

For complete documentation, see [DOCKER_SETUP.md](./DOCKER_SETUP.md)

## 🆘 Troubleshooting

### Port Already in Use?

Edit `.env.development` and change the ports:
```bash
FRONTEND_PORT=3001
BACKEND_PORT=8001
```

### Services Not Starting?

```bash
# Check what's wrong
docker-compose logs

# Clean restart
docker-compose down -v
docker-compose up --build
```

### Need to Reset Everything?

```bash
# Windows
.\docker-manager.ps1 purge

# Linux/Mac
./docker-manager.sh purge
```

---

**That's it! Happy coding! 🐼**
