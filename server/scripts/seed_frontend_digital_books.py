r"""Seed digital books from frontend catalog into backend books/genres tables.

Usage (from repo root):
    .venv\Scripts\python server\scripts\seed_frontend_digital_books.py
"""

import asyncio
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select

from app.core.constants import AgeGroup, BookType, Language, Style, Theme
from app.db.session import AsyncSessionLocal
from app.models.book import Book
from app.models.genre import Genre


@dataclass
class FrontendBook:
    title: str
    price: int
    age: str
    pages: int
    style: str
    emoji: str
    rat: float
    rev: int
    desc: str


BOOKS_BY_COLLECTION: dict[str, list[FrontendBook]] = {
    "talecraft": [
        FrontendBook("The Brave Quest", 399, "3-8", 24, "Watercolor", "🏰", 4.9, 189, "A thrilling kingdom adventure where your child defeats the shadow dragon and restores light to the land."),
        FrontendBook("Enchanted Forest", 399, "4-9", 28, "Animation", "🌳", 4.8, 145, "Your child discovers a secret forest where animals talk, trees sing, and magic awaits around every corner."),
        FrontendBook("Space Captain", 449, "5-10", 32, "Pop Art", "🚀", 4.9, 210, "Blast off to save Planet Zoop! Your child commands the starship through asteroid fields and alien encounters."),
        FrontendBook("Ocean Rescue", 399, "3-7", 24, "Watercolor", "🌊", 4.7, 98, "Dive deep with dolphins and sea turtles as your child becomes the hero who saves the coral reef."),
    ],
    "personacolor": [
        FrontendBook("My Magical World", 199, "3-7", 10, "Line Art", "🧚", 4.9, 267, "10 enchanting scenes - castles, dragons, fairies - all featuring your child's face as the main character."),
        FrontendBook("Superhero Me!", 199, "4-9", 10, "Comic", "🦸", 4.8, 198, "Your child becomes a superhero across 10 action-packed scenes. Color your own powers and costume!"),
        FrontendBook("Animal Friends", 199, "2-6", 10, "Cute", "🐾", 4.7, 156, "Your little one surrounded by adorable animals - pandas, kittens, bunnies - in beautiful coloring scenes."),
        FrontendBook("Royal Adventures", 199, "3-8", 10, "Fantasy", "👑", 4.9, 234, "Tiaras, castles, magical gardens - your child as the princess or prince of a fairy tale kingdom."),
    ],
    "skillsprint": [
        FrontendBook("21-Day Drawing Challenge", 149, "5-10", 24, "Activity", "✏️", 4.8, 134, "One drawing mission per day for 21 days. By the end, your child will have a full portfolio!"),
        FrontendBook("21-Day Kindness Challenge", 129, "4-9", 24, "Guided", "💖", 4.9, 189, "Daily kindness missions that build empathy, gratitude and emotional intelligence. With certificate!"),
        FrontendBook("21-Day Science Explorer", 149, "6-12", 24, "Experiment", "🔬", 4.7, 98, "Real experiments with household items. Volcanoes, crystals, slime - one discovery per day!"),
        FrontendBook("21-Day Reading Champion", 129, "5-10", 24, "Tracker", "📚", 4.8, 167, "Build a daily reading habit with fun trackers, book reviews and a champion certificate at the end."),
    ],
    "rootstales": [
        FrontendBook("Tales of Ganesha", 99, "4-8", 12, "Pencil Art", "🐘", 5.0, 345, "Beautifully illustrated stories of Lord Ganesha - wisdom, humor, and divine adventures for young minds."),
        FrontendBook("Hanuman's Great Leap", 129, "5-10", 14, "Pencil Art", "🙏", 4.9, 312, "The epic story of Hanuman's leap across the ocean - courage, devotion, and divine strength."),
        FrontendBook("Krishna's Butter Adventures", 99, "2-6", 10, "Animation", "🧈", 5.0, 389, "Little Krishna's playful butter-stealing adventures - told with love, humor, and vibrant illustrations."),
        FrontendBook("Festivals of India", 129, "4-9", 16, "Watercolor", "🪔", 4.8, 234, "Diwali, Holi, Pongal, Eid, Christmas - the stories behind India's beautiful festivals."),
    ],
    "moneyminds": [
        FrontendBook("My First Piggy Bank", 99, "4-7", 12, "Cartoon", "🐷", 4.7, 145, "Save, spend, share - the three jars that teach kids money basics through fun stories and activities."),
        FrontendBook("Save, Spend & Share", 129, "6-10", 14, "Activity", "💸", 4.8, 112, "Real-world money skills through games, budgets, and smart choices. Financial literacy made fun!"),
        FrontendBook("Lemonade Stand Adventure", 149, "8-12", 18, "Story", "🍋", 4.9, 98, "Start a business from scratch! Costs, pricing, marketing - all through an exciting lemonade stand story."),
        FrontendBook("Money Math Fun", 99, "5-9", 12, "Puzzle", "🧮", 4.6, 87, "Addition, subtraction, fractions - all through money puzzles that make math feel like a game."),
    ],
    "buildbrain": [
        FrontendBook("Kitchen Science", 149, "5-10", 16, "Activity", "🧪", 4.8, 178, "Volcanoes from baking soda, crystals from sugar, rainbows from milk - real experiments, real fun!"),
        FrontendBook("Paper Robot Builder", 129, "7-12", 14, "STEM", "🤖", 4.7, 134, "Build working paper mechanisms - levers, pulleys, gears. Engineering basics through hands-on fun!"),
        FrontendBook("Coding Without Computers", 149, "6-11", 18, "Logic", "💻", 4.9, 167, "Algorithms, loops, debugging - computer science concepts taught through puzzles and board games."),
        FrontendBook("Math Puzzle Mania", 99, "5-9", 12, "Puzzle", "🔢", 4.6, 98, "Sudoku, logic grids, pattern recognition - brain-building math puzzles kids actually enjoy!"),
    ],
    "artvault": [
        FrontendBook("My First Masterpiece", 99, "3-6", 12, "Guided", "🖌️", 4.8, 201, "Step-by-step drawing for tiny artists. Simple shapes become beautiful art. Confidence grows with every page!"),
        FrontendBook("Mandala Magic", 129, "6-12", 16, "Zen", "🔵", 4.9, 178, "Calming mandala patterns that develop focus, patience and creativity. Perfect for quiet afternoon art."),
        FrontendBook("Cartoon Creator", 149, "7-12", 18, "Tutorial", "✍️", 4.7, 145, "Learn to draw your own cartoon characters! Expressions, poses, stories - become a real cartoonist."),
        FrontendBook("Origami Adventures", 129, "5-10", 14, "Craft", "🦢", 4.8, 123, "Fold cranes, frogs, flowers and boats. Step-by-step origami with beautiful illustrated instructions."),
    ],
    "kidsceo": [
        FrontendBook("My First Business Plan", 149, "8-14", 20, "Workbook", "📋", 4.8, 89, "From idea to execution - a real business plan workbook that turns young dreamers into young doers."),
        FrontendBook("The Idea Factory", 129, "7-12", 16, "Creative", "💡", 4.9, 112, "100 business ideas for kids + tools to evaluate them. Creativity meets entrepreneurship!"),
        FrontendBook("Marketing for Mini Moguls", 149, "9-15", 18, "Guide", "📢", 4.7, 78, "Logos, slogans, social media basics - marketing fundamentals through fun, hands-on projects."),
        FrontendBook("Budget Boss Kids", 129, "8-13", 14, "Activity", "📊", 4.8, 98, "Track income, expenses, savings goals. Real budgeting skills through an engaging workbook format."),
    ],
    "lifepath": [
        FrontendBook("Life Skills Board Classic", 199, "5-12", 1, "A3 Board", "🎯", 4.9, 234, "25 squares of life challenges - cooking, cleaning, empathy, budgeting. Roll, land, DO. Family game night essential!"),
        FrontendBook("Money Wisdom Board", 199, "7-14", 1, "A3 Board", "💎", 4.8, 178, "Save, invest, budget, donate - financial wisdom in a fun board game format. Snake eats overspending!"),
        FrontendBook("Friendship Board", 199, "4-10", 1, "A3 Board", "🤝", 4.9, 189, "Empathy, sharing, conflict resolution - social skills through a colorful family board game."),
        FrontendBook("Science Discovery Board", 199, "6-12", 1, "A3 Board", "🔭", 4.7, 145, "Land on a square = do a real science experiment! 25 experiments in one exciting board game."),
    ],
    "lifeready": [
        FrontendBook("Feelings & Emotions", 149, "4-8", 20, "Activity", "💓", 4.9, 234, "Name it, tame it, express it - emotional intelligence workbook that helps children understand their feelings."),
        FrontendBook("Friendship Skills", 129, "5-10", 16, "Guided", "🫂", 4.8, 189, "Making friends, being kind, handling conflicts - the social skills every child needs but school doesn't teach."),
        FrontendBook("My Daily Routine", 99, "4-8", 14, "Tracker", "⏰", 4.7, 167, "Morning routines, bedtime habits, hygiene checklists - building independence one day at a time."),
        FrontendBook("Bounce Back!", 149, "7-13", 18, "Workbook", "💪", 4.9, 198, "Failed a test? Lost a match? This workbook teaches kids that falling down is how you learn to fly."),
    ],
    "mindfulkids": [
        FrontendBook("Breathe & Be Calm", 129, "4-10", 18, "Activity", "🧘", 4.9, 214, "Simple breathing games, body-scan stories and calming rituals that help children settle anxiety and sleep better every night."),
    ],
}


GENRE_BY_COLLECTION = {
    "talecraft": "adventure",
    "personacolor": "comedy",
    "skillsprint": "educational",
    "rootstales": "moral",
    "mindfulkids": "moral",
    "moneyminds": "educational",
    "buildbrain": "educational",
    "artvault": "comedy",
    "kidsceo": "educational",
    "lifepath": "adventure",
    "lifeready": "moral",
}


def normalize_style(style_value: str) -> Style:
    if "animation" in style_value.lower():
        return Style.ANIMATION
    return Style.ILLUSTRATION


def normalize_age_group(age_value: str) -> AgeGroup:
    digits = [int(x) for x in "".join(ch if ch.isdigit() else " " for ch in age_value).split() if x.isdigit()]
    if not digits:
        return AgeGroup.AGE_5_9
    upper = max(digits)
    return AgeGroup.AGE_10_14 if upper >= 10 else AgeGroup.AGE_5_9


def resolve_book_type(collection_id: str) -> BookType:
    if collection_id == "personacolor":
        return BookType.COLORING
    return BookType.STORY


async def get_or_create_genre(session, name: str) -> Genre:
    result = await session.execute(select(Genre).where(Genre.name == name))
    genre = result.scalar_one_or_none()
    if genre:
        return genre
    genre = Genre(name=name)
    session.add(genre)
    await session.flush()
    return genre


async def seed() -> None:
    created = 0
    updated = 0
    deleted = 0

    async with AsyncSessionLocal() as session:
        for collection_id, books in BOOKS_BY_COLLECTION.items():
            if not books:
                continue

            genre_name = GENRE_BY_COLLECTION.get(collection_id, "educational")
            genre = await get_or_create_genre(session, genre_name)
            item = books[0]

            result = await session.execute(
                select(Book).where(
                    Book.collection_id == collection_id,
                    Book.book_name == item.title,
                )
            )
            existing = result.scalar_one_or_none()
            is_bestseller = item.rev >= 180

            if existing:
                existing.description = item.desc
                existing.book_tag = "BESTSELLER" if is_bestseller else None
                existing.emoji = item.emoji
                existing.total_pages = item.pages
                existing.age_label = item.age
                existing.style_label = item.style
                existing.book_type = resolve_book_type(collection_id)
                existing.theme = Theme.HUMAN
                existing.style = normalize_style(item.style)
                existing.age_group = normalize_age_group(item.age)
                existing.language = Language.ENGLISH
                existing.genre_id = genre.id
                existing.price = Decimal(str(item.price))
                existing.rating = float(item.rat)
                existing.total_ratings = int(item.rev)
                existing.is_bestseller = is_bestseller
                keeper_id = existing.id
                updated += 1
            else:
                keeper = Book(
                    book_name=item.title,
                    description=item.desc,
                    book_tag="BESTSELLER" if is_bestseller else None,
                    collection_id=collection_id,
                    emoji=item.emoji,
                    total_pages=item.pages,
                    age_label=item.age,
                    style_label=item.style,
                    book_type=resolve_book_type(collection_id),
                    theme=Theme.HUMAN,
                    style=normalize_style(item.style),
                    age_group=normalize_age_group(item.age),
                    language=Language.ENGLISH,
                    genre_id=genre.id,
                    price=Decimal(str(item.price)),
                    rating=float(item.rat),
                    total_ratings=int(item.rev),
                    download_count=0,
                    is_bestseller=is_bestseller,
                )
                session.add(keeper)
                await session.flush()
                keeper_id = keeper.id
                created += 1

            all_in_collection = await session.execute(
                select(Book).where(Book.collection_id == collection_id)
            )
            extras = [row for row in all_in_collection.scalars().all() if row.id != keeper_id]
            for extra in extras:
                await session.delete(extra)
                deleted += 1

        await session.commit()

    print(f"Seed complete. created={created}, updated={updated}, deleted={deleted}")


if __name__ == "__main__":
    asyncio.run(seed())
