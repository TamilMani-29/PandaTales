"""
Comprehensive seed data script for PandaTales.

Populates all tables with consistent, realistic sample data for app testing.

Usage:
    (from server/ directory with venv active)
    python scripts/seed_data.py

    To reset and re-seed:
    python scripts/seed_data.py --reset
"""

import argparse
import asyncio
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models import (
    Address,
    ChildProfile,
    ColoringBookTemplate,
    GeneratedBook,
    GenerationConfig,
    StoryBookTemplate,
    User,
)

settings = get_settings()

# ---------------------------------------------------------------------------
# Fixed UUIDs – keep stable so re-runs are idempotent
# ---------------------------------------------------------------------------

# Users
USER_1_ID = UUID("00000000-0000-0000-0000-000000000001")  # test@pandatales.com
USER_2_ID = UUID("00000000-0000-0000-0000-000000000002")  # jane@example.com

# Child profiles
CHILD_EMMA_ID = UUID("00000000-0000-0000-0001-000000000001")   # Emma, 5f, user1
CHILD_LUCAS_ID = UUID("00000000-0000-0000-0001-000000000002")  # Lucas, 7m, user1
CHILD_SOPHIE_ID = UUID("00000000-0000-0000-0001-000000000003") # Sophie, 4f, user2

# Addresses
ADDR_USER1_ID = UUID("00000000-0000-0000-0002-000000000001")
ADDR_USER2_ID = UUID("00000000-0000-0000-0002-000000000002")

# Story book templates
STORY_TPL_1 = UUID("00000000-0000-0000-0003-000000000001")  # Panda's Magical Forest
STORY_TPL_2 = UUID("00000000-0000-0000-0003-000000000002")  # The Dragon's Secret Kingdom
STORY_TPL_3 = UUID("00000000-0000-0000-0003-000000000003")  # Space Explorer Journey
STORY_TPL_4 = UUID("00000000-0000-0000-0003-000000000004")  # Ocean Kingdom Chronicles (series 1)
STORY_TPL_5 = UUID("00000000-0000-0000-0003-000000000005")  # Ocean Kingdom: The Deep Dive (series 2)
STORY_TPL_6 = UUID("00000000-0000-0000-0003-000000000006")  # Goodnight Little Panda

# Coloring book templates
COLOR_TPL_1 = UUID("00000000-0000-0000-0004-000000000001")  # Magical Animals Coloring
COLOR_TPL_2 = UUID("00000000-0000-0000-0004-000000000002")  # Fantasy Forest Friends
COLOR_TPL_3 = UUID("00000000-0000-0000-0004-000000000003")  # Space & Planets
COLOR_TPL_4 = UUID("00000000-0000-0000-0004-000000000004")  # Baby Animals First Colors

# Generation configs (coloring themes)
CONFIG_TROPICAL = UUID("00000000-0000-0000-0005-000000000001")
CONFIG_FOREST   = UUID("00000000-0000-0000-0005-000000000002")
CONFIG_OCEAN    = UUID("00000000-0000-0000-0005-000000000003")
CONFIG_SPACE    = UUID("00000000-0000-0000-0005-000000000004")

# Generated books
BOOK_1 = UUID("00000000-0000-0000-0006-000000000001")  # Emma – Panda story (completed)
BOOK_2 = UUID("00000000-0000-0000-0006-000000000002")  # Lucas – Animals coloring (purchased)
BOOK_3 = UUID("00000000-0000-0000-0006-000000000003")  # Sophie – Goodnight Panda (completed)
BOOK_4 = UUID("00000000-0000-0000-0006-000000000004")  # Emma – Dragon story (processing)

# Password hash for "test123"
PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7MXvL1pm"

# ---------------------------------------------------------------------------
# Cover / preview image placeholders (Picsum Photos – deterministic by ID)
# ---------------------------------------------------------------------------
def cover(seed: int) -> str:
    return f"https://picsum.photos/seed/pt{seed}/400/500"

def preview(seed: int) -> str:
    return f"https://picsum.photos/seed/ptpv{seed}/800/600"

def page_img(seed: int) -> str:
    return f"https://picsum.photos/seed/ptp{seed}/1200/900"


# ===========================================================================
# Seed functions
# ===========================================================================

async def seed_users(session: AsyncSession) -> None:
    for uid, email, first, last, phone in [
        (USER_1_ID, "test@pandatales.com", "Alex",  "Johnson", "+12025550101"),
        (USER_2_ID, "jane@example.com",    "Jane",  "Parker",  "+14155550199"),
    ]:
        existing = await session.get(User, uid)
        if existing:
            print(f"  ↳ User already exists: {email}")
            continue
        user = User(
            id=uid,
            email=email,
            password_hash=PASSWORD_HASH,
            first_name=first,
            last_name=last,
            phone=phone,
            email_verified=True,
            phone_verified=False,
            role="user",
            last_login_at=datetime.now(timezone.utc),
        )
        session.add(user)
        print(f"  ✅ Created user: {email}  (password: test123)")


async def seed_child_profiles(session: AsyncSession) -> None:
    children = [
        dict(
            id=CHILD_EMMA_ID,
            user_id=USER_1_ID,
            name="Emma",
            age=5,
            gender="female",
            birth_date=date(2020, 3, 15),
            books_created_count=2,
        ),
        dict(
            id=CHILD_LUCAS_ID,
            user_id=USER_1_ID,
            name="Lucas",
            age=7,
            gender="male",
            birth_date=date(2018, 7, 22),
            books_created_count=1,
        ),
        dict(
            id=CHILD_SOPHIE_ID,
            user_id=USER_2_ID,
            name="Sophie",
            age=4,
            gender="female",
            birth_date=date(2021, 11, 5),
            books_created_count=1,
        ),
    ]
    for data in children:
        existing = await session.get(ChildProfile, data["id"])
        if existing:
            print(f"  ↳ Child profile already exists: {data['name']}")
            continue
        session.add(ChildProfile(**data))
        print(f"  ✅ Created child profile: {data['name']}")


async def seed_addresses(session: AsyncSession) -> None:
    addresses = [
        dict(
            id=ADDR_USER1_ID,
            user_id=USER_1_ID,
            first_name="Alex",
            last_name="Johnson",
            address_line1="123 Main Street",
            address_line2="Apt 4B",
            city="Springfield",
            state="Illinois",
            postal_code="62701",
            country="US",
            phone="+12025550101",
            is_default=True,
        ),
        dict(
            id=ADDR_USER2_ID,
            user_id=USER_2_ID,
            first_name="Jane",
            last_name="Parker",
            address_line1="456 Oak Avenue",
            city="Austin",
            state="Texas",
            postal_code="78701",
            country="US",
            phone="+14155550199",
            is_default=True,
        ),
    ]
    for data in addresses:
        existing = await session.get(Address, data["id"])
        if existing:
            print(f"  ↳ Address already exists for user {data['user_id']}")
            continue
        session.add(Address(**data))
        print(f"  ✅ Created address: {data['address_line1']}, {data['city']}")


async def seed_story_templates(session: AsyncSession) -> None:
    templates = [
        dict(
            id=STORY_TPL_1,
            title="Panda's Magical Forest Adventure",
            description="Join Bao the panda on a whimsical journey through an enchanted forest filled with friendly creatures and hidden treasures.",
            long_description="In this delightful story, young readers follow Bao the personalized panda as they explore a magical forest, make new friends, and learn the value of kindness and sharing. Each page features vibrant illustrations and your child's name woven seamlessly into the narrative.",
            book_type="single",
            genre="adventure",
            age_group="3-5",
            story_theme="friendship and kindness",
            moral_lesson="True friendship means helping others and sharing what you have.",
            reading_level="beginner",
            price=14.99,
            cover_image_url=cover(1),
            preview_images=[preview(10), preview(11), preview(12)],
            total_pages=24,
            features=[
                "Personalized with your child's name",
                "Vibrant full-color illustrations",
                "Age-appropriate vocabulary",
                "Interactive story elements",
            ],
            learning_outcomes=[
                "Develops early reading skills",
                "Teaches empathy and kindness",
                "Encourages imagination",
            ],
            chapters=[
                {"number": 1, "title": "The Bamboo Path", "pages": "1-8"},
                {"number": 2, "title": "A New Friend",    "pages": "9-16"},
                {"number": 3, "title": "The Hidden Treasure", "pages": "17-24"},
            ],
            customization_options={"child_name": True, "child_age": True, "dedication": True},
            tags=["panda", "adventure", "forest", "friendship", "animals"],
            is_published=True,
        ),
        dict(
            id=STORY_TPL_2,
            title="The Dragon's Secret Kingdom",
            description="A young brave hero discovers a hidden kingdom ruled by a friendly dragon and must solve ancient puzzles to save it.",
            long_description="This exciting adventure story takes your child through mysterious caves and soaring mountains. Personalized with their name as the hero, children learn about bravery, problem-solving, and the power of believing in yourself.",
            book_type="single",
            genre="fantasy",
            age_group="6-8",
            story_theme="bravery and problem-solving",
            moral_lesson="Courage means facing your fears even when it's difficult.",
            reading_level="intermediate",
            price=16.99,
            cover_image_url=cover(2),
            preview_images=[preview(20), preview(21), preview(22)],
            total_pages=32,
            features=[
                "Personalized hero with your child's name",
                "Puzzle pages throughout the story",
                "Dragon companion character",
                "Map illustration of the Kingdom",
            ],
            learning_outcomes=[
                "Builds reading comprehension",
                "Promotes critical thinking",
                "Encourages bravery and resilience",
            ],
            chapters=[
                {"number": 1, "title": "The Hidden Cave",   "pages": "1-8"},
                {"number": 2, "title": "The Dragon's Plea",  "pages": "9-16"},
                {"number": 3, "title": "Ancient Puzzles",   "pages": "17-24"},
                {"number": 4, "title": "The Kingdom Saved", "pages": "25-32"},
            ],
            customization_options={"child_name": True, "child_gender": True, "dedication": True},
            tags=["dragon", "fantasy", "kingdom", "puzzles", "adventure", "bravery"],
            is_published=True,
        ),
        dict(
            id=STORY_TPL_3,
            title="Space Explorer Journey",
            description="Blast off with your child as they pilot their very own rocket ship on a mission to discover new planets and meet alien friends.",
            long_description="An out-of-this-world personalized adventure where your child becomes a real astronaut. They'll travel through colorful galaxies, land on strange planets, and make friends with lovable aliens before returning home as a true space hero.",
            book_type="single",
            genre="science-fiction",
            age_group="6-8",
            story_theme="curiosity and discovery",
            moral_lesson="Exploring new things helps us learn and grow.",
            reading_level="intermediate",
            price=15.99,
            cover_image_url=cover(3),
            preview_images=[preview(30), preview(31), preview(32)],
            total_pages=28,
            features=[
                "Child is the astronaut hero",
                "Educational facts about planets",
                "Alien character designs",
                "Mission log page",
            ],
            learning_outcomes=[
                "Sparks interest in science and space",
                "Teaches curiosity and open-mindedness",
                "Introduces basic astronomy concepts",
            ],
            chapters=[
                {"number": 1, "title": "Countdown to Launch",  "pages": "1-7"},
                {"number": 2, "title": "Planet Zara",          "pages": "8-14"},
                {"number": 3, "title": "The Alien Village",    "pages": "15-21"},
                {"number": 4, "title": "Back to Earth",        "pages": "22-28"},
            ],
            customization_options={"child_name": True, "child_age": True, "dedication": True},
            tags=["space", "astronaut", "planets", "science", "adventure", "aliens"],
            is_published=True,
        ),
        dict(
            id=STORY_TPL_4,
            title="Ocean Kingdom Chronicles",
            description="Dive deep into the Ocean Kingdom where an unlikely hero discovers they hold the key to saving an underwater civilization.",
            long_description="Book 1 of the Ocean Kingdom Chronicles series. Your child's personalized character discovers a glowing pearl that grants them the ability to breathe underwater, leading them into a magnificent world of merfolk, giant sea creatures, and ancient coral ruins.",
            book_type="series",
            series_id=STORY_TPL_4,
            book_number=1,
            genre="fantasy",
            age_group="9-12",
            story_theme="responsibility and leadership",
            moral_lesson="With great ability comes the responsibility to use it wisely.",
            reading_level="advanced",
            price=18.99,
            cover_image_url=cover(4),
            preview_images=[preview(40), preview(41), preview(42)],
            total_pages=48,
            features=[
                "First in a 3-book series",
                "Richly detailed world-building",
                "Multiple named characters",
                "Chapter illustrations",
                "Glossary of ocean terms",
            ],
            learning_outcomes=[
                "Develops advanced reading fluency",
                "Teaches leadership and responsibility",
                "Introduces marine biology concepts",
            ],
            chapters=[
                {"number": 1, "title": "The Glowing Pearl",     "pages": "1-12"},
                {"number": 2, "title": "Beneath the Surface",   "pages": "13-24"},
                {"number": 3, "title": "The Coral City",        "pages": "25-36"},
                {"number": 4, "title": "The Ancient Prophecy",  "pages": "37-48"},
            ],
            customization_options={"child_name": True, "child_gender": True, "dedication": True, "friend_name": True},
            tags=["ocean", "underwater", "merfolk", "fantasy", "series", "adventure"],
            is_published=True,
        ),
        dict(
            id=STORY_TPL_5,
            title="Ocean Kingdom Chronicles: The Deep Dive",
            description="Return to the Ocean Kingdom as our hero ventures into the darkest trenches to uncover the truth about an ancient sea monster.",
            long_description="Book 2 of the Ocean Kingdom Chronicles. Picking up where the first book ended, your child's character must gather courage and allies to descend into the Midnight Trench, where an ancient creature holds a prophecy that could change the Ocean Kingdom forever.",
            book_type="series",
            series_id=STORY_TPL_4,  # Self-referencing series group
            book_number=2,
            genre="fantasy",
            age_group="9-12",
            story_theme="courage under pressure",
            moral_lesson="True bravery is helping others even when you are afraid.",
            reading_level="advanced",
            price=18.99,
            cover_image_url=cover(5),
            preview_images=[preview(50), preview(51), preview(52)],
            total_pages=52,
            features=[
                "Second in the 3-book series",
                "Continues from Book 1 characters",
                "New deep-sea creature illustrations",
                "Bonus activity pages",
            ],
            learning_outcomes=[
                "Reinforces advanced reading skills",
                "Explores themes of courage and trust",
                "Builds on science of deep-sea environments",
            ],
            chapters=[
                {"number": 1, "title": "Old Friends, New Troubles", "pages": "1-13"},
                {"number": 2, "title": "Into the Midnight Trench",  "pages": "14-26"},
                {"number": 3, "title": "The Ancient Leviathan",     "pages": "27-39"},
                {"number": 4, "title": "A Kingdom United",          "pages": "40-52"},
            ],
            customization_options={"child_name": True, "child_gender": True, "dedication": True, "friend_name": True},
            tags=["ocean", "underwater", "sea-monster", "fantasy", "series", "adventure"],
            is_published=True,
        ),
        dict(
            id=STORY_TPL_6,
            title="Goodnight, Little Panda",
            description="A soothing bedtime story where a little panda says goodnight to all its forest friends before drifting off to dreamland.",
            long_description="This gentle, rhyming bedtime story features beautiful watercolor-style illustrations and your baby's name throughout. Perfect for establishing a calming bedtime routine, the story follows a sleepy panda saying the sweetest goodnights.",
            book_type="single",
            genre="bedtime",
            age_group="0-2",
            story_theme="sleep and comfort",
            moral_lesson="A good day deserves a peaceful night's rest.",
            reading_level="beginner",
            price=12.99,
            cover_image_url=cover(6),
            preview_images=[preview(60), preview(61)],
            total_pages=16,
            features=[
                "Simple rhyming text",
                "Watercolor-style illustrations",
                "Personalized with baby's name",
                "Soft, calming color palette",
            ],
            learning_outcomes=[
                "Supports early language development",
                "Creates positive bedtime associations",
                "Encourages parent-child bonding",
            ],
            chapters=[
                {"number": 1, "title": "Goodnight Forest", "pages": "1-8"},
                {"number": 2, "title": "Sweet Dreams",     "pages": "9-16"},
            ],
            customization_options={"child_name": True, "dedication": True},
            tags=["bedtime", "panda", "baby", "rhyme", "sleep", "toddler"],
            is_published=True,
        ),
    ]

    for data in templates:
        existing = await session.get(StoryBookTemplate, data["id"])
        if existing:
            print(f"  ↳ Story template already exists: {data['title']}")
            continue
        session.add(StoryBookTemplate(**data))
        print(f"  ✅ Created story template: {data['title']}")


async def seed_coloring_templates(session: AsyncSession) -> None:
    templates = [
        dict(
            id=COLOR_TPL_1,
            title="Magical Animals Coloring Adventure",
            description="A coloring book filled with adorable cartoon animals in enchanted settings, perfect for young artists.",
            long_description="This 24-page coloring book features cute cartoon animals — pandas, foxes, rabbits, and owls — each set in magical scenes like rainbow meadows, mushroom villages, and starlit forests. Simple outlines are perfect for little hands learning to color.",
            theme="animals",
            age_group="3-5",
            price=9.99,
            cover_image_url=cover(7),
            preview_images=[preview(70), preview(71), preview(72)],
            sample_pages=[page_img(71), page_img(72), page_img(73)],
            total_pages=24,
            page_types=[
                "Single character scenes",
                "Animal families",
                "Nature backgrounds",
                "Simple patterns",
            ],
            customization_options={"child_name_on_cover": True},
            tags=["animals", "cartoon", "simple", "cute", "beginner-friendly"],
            is_published=True,
        ),
        dict(
            id=COLOR_TPL_2,
            title="Fantasy Forest Friends",
            description="Detailed illustrations of forest creatures, fairy doors, and magical plants for children who love to color for hours.",
            long_description="Thirty beautifully detailed pages featuring unicorns, dragons, fairies, and woodland creatures. Each scene is set in an elaborate fantasy forest with intricate backgrounds that challenge and delight young colorists who are ready for something more complex.",
            theme="nature",
            age_group="6-8",
            price=11.99,
            cover_image_url=cover(8),
            preview_images=[preview(80), preview(81), preview(82)],
            sample_pages=[page_img(81), page_img(82), page_img(83)],
            total_pages=30,
            page_types=[
                "Full-page scenes",
                "Character portraits",
                "Pattern borders",
                "Double-page spreads",
            ],
            customization_options={"child_name_on_cover": True, "dedication_page": True},
            tags=["fantasy", "forest", "detailed", "fairies", "unicorns", "dragons"],
            is_published=True,
        ),
        dict(
            id=COLOR_TPL_3,
            title="Space & Planets Coloring Book",
            description="Explore the cosmos through detailed line art of rockets, astronauts, alien worlds, and breathtaking nebulae.",
            long_description="Twenty-eight pages of galactic coloring fun! From a personalized astronaut character to exotic alien landscapes and swirling galaxies, this coloring book doubles as an educational journey through our solar system and beyond. Each page includes a fun space fact.",
            theme="space",
            age_group="9-12",
            price=12.99,
            cover_image_url=cover(9),
            preview_images=[preview(90), preview(91), preview(92)],
            sample_pages=[page_img(91), page_img(92), page_img(93)],
            total_pages=28,
            page_types=[
                "Full-page planetary scenes",
                "Spaceship blueprints",
                "Alien character pages",
                "Galaxy mandalas",
                "Astronaut portraits",
            ],
            customization_options={"child_name_on_cover": True, "astronaut_name": True},
            tags=["space", "planets", "astronaut", "sci-fi", "educational", "detailed"],
            is_published=True,
        ),
        dict(
            id=COLOR_TPL_4,
            title="Baby Animals First Colors",
            description="Large, bold outlines of beloved baby animals for the very youngest artists to fill with their favorite colors.",
            long_description="Twelve extra-large coloring pages featuring baby pandas, ducklings, puppies, kittens, and more. The thick black outlines and generous spaces are perfectly sized for toddler hands, making this an ideal first coloring book experience.",
            theme="animals",
            age_group="0-2",
            price=7.99,
            cover_image_url=cover(10),
            preview_images=[preview(100), preview(101)],
            sample_pages=[page_img(101), page_img(102)],
            total_pages=12,
            page_types=[
                "Single large animal per page",
                "Extra-thick outlines",
                "Minimal background detail",
            ],
            customization_options={"child_name_on_cover": True},
            tags=["baby", "animals", "simple", "toddler", "first-coloring", "large-outlines"],
            is_published=True,
        ),
    ]

    for data in templates:
        existing = await session.get(ColoringBookTemplate, data["id"])
        if existing:
            print(f"  ↳ Coloring template already exists: {data['title']}")
            continue
        session.add(ColoringBookTemplate(**data))
        print(f"  ✅ Created coloring template: {data['title']}")


async def seed_generation_configs(session: AsyncSession) -> None:
    configs = [
        dict(
            id=CONFIG_TROPICAL,
            config_type="theme",
            name="tropical_animals",
            display_name="Tropical Animals",
            description="Vibrant jungle and tropical animals including parrots, monkeys, toucans, and exotic flowers.",
            icon_url="https://picsum.photos/seed/icon1/64/64",
            preview_image_url=cover(11),
            config_data={
                "base_prompt": "Create a coloring page featuring {theme_description} in a tropical jungle setting with vibrant foliage",
                "style_parameters": {"line_weight": "medium", "detail_level": "medium", "background": "tropical"},
                "sample_keywords": ["parrot", "monkey", "toucan", "tropical flowers", "palm trees"],
            },
            category="nature",
            tags=["tropical", "jungle", "animals", "colorful"],
            applies_to="coloring_book",
            max_photos=20,
            min_photos=1,
            is_active=True,
            is_premium=False,
            is_default=False,
            sort_order=1,
            usage_count=42,
        ),
        dict(
            id=CONFIG_FOREST,
            config_type="theme",
            name="enchanted_forest",
            display_name="Enchanted Forest",
            description="Mystical woodland creatures and magical plants in an enchanted forest setting.",
            icon_url="https://picsum.photos/seed/icon2/64/64",
            preview_image_url=cover(12),
            config_data={
                "base_prompt": "Create a coloring page featuring {theme_description} in a magical enchanted forest with glowing mushrooms and fairy lights",
                "style_parameters": {"line_weight": "fine", "detail_level": "high", "background": "forest"},
                "sample_keywords": ["deer", "fox", "owl", "mushrooms", "fairy", "ancient tree"],
            },
            category="fantasy",
            tags=["forest", "fantasy", "magical", "woodland"],
            applies_to="coloring_book",
            max_photos=20,
            min_photos=1,
            is_active=True,
            is_premium=False,
            is_default=True,
            sort_order=2,
            usage_count=89,
        ),
        dict(
            id=CONFIG_OCEAN,
            config_type="theme",
            name="ocean_adventure",
            display_name="Ocean Adventure",
            description="Underwater scenes with dolphins, sea turtles, colorful fish, and coral reefs.",
            icon_url="https://picsum.photos/seed/icon3/64/64",
            preview_image_url=cover(13),
            config_data={
                "base_prompt": "Create a coloring page featuring {theme_description} in an underwater ocean setting with coral reefs and colorful fish",
                "style_parameters": {"line_weight": "medium", "detail_level": "medium", "background": "ocean"},
                "sample_keywords": ["dolphin", "seahorse", "sea turtle", "coral", "jellyfish", "tropical fish"],
            },
            category="nature",
            tags=["ocean", "underwater", "sea", "animals"],
            applies_to="coloring_book",
            max_photos=20,
            min_photos=1,
            is_active=True,
            is_premium=False,
            is_default=False,
            sort_order=3,
            usage_count=67,
        ),
        dict(
            id=CONFIG_SPACE,
            config_type="theme",
            name="space_explorer",
            display_name="Space Explorer",
            description="Rockets, astronauts, planets, and alien creatures in an outer-space adventure.",
            icon_url="https://picsum.photos/seed/icon4/64/64",
            preview_image_url=cover(14),
            config_data={
                "base_prompt": "Create a coloring page featuring {theme_description} in an outer space setting with stars, planets, and rockets",
                "style_parameters": {"line_weight": "medium", "detail_level": "high", "background": "space"},
                "sample_keywords": ["rocket", "astronaut", "planet", "alien", "stars", "moon", "galaxy"],
            },
            category="science-fiction",
            tags=["space", "planets", "astronaut", "sci-fi", "premium"],
            applies_to="coloring_book",
            max_photos=20,
            min_photos=1,
            is_active=True,
            is_premium=True,
            is_default=False,
            sort_order=4,
            usage_count=35,
        ),
    ]

    for data in configs:
        existing = await session.get(GenerationConfig, data["id"])
        if existing:
            print(f"  ↳ GenerationConfig already exists: {data['display_name']}")
            continue
        session.add(GenerationConfig(**data))
        print(f"  ✅ Created GenerationConfig: {data['display_name']}")


async def seed_generated_books(session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)

    books = [
        # ── Book 1: Emma's story book, completed (not yet purchased) ──────────
        dict(
            id=BOOK_1,
            user_id=USER_1_ID,
            template_type="story_book",
            template_id=STORY_TPL_1,
            generation_type=None,
            theme_config_id=None,
            selected_theme_name=None,
            child_id=CHILD_EMMA_ID,
            child_name="Emma",
            child_age=5,
            child_gender="female",
            status="completed",
            progress=100,
            current_step="complete",
            queue_position=None,
            estimated_completion_time=None,
            generation_steps={
                "upload": {"status": "done", "duration_s": 2},
                "generate_cover": {"status": "done", "duration_s": 18},
                "generate_pages": {"status": "done", "duration_s": 120},
                "assemble_pdf": {"status": "done", "duration_s": 8},
            },
            photos=[
                "https://picsum.photos/seed/emma1/300/300",
                "https://picsum.photos/seed/emma2/300/300",
            ],
            cover_image_url=cover(1),
            total_pages=24,
            preview_pages=[
                {
                    "page_number": 1,
                    "image_url": page_img(1),
                    "thumbnail_url": f"https://picsum.photos/seed/ptp1t/200/150",
                    "text_content": "Once upon a time, in the heart of the Bamboo Forest, there lived a little panda named Emma.",
                    "is_preview": True,
                    "is_blurred": False,
                },
                {
                    "page_number": 2,
                    "image_url": page_img(2),
                    "thumbnail_url": f"https://picsum.photos/seed/ptp2t/200/150",
                    "text_content": "Emma loved exploring every path in the forest, collecting shiny pebbles and bright flowers.",
                    "is_preview": True,
                    "is_blurred": False,
                },
                {
                    "page_number": 3,
                    "image_url": page_img(3),
                    "thumbnail_url": f"https://picsum.photos/seed/ptp3t/200/150",
                    "text_content": "One morning she found a golden acorn that glowed with a mysterious light…",
                    "is_preview": False,
                    "is_blurred": True,
                },
            ],
            is_purchased=False,
            purchased_at=None,
            generation_duration=148,
            completed_at=datetime(2026, 3, 10, 14, 30, 0, tzinfo=timezone.utc),
            failed_at=None,
            parent_email="test@pandatales.com",
        ),
        # ── Book 2: Lucas's coloring book, completed AND purchased ────────────
        dict(
            id=BOOK_2,
            user_id=USER_1_ID,
            template_type="coloring_book",
            template_id=COLOR_TPL_1,
            generation_type="theme_based",
            theme_config_id=CONFIG_FOREST,
            selected_theme_name="Enchanted Forest",
            child_id=CHILD_LUCAS_ID,
            child_name="Lucas",
            child_age=7,
            child_gender="male",
            status="completed",
            progress=100,
            current_step="complete",
            queue_position=None,
            estimated_completion_time=None,
            generation_steps={
                "upload": {"status": "done", "duration_s": 1},
                "generate_pages": {"status": "done", "duration_s": 95},
                "assemble_pdf": {"status": "done", "duration_s": 6},
            },
            photos=[
                "https://picsum.photos/seed/lucas1/300/300",
            ],
            cover_image_url=cover(8),
            total_pages=24,
            preview_pages=[
                {
                    "page_number": 1,
                    "image_url": page_img(20),
                    "thumbnail_url": f"https://picsum.photos/seed/ptp20t/200/150",
                    "text_content": None,
                    "is_preview": True,
                    "is_blurred": False,
                },
                {
                    "page_number": 2,
                    "image_url": page_img(21),
                    "thumbnail_url": f"https://picsum.photos/seed/ptp21t/200/150",
                    "text_content": None,
                    "is_preview": True,
                    "is_blurred": False,
                },
                {
                    "page_number": 3,
                    "image_url": page_img(22),
                    "thumbnail_url": f"https://picsum.photos/seed/ptp22t/200/150",
                    "text_content": None,
                    "is_preview": False,
                    "is_blurred": True,
                },
            ],
            is_purchased=True,
            purchased_at=datetime(2026, 3, 11, 9, 15, 0, tzinfo=timezone.utc),
            generation_duration=102,
            completed_at=datetime(2026, 3, 11, 9, 0, 0, tzinfo=timezone.utc),
            failed_at=None,
            parent_email="test@pandatales.com",
        ),
        # ── Book 3: Sophie's bedtime story, completed (not purchased) ─────────
        dict(
            id=BOOK_3,
            user_id=USER_2_ID,
            template_type="story_book",
            template_id=STORY_TPL_6,
            generation_type=None,
            theme_config_id=None,
            selected_theme_name=None,
            child_id=CHILD_SOPHIE_ID,
            child_name="Sophie",
            child_age=4,
            child_gender="female",
            status="completed",
            progress=100,
            current_step="complete",
            queue_position=None,
            estimated_completion_time=None,
            generation_steps={
                "upload": {"status": "done", "duration_s": 1},
                "generate_cover": {"status": "done", "duration_s": 14},
                "generate_pages": {"status": "done", "duration_s": 85},
                "assemble_pdf": {"status": "done", "duration_s": 5},
            },
            photos=[
                "https://picsum.photos/seed/sophie1/300/300",
            ],
            cover_image_url=cover(6),
            total_pages=16,
            preview_pages=[
                {
                    "page_number": 1,
                    "image_url": page_img(30),
                    "thumbnail_url": f"https://picsum.photos/seed/ptp30t/200/150",
                    "text_content": "The moon rose high above the bamboo forest, and little Sophie the panda yawned a big, fluffy yawn.",
                    "is_preview": True,
                    "is_blurred": False,
                },
                {
                    "page_number": 2,
                    "image_url": page_img(31),
                    "thumbnail_url": f"https://picsum.photos/seed/ptp31t/200/150",
                    "text_content": "\"Goodnight, fireflies,\" said Sophie, watching their soft glow blink through the leaves.",
                    "is_preview": True,
                    "is_blurred": False,
                },
                {
                    "page_number": 3,
                    "image_url": page_img(32),
                    "thumbnail_url": f"https://picsum.photos/seed/ptp32t/200/150",
                    "text_content": "\"Goodnight, river,\" she whispered as the water sang its quiet lullaby…",
                    "is_preview": False,
                    "is_blurred": True,
                },
            ],
            is_purchased=False,
            purchased_at=None,
            generation_duration=105,
            completed_at=datetime(2026, 3, 12, 20, 45, 0, tzinfo=timezone.utc),
            failed_at=None,
            parent_email="jane@example.com",
        ),
        # ── Book 4: Emma's dragon story, currently processing ─────────────────
        dict(
            id=BOOK_4,
            user_id=USER_1_ID,
            template_type="story_book",
            template_id=STORY_TPL_2,
            generation_type=None,
            theme_config_id=None,
            selected_theme_name=None,
            child_id=CHILD_EMMA_ID,
            child_name="Emma",
            child_age=5,
            child_gender="female",
            status="processing",
            progress=45,
            current_step="Generating story pages (page 11 of 32)…",
            queue_position=None,
            estimated_completion_time=90,
            generation_steps={
                "upload": {"status": "done", "duration_s": 2},
                "generate_cover": {"status": "done", "duration_s": 20},
                "generate_pages": {"status": "in_progress", "current_page": 11, "total_pages": 32},
                "assemble_pdf": {"status": "pending"},
            },
            photos=[
                "https://picsum.photos/seed/emma3/300/300",
            ],
            cover_image_url=cover(2),
            total_pages=None,
            preview_pages=None,
            is_purchased=False,
            purchased_at=None,
            generation_duration=None,
            completed_at=None,
            failed_at=None,
            parent_email="test@pandatales.com",
        ),
    ]

    for data in books:
        existing = await session.get(GeneratedBook, data["id"])
        if existing:
            print(f"  ↳ GeneratedBook already exists: {data['child_name']} – {data['template_id']}")
            continue
        session.add(GeneratedBook(**data))
        print(f"  ✅ Created GeneratedBook: {data['child_name']} / {data['template_type']} / status={data['status']}")


# ===========================================================================
# Reset helper
# ===========================================================================

async def reset_seed_data(session: AsyncSession) -> None:
    """Remove only the rows inserted by this script (keyed by fixed UUIDs)."""
    print("\n🗑️  Resetting seed data…")

    book_ids = [BOOK_1, BOOK_2, BOOK_3, BOOK_4]
    await session.execute(delete(GeneratedBook).where(GeneratedBook.id.in_(book_ids)))

    config_ids = [CONFIG_TROPICAL, CONFIG_FOREST, CONFIG_OCEAN, CONFIG_SPACE]
    await session.execute(delete(GenerationConfig).where(GenerationConfig.id.in_(config_ids)))

    color_ids = [COLOR_TPL_1, COLOR_TPL_2, COLOR_TPL_3, COLOR_TPL_4]
    await session.execute(delete(ColoringBookTemplate).where(ColoringBookTemplate.id.in_(color_ids)))

    story_ids = [STORY_TPL_1, STORY_TPL_2, STORY_TPL_3, STORY_TPL_4, STORY_TPL_5, STORY_TPL_6]
    await session.execute(delete(StoryBookTemplate).where(StoryBookTemplate.id.in_(story_ids)))

    addr_ids = [ADDR_USER1_ID, ADDR_USER2_ID]
    await session.execute(delete(Address).where(Address.id.in_(addr_ids)))

    child_ids = [CHILD_EMMA_ID, CHILD_LUCAS_ID, CHILD_SOPHIE_ID]
    await session.execute(delete(ChildProfile).where(ChildProfile.id.in_(child_ids)))

    user_ids = [USER_1_ID, USER_2_ID]
    await session.execute(delete(User).where(User.id.in_(user_ids)))

    await session.commit()
    print("✅ Seed data reset complete.\n")


# ===========================================================================
# Main
# ===========================================================================

async def run(reset: bool = False) -> None:
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        if reset:
            await reset_seed_data(session)

        print("\n👤 Seeding users…")
        await seed_users(session)
        await session.commit()

        print("\n👶 Seeding child profiles…")
        await seed_child_profiles(session)
        await session.commit()

        print("\n📬 Seeding addresses…")
        await seed_addresses(session)
        await session.commit()

        print("\n📖 Seeding story book templates…")
        await seed_story_templates(session)
        await session.commit()

        print("\n🎨 Seeding coloring book templates…")
        await seed_coloring_templates(session)
        await session.commit()

        print("\n⚙️  Seeding generation configs (themes)…")
        await seed_generation_configs(session)
        await session.commit()

        print("\n📚 Seeding generated books…")
        await seed_generated_books(session)
        await session.commit()

    await engine.dispose()
    print("\n✨ All seed data inserted successfully!\n")
    print("=" * 60)
    print("Test credentials")
    print("=" * 60)
    print("  Email:    test@pandatales.com   (Alex Johnson)")
    print("  Email:    jane@example.com      (Jane Parker)")
    print("  Password: test123  (both accounts)")
    print()
    print("Generated books")
    print("-" * 60)
    print(f"  BOOK_1  {BOOK_1}  – Emma / story / completed")
    print(f"  BOOK_2  {BOOK_2}  – Lucas / coloring / purchased")
    print(f"  BOOK_3  {BOOK_3}  – Sophie / story / completed")
    print(f"  BOOK_4  {BOOK_4}  – Emma / story / processing")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed PandaTales database with sample data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing seed rows before inserting fresh data",
    )
    args = parser.parse_args()

    print("🌱 Starting PandaTales seed data…")
    asyncio.run(run(reset=args.reset))
