# Script to update category_type values in the database
# Usage: Run with your backend venv active: python scripts/update_category_types.py

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.book_category import BookCategory

def update_category_types():
    session: Session = SessionLocal()
    try:
        # Update 'story' to 'personalized_story'
        session.query(BookCategory).filter(BookCategory.category_type == 'story').update({BookCategory.category_type: 'personalized_story'})
        # Update 'coloring' to 'personalized_coloring'
        session.query(BookCategory).filter(BookCategory.category_type == 'coloring').update({BookCategory.category_type: 'personalized_coloring'})
        session.commit()
        print('Category types updated successfully.')
    except Exception as e:
        session.rollback()
        print('Error updating category types:', e)
    finally:
        session.close()

if __name__ == '__main__':
    update_category_types()
