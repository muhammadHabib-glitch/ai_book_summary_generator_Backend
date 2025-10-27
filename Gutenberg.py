import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base

# --- SQLAlchemy Base setup ---
Base = declarative_base()


class Book(Base):
    __tablename__ = 'Books'
    book_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
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
engine = create_engine(DATABASE_URI, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

# --- Load data from JSON file ---
json_file = 'gutenberg_books.json'
with open(json_file, 'r', encoding='utf-8') as f:
    books = json.load(f)

total_books = len(books)
print(f"📘 Total books to insert: {total_books}")

# --- Insert data into the database in batches ---
BATCH_SIZE = 100
batch = []

for index, book_data in enumerate(books, start=1):
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
        batch.append(new_book)

        # Commit every 100 records
        if len(batch) >= BATCH_SIZE:
            session.add_all(batch)
            session.commit()
            progress = (index / total_books) * 100
            print(f"✅ Inserted batch up to record {index} ({progress:.2f}% done)")
            batch.clear()

    except Exception as e:
        session.rollback()
        print(f"⚠️ Error adding {book_data.get('Book Name')}: {e}")

# --- Insert remaining records ---
if batch:
    try:
        session.add_all(batch)
        session.commit()
        progress = (total_books / total_books) * 100
        print(f"✅ Final batch inserted ({progress:.2f}% done)")
    except Exception as e:
        session.rollback()
        print("❌ Failed to insert final batch:", e)

session.close()
print("🎉 All books inserted successfully in batches!")
