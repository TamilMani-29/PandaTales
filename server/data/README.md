# Story Book Template Seeding

This directory contains JSON data files and configuration for seeding story book templates into the database.

## 📁 Files

- **`story_book_templates.json`** - Template data (safe to edit and commit)
- **`seed_config.json`** - Database configuration (customize locally, DO NOT commit with real credentials)
- **`seed_config.example.json`** - Example configuration template

## 🚀 Quick Start

### 1. Configure Database Connection

Edit `seed_config.json` with your database credentials:

```json
{
  "database": {
    "url": "postgresql+asyncpg://your_user:your_password@localhost:5432/your_database"
  }
}
```

**For Docker containers:**
```json
{
  "database": {
    "url": "postgresql+asyncpg://pandatales_dev:pandatales@localhost:5432/pandatales_dev"
  }
}
```

### 2. Run the Seeder

```bash
# From server/ directory with venv activated
python scripts/seed_story_templates.py

# Or use the helper script
./scripts/seed_templates.sh   # Linux/Mac
./scripts/seed_templates.ps1  # Windows
```

## 📝 Editing Templates

Edit `story_book_templates.json` to add, modify, or remove templates:

```json
[
  {
    "id": "00000000-0000-0000-0003-000000000001",
    "title": "Your Story Title",
    "description": "Short description...",
    "long_description": "Detailed description...",
    "book_type": "single",
    "genre": "adventure",
    "age_group": "3-5",
    "price": 14.99,
    "cover_image_url": "https://example.com/cover.jpg",
    "preview_images": [
      "https://example.com/preview1.jpg",
      "https://example.com/preview2.jpg"
    ],
    "total_pages": 24,
    "features": [
      "Feature 1",
      "Feature 2"
    ],
    "learning_outcomes": [
      "Learning outcome 1",
      "Learning outcome 2"
    ],
    "chapters": [
      {"number": 1, "title": "Chapter Title", "pages": "1-8"}
    ],
    "prompts_config": {
      "style": "watercolor illustration",
      "story_lines": ["Line 1", "Line 2"],
      "scenes": ["Scene 1", "Scene 2"],
      "negative_prompt": "scary, dark"
    },
    "customization_options": {
      "child_name": true,
      "child_age": true,
      "dedication": true
    },
    "tags": ["tag1", "tag2"],
    "is_published": true
  }
]
```

## 🔍 Field Reference

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | string | Book title | "Panda's Adventure" |
| `description` | string | Short description | "A magical journey..." |
| `genre` | string | Genre | "adventure", "fantasy", "bedtime" |
| `age_group` | string | Target age | "0-2", "3-5", "6-8", "9-12" |
| `price` | number | Price in USD | 14.99 |
| `cover_image_url` | string | Cover image URL | "https://..." |
| `total_pages` | integer | Number of pages | 24 |

### Optional Fields

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `id` | string (UUID) | Template ID | Auto-generated if not provided |
| `long_description` | string | Detailed description | - |
| `book_type` | string | "single" or "series" | Must be "single", "series", or null |
| `series_id` | string (UUID) | Series identifier | Required if book_type is "series" |
| `book_number` | integer | Book number in series | Required if book_type is "series" |
| `story_theme` | string | Main theme | - |
| `moral_lesson` | string | Moral/lesson | - |
| `reading_level` | string | Reading difficulty | "beginner", "intermediate", "advanced" |
| `preview_images` | array | Preview image URLs | Array of strings |
| `features` | array | Book features | Array of strings |
| `learning_outcomes` | array | Educational outcomes | Array of strings |
| `chapters` | array | Chapter structure | Array of objects with number, title, pages |
| `prompts_config` | object | AI generation prompts | See structure below |
| `customization_options` | object | Personalization options | Object with boolean fields |
| `tags` | array | Search/filter tags | Array of strings |
| `is_published` | boolean | Published status | Default: true |

### prompts_config Structure

```json
{
  "style": "art style description",
  "story_lines": ["story element 1", "story element 2"],
  "scenes": ["scene description 1", "scene description 2"],
  "backgrounds": ["background description 1"],
  "negative_prompt": "things to avoid in generation"
}
```

## 🛠️ Advanced Usage

### Custom Database URL (One-time Override)

```bash
python scripts/seed_story_templates.py --db-url "postgresql+asyncpg://user:pass@host/db"
```

### Custom JSON File

```bash
python scripts/seed_story_templates.py --file data/my_templates.json
```

### Update Existing Templates

```bash
python scripts/seed_story_templates.py --update
```

### Dry Run (Validate Without Inserting)

```bash
python scripts/seed_story_templates.py --dry-run
```

### Skip Validation (Not Recommended)

```bash
python scripts/seed_story_templates.py --no-validate
```

## 🔐 Database Credentials

### Docker Development

If running with Docker Compose dev environment:

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
    "url": "postgresql+asyncpg://pandatales_prod:your_prod_password@localhost:5432/pandatales_prod"
  }
}
```

### Environment Variable

Alternatively, set `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"
python scripts/seed_story_templates.py
```

## ✅ Validation Rules

The seeder validates:

- ✅ Required fields are present
- ✅ Age group is valid (0-2, 3-5, 6-8, 9-12)
- ✅ Book type is valid (single, series, null)
- ✅ Reading level is valid (beginner, intermediate, advanced, null)
- ✅ Price is non-negative
- ✅ Total pages is positive
- ✅ UUIDs are valid format
- ✅ Series books have series_id and book_number

## 📊 Output

The script provides colored output:

- 🟢 **Green (✅)**: Successfully created templates
- 🟡 **Yellow (⚠️)**: Skipped existing templates
- 🔵 **Blue (ℹ️)**: Info messages
- 🔴 **Red (❌)**: Errors

## 🔄 Workflow

1. **Edit** `story_book_templates.json` with your template data
2. **Validate** with `--dry-run` flag
3. **Seed** by running the script
4. **Update** existing templates with `--update` flag if needed

## 🚨 Important Notes

- **IDs**: If you provide `id` fields, they must be valid UUIDs. Omit `id` to auto-generate.
- **Duplicates**: By default, existing templates (matched by ID) are skipped. Use `--update` to overwrite.
- **Validation**: Always run with validation enabled (default) to catch errors before inserting.
- **Backup**: Always backup your database before bulk operations.

## 🐛 Troubleshooting

### "Templates file not found"
- Ensure you're running from the `server/` directory
- Check the file path is correct (default: `data/story_book_templates.json`)

### "Database URL not provided"
- Create `data/seed_config.json` with database URL
- Or use `--db-url` flag
- Or set `DATABASE_URL` environment variable

### "Invalid JSON"
- Validate JSON syntax at [jsonlint.com](https://jsonlint.com)
- Check for missing commas, quotes, brackets

### "Validation failed"
- Read error messages carefully
- Fix data according to validation rules
- Use `--dry-run` to validate before inserting

## 📚 Examples

See `story_book_templates.json` for complete examples of:
- Single story books
- Series books
- Different age groups
- Various genres
- Complete prompts_config structures
