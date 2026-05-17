"""Sync personalized flag on book_categories from books table.

Any category that has at least one book with is_personalized=true should
itself be marked personalized=true.  This corrects categories that were
created with the default (false) even though they hold personalized books.

Revision ID: 20260517_0002_fix_personalized_flag_on_book_categories
Revises: 20260517_0001_drop_book_tag_from_books
Create Date: 2026-05-17
"""

from typing import Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260517_0002_fix_personalized_flag_on_book_categories"
down_revision: Union[str, None] = "20260517_0001_drop_book_tag_from_books"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Mark a category as personalized=true when it owns at least one
    # book whose book_type option value contains 'personal'.
    op.execute(
        """
        UPDATE book_categories bc
        SET    personalized = true
        WHERE  EXISTS (
                   SELECT 1
                   FROM   books b
                   JOIN   book_attribute_options bao
                          ON bao.id = b.book_type_id
                   WHERE  b.category_id = bc.category_id
                     AND  bao.option_type = 'book_type'
                     AND  lower(bao.value) LIKE '%personal%'
               )
        """
    )

    # Fallback: if a book has is_personalized=true but its book_type_id is
    # NULL, also promote the parent category.
    op.execute(
        """
        UPDATE book_categories bc
        SET    personalized = true
        WHERE  EXISTS (
                   SELECT 1
                   FROM   books b
                   WHERE  b.category_id = bc.category_id
                     AND  b.is_personalized = true
               )
        """
    )


def downgrade() -> None:
    # Reverting is not safe because we cannot distinguish categories that
    # were already personalized=true before this migration.
    pass
