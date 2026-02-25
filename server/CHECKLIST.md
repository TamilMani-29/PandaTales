# Getting Started Checklist

Use this checklist to get your StoryBloom backend up and running.

## ✅ Pre-Installation

- [ ] Install Python 3.11 or higher
- [ ] Install Docker Desktop (recommended) or Docker Engine
- [ ] Install Git
- [ ] Install a code editor (VS Code recommended)

## ✅ Installation

### Option A: Docker (Recommended)

- [ ] Clone the repository
- [ ] Navigate to `server/` directory
- [ ] Copy `.env.example` to `.env`
  ```powershell
  Copy-Item .env.example .env
  ```
- [ ] Review and update `.env` if needed (defaults should work)
- [ ] Start all services
  ```powershell
  docker-compose up -d
  ```
- [ ] Check if all services are running
  ```powershell
  docker-compose ps
  ```
- [ ] View API logs
  ```powershell
  docker-compose logs -f api
  ```
- [ ] Open API docs in browser: http://localhost:8000/docs
- [ ] Test health endpoint: http://localhost:8000/health

### Option B: Local Development

- [ ] Install uv package manager
  ```powershell
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- [ ] Navigate to `server/` directory
- [ ] Create virtual environment
  ```powershell
  uv venv
  ```
- [ ] Activate virtual environment
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- [ ] Install dependencies
  ```powershell
  uv pip install -e ".[dev]"
  ```
- [ ] Copy `.env.example` to `.env`
- [ ] Update `.env` with your PostgreSQL and MinIO settings
- [ ] Ensure PostgreSQL is running (localhost:5432)
- [ ] Ensure MinIO is running (localhost:9000)
- [ ] Run database migrations
  ```powershell
  alembic upgrade head
  ```
- [ ] Initialize MinIO bucket
  ```powershell
  python scripts/init_minio.py
  ```
- [ ] Start development server
  ```powershell
  uvicorn app.main:app --reload
  ```
- [ ] Open API docs: http://localhost:8000/docs

## ✅ Verification

- [ ] API is accessible at http://localhost:8000
- [ ] Swagger UI loads at http://localhost:8000/docs
- [ ] Health check returns success: `GET http://localhost:8000/health`
- [ ] Book templates endpoint works: `GET http://localhost:8000/api/v1/templates`
- [ ] No errors in logs

### Docker Verification
- [ ] PostgreSQL container is running
  ```powershell
  docker-compose ps postgres
  ```
- [ ] MinIO container is running
  ```powershell
  docker-compose ps minio
  ```
- [ ] API container is running
  ```powershell
  docker-compose ps api
  ```
- [ ] MinIO console accessible: http://localhost:9001
- [ ] Can log into MinIO (minioadmin/minioadmin123)

## ✅ First API Tests

### Using Swagger UI (http://localhost:8000/docs)

- [ ] Test `GET /health` endpoint
- [ ] Test `GET /api/v1/templates` (should return empty list)
- [ ] Test `GET /api/v1/templates/genres/list` (should return empty list)

### Using cURL or Postman

- [ ] Health check
  ```powershell
  curl http://localhost:8000/health
  ```
- [ ] List templates
  ```powershell
  curl http://localhost:8000/api/v1/templates
  ```
- [ ] List genres
  ```powershell
  curl http://localhost:8000/api/v1/templates/genres/list
  ```

## ✅ Development Tools

- [ ] Code formatter installed (black)
- [ ] Linter installed (ruff)
- [ ] Type checker installed (mypy)
- [ ] Test framework installed (pytest)

### Run Code Quality Checks

- [ ] Format code
  ```powershell
  black app/
  ```
- [ ] Check for linting issues
  ```powershell
  ruff check app/
  ```
- [ ] Run type checking
  ```powershell
  mypy app/
  ```

## ✅ Database

- [ ] Database migrations are up to date
  ```powershell
  alembic current
  ```
- [ ] Can connect to PostgreSQL
  ```powershell
  # With Docker
  docker-compose exec postgres psql -U storybloom -d storybloom
  ```
- [ ] Book templates table exists
  ```sql
  \dt book_templates
  ```

## ✅ Next Steps

- [ ] Read [BUILD_SUMMARY.md](BUILD_SUMMARY.md) for architecture overview
- [ ] Review [README.md](README.md) for detailed documentation
- [ ] Check [QUICKSTART.md](QUICKSTART.md) for common tasks
- [ ] Explore API endpoints in Swagger UI
- [ ] Read API design docs in `api-docs/` folder

## ✅ Optional: Production Setup

- [ ] Generate strong JWT secret key
  ```python
  import secrets
  print(secrets.token_urlsafe(32))
  ```
- [ ] Update `JWT_SECRET_KEY` in `.env`
- [ ] Configure production database URL
- [ ] Configure MinIO or AWS S3
- [ ] Set up OpenAI API key (for AI generation)
- [ ] Set up Stripe API keys (for payments)
- [ ] Configure email service (for notifications)
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

## 🆘 Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace <PID> with actual ID)
taskkill /PID <PID> /F
```

### Docker Issues

```powershell
# Stop all containers
docker-compose down

# Remove volumes and start fresh
docker-compose down -v
docker-compose up -d --build
```

### Database Migration Issues

```powershell
# Check current version
alembic current

# View migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Apply migrations
alembic upgrade head
```

### Import Errors

All import errors are expected before installing dependencies:

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
uv pip install -e ".[dev]"
```

## 📚 Resources

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **MinIO Console**: http://localhost:9001
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Pydantic Docs**: https://docs.pydantic.dev/

## ✅ You're Done!

If all checkboxes are checked, your StoryBloom backend is ready for development!

Next: Start building the Authentication module or any other module from the API documentation.
