import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# ------------------------------
# Ensure /tmp exists (optional for Render)
# ------------------------------
os.makedirs("/tmp", exist_ok=True)

# ------------------------------
# DATABASE_URL from environment
# Example for Render Postgres:
# postgres://username:password@host:port/dbname
# ------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/mydb"  # fallback local
)

# ------------------------------
# SQLAlchemy Engine & Session
# ------------------------------
engine = create_engine(DATABASE_URL, echo=True)  # echo=True logs SQL for debug
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
