"""Drop all tables and reset migrations to start fresh"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def reset_database():
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://storybloom_user:storybloom_secret@localhost:5432/storybloom")
    
    print(f"Connecting to database...")
    engine = create_async_engine(database_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Drop all tables in cascade mode
            print("\nDropping all tables...")
            await conn.execute(text("""
                DROP SCHEMA public CASCADE;
                CREATE SCHEMA public;
                GRANT ALL ON SCHEMA public TO public;
            """))
            
            print("✓ All tables dropped successfully!")
            print("\nNow run: alembic upgrade head")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    response = input("This will DROP ALL TABLES in the database. Are you sure? (yes/no): ")
    if response.lower() == 'yes':
        asyncio.run(reset_database())
    else:
        print("Operation cancelled.")
