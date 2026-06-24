#!/usr/bin/env python3
"""
Auto-seed script for Docker containers

This script is called automatically when the backend container starts.
It seeds story book templates if they don't exist.

Features:
- Only seeds missing templates (incremental)
- Silent mode for clean container logs
- Uses environment variables for DB connection
- Exits cleanly on errors
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.story_book_template import StoryBookTemplate


async def auto_seed():
    """Auto-seed templates on container startup"""
    
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("⚠️  DATABASE_URL not set, skipping auto-seed")
        return 0
    
    # Determine environment
    app_env = os.getenv("APP_ENV", "development")
    
    # Load templates file
    templates_file = Path(__file__).parent.parent / "data" / "story_book_templates.json"
    if not templates_file.exists():
        print(f"⚠️  Templates file not found: {templates_file}, skipping auto-seed")
        return 0
    
    try:
        with open(templates_file, 'r', encoding='utf-8') as f:
            templates_data = json.load(f)
    except Exception as e:
        print(f"⚠️  Error loading templates file: {e}, skipping auto-seed")
        return 0
    
    if not templates_data:
        print("ℹ️  No templates to seed")
        return 0
    
    # Create database engine
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    created = 0
    skipped = 0
    
    try:
        async with async_session() as session:
            for data in templates_data:
                # Get template ID
                template_id = None
                if "id" in data and data["id"]:
                    try:
                        template_id = UUID(data["id"])
                    except (ValueError, TypeError):
                        pass
                
                # Check if exists
                if template_id:
                    existing = await session.get(StoryBookTemplate, template_id)
                    if existing:
                        skipped += 1
                        continue
                
                # Convert series_id if present
                if "series_id" in data and data["series_id"]:
                    try:
                        data["series_id"] = UUID(data["series_id"])
                    except (ValueError, TypeError):
                        data["series_id"] = None
                
                # Create template
                template_dict = {k: v for k, v in data.items() if k != "id"}
                if template_id:
                    template_dict["id"] = template_id
                
                template = StoryBookTemplate(**template_dict)
                session.add(template)
                created += 1
            
            await session.commit()
        
        if created > 0:
            print(f"✅ Auto-seeded {created} story book template(s)")
        if skipped > 0:
            print(f"ℹ️  Skipped {skipped} existing template(s)")
        
        return 0
    
    except Exception as e:
        print(f"⚠️  Error during auto-seed: {e}")
        return 0  # Don't fail container startup
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(auto_seed())
    sys.exit(exit_code)
