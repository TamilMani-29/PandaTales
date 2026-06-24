# 🐼 PandaTales

A full-stack application for creating personalized story books and coloring books for children.

## 🚀 Quick Start with Docker

The easiest way to run PandaTales is using Docker:

```bash
# 1. Copy environment configuration
cp .env.example .env.development

# 2. Start all services
docker-compose up

# 3. Open http://localhost:3000
```

For detailed instructions, see [DOCKER_QUICKSTART.md](./DOCKER_QUICKSTART.md)

## 📚 Documentation

- **[Docker Quick Start](./DOCKER_QUICKSTART.md)** - Get started in 5 minutes
- **[Docker Setup Guide](./DOCKER_SETUP.md)** - Complete Docker documentation
- **[Server README](./server/README.md)** - Backend API documentation
- **[Client README](./client/README.md)** - Frontend documentation (if exists)

## 🏗️ Tech Stack

### Frontend
- **Framework**: Next.js 14
- **UI Library**: React
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: TanStack Query

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Storage**: MinIO (S3-compatible)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Nginx (production)

## 🛠️ Development

### With Docker (Recommended)

```bash
# Start development environment with hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or use the helper script
./docker-manager.sh start development  # Linux/Mac
.\docker-manager.ps1 start development # Windows
```

### Manual Setup

#### Backend (Python/FastAPI)

```bash
cd server
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload
```

#### Frontend (Next.js)

```bash
cd client
npm install
npm run dev
```

## 🌐 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js application |
| Backend API | http://localhost:8000 | FastAPI server |
| API Documentation | http://localhost:8000/docs | Swagger UI |
| MinIO Console | http://localhost:9001 | Object storage admin |
| PostgreSQL | localhost:5432 | Database |

## 📦 Project Structure

```
PandaTales/
├── client/              # Next.js frontend application
├── server/              # FastAPI backend application
├── nginx/               # Nginx configuration (production)
├── docker-compose.yml   # Main Docker Compose file
├── .env.development     # Development environment variables
└── .env.production      # Production environment variables
```

## 🔧 Docker Management

Use the provided scripts for easy Docker management:

```bash
# Linux/Mac
./docker-manager.sh [command]

# Windows PowerShell
.\docker-manager.ps1 [command]
```

Available commands: `start`, `stop`, `restart`, `build`, `logs`, `status`, `clean`, `purge`

## 🔐 Environment Variables

See `.env.example` for all available configuration options.

Required for full functionality:
- `OPENAI_API_KEY` - For AI-powered story generation
- `STRIPE_SECRET_KEY` - For payment processing
- `JWT_SECRET_KEY` - For authentication

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines first.

---

Made with ❤️ for children's imagination