import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load .env only for local development
load_dotenv()

# ------------------------------
# DATABASE_URL (NO localhost fallback)
# ------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL is not set")

# ------------------------------
# SQLAlchemy Engine & Session
# ------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # prevents stale connections on Render
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
