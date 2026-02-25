#!/bin/bash

# Database migration script for StoryBloom

set -e

echo "================================"
echo "StoryBloom Database Migration"
echo "================================"
echo ""

# Check if alembic is available
if ! command -v alembic &> /dev/null; then
    echo "❌ Alembic is not installed!"
    echo "Please activate your virtual environment and install dependencies:"
    echo "  source .venv/bin/activate"
    echo "  uv pip install -e ."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Using default DATABASE_URL from environment"
fi

# Function to show usage
show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  upgrade      Apply all pending migrations (default)"
    echo "  downgrade    Rollback last migration"
    echo "  current      Show current migration version"
    echo "  history      Show migration history"
    echo "  create       Create a new migration (requires message)"
    echo "  reset        Reset database (downgrade all and upgrade)"
    echo ""
    echo "Examples:"
    echo "  $0 upgrade"
    echo "  $0 create \"Add user table\""
    echo "  $0 downgrade"
    exit 1
}

# Parse command
COMMAND=${1:-upgrade}

case $COMMAND in
    upgrade)
        echo "📦 Applying migrations..."
        alembic upgrade head
        echo "✅ Migrations applied successfully!"
        ;;
    
    downgrade)
        echo "⏪ Rolling back last migration..."
        alembic downgrade -1
        echo "✅ Rollback completed!"
        ;;
    
    current)
        echo "📍 Current migration version:"
        alembic current
        ;;
    
    history)
        echo "📜 Migration history:"
        alembic history
        ;;
    
    create)
        if [ -z "$2" ]; then
            echo "❌ Error: Migration message required!"
            echo "Usage: $0 create \"Your migration message\""
            exit 1
        fi
        echo "✏️  Creating new migration: $2"
        alembic revision --autogenerate -m "$2"
        echo "✅ Migration created!"
        echo "⚠️  Please review the generated migration file before applying it."
        ;;
    
    reset)
        echo "🔄 Resetting database..."
        echo "⚠️  This will rollback all migrations and reapply them."
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            alembic downgrade base
            alembic upgrade head
            echo "✅ Database reset completed!"
        else
            echo "❌ Reset cancelled"
            exit 1
        fi
        ;;
    
    help|--help|-h)
        show_usage
        ;;
    
    *)
        echo "❌ Error: Unknown command '$COMMAND'"
        echo ""
        show_usage
        ;;
esac
