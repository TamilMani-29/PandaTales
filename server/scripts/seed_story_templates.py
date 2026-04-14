"""
Seed Story Book Templates from JSON

This script reads story book template data from a JSON file and seeds it into the database.

Features:
- JSON-driven configuration
- Validation of required fields
- Skip duplicates or update existing
- Database credential configuration
- Progress reporting

Usage:
    From server/ directory with venv active:
    
    # Seed with default config
    python scripts/seed_story_templates.py
    
    # Seed with custom config
    python scripts/seed_story_templates.py --config data/custom_config.json
    
    # Seed with custom JSON file
    python scripts/seed_story_templates.py --file data/my_templates.json
    
    # Update existing templates
    python scripts/seed_story_templates.py --update
    
    # Use custom database URL
    python scripts/seed_story_templates.py --db-url "postgresql+asyncpg://user:pass@localhost/db"
    
    # Dry run (validate without inserting)
    python scripts/seed_story_templates.py --dry-run

Environment Variables (alternative to --db-url):
    DATABASE_URL: Database connection string
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.story_book_template import StoryBookTemplate


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg: str) -> None:
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_warning(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")


def print_error(msg: str) -> None:
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def print_info(msg: str) -> None:
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")


def print_header(msg: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{msg:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")


REQUIRED_FIELDS = [
    "title",
    "description",
    "genre",
    "age_group",
    "price",
    "cover_image_url",
    "total_pages",
]

VALID_AGE_GROUPS = ["0-2", "3-5", "6-8", "9-12"]
VALID_BOOK_TYPES = ["single", "series", None]
VALID_READING_LEVELS = ["beginner", "intermediate", "advanced", None]


def validate_template(data: dict[str, Any], index: int) -> tuple[bool, list[str]]:
    """
    Validate a story book template data dictionary.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in data or data[field] is None or data[field] == "":
            errors.append(f"Missing required field: '{field}'")
    
    # Validate age_group
    if "age_group" in data and data["age_group"] not in VALID_AGE_GROUPS:
        errors.append(f"Invalid age_group: '{data['age_group']}'. Must be one of {VALID_AGE_GROUPS}")
    
    # Validate book_type
    if "book_type" in data and data["book_type"] not in VALID_BOOK_TYPES:
        errors.append(f"Invalid book_type: '{data['book_type']}'. Must be one of {VALID_BOOK_TYPES}")
    
    # Validate reading_level
    if "reading_level" in data and data["reading_level"] not in VALID_READING_LEVELS:
        errors.append(f"Invalid reading_level: '{data['reading_level']}'. Must be one of {VALID_READING_LEVELS}")
    
    # Validate price
    if "price" in data:
        try:
            price = float(data["price"])
            if price < 0:
                errors.append("Price must be non-negative")
        except (ValueError, TypeError):
            errors.append(f"Invalid price: '{data['price']}'. Must be a number")
    
    # Validate total_pages
    if "total_pages" in data:
        try:
            pages = int(data["total_pages"])
            if pages <= 0:
                errors.append("total_pages must be positive")
        except (ValueError, TypeError):
            errors.append(f"Invalid total_pages: '{data['total_pages']}'. Must be an integer")
    
    # Validate series fields
    if data.get("book_type") == "series":
        if "book_number" not in data or data["book_number"] is None:
            errors.append("book_number is required when book_type is 'series'")
        if "series_id" not in data or data["series_id"] is None:
            errors.append("series_id is required when book_type is 'series'")
    
    # Validate UUID if provided
    if "id" in data and data["id"] is not None:
        try:
            UUID(data["id"])
        except (ValueError, TypeError):
            errors.append(f"Invalid UUID format for 'id': '{data['id']}'")
    
    if "series_id" in data and data["series_id"] is not None:
        try:
            UUID(data["series_id"])
        except (ValueError, TypeError):
            errors.append(f"Invalid UUID format for 'series_id': '{data['series_id']}'")
    
    return len(errors) == 0, errors


async def seed_story_templates(
    session: AsyncSession,
    templates_data: list[dict[str, Any]],
    skip_duplicates: bool = True,
    update_existing: bool = False,
    dry_run: bool = False,
) -> tuple[int, int, int]:
    """
    Seed story book templates into the database.
    
    Args:
        session: Database session
        templates_data: List of template dictionaries from JSON
        skip_duplicates: Skip templates that already exist
        update_existing: Update existing templates with new data
        dry_run: Validate without inserting
    
    Returns:
        Tuple of (created_count, updated_count, skipped_count)
    """
    created = 0
    updated = 0
    skipped = 0
    
    for idx, data in enumerate(templates_data, 1):
        title = data.get("title", f"Template {idx}")
        
        # Convert string UUID to UUID object if present
        template_id = None
        if "id" in data and data["id"]:
            try:
                template_id = UUID(data["id"])
            except (ValueError, TypeError):
                print_error(f"Invalid UUID for '{title}', will auto-generate")
        
        # Check if template already exists
        existing = None
        if template_id:
            existing = await session.get(StoryBookTemplate, template_id)
        
        if existing:
            if update_existing and not dry_run:
                # Update existing template
                for key, value in data.items():
                    if key != "id" and hasattr(existing, key):
                        setattr(existing, key, value)
                print_info(f"[{idx}/{len(templates_data)}] Updated: {title}")
                updated += 1
            else:
                print_warning(f"[{idx}/{len(templates_data)}] Skipped (already exists): {title}")
                skipped += 1
            continue
        
        # Convert series_id string to UUID if present
        if "series_id" in data and data["series_id"]:
            try:
                data["series_id"] = UUID(data["series_id"])
            except (ValueError, TypeError):
                data["series_id"] = None
        
        # Create new template
        if dry_run:
            print_info(f"[{idx}/{len(templates_data)}] Would create: {title}")
        else:
            template_dict = {k: v for k, v in data.items() if k != "id"}
            if template_id:
                template_dict["id"] = template_id
            
            template = StoryBookTemplate(**template_dict)
            session.add(template)
            print_success(f"[{idx}/{len(templates_data)}] Created: {title}")
        
        created += 1
    
    if not dry_run:
        await session.commit()
    
    return created, updated, skipped


async def main():
    parser = argparse.ArgumentParser(
        description="Seed story book templates from JSON file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--file",
        default="data/story_book_templates.json",
        help="Path to JSON file with template data (default: data/story_book_templates.json)"
    )
    parser.add_argument(
        "--config",
        default="data/seed_config.json",
        help="Path to configuration JSON file (default: data/seed_config.json)"
    )
    parser.add_argument(
        "--db-url",
        help="Database URL (overrides config file and environment)"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing templates instead of skipping them"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and show what would be done without making changes"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation (not recommended)"
    )
    
    args = parser.parse_args()
    
    print_header("Story Book Template Seeder")
    
    # Determine paths
    script_dir = Path(__file__).parent
    server_dir = script_dir.parent
    
    templates_file = server_dir / args.file
    config_file = server_dir / args.config
    
    # Load configuration
    db_url = args.db_url
    if not db_url and config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                db_url = config.get("database", {}).get("url")
        except Exception as e:
            print_warning(f"Could not load config file: {e}")
    
    # Fallback to environment variable
    if not db_url:
        import os
        db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print_error("Database URL not provided!")
        print_info("Provide via: --db-url, config file, or DATABASE_URL environment variable")
        sys.exit(1)
    
    print_info(f"Database: {db_url.split('@')[1] if '@' in db_url else 'configured'}")
    print_info(f"Templates file: {templates_file}")
    
    # Load templates data
    if not templates_file.exists():
        print_error(f"Templates file not found: {templates_file}")
        sys.exit(1)
    
    try:
        with open(templates_file, 'r', encoding='utf-8') as f:
            templates_data = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in templates file: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error reading templates file: {e}")
        sys.exit(1)
    
    if not isinstance(templates_data, list):
        print_error("Templates file must contain a JSON array")
        sys.exit(1)
    
    print_info(f"Loaded {len(templates_data)} templates from file")
    
    # Validate templates
    if not args.no_validate:
        print("\n" + Colors.BOLD + "Validating templates..." + Colors.RESET)
        all_valid = True
        for idx, data in enumerate(templates_data, 1):
            is_valid, errors = validate_template(data, idx)
            if not is_valid:
                all_valid = False
                title = data.get("title", f"Template {idx}")
                print_error(f"Template {idx} '{title}' has validation errors:")
                for error in errors:
                    print(f"  • {error}")
        
        if not all_valid:
            print_error("\nValidation failed! Fix errors and try again.")
            sys.exit(1)
        
        print_success(f"All {len(templates_data)} templates validated successfully\n")
    
    if args.dry_run:
        print_warning("DRY RUN MODE - No changes will be made\n")
    
    # Create database engine
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Seed templates
    try:
        async with async_session() as session:
            created, updated, skipped = await seed_story_templates(
                session,
                templates_data,
                skip_duplicates=not args.update,
                update_existing=args.update,
                dry_run=args.dry_run,
            )
        
        # Summary
        print_header("Summary")
        if args.dry_run:
            print_info(f"Would create: {created}")
            print_info(f"Would update: {updated}")
            print_info(f"Would skip:   {skipped}")
        else:
            print_success(f"Created: {created}")
            if updated > 0:
                print_success(f"Updated: {updated}")
            if skipped > 0:
                print_warning(f"Skipped: {skipped}")
            print_success("\n✨ Seeding completed successfully!")
    
    except Exception as e:
        print_error(f"Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
