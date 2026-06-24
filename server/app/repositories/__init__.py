"""Data repositories"""

from app.repositories.address import AddressRepository
from app.repositories.coloring_book_template import ColoringBookTemplateRepository
from app.repositories.generated_book import GeneratedBookRepository
from app.repositories.generation_config import GenerationConfigRepository
from app.repositories.story_book_template import StoryBookTemplateRepository
from app.repositories.child_profile import ChildProfileRepository
from app.repositories.user import UserRepository

__all__ = [
    "AddressRepository",
    "ColoringBookTemplateRepository",
    "GeneratedBookRepository",
    "GenerationConfigRepository",
    "StoryBookTemplateRepository",
    "ChildProfileRepository",
    "UserRepository",
]
