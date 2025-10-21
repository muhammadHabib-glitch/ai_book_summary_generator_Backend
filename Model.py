from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from datetime import datetime
from Config import Base, engine

# -------------------- Users --------------------
class Users(Base):
    __tablename__ = "Users"
    user_id         = Column(Integer, primary_key=True, autoincrement=True)
    full_name       = Column(String(100), nullable=False)
    email           = Column(String(255), unique=True, nullable=False)
    password_hash   = Column(String(255), nullable=False)
    plan            = Column(String(20), nullable=False, default="Demo")
    email_confirmed = Column('EmailConfirmed', Boolean, nullable=False, default=False)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow)
    # OTP fields (single-table)
    otp_hash        = Column('OTPHash', String(64))       # sha256 hex
    otp_expires_at  = Column('OTPExpiresAt', DateTime)
    otp_attempts    = Column('OTPAttempts', Integer, nullable=False, default=0)
    profile_image = Column(String, nullable=True)

# -------------------- Auth OTP --------------------
class AuthOTP(Base):
    __tablename__ = "Auth_OTP"

    otp_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    otp_code = Column(String(10), nullable=False)
    is_verified = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)

# -------------------- Books --------------------
class Books(Base):
    __tablename__ = "Books"

    book_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255))
    cover_image_url = Column(String(500))
    main_category = Column(String(100))
    sub_category = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)  #

# -------------------- Summaries --------------------
class Summaries(Base):
    __tablename__ = "Summaries"

    summary_id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("Books.book_id"))
    summary_type = Column(String(10), nullable=False)  # 1min, 10min, 30min
    content = Column(Text, nullable=False)
    audio_url = Column(String(500))

# -------------------- Audio Uploads --------------------
class AudioUploads(Base):
    __tablename__ = "AudioUploads"

    audio_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    file_url = Column(String(500), nullable=False)
    transcript = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# -------------------- Questions (Chat History) --------------------
class Questions(Base):
    __tablename__ = "Questions"

    question_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    book_id = Column(Integer, ForeignKey("Books.book_id"), nullable=True)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# -------------------- Library (Favorites) --------------------
class Library(Base):
    __tablename__ = "Library"

    library_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    book_id = Column(Integer, ForeignKey("Books.book_id"))
    created_at = Column(DateTime, default=datetime.utcnow)

# -------------------- Notifications --------------------
class Notifications(Base):
    __tablename__ = "Notifications"

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PendingUsers(Base):
    __tablename__ = "PendingUsers"
    id = Column(String(36), primary_key=True)  # uuid string
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    confirm_token = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # optional


# -------------------- Create all tables --------------------
Base.metadata.create_all(bind=engine)
