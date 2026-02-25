# Quick Start Guide for StoryBloom Backend

## 🚀 Get Started in 5 Minutes

### Option 1: Docker (Recommended)

```powershell
# 1. Copy environment file
Copy-Item .env.example .env

# 2. Start everything
docker-compose up -d

# 3. Check if services are running
docker-compose ps

# 4. View logs
docker-compose logs -f api

# 5. Open API docs
# http://localhost:8000/docs
```

### Option 2: Local Development

```powershell
# 1. Install uv
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Create virtual environment
uv venv

# 3. Activate virtual environment
.venv\Scripts\Activate.ps1

# 4. Install dependencies
uv pip install -e ".[dev]"

# 5. Copy environment file
Copy-Item .env.example .env

# 6. Edit .env with your database and minio settings

# 7. Run migrations
alembic upgrade head

# 8. Start server
uvicorn app.main:app --reload

# 9. Open API docs
# http://localhost:8000/docs
```

## 📋 Available Endpoints

### Health Check
```
GET /health
```

### Book Templates
```
GET    /api/v1/templates              # List templates
GET    /api/v1/templates/{id}         # Get template
POST   /api/v1/templates              # Create template (admin)
PATCH  /api/v1/templates/{id}         # Update template (admin)
DELETE /api/v1/templates/{id}         # Delete template (admin)
GET    /api/v1/templates/genres/list  # List genres
GET    /api/v1/templates/series/{id}  # Get series templates
```

## 🧪 Test the API

```powershell
# Health check
curl http://localhost:8000/health

# List templates
curl http://localhost:8000/api/v1/templates

# Get template by ID
curl http://localhost:8000/api/v1/templates/{uuid}

# Create template (requires admin auth - to be implemented)
curl -X POST http://localhost:8000/api/v1/templates \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Space Explorer",
    "description": "Journey through the cosmos",
    "template_type": "story_book",
    "genre": "adventure",
    "age_group": "6-8",
    "base_price": 19.99
  }'
```

## 🐛 Troubleshooting

### Port already in use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Docker issues
```powershell
# Stop all containers
docker-compose down

# Remove volumes and start fresh
docker-compose down -v
docker-compose up -d --build
```

### Database migration issues
```powershell
# Check current version
alembic current

# View history
alembic history

# Rollback and reapply
alembic downgrade -1
alembic upgrade head
```

## 📚 Learn More

- **API Documentation**: http://localhost:8000/docs
- **Full README**: [README.md](README.md)
- **API Design Docs**: [api-docs/](api-docs/)
- **Database Schema**: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
