import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Ensure /tmp exists (writable on Render)
os.makedirs("/tmp", exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/app.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
