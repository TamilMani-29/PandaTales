"""Check which tables exist in the database"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_tables():
    # Use the database URL from environment or default
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://storybloom_user:storybloom_secret@localhost:5432/storybloom")
    
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """))
        
        tables = result.fetchall()
        
        print("\n=== Tables in database ===")
        for table in tables:
            print(f"  - {table[0]}")
        print(f"\nTotal: {len(tables)} tables\n")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_tables())
