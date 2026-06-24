r"""Seed frontend collection cards into book_categories table.

Usage (from server/ directory):
    python scripts/seed_frontend_categories.py
"""

import asyncio
from dataclasses import dataclass

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.book_category import BookCategory


@dataclass
class FrontendCategory:
    collection_id: str
    name: str
    tag: str
    emoji: str
    color: str
    grad: str
    description: str
    personalized: bool = False


CATEGORIES: list[FrontendCategory] = [
    FrontendCategory("talecraft", "TaleCraft", "Personalised Story Books", "📖", "#FF6B6B", "linear-gradient(135deg,#FF6B6B,#EE5A24)", "Your child's name, world & imagination woven into a stunning illustrated storybook. Every book is uniquely theirs - a gift treasured forever.", True),
    FrontendCategory("personacolor", "PersonaColor", "Personalised Coloring Books with Your Photo", "🎨", "#A29BFE", "linear-gradient(135deg,#A29BFE,#6C5CE7)", "Upload your child's photo - we turn it into beautiful coloring art pages. Pick a magical theme & get a one-of-a-kind coloring book made just for them.", True),
    FrontendCategory("skillsprint", "SkillSprint", "21-Day Challenge Books", "⚡", "#FFB830", "linear-gradient(135deg,#FFB830,#E67E22)", "21-day workbooks. One skill, daily missions, epic certificate at the end. Kids actually finish these - and beg for more."),
    FrontendCategory("rootstales", "RootsTales", "Indian Heritage Story Books", "🪔", "#E17055", "linear-gradient(135deg,#E17055,#D63031)", "Ancient stories, festivals & heroes of India retold for today's global kids. Beautiful modern illustrations, timeless wisdom."),
    FrontendCategory("moneyminds", "MoneyMinds", "Financial Literacy for Kids", "💰", "#00B894", "linear-gradient(135deg,#00B894,#00CEC9)", "The most important subject schools don't teach - money. Real financial skills through stories, games, and activities kids aged 5-15 love."),
    FrontendCategory("buildbrain", "BuildBrain", "STEM Activity Books", "🧠", "#0984E3", "linear-gradient(135deg,#0984E3,#74B9FF)", "Hands-on science, coding & engineering activity books with real experiments kids can do at home. No special equipment needed."),
    FrontendCategory("artvault", "ArtVault", "Art & Creativity Books", "🚀", "#E84393", "linear-gradient(135deg,#E84393,#FD79A8)", "From first doodles to gallery-worthy masterpieces - structured art books that grow creativity, confidence and joy."),
    FrontendCategory("kidsceo", "KidsCEO", "Young Entrepreneur Workbooks", "👔", "#FDCB6E", "linear-gradient(135deg,#FDCB6E,#F39C12)", "12-week workbooks that teach kids to think like entrepreneurs. Business plans, budgets & real projects from day one."),
    FrontendCategory("lifepath", "LifePath Board", "A3 Life-Skills Snake & Ladder Cards", "🎲", "#00CEC9", "linear-gradient(135deg,#00CEC9,#81ECEC)", "Giant A3 printed game card - 25 squares of life skills, money wisdom, challenges & fun. Roll the dice, land on a square, DO the challenge!"),
    FrontendCategory("lifeready", "LifeReady", "Real-Life Skills Schools Never Teach", "🌟", "#6C5CE7", "linear-gradient(135deg,#6C5CE7,#A29BFE)", "From tying shoes to managing emotions, making friends to handling failure - practical, emotional and social skills that shape who they become."),
    FrontendCategory("mindfulkids", "MindfulKids", "Calm, Focus & Well-Being for Children", "🧘", "#26C6DA", "linear-gradient(135deg,#26C6DA,#00838F)", "Breathing exercises, mindfulness activities and calming stories that help children manage anxiety, build focus and sleep better every night."),
]


async def seed_categories() -> None:
    created = 0
    updated = 0

    async with AsyncSessionLocal() as session:
        for item in CATEGORIES:
            result = await session.execute(
                select(BookCategory).where(BookCategory.collection_id == item.collection_id)
            )
            row = result.scalar_one_or_none()

            if row:
                row.name = item.name
                row.tag = item.tag
                row.description = item.description
                row.emoji = item.emoji
                row.color = item.color
                row.grad = item.grad
                row.personalized = item.personalized
                row.is_active = True
                updated += 1
            else:
                session.add(
                    BookCategory(
                        collection_id=item.collection_id,
                        name=item.name,
                        tag=item.tag,
                        description=item.description,
                        emoji=item.emoji,
                        color=item.color,
                        grad=item.grad,
                        personalized=item.personalized,
                        is_active=True,
                    )
                )
                created += 1

        await session.commit()

    print(f"Category seed complete. created={created}, updated={updated}")


if __name__ == "__main__":
    asyncio.run(seed_categories())
