from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
import os

Base = declarative_base()
DATABASE_URI = (
    "mssql+pyodbc://sa:DevTeam%4012345@localhost/KotuBriefBackend?"
    "driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no&TrustServerCertificate=yes"
)

# DATABASE_URI = r"mssql+pyodbc://sa:habibfarooq12345@DESKTOP-8TUN3M3\SQLEXPRESS/KotuBrief?driver=ODBC+Driver+17+for+SQL+Server"

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

