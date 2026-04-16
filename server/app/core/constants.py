"""Domain constants and fixed enum values for catalog books."""

from enum import StrEnum


class BookType(StrEnum):
    STORY = "story"
    COLORING = "coloring"


class Theme(StrEnum):
    HUMAN = "human"


class Style(StrEnum):
    ANIMATION = "animation"
    ILLUSTRATION = "illustration"


class AgeGroup(StrEnum):
    AGE_5_9 = "5-9"
    AGE_10_14 = "10-14"


class Language(StrEnum):
    ENGLISH = "english"


DEFAULT_GENRES: tuple[str, ...] = (
    "fantasy",
    "educational",
    "moral",
    "adventure",
    "comedy",
    "bedtime",
)
