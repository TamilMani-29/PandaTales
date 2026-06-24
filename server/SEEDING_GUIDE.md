# Seeding Story Book Templates

## ⚡ Quick Start: Automatic Seeding (Recommended)

**Templates are now seeded automatically when containers start!**

Just start your containers and seeding happens automatically:

```bash
# Development
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d
```

**That's it!** Templates from `data/story_book_templates.json` are automatically seeded.

See **[AUTO_SEEDING.md](../AUTO_SEEDING.md)** for full details.

---

## 📖 Manual Seeding (Optional)

This guide explains how to manually seed story book templates for advanced use cases.

## 🎯 Overview

The seeding system allows you to:
- Define templates in a simple JSON file
- Validate data before inserting
- Update existing templates
- Configure database credentials separately
- Track what was created/updated/skipped

## 📁 Files Structure

```
server/
├── data/
│   ├── story_book_templates.json      # Template data (edit this!)
│   ├── seed_config.json              # DB credentials (create from example)
│   ├── seed_config.example.json      # Template for config
│   └── README.md                     # Detailed documentation
├── scripts/
│   ├── seed_story_templates.py       # Main seeding script
│   ├── seed_templates.ps1            # Windows helper script
│   └── seed_templates.sh             # Linux/Mac helper script
```

## 🚀 Quick Start

### 1. Configure Database

Create `data/seed_config.json` from the example:

```bash
cd server
cp data/seed_config.example.json data/seed_config.json
```

Edit `data/seed_config.json`:

```json
{
  "database": {
    "url": "postgresql+asyncpg://pandatales_dev:pandatales@localhost:5432/pandatales_dev"
  }
}
```

### 2. Activate Virtual Environment

```bash
# Windows
.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate
```

### 3. Run Seeder

**Option A: Use helper script (recommended)**

```bash
# Windows PowerShell
./scripts/seed_templates.ps1

# Linux/Mac
./scripts/seed_templates.sh
```

**Option B: Run directly**

```bash
python scripts/seed_story_templates.py
```

## 📝 Editing Templates

Edit `data/story_book_templates.json`:

```json
[
  {
    "title": "Your Story Title",
    "description": "Short description",
    "genre": "adventure",
    "age_group": "3-5",
    "price": 14.99,
    "cover_image_url": "https://example.com/cover.jpg",
    "total_pages": 24,
    "features": ["Feature 1", "Feature 2"],
    "learning_outcomes": ["Outcome 1"],
    "chapters": [
      {"number": 1, "title": "Chapter 1", "pages": "1-8"}
    ],
    "tags": ["tag1", "tag2"],
    "is_published": true
  }
]
```

## 🔐 Database Credentials

### Docker Development

```json
{
  "database": {
    "url": "postgresql+asyncpg://pandatales_dev:pandatales@localhost:5432/pandatales_dev"
  }
}
```

### Docker Production

```json
{
  "database": {
    "url": "postgresql+asyncpg://pandatales_prod:YOUR_PASSWORD@localhost:5432/pandatales_prod"
  }
}
```

### Using Environment Variable

```bash
# Set environment variable
export DATABASE_URL="postgresql+asyncpg://user:pass@host/db"

# Run without config file
python scripts/seed_story_templates.py
```

## ⚙️ Command Options

### Dry Run (Test Without Inserting)

```bash
python scripts/seed_story_templates.py --dry-run
```

### Update Existing Templates

```bash
python scripts/seed_story_templates.py --update
```

### Custom Database URL

```bash
python scripts/seed_story_templates.py --db-url "postgresql+asyncpg://user:pass@host/db"
```

### Custom JSON File

```bash
python scripts/seed_story_templates.py --file data/my_templates.json
```

### All Options

```bash
python scripts/seed_story_templates.py --help
```

## ✅ Validation

The script automatically validates:
- Required fields are present
- Age groups are valid (0-2, 3-5, 6-8, 9-12)
- Book types are valid (single, series)
- Reading levels are valid (beginner, intermediate, advanced)
- Prices are non-negative
- Total pages are positive
- UUIDs have correct format

## 📊 Example Output

```
==============================================================
              Story Book Template Seeder
==============================================================

ℹ️  Database: localhost:5432/pandatales_dev
ℹ️  Templates file: data/story_book_templates.json
ℹ️  Loaded 4 templates from file

Validating templates...
✅ All 4 templates validated successfully

[1/4] ✅ Created: Panda's Magical Forest Adventure
[2/4] ✅ Created: The Dragon's Secret Kingdom
[3/4] ✅ Created: Space Explorer Journey
[4/4] ✅ Created: Goodnight, Little Panda

==============================================================
                        Summary
==============================================================

✅ Created: 4
⚠️  Skipped: 0

✨ Seeding completed successfully!
```

## 🐛 Troubleshooting

### "Templates file not found"

Make sure you're in the `server/` directory:

```bash
cd server
python scripts/seed_story_templates.py
```

### "Database URL not provided"

Create `data/seed_config.json` or set `DATABASE_URL`:

```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"
```

### "Invalid JSON"

Validate your JSON at [jsonlint.com](https://jsonlint.com)

### "Validation failed"

Read the error messages and fix the data according to the validation rules.

## 🔄 Workflow

1. **Start database** (Docker or local PostgreSQL)
2. **Edit** `data/story_book_templates.json`
3. **Validate** with `--dry-run`
4. **Seed** by running the script
5. **Verify** in database or through API

## 📚 Complete Documentation

See `data/README.md` for:
- Complete field reference
- Validation rules
- Advanced usage
- Examples
- Best practices

## 🎓 Examples

The included `story_book_templates.json` has examples of:
- ✅ Single story books
- ✅ Series books
- ✅ Different age groups (0-2, 3-5, 6-8, 9-12)
- ✅ Various genres (adventure, fantasy, bedtime, sci-fi)
- ✅ Complete prompts_config for AI generation
- ✅ Customization options
- ✅ Chapters and learning outcomes

Use these as templates for creating your own story books!
