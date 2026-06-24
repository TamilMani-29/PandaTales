# Story Book Template Seeding System - Summary

## ⚡ NEW: Automatic Seeding!

**Templates now seed automatically when Docker containers start!**

- ✅ No manual steps needed
- ✅ Only new templates are added (incremental)
- ✅ Works in both dev and prod
- ✅ Edit JSON → Restart containers → Done!

See **[AUTO_SEEDING.md](AUTO_SEEDING.md)** for details.

---

## ✅ What Was Created

A complete JSON-driven seeding system for story book templates that allows you to:
- Define template data in JSON files
- Configure database credentials separately  
- Validate data before inserting
- Update or skip existing templates
- Track progress with colored output

## 📁 Files Created

```
server/
├── data/
│   ├── story_book_templates.json      # ✅ Template data (4 examples included)
│   ├── seed_config.json              # ✅ DB configuration (customize this!)
│   ├── seed_config.example.json      # ✅ Configuration template
│   └── README.md                     # ✅ Detailed field reference
│
├── scripts/
│   ├── seed_story_templates.py       # ✅ Main seeding script (Python)
│   ├── seed_templates.ps1            # ✅ Helper script (Windows)
│   └── seed_templates.sh             # ✅ Helper script (Linux/Mac)
│
└── SEEDING_GUIDE.md                  # ✅ Quick start guide
```

## 🎯 Key Features

### 1. JSON-Driven Configuration
All template data in easy-to-edit JSON format:
```json
{
  "title": "Panda's Adventure",
  "description": "A magical journey...",
  "genre": "adventure",
  "age_group": "3-5",
  "price": 14.99,
  "total_pages": 24,
  ...
}
```

### 2. Automatic Validation
- ✅ Required fields checked
- ✅ Age groups validated (0-2, 3-5, 6-8, 9-12)
- ✅ Book types validated (single, series)
- ✅ Reading levels validated (beginner, intermediate, advanced)
- ✅ Prices must be non-negative
- ✅ Pages must be positive
- ✅ UUIDs validated

### 3. Separate Database Configuration
Configure credentials once in `seed_config.json`:
```json
{
  "database": {
    "url": "postgresql+asyncpg://user:pass@host/db"
  }
}
```

### 4. Flexible Execution
```bash
# Simple run
python scripts/seed_story_templates.py

# Dry run (validate only)
python scripts/seed_story_templates.py --dry-run

# Update existing
python scripts/seed_story_templates.py --update

# Custom database
python scripts/seed_story_templates.py --db-url "postgresql://..."

# Custom file
python scripts/seed_story_templates.py --file data/my_templates.json
```

### 5. Progress Reporting
Colored terminal output shows exactly what happened:
- 🟢 Created templates
- 🟡 Skipped (duplicates)
- 🟢 Updated templates  
- 🔵 Info messages
- 🔴 Errors with details

## 🚀 Quick Start

### 1. Configure Database

Edit `server/data/seed_config.json`:

```json
{
  "database": {
    "url": "postgresql+asyncpg://pandatales_dev:pandatales@localhost:5432/pandatales_dev"
  }
}
```

### 2. Run Seeder

**Windows:**
```powershell
cd server  
./scripts/seed_templates.ps1
```

**Linux/Mac:**
```bash
cd server
./scripts/seed_templates.sh
```

**Or directly:**
```bash
cd server
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
python scripts/seed_story_templates.py
```

## 📝 Example Templates Included

The `story_book_templates.json` includes 4 complete examples:

1. **Panda's Magical Forest Adventure** (3-5, adventure, beginner)
2. **The Dragon's Secret Kingdom** (6-8, fantasy, intermediate)
3. **Space Explorer Journey** (6-8, sci-fi, intermediate)
4. **Goodnight, Little Panda** (0-2, bedtime, beginner)

Each includes:
- Complete metadata (title, description, genre, age group)
- Pricing information
- Cover and preview images
- Features and learning outcomes
- Chapter structure
- AI prompts configuration
- Customization options
- Tags for search/filtering

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
    "url": "postgresql+asyncpg://pandatales_prod:YOUR_PROD_PASSWORD@localhost:5432/pandatales_prod"
  }
}
```

### Environment Variable
```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@host/db"
python scripts/seed_story_templates.py
```

## ✅ Test Results

Script tested successfully:
- ✅ JSON loading works
- ✅ Validation works (all 4 templates passed)
- ✅ Dry-run mode works
- ✅ Colored output works
- ✅ Progress reporting works
- ⏸️ Database connection (test when DB is running)

## 📚 Documentation Structure

1. **SEEDING_GUIDE.md** - Quick start guide
2. **data/README.md** - Complete field reference and examples
3. **This file** - Overview and summary

## 🎓 How to Add New Templates

1. Open `server/data/story_book_templates.json`
2. Copy an existing template as a starting point
3. Modify the fields:
   - Change title, description, genre, age_group, etc.
   - Update price and total_pages
   - Customize features, learning_outcomes, chapters
   - Configure prompts_config for AI generation
   - Set tags for search
4. Validate with dry-run:
   ```bash
   python scripts/seed_story_templates.py --dry-run
   ```
5. Run the seeder:
   ```bash
   python scripts/seed_story_templates.py
   ```

## 🔄 Update Workflow

To update existing templates:
1. Modify `story_book_templates.json`
2. Run with update flag:
   ```bash
   python scripts/seed_story_templates.py --update
   ```

## 🐛 Troubleshooting

### "Templates file not found"
→ Make sure you're in the `server/` directory

### "Database URL not provided"
→ Create `data/seed_config.json` or set `DATABASE_URL` env var

### "Invalid JSON"
→ Validate at [jsonlint.com](https://jsonlint.com)

### "Validation failed"
→ Read error messages and fix according to validation rules

### "Connection failed"
→ Make sure database is running:
```bash
docker-compose -f docker-compose.dev.yml up -d postgres
```

## 🎯 Next Steps

1. **Start your database:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d postgres
   ```

2. **Test the seeder:**
   ```bash
   cd server
   ./scripts/seed_templates.ps1 --dry-run
   ```

3. **Seed the templates:**
   ```bash
   ./scripts/seed_templates.ps1
   ```

4. **Verify in database:**
   ```bash
   docker exec -it pandatales_postgres_dev psql -U pandatales_dev -d pandatales_dev -c "SELECT id, title, genre, age_group, price FROM story_book_templates;"
   ```

5. **Add more templates:**
   - Edit `data/story_book_templates.json`
   - Run seeder again

## 🔗 Related Files

- [server/SEEDING_GUIDE.md](./server/SEEDING_GUIDE.md) - Quick start guide
- [server/data/README.md](./server/data/README.md) - Complete field reference
- [server/data/story_book_templates.json](./server/data/story_book_templates.json) - Template data
- [server/scripts/seed_story_templates.py](./server/scripts/seed_story_templates.py) - Seeding script

## ✨ Benefits

- **Easy Updates**: Edit JSON, run script, done!
- **Safe**: Validates before inserting
- **Flexible**: Skip or update duplicates
- **Secure**: Database credentials separate from data
- **Trackable**: Templates in git, credentials are not
- **Testable**: Dry-run mode validates without changes
- **Clear**: Colored output shows exactly what happened

---

**Ready to use!** Start by configuring your database in `server/data/seed_config.json` and run the seeder. 🚀
