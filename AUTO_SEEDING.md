# Automatic Seeding in Docker Containers

## 🎯 Overview

The PandaTales application now includes **automatic seeding** of story book templates when database containers start up. This happens for both development and production environments.

## ✨ Features

- ✅ **Automatic**: Seeds run when backend container starts
- ✅ **Incremental**: Only seeds new templates (skips existing)
- ✅ **Safe**: Won't overwrite existing data
- ✅ **Silent**: Clean logs, no noise in container output
- ✅ **Both Environments**: Works in dev and prod

## 🔄 How It Works

### Startup Sequence

When the backend container starts:

```
1. Wait for dependencies (PostgreSQL, MinIO)
2. Run database migrations (alembic upgrade head)
3. Auto-seed story book templates (python scripts/auto_seed.py)
4. Start the application server
```

### Seeding Logic

```python
For each template in data/story_book_templates.json:
    If template ID exists in database:
        → Skip (already seeded)
    Else:
        → Insert new template
```

## 📝 Adding New Templates

Simply edit `server/data/story_book_templates.json` and restart containers:

```bash
# 1. Edit the JSON file
notepad server\data\story_book_templates.json

# 2. Add your new template
{
  "id": "00000000-0000-0000-0003-000000000999",
  "title": "New Story Title",
  ...
}

# 3. Restart containers
docker-compose -f docker-compose.dev.yml restart backend
```

**Result**: Only the new template will be seeded!

## 🚀 First Time Setup

### Development

```bash
# Start all services (auto-seeding happens automatically)
docker-compose -f docker-compose.dev.yml up -d

# Check logs to see seeding
docker-compose -f docker-compose.dev.yml logs backend
```

Expected output:
```
backend_dev | Running database migrations...
backend_dev | Auto-seeding story book templates...
backend_dev | ✅ Auto-seeded 4 story book template(s)
backend_dev | Starting FastAPI server with hot-reload...
```

### Production

```bash
# Start all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d

# Check logs
docker-compose logs backend
```

## 📊 Seeding Scenarios

### Scenario 1: Fresh Database

```
Templates in JSON: 4
Templates in DB: 0

Result: ✅ Auto-seeded 4 story book template(s)
```

### Scenario 2: Existing Data

```
Templates in JSON: 4
Templates in DB: 4

Result: ℹ️  Skipped 4 existing template(s)
```

### Scenario 3: New Templates Added

```
Templates in JSON: 6 (added 2 new)
Templates in DB: 4

Result: 
✅ Auto-seeded 2 story book template(s)
ℹ️  Skipped 4 existing template(s)
```

## 🔧 Configuration

### Template Data Location

```
server/
└── data/
    └── story_book_templates.json  ← Edit this file
```

### Auto-Seed Script

```
server/
└── scripts/
    └── auto_seed.py  ← Runs automatically on startup
```

## 🐛 Troubleshooting

### No auto-seeding happening?

**Check logs:**
```bash
docker-compose -f docker-compose.dev.yml logs backend | grep -i seed
```

**Common issues:**

1. **Templates file not found**
   - Ensure `server/data/story_book_templates.json` exists
   - Check file is mounted in container

2. **DATABASE_URL not set**
   - Verify environment variables in compose file
   - Check backend container environment

3. **Permission errors**
   - File should be readable by container user

### Verify seeding worked

**Check database:**
```bash
# Development
docker exec -it pandatales_postgres_dev psql -U pandatales_dev -d pandatales_dev \
  -c "SELECT id, title FROM story_book_templates;"

# Production  
docker exec -it pandatales_postgres_prod psql -U pandatales_prod -d pandatales_prod \
  -c "SELECT id, title FROM story_book_templates;"
```

## 🔄 Manual Seeding (Alternative)

You can still manually seed if needed:

```bash
# Enter backend container
docker exec -it pandatales_backend_dev sh

# Run manual seeder with full validation
python scripts/seed_story_templates.py --dry-run
python scripts/seed_story_templates.py
```

## 📁 File Mounts

### Development (`docker-compose.dev.yml`)

```yaml
volumes:
  - ./server/app:/app/app          # Hot-reload code
  - ./server/alembic:/app/alembic  # Migrations
  - ./server/data:/app/data        # Template data
  - ./server/scripts:/app/scripts  # Seeding scripts
```

### Production (`docker-compose.prod.yml`)

```yaml
volumes:
  - ./server/data:/app/data        # Only data directory
```

**Why?** In production, code is baked into the image. We only mount data directory to allow template updates without rebuilding.

## ✅ Benefits

1. **Zero Manual Steps**: No need to remember to seed
2. **Consistent State**: All environments start with templates
3. **Easy Updates**: Just edit JSON and restart
4. **Safe Operations**: Won't duplicate or overwrite
5. **Clean Logs**: Informative but not noisy

## 🎓 Best Practices

### 1. Use UUIDs for Template IDs

```json
{
  "id": "00000000-0000-0000-0003-000000000001",
  ...
}
```

This ensures templates are recognized across environments.

### 2. Test in Development First

```bash
# Add template to JSON
# Restart dev
docker-compose -f docker-compose.dev.yml restart backend

# Verify it worked
docker-compose -f docker-compose.dev.yml logs backend | grep -i seed
```

### 3. Backup Before Major Updates

```bash
# Backup database
docker exec pandatales_postgres_dev pg_dump -U pandatales_dev pandatales_dev > backup.sql
```

### 4. Monitor Logs on Deployment

```bash
# Watch production seeding
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend
```

## 🔗 Related Documentation

- [SEEDING_GUIDE.md](../server/SEEDING_GUIDE.md) - Manual seeding guide
- [server/data/README.md](../server/data/README.md) - Template field reference
- [SEEDING_SYSTEM_SUMMARY.md](SEEDING_SYSTEM_SUMMARY.md) - System overview

## 📝 Summary

**Auto-seeding is now fully automatic!**

- ✅ Runs on every container startup
- ✅ Only adds new templates
- ✅ Safe and incremental
- ✅ Works in dev and prod
- ✅ Edit JSON → Restart → Done!

No manual steps needed. Just edit `server/data/story_book_templates.json` and restart your containers! 🚀
