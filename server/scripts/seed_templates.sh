#!/bin/bash
# Seed Story Book Templates - Bash Script

echo "=================================================="
echo "   Story Book Template Seeder"
echo "=================================================="
echo ""

# Check if we're in the server directory
if [ ! -d "app" ]; then
    echo "❌ Error: Please run this script from the server/ directory"
    exit 1
fi

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment (.venv) not found"
    echo "   Run: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if JSON file exists
if [ ! -f "data/story_book_templates.json" ]; then
    echo "❌ Error: data/story_book_templates.json not found"
    exit 1
fi

# Check if config exists
if [ ! -f "data/seed_config.json" ]; then
    echo "⚠️  Warning: data/seed_config.json not found"
    echo "   Using default database URL or DATABASE_URL environment variable"
fi

echo ""

# Run the seeder
echo "🌱 Starting seeder..."
echo ""

python scripts/seed_story_templates.py "$@"

exitCode=$?

echo ""
if [ $exitCode -eq 0 ]; then
    echo "✅ Seeding completed successfully!"
else
    echo "❌ Seeding failed with exit code $exitCode"
fi

exit $exitCode
