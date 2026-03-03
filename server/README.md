# PandaTales Backend API

AI-Powered Children's Coloring Book Generation Platform - Backend API built with FastAPI.

## Tech Stack

- **Framework**: FastAPI 0.109+
- **Package Manager**: uv
- **Database**: PostgreSQL 15+ with asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **File Storage**: MinIO (S3-compatible)
- **Task Queue**: Celery
- **Logging**: Structlog
- **Validation**: Pydantic 2.5+
- **AI**: OpenAI API
- **Payments**: Stripe

## Architecture

```
app/
├── api/              # API routes and endpoints
│   └── v1/           # API version 1
│       └── endpoints/ # Route handlers
├── core/             # Core configuration
├── db/               # Database session and connection
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic validation schemas
├── repositories/     # Data access layer (Repository pattern)
├── services/         # Business logic layer (Service pattern)
├── common/           # Common utilities (exceptions, responses, pagination, logging)
└── main.py           # FastAPI application entry point
```

## Prerequisites

- Python 3.11+
- uv (Python package manager)
- Docker & Docker Compose (for local development)
- PostgreSQL 15+ (if not using Docker)
- MinIO (if not using Docker)

## Setup

### 1. Install uv

```bash
# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup Project

```bash
cd server

# Create virtual environment
uv venv

# Activate virtual environment
# On Windows (PowerShell)
.venv\Scripts\Activate.ps1

# On macOS/Linux
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# At minimum, configure:
# - DATABASE_URL
# - MINIO settings
# - JWT_SECRET_KEY
```

### 4. Run with Docker (Recommended for Development)

```bash
# Start all services (PostgreSQL, MinIO, FastAPI)
docker-compose up -d

# Check logs
docker-compose logs -f api

# Stop services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

The API will be available at `http://localhost:8000`.

Services:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin123)
- **PostgreSQL**: localhost:5432

### 5. Run Locally (Without Docker)

Ensure PostgreSQL and MinIO are running separately.

```bash
# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

## Development

### Code Quality

```bash
# Format code
black app/
ruff check app/ --fix

# Type checking
mypy app/

# Run all checks
black app/ && ruff check app/ --fix && mypy app/
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_book_templates.py -v
```

### Adding a New Module

1. **Create Model** (`app/models/your_model.py`)
```python
from app.models.base import BaseModel
from sqlalchemy import Column, String

class YourModel(BaseModel):
    __tablename__ = "your_table"
    name = Column(String(100), nullable=False)
```

2. **Create Migration**
```bash
alembic revision --autogenerate -m "Add your_table"
alembic upgrade head
```

3. **Create Schemas** (`app/schemas/your_model.py`)
```python
from pydantic import BaseModel

class YourModelCreate(BaseModel):
    name: str

class YourModelResponse(YourModelCreate):
    id: UUID
    created_at: datetime
```

4. **Create Repository** (`app/repositories/your_model.py`)
```python
from app.repositories.base import BaseRepository
from app.models.your_model import YourModel

class YourModelRepository(BaseRepository[YourModel]):
    pass
```

5. **Create Service** (`app/services/your_model.py`)
```python
from app.services.base import BaseService

class YourModelService(BaseService):
    pass
```

6. **Create Routes** (`app/api/v1/endpoints/your_model.py`)
```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/your-models", tags=["Your Models"])

@router.get("/")
async def list_items():
    return {"items": []}
```

7. **Register Router** (in `app/api/v1/router.py`)
```python
from app.api.v1.endpoints import your_model
api_router.include_router(your_model.router)
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

For detailed API design documentation, see:
- [API_DESIGN_OVERVIEW.md](./API_DESIGN_OVERVIEW.md) - Architecture overview
- [api-docs/](./api-docs/) - Detailed API specifications for each module

## Project Status

### Completed Modules
- ✅ Book Templates API (CRUD + filtering + series management)

### In Progress
- 🔄 Authentication & Authorization
- 🔄 User Management

### Planned
- ⏳ Story Generation
- ⏳ Book Customization
- ⏳ Payment Processing
- ⏳ Admin Dashboard

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `MINIO_ENDPOINT`: MinIO server endpoint
- `MINIO_ACCESS_KEY`: MinIO access key
- `MINIO_SECRET_KEY`: MinIO secret key
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `OPENAI_API_KEY`: OpenAI API key for story generation
- `STRIPE_SECRET_KEY`: Stripe secret key for payments

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Connect to PostgreSQL
docker-compose exec postgres psql -U pandatales -d pandatales
```

### MinIO Issues

```bash
# Check MinIO status
docker-compose ps minio

# Access MinIO console
Open http://localhost:9001 in browser
Login with minioadmin/minioadmin123
```

### Reset Everything

```bash
# Stop and remove all containers, volumes, and networks
docker-compose down -v

# Rebuild and start
docker-compose up -d --build
```

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the development team.
{
  "items": [...],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalPages": 5,
    "totalItems": 95,
    "hasNext": true,
    "hasPrev": false
  }
}
```

## 🧪 Testing Strategy

### Test Coverage Goals
- Unit tests: 80%+
- Integration tests: All critical flows
- API endpoint tests: 100%
- Load tests: High-traffic scenarios

### Test Environment
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov

# Run specific module
pytest tests/test_auth.py -v
```

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Project setup & structure
- [ ] Database models & migrations
- [ ] Authentication system
- [ ] User management
- [ ] JWT implementation

### Phase 2: Core Features (Week 3-4)
- [ ] Book templates CRUD
- [ ] Search & filtering
- [ ] Book generation (mock)
- [ ] Image upload & processing
- [ ] Background task setup (Celery)

### Phase 3: AI Integration (Week 5-6)
- [ ] OpenAI API integration
- [ ] Story generation logic
- [ ] Image processing pipeline
- [ ] PDF generation
- [ ] Preview system

### Phase 4: E-commerce (Week 7-8)
- [ ] Cart management
- [ ] Order processing
- [ ] Stripe integration
- [ ] Payment webhooks
- [ ] Invoice generation

### Phase 5: Production Ready (Week 9-10)
- [ ] Error handling & logging
- [ ] Rate limiting
- [ ] Caching layer
- [ ] Security hardening
- [ ] Performance optimization
- [ ] Monitoring & analytics

## 📝 Environment Setup

### Required Environment Variables

```ini
# .env
# Application
APP_NAME=PandaTales
APP_VERSION=1.0.0
DEBUG=False
SECRET_KEY=your-secret-key-min-32-chars
ALLOWED_ORIGINS=http://localhost:3000,https://pandatales.com

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/pandatales

# AWS
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-1
S3_BUCKET_NAME=pandatales-books
CLOUDFRONT_DOMAIN=cdn.pandatales.com

# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4

# Stripe
STRIPE_PUBLIC_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# OAuth
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@pandatales.com
SMTP_PASSWORD=xxx
SMTP_FROM=Panda Tales <noreply@pandatales.com>

# Celery (Optional - requires message broker)
# CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
# CELERY_RESULT_BACKEND=db+postgresql://user:pass@localhost:5432/pandatales

# Security
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## 📚 Additional Resources

### External Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Stripe API Reference](https://stripe.com/docs/api)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Celery Documentation](https://docs.celeryproject.org/)

### Project Structure
```
server/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── config.py          # Configuration
│   │   ├── security.py        # Auth utilities
│   │   └── database.py        # DB connection
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py        # Auth endpoints
│   │       ├── users.py       # User endpoints
│   │       ├── templates.py   # Template endpoints
│   │       ├── books.py       # Book endpoints
│   │       ├── orders.py      # Order endpoints
│   │       └── payments.py    # Payment endpoints
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   ├── tasks/                 # Celery tasks
│   └── utils/                 # Utilities
├── tests/                     # Test files
├── alembic/                   # Database migrations
├── requirements.txt           # Dependencies
└── README.md
```

## 🤝 Contributing

When implementing the API:

1. Follow the API specifications exactly
2. Maintain consistent response formats
3. Implement proper error handling
4. Add comprehensive logging
5. Write tests for all endpoints
6. Document any deviations from specs

## 📧 Support

For questions about the API design:
- Review the relevant API documentation
- Check common patterns in overview
- Refer to external documentation links

## 📄 License

Panda Tales API Documentation - All Rights Reserved

---

**Next Steps:**
1. Review [API_DESIGN_OVERVIEW.md](./API_DESIGN_OVERVIEW.md)
2. Set up development environment
3. Start with authentication module
4. Follow implementation roadmap
5. Build incrementally and test thoroughly
