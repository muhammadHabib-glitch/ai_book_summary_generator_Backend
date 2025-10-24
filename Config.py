
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
import os

Base = declarative_base()



DATABASE_URI = (
    "mssql+pyodbc://sa:DevTeam%4012345@localhost/KotuBriefBackend?"
    "driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no&TrustServerCertificate=yes"
)

engine = create_engine(DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)

# config.py
UPLOAD_FOLDER = "uploads/profile_images"
UPLOAD_FOLDER = "uploads/profile_images"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Upload folder
UPLOADFOLDER = 'uploads/BookImage'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)



MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 'kotubriefapp@gmail.com'        # must match sender
MAIL_PASSWORD = 'vstpbouwbnacdwem'               # the 16-char App Password
MAIL_DEFAULT_SENDER = ('KotuBrief', MAIL_USERNAME)



JWT_SECRET = os.environ.get("JWT_SECRET", "change-this-in-production")
JWT_ALGO = "HS256"
JWT_EXPIRES_MIN = 60  # token lifetime
# add a flag
DEV_BYPASS_AUTH = True






# from dotenv import load_dotenv, find_dotenv
# from sqlalchemy.orm import declarative_base, sessionmaker
# from sqlalchemy import create_engine
# import os

# # ✅ Explicitly locate and load your .env file
# env_path = find_dotenv()
# print(f"🧩 Loading .env from: {env_path}")
# load_dotenv(env_path)
#
# Base = declarative_base()
#
# # ✅ Fetch DATABASE_URL from environment
# DATABASE_URL = os.getenv("DATABASE_URL")
#
# if not DATABASE_URL or DATABASE_URL.strip() == "":
#     raise ValueError("❌ DATABASE_URL environment variable is missing or empty!")
#
# # ✅ Convert old-style 'postgres://' to 'postgresql://'
# if DATABASE_URL.startswith("postgres://"):
#     DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
#
# print(f"🔗 Using DATABASE_URL: {DATABASE_URL}")
#
# # ✅ Create SQLAlchemy engine
# try:
#     engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
# except Exception as e:
#     raise ValueError(f"❌ Could not create SQLAlchemy engine. Error: {str(e)}")
#
# Session = sessionmaker(bind=engine)
# # ✅ Auto-create tables on startup
# from Model import *   # Import all your SQLAlchemy models here
# Base.metadata.create_all(engine)
#
#
# -----------------------------------------------------------------------
# from sqlalchemy.orm import declarative_base, sessionmaker
# from sqlalchemy import create_engine
# import os
#
# Base = declarative_base()
#
# # Get the database URL from Railway environment variable
# DATABASE_URL = os.getenv("DATABASE_URL")
#
# # Create engine and session
# engine = create_engine(DATABASE_URL, echo=True)
# Session = sessionmaker(bind=engine)
#
# # Upload folder setup (unchanged)
# UPLOAD_FOLDER = "uploads/profile_images"
# ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
#
# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)
#
# # Mail settings (unchanged)
# MAIL_SERVER = 'smtp.gmail.com'
# MAIL_PORT = 587
# MAIL_USE_TLS = True
# MAIL_USE_SSL = False
# MAIL_USERNAME = 'kotubriefapp@gmail.com'
# MAIL_PASSWORD = 'vstpbouwbnacdwem'
# MAIL_DEFAULT_SENDER = ('KotuBrief', MAIL_USERNAME)
#
# JWT_SECRET = os.environ.get("JWT_SECRET", "change-this-in-production")
# JWT_ALGO = "HS256"
# JWT_EXPIRES_MIN = 60
# DEV_BYPASS_AUTH = True
#
# ---------------------------------------------------------------------------