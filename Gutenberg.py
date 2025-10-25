import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base

# --- SQLAlchemy Base setup ---
Base = declarative_base()


class Book(Base):
    __tablename__ = 'Books'
    book_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)   # 👈 This allows NULL
    title = Column(String(255))
    author = Column(String(255))
    cover_image_url = Column(String(500))
    main_category = Column(String(100))
    sub_category = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    description = Column(Text, nullable=True)

# --- Database connection ---
DATABASE_URI = (
    "mssql+pyodbc://sa:DevTeam%4012345@localhost/KotuBriefBackend?"
    "driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no&TrustServerCertificate=yes"
)
engine = create_engine(DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

# --- Load data from JSON file ---
json_file = 'gutenberg_books.json'
with open(json_file, 'r', encoding='utf-8') as f:
    books = json.load(f)

# --- Insert data into the database ---
for book_data in books:
    try:
        new_book = Book(
            user_id=None,
            title=book_data.get("Book Name"),
            author=book_data.get("Author Name"),
            cover_image_url=book_data.get("Image URL"),
            main_category=book_data.get("Category"),
            sub_category=book_data.get("Sub Category"),
            created_at=datetime.now(),
            description=None
        )
        session.add(new_book)
    except Exception as e:
        print(f"⚠️ Error adding {book_data.get('Book Name')}: {e}")

# --- Commit all inserts ---
try:
    session.commit()
    print("✅ All books inserted successfully!")
except Exception as e:
    session.rollback()
    print("❌ Failed to insert books:", e)
finally:
    session.close()
